import os
import time
import logging
import json
import re

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, flash, current_app
)
from flask_login import (
    login_user, login_required,
    logout_user, current_user
)
from .models import (
    db,
    User,
    ResumeAnalysis,
    UserPreference,
)
from .utils import process_resume_file, fetch_jobs_from_adzuna, rank_jobs_by_similarity
import re

import re
from typing import Optional

# Pre-compile the pattern (VERBOSE mode for readability)
import re
from typing import Optional

# Regex pattern to match various experience formats
_EXPERIENCE_PATTERN = re.compile(r"""
    # 1) Dash or en-dash ranges: "2-5 years" or "three-five yrs"
    (?:(?P<min1>\d+)|(?P<min1_word>one|two|three|four|five|six|seven|eight|nine|ten))\s*[–-]\s*(?:(?P<max1>\d+)|(?P<max1_word>one|two|three|four|five|six|seven|eight|nine|ten))\s*(?:years?|yrs?)\b
  | # 2) "to" ranges: "2 to 5 years" or "three to five yrs"
    (?:(?P<min2>\d+)|(?P<min2_word>one|two|three|four|five|six|seven|eight|nine|ten))\s+to\s+(?:(?P<max2>\d+)|(?P<max2_word>one|two|three|four|five|six|seven|eight|nine|ten))\s*(?:years?|yrs?)\b
  | # 3) Plus notation: "3+ years" or "three plus yrs"
    (?:(?P<min3>\d+)|(?P<min3_word>one|two|three|four|five|six|seven|eight|nine|ten))\s*(?:\+|plus)\s*(?:years?|yrs?)\b
  | # 4) "at least" / "minimum": "at least 4 years" or "minimum three yrs"
    (?:at\s*least|atleast|minimum)\b.*?(?:(?P<min4>\d+)|(?P<min4_word>one|two|three|four|five|six|seven|eight|nine|ten))\s*(?:years?|yrs?)\b
  | # 5) Fallback single number: "5 years" or "five yrs"
    (?:(?P<min5>\d+)|(?P<min5_word>one|two|three|four|five|six|seven|eight|nine|ten))\s*(?:years?|yrs?)\b
""", re.IGNORECASE | re.VERBOSE)

# Mapping of number words to their numeric values
_NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
}

def _word_to_number(word: Optional[str]) -> float:
    """Convert a number word to its numeric value (e.g., 'three' -> 3.0)."""
    if not word:
        return 0.0
    return float(_NUMBER_WORDS.get(word.lower(), 0))

def extract_required_experience(text: str) -> float:
    """
    Extract the minimum required experience in years from a job description snippet.
    Supports patterns like:
      - "3+ years", "2-5 yrs", "five years", "at least three years"
    Returns the lowest bound as a float.
    If nothing matches, uses fallback logic to check for fresher-friendly phrases or presence of 'experience'.
    """
    if not text:
        return 0.0

    match = _EXPERIENCE_PATTERN.search(text)
    if match:
        for group_prefix in ['min1', 'min2', 'min3', 'min4', 'min5']:
            if match.group(group_prefix):
                return float(match.group(group_prefix))
            word_value = _word_to_number(match.group(f"{group_prefix}_word"))
            if word_value > 0:
                return word_value

    # Lowercase the text for easier keyword matching
    text_lower = text.lower()

    # Keywords that imply no experience is required
    no_exp_keywords = [
        "no experience", "fresher", "entry level", "training provided",
        "on the job training", "gain experience", "will be trained", "learn"
    ]

    if any(phrase in text_lower for phrase in no_exp_keywords):
        return 0.0

    # If "experience" is mentioned in any form, assume minimal requirement (1 year)
    if "experience" in text_lower or 'exp' in text_lower:
        return 1.0

    return 0.0


# — Configure file‐based logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filename="app.log"
)
logger = logging.getLogger(__name__)

routes_bp = Blueprint("routes", __name__)

BASE_DIR      = os.path.dirname(__file__)
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXT   = {"pdf"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT
    )




@routes_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            email=request.form["email"]
        ).first()

        if user and user.check_password(request.form["password"]):
            login_user(user)
            flash("Login successful", "success")
            return redirect(url_for("routes.dashboard"))

        flash("Invalid credentials", "error")

    return render_template("index.html")


@routes_bp.route("/signup", methods=["POST"])
def signup():
    pw  = request.form["password"]
    cpw = request.form["confirm_password"]

    if pw != cpw:
        flash("Passwords must match", "error")
        return redirect(url_for("routes.login"))

    if User.query.filter_by(
        email=request.form["email"]
    ).first():
        flash("Email already exists", "error")
        return redirect(url_for("routes.login"))

    u = User(email=request.form["email"])
    u.set_password(pw)
    db.session.add(u)
    db.session.commit()

    flash("Registered — please log in", "success")
    return redirect(url_for("routes.login"))


@routes_bp.route("/dashboard")
@login_required
def dashboard():
    analysis = ResumeAnalysis.query.filter_by(
        user_id=current_user.id
    ).first()

    return render_template(
        "dashboard.html",
        details=analysis.to_dict() if analysis else None
    )


@routes_bp.route("/upload_resume", methods=["POST"])
@login_required
def upload_resume():
    f = request.files.get("resume")
    if not f or not allowed_file(f.filename):
        flash("Please upload a PDF file.", "error")
        return redirect(url_for("routes.dashboard"))

    # Save PDF locally
    filename = f"{int(time.time())}_{current_user.id}.pdf"
    path     = os.path.join(UPLOAD_FOLDER, filename)
    f.save(path)

    # Analyze via DeepSeek
    result = process_resume_file(path)

    # Remove old analysis & store new
    ResumeAnalysis.query.filter_by(
        user_id=current_user.id
    ).delete()

    ra = ResumeAnalysis(
        user_id=current_user.id,
        skills=json.dumps(result["skills"]),
        projects=json.dumps(result["projects"]),
        experience=json.dumps(result["experience"]),
        experience_years=result["experience_years"],
        suggested_roles=json.dumps(result["roles"])
    )

    current_user.resume_filename = filename
    db.session.add(ra)
    db.session.commit()

    flash("Resume uploaded and analyzed successfully!", "success")
    return redirect(url_for("routes.dashboard"))


@routes_bp.route("/delete_resume", methods=["POST"])
@login_required
def delete_resume():
    # Remove file + analysis + preferences
    if current_user.resume_filename:
        try:
            os.remove(
                os.path.join(
                    UPLOAD_FOLDER,
                    current_user.resume_filename
                )
            )
        except OSError:
            pass

        ResumeAnalysis.query.filter_by(
            user_id=current_user.id
        ).delete()

        UserPreference.query.filter_by(
            user_id=current_user.id
        ).delete()

        current_user.resume_filename = ""
        db.session.commit()

        flash("Resume, analysis, and preferences cleared.", "success")

    return redirect(url_for("routes.dashboard"))


@routes_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("routes.login"))


@routes_bp.route("/get-jobs", methods=["GET"])
@login_required
def get_jobs():
    analysis = ResumeAnalysis.query.filter_by(user_id=current_user.id).first()

    if not analysis:
        flash("Upload & analyze your resume first.", "error")
        return redirect(url_for("routes.dashboard"))

    data_path = os.path.join(current_app.root_path, "static", "data", "cities.json")
    with open(data_path, "r") as f:
        cities_data = json.load(f)

    exp_years = analysis.experience_years or 0.0
    if exp_years < 2:
        flash(
            f"We detected only {exp_years:.1f} years of experience. "
            "Sorry, we currently support users with at least 2 years of experience.",
            "warning"
        )
        return redirect(url_for("routes.dashboard"))

    # 🚀 Flash the loading message here
    flash("Please wait while we fetch the perfect jobs for you...", "info")

    return render_template("get_jobs.html", cities_data=cities_data)



@routes_bp.route("/submit-preferences", methods=["POST"])
@login_required
def submit_preferences():
    is_remote = "remote" in request.form
    country   = request.form["country"]
    city      = request.form.get("city") or None

    pref = UserPreference.query.filter_by(
        user_id=current_user.id
    ).first()

    if not pref:
        pref = UserPreference(user_id=current_user.id)

    pref.is_remote = is_remote
    pref.country   = country
    pref.city      = city

    db.session.add(pref)
    db.session.commit()
    '''exp_years = analysis.experience_years or 0.0
    if exp_years < 4:
        # If less than 4, block the job‐search flow
        flash(
            f"We detected only {exp_years:.1f} years of experience. "
            "Sorry, we currently support users with at least 4 years of experience.",
            "warning"
        )'''


    return redirect(url_for("routes.fetch_jobs"))


@routes_bp.route("/fetch_jobs", methods=["GET"])
@login_required
def fetch_jobs():
    # 1) Load analysis & preferences
    analysis = ResumeAnalysis.query.filter_by(user_id=current_user.id).first()
    preferences = UserPreference.query.filter_by(user_id=current_user.id).first()

    if not analysis or not preferences:
        flash("Missing analysis or preferences.", "error")
        return redirect(url_for("routes.dashboard"))

    candidate_exp = analysis.experience_years or 0.0
    roles = json.loads(analysis.suggested_roles)
    country = preferences.country
    city = preferences.city
    remote = preferences.is_remote

    # 2) Fetch raw jobs from Adzuna (all jobs)
    raw_jobs = []
    for role in roles:
        raw_jobs.extend(
            fetch_jobs_from_adzuna(
                role=role,
                country=country,
                city=city if city else None,
                is_remote=remote,
                max_results=1000
            )
        )

    # 3) De-duplicate by job["id"]
    unique = {}
    for job in raw_jobs:
        job_id = job.get("id")
        if job_id and job_id not in unique:
            unique[job_id] = job
    deduped = list(unique.values())

    # 4) Filter out listings requiring more experience
    valid_jobs = []
    for job in deduped:
        desc = job.get("description", "") or job.get("snippet", "")
        desc_lower = desc.lower()
        req_exp = extract_required_experience(desc)

        # 🔍 Skip if vague "experience" mentioned with no extractable value
        if "experience" in desc_lower and req_exp == 1.0:
            continue

        if candidate_exp >= req_exp:
            valid_jobs.append(job)

    # 4.5) Remove roles not matching candidate experience level
    senior_keywords = ["senior", "sr", "lead", "manager", "principal", "architect", "head", "director", "vp", "executive"]
    junior_keywords = ["junior", "jr", "intern", "fresher", "graduate", "entry-level", "entry level", "associate"]

    senior_pattern = re.compile(r'\b(' + '|'.join(senior_keywords) + r')\b', re.IGNORECASE)
    junior_pattern = re.compile(r'\b(' + '|'.join(junior_keywords) + r')\b', re.IGNORECASE)

    filtered_jobs = []
    for job in valid_jobs:
        title = job.get("title") or ""
        title_lower = title.lower()

        if candidate_exp < 3:
            if not senior_pattern.search(title_lower):
                filtered_jobs.append(job)
        elif candidate_exp >= 4:
            if not junior_pattern.search(title_lower):
                filtered_jobs.append(job)
        else:
            filtered_jobs.append(job)  # Mid-level

    valid_jobs = filtered_jobs

    # 5) Apply ML ranking algorithm
    ranked_jobs = rank_jobs_by_similarity(
        resume_skills=analysis.skills,
        resume_projects=json.loads(analysis.projects),
        resume_experience=json.loads(analysis.experience),
        jobs=valid_jobs,
        top_k=len(valid_jobs)
    )

    # 6) Sort by match score
    ranked_sorted = sorted(ranked_jobs, key=lambda job: job['match_score'], reverse=True)

    # 7) Top 100
    top_100_jobs = ranked_sorted[:100]

    # 8) Flash message
    flash(f"{len(valid_jobs)} valid jobs found after filtering by experience.", "info")

    # 9) Render page
    return render_template("jobs_raw.html", jobs=top_100_jobs)





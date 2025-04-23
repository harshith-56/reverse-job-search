import json
import os
import logging
import requests
import fitz
from time import sleep
from pathlib import Path
from typing import Dict

# — configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filename="resume_parser.log",
)
logger = logging.getLogger(__name__)

# — your DeepSeek keys and endpoint
DEEPSEEK_KEYS = [
    "deepseek_key_1",
    "deepseek_key_2",
]
API_URL     = "https://api.deepseek.com/v1/chat/completions"
MAX_RETRIES = 3
RETRY_DELAY = 2

class PDFError(Exception):
    pass

def pdf_to_text(pdf_path: str) -> str:
    """Extract text from a PDF using PyMuPDF."""
    if not Path(pdf_path).exists():
        raise PDFError(f"File not found: {pdf_path}")

    text_chunks = []
    try:
        doc = fitz.open(pdf_path)
        for page in doc:
            text_chunks.append(page.get_text())
        doc.close()

    except Exception as e:
        raise PDFError(f"Error reading PDF: {e}")

    full = "\n".join(text_chunks).strip()
    if not full:
        raise PDFError("Extracted text is empty.")
    logger.info(f"[PDF → text] {len(full)} chars")
    return full

def analyze_with_deepseek(resume_text: str) -> Dict:
    """
    Calls DeepSeek’s chat endpoint with your prompt, rotates keys on error,
    and returns a dict containing:
      { skills, projects, experience, experience_years, suggested_roles }
    """
    PROMPT = (
    "You are an expert AI resume parser and career advisor.\n\n"

    "Your task is to analyze the provided resume text and extract the following fields with precision:\n\n"

    "1. skills: A comma-separated string listing only the technical skills the candidate possesses.\n"
    "   - Include programming languages, libraries, frameworks, tools, platforms, databases, or software.\n"
    "   - Exclude soft skills, team activities, or general traits like leadership or communication.\n\n"

    "2. projects: An array of strings, each describing one project from the resume.\n"
    "   - Include only personal, academic, or professional projects clearly mentioned.\n"
    "   - Use concise one-line titles or summaries for each project.\n\n"

    "3. experience: An array of strings, each describing professional work done at a company or organization.\n"
    "   - Include only real work experiences like internships, jobs, or freelance gigs.\n"
    "   - Do NOT include college club roles, coursework, certifications, or participation in competitions.\n"
    "   - Each entry should mention company name, role, and a short summary.\n\n"

    "4. experience_years: A number estimating the total years of professional experience (from internships or jobs only).\n"
    "   - If the candidate has no formal experience, return 0.\n\n"

    "5. suggested_roles: An array of 3 specific job roles that best match the candidate’s technical skills.\n"
    "   - These roles must be based only on technical skills — NOT generic roles like 'Software Engineer', 'Backend Engineer', 'Full Stack Developer', or 'Frontend Engineer'.\n"
    "   - Examples of valid roles: 'Python Developer', 'Java Developer', 'Machine Learning Engineer', 'React Developer', 'DevOps Engineer', 'Cloud Engineer', 'AI Engineer', etc.\n"
    "   - Do not repeat similar titles (e.g., avoid suggesting both 'Python Developer' and 'Backend Python Developer').\n\n"

    "⛔ Strict Rules:\n"
    "- Output must be a valid JSON dictionary only. No extra text, explanations, or formatting.\n"
    "- If a field (like projects or experience) is not found in the resume, return an empty array [].\n"
    "- If skills are not found, return an empty string.\n"
    "- Do not omit any keys.\n"
    "- Follow JSON syntax strictly: double quotes only.\n\n"

    "✅ Output format:\n"
    "{\n"
    '  "skills": "skill1, skill2, skill3",\n'
    '  "projects": ["project 1", "project 2"],\n'
    '  "experience": ["experience 1", "experience 2"],\n'
    '  "experience_years": 1,\n'
    '  "suggested_roles": ["Python Developer", "Machine Learning Engineer"]\n'
    "}"
    )

    headers = { "Content-Type": "application/json" }
    last_err = None
    required_keys = {"skills", "projects", "experience", "experience_years", "suggested_roles"}

    for key in DEEPSEEK_KEYS:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                headers["Authorization"] = f"Bearer {key}"
                payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        { "role": "system", "content": PROMPT },
                        { "role": "user",   "content": resume_text }
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1500,
                    "response_format": { "type": "json_object" }
                }

                logger.info(f"[DeepSeek] key={key[:4]} attempt={attempt}")
                resp = requests.post(API_URL, headers=headers, json=payload, timeout=30)

                if resp.status_code == 429:
                    delay = RETRY_DELAY * attempt
                    logger.warning(f"Rate limited → sleeping {delay}s")
                    sleep(delay)
                    continue

                resp.raise_for_status()
                data = resp.json()
                raw  = data["choices"][0]["message"]["content"]
                logger.debug(f"[DeepSeek raw] {raw}")

                parsed = json.loads(raw)

                if not required_keys.issubset(parsed):
                    raise ValueError(f"Missing one of required keys → found: {list(parsed.keys())}")

                return {
                    "skills"          : parsed["skills"],
                    "projects"        : parsed["projects"],
                    "experience"      : parsed["experience"],
                    "experience_years": parsed["experience_years"],
                    "roles"           : parsed["suggested_roles"],
                }

            except Exception as e:
                last_err = str(e)
                logger.error(f"[DeepSeek error] {e}")
                sleep(RETRY_DELAY)

    logger.critical(f"All DeepSeek calls failed: {last_err}")
    return {
        "skills"          : "",
        "projects"        : [],
        "experience"      : [],
        "experience_years": 0.0,
        "roles"           : []
    }

def process_resume_file(pdf_path: str) -> Dict:
    """
    Full pipeline: extract text, call DeepSeek, return dict plus
    a processing_status flag.
    """
    try:
        text = pdf_to_text(pdf_path)
        logger.info(f"[RESUME TEXT]\n{text[:200]}...")
        result = analyze_with_deepseek(text)
        return { **result, "processing_status": "success" }

    except Exception as e:
        logger.error(f"process_resume_file failed: {e}")
        return {
            "skills"          : "",
            "projects"        : [],
            "experience"      : [],
            "experience_years": 0.0,
            "roles"           : [],
            "processing_status": "failed",
            "error_message"    : str(e)
        }


from .models import UserPreference, ResumeAnalysis
import requests
import logging
from flask_login import current_user

# Your Adzuna API keys
adzuna_keys = [
    {"app_id": "app_id1", "app_key": "key1"},
    {"app_id": "app_id2", "app_key": "key2"},
    'enter all your api keys here'

]

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)

def fetch_jobs_from_adzuna(role, country, city=None, is_remote=False, max_results=100):
    # Convert country code to lowercase (e.g., "US" → "us")
    country_code = country.lower()  # Adzuna requires lowercase country codes

    all_jobs = []
    page = 1
    used_keys = 0

    # Log job search parameters
    logger.info(f"Starting job search for role: {role}, country: {country_code}, city: {city}, remote: {is_remote}")

    while len(all_jobs) < max_results and used_keys < len(adzuna_keys):
        key = adzuna_keys[used_keys]

        while len(all_jobs) < max_results:
            url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/{page}"
            params = {
                "app_id": key["app_id"],
                "app_key": key["app_key"],
                "results_per_page": 20,
                "what": role,
                "content-type": "application/json",
            }

            # Only pass city if it's not a remote job
            if not is_remote and city:
                params["where"] = city  # Adzuna automatically URL-encodes spaces

            if is_remote:
                params["remote"] = 1  # Correct parameter for remote jobs

            try:
                logger.info(f"Request URL: {url} with params {params}")
                res = requests.get(url, params=params)
                logger.info(f"Response Status Code: {res.status_code}")

                if res.status_code != 200:
                    logger.warning(f"API failed with key {used_keys}, status code: {res.status_code}. Response: {res.text}")
                    break

                data = res.json()

                # Log full API response for debugging
                logger.info(f"Response Data: {data}")

                results = data.get("results", [])
                if not results:
                    logger.warning("No results found.")
                    break

                all_jobs.extend(results)
                page += 1

            except Exception as e:
                logger.error(f"Exception during API call: {e}")
                break

        used_keys += 1

    logger.info(f"Job search complete. Found {len(all_jobs)} jobs for role: {role}")
    return all_jobs[:max_results]



from sentence_transformers import SentenceTransformer
import numpy as np

# Load once at import time (singleton)
_model = SentenceTransformer("sentence-transformers/msmarco-MiniLM-L6-cos-v5")

def rank_jobs_by_similarity(
    resume_skills: str,
    resume_projects: list,
    resume_experience: list,
    jobs: list,
    top_k: int = 20
) -> list:
    """
    Given resume fields and a list of job dicts, compute a similarity score
    for each job and return the top_k jobs sorted by descending score.
    
    - resume_skills: comma-separated string
    - resume_projects/experience: lists of strings
    - jobs: list of dicts, each must have a 'description' or 'title' key
    - top_k: return at most this many jobs
    """
    # 1) Prepare resume text  
    resume_text = "\n".join([
        resume_skills,
        *resume_projects,
        *resume_experience
    ])
    
    # 2) Collect job texts
    job_texts = []
    for job in jobs:
        # prefer full description if available, else title
        text = job.get("description") or job.get("title", "")
        job_texts.append(text)
    
    # 3) Embed all texts in a single batch
    embeddings = _model.encode(
        [resume_text, *job_texts],
        convert_to_tensor=False,
        normalize_embeddings=True
    )
    resume_emb, job_embs = embeddings[0], embeddings[1:]
    
    # 4) Compute cosine similarities
    # cos_sim = resume_emb · job_emb / (||resume_emb|| * ||job_emb||)
    # since we normalized embeddings, dot product = cosine similarity
    scores = np.dot(job_embs, resume_emb)
    
    # 5) Sort by score descending
    idx_sorted = np.argsort(-scores)
    
    top_jobs = []
    for idx in idx_sorted[:top_k]:
        job = jobs[idx].copy()
        job["match_score"] = float(scores[idx])  # attach score
        top_jobs.append(job)
    
    return top_jobs

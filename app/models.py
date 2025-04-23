from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
import json

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    resume_filename = db.Column(db.String(300), default="", nullable=False)

    resume_analysis = db.relationship(
        "ResumeAnalysis",
        backref="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def set_password(self, pwd):
        self.password = bcrypt.generate_password_hash(pwd).decode("utf-8")

    def check_password(self, pwd):
        return bcrypt.check_password_hash(self.password, pwd)

class ResumeAnalysis(db.Model):
    __tablename__ = "resume_analysis"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    skills = db.Column(db.Text, nullable=False, default="[]")
    projects = db.Column(db.Text, nullable=False, default="[]")
    experience = db.Column(db.Text, nullable=False, default="[]")
    experience_years = db.Column(db.Float, nullable=False, default=0.0)
    suggested_roles = db.Column(db.Text, nullable=False, default="[]")
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

    def to_dict(self):
        return {
            "skills": json.loads(self.skills),
            "projects": json.loads(self.projects),
            "experience": json.loads(self.experience),
            "experience_years": self.experience_years,
            "roles": json.loads(self.suggested_roles),
        }
class UserPreference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    country = db.Column(db.String(100))
    city = db.Column(db.String(100))
    is_remote = db.Column(db.Boolean, default=False)
    job_results = db.Column(db.Text)  # Store job JSON as a string if needed
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    user = db.relationship('User', backref=db.backref('preference', uselist=False))

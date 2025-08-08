#Reverse Job Search
Reverse Job Search is an AI-powered career platform that simplifies and automates the job discovery process. Instead of users searching through hundreds of job listings, the system analyzes uploaded resumes and intelligently recommends the most relevant job opportunities using machine learning and semantic similarity.

#Project Overview
This platform transforms traditional job search by using AI to:

Parse resumes and extract candidate information

Suggest suitable roles based on skills and experience

Fetch real-time job listings from the Adzuna API

Rank jobs using semantic similarity to recommend the best matches

It is built using Python (Flask), integrated with OpenAI's DeepSeek API, HuggingFace transformer models, and Adzuna's job search API.

Key Features
AI Resume Analysis: Extracts skills, experience, projects, and suggests relevant job roles using DeepSeek API.

Semantic Job Ranking: Matches resumes to job descriptions using sentence-transformers models.

Real-time Job Fetching: Pulls jobs dynamically based on user preferences and role suggestions.

User Preference Management: Allows users to set preferred city, country, and (optional) remote preferences.

Secure User Authentication: Built with Flask-Login and SQLAlchemy ORM.

Paginated UI: Displays job results in a clean, responsive, paginated card-based interface.

Modular Architecture: Components like resume analysis, job fetching, and ranking are loosely coupled for scalability.

Technologies Used
Backend

Python 3.8+

Flask Framework

SQLAlchemy ORM

SQLite (development database)

OpenAI API (for DeepSeek resume analysis)

HuggingFace sentence-transformers (msmarco-MiniLM-L6-cos-v5)

Frontend

HTML5, CSS3, JavaScript

Responsive dashboard and job cards

APIs

Adzuna Job Search API

DeepSeek via OpenAI API interface

Workflow
User registers and uploads a resume (PDF or DOCX).

Resume is parsed using the DeepSeek API to extract skills, experience, projects, and suggested job roles.

Based on these roles and preferences, jobs are fetched from Adzuna.

The MSMARCO MiniLM model calculates semantic similarity between the resume and each job description.

Top 100 job matches are stored in the database and displayed in the dashboard.

Modules
routes.py: Manages routes, views, and session handling

utils.py: Contains resume parsing, job fetching, AI ranking logic

models.py: SQLAlchemy models for users, resumes, jobs, and preferences

Requirements
Software

Python 3.8+

Flask

SQLAlchemy

sentence-transformers

requests

PyPDF2 / python-docx

Flask-Login

Hardware (Recommended)

8 GB RAM (16 GB for ML model speed)

5 GB free disk space

Stable internet for API access

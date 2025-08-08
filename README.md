# Reverse Job Search

Reverse Job Search is an AI-powered career matchmaking platform that automates and enhances the job discovery process. Instead of requiring users to search manually through job boards, the system intelligently analyzes uploaded resumes and recommends the most relevant job opportunities based on skills, experience, and preferences.

## Overview

This platform uses artificial intelligence and machine learning to:

- Parse resumes and extract structured candidate data
- Suggest job roles based on technical background and experience
- Fetch live job listings from the Adzuna API using suggested roles
- Rank jobs by semantic similarity between resume content and job descriptions

It is built using Python with the Flask framework and integrates AI capabilities through OpenAI’s DeepSeek API and HuggingFace transformer models.

## Key Features

- Resume analysis using AI to extract skills, experience, and projects
- Role suggestions based on the candidate's technical profile
- Real-time job fetching from Adzuna API
- Job ranking using sentence-transformer-based semantic similarity
- Location and experience-based filtering
- Secure authentication system with Flask-Login
- Clean, responsive UI with paginated job listings

## Technologies Used

- Python 3.8+
- Flask Framework
- SQLAlchemy ORM
- OpenAI API (DeepSeek)
- HuggingFace Transformers (msmarco-MiniLM-L6-cos-v5)
- HTML5, CSS3, JavaScript
- Adzuna Job Search API

## Setup Instructions

1. Prerequisites:  
   - Python 3.8 or higher  
   - Pip (Python package installer)  
   - Git (download and install from https://git-scm.com/)

2. Setup Steps (open command prompt or terminal on your system and run the commands given below):

   a. Clone the repository:  
   i. git init  
   ii. git clone https://github.com/harshith-56/reverse-job-search.git  
   iii. cd reverse-job-search  

   b. Create and activate virtual environment (recommended):  
   i. python -m venv venv  
   ii. source venv/bin/activate (On Windows: venv\Scripts\activate)  

   c. Install dependencies:  
   i. pip install -r requirements.txt  

## API Setup

This application uses Firebase and external APIs for backend services.

1. DeepSeek API:  
   - You must have 2 DeepSeek API keys.  
   - Open utils.py and replace placeholder keys with your real keys in the line:  
     api_keys = ["<YOUR_FIRST_KEY>", "<YOUR_SECOND_KEY>"]

2. Adzuna API:  
   - Sign up at https://developer.adzuna.com/  
   - Add your APP_ID and APP_KEY in utils.py.

3. Generate Service Account Credentials:  
   - Go to  Project Settings > Service Accounts  
   - Generate and download the private key JSON file  
   - Save it as serviceAccountKey.json in the project root directory (/reverse-job-search/serviceAccountKey.json)

4. Running the Application:  
   - Make sure the virtual environment is activated, then run:  
     python run.py  
   - The app will launch and be accessible at: http://127.0.0.1:5000/

## Future Scope

- Enable remote job filtering  
- Mobile application using Flutter or React Native  
- Email alerts for job recommendations  
- Resume builder with improvement suggestions  
- Application tracker and job history  
- Integration with LinkedIn and other platforms  
- AI-based skill gap analysis and interview preparation tools

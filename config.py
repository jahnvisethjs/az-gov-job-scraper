"""
Configuration file for Arizona city job sites and application settings.
"""
import os
from typing import List, Dict

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Rate Limiting (Gemini Free Tier)
GEMINI_RPM = 15  # Requests per minute
GEMINI_RPD = 1500  # Requests per day
GEMINI_TPD = 1_000_000  # Tokens per day

# Model Configuration
GEMINI_MODEL = "gemini-2.5-flash"  # Fixed: was "gemini-1.5-flash"
GEMINI_EMBEDDING_MODEL = "models/embedding-001"

# Arizona City Job Sites
ARIZONA_CITIES: List[Dict[str, str]] = [
    {
        "name": "City of Tempe",
        "url": "https://www.tempe.gov/government/human-resources/careers",
        "state": "enabled"
    },
    {
        "name": "City of Phoenix",
        "url": "https://www.phoenix.gov/administration/departments/hr/careers",
        "state": "enabled"
    },
    {
        "name": "City of Mesa",
        "url": "https://www.mesaaz.gov/government/human-resources/jobs",
        "state": "enabled"
    },
    {
        "name": "Apache Junction",
        "url": "https://www.apachejunctionaz.gov/818/Employment",
        "state": "enabled"
    },
    {
        "name": "City of Scottsdale",
        "url": "https://www.scottsdaleaz.gov/careers",
        "state": "enabled"
    },
    {
        "name": "Cottonwood",
        "url": "https://www.cottonwoodaz.gov/600/Employment-Opportunities",
        "state": "enabled"
    },
    {
        "name": "Pima County",
        "url": "https://www.pima.gov/987/Job-Openings-in-Pima-County",
        "state": "enabled"
    },
    {
        "name": "Buckeye",
        "url": "https://www.buckeyeaz.gov/government/human-resources/careers",
        "state": "enabled"
    },
    {
        "name": "Goodyear",
        "url": "https://www.goodyearaz.gov/government/departments/human-resources/careers",
        "state": "enabled"
    },
    {
        "name": "Snowflake",
        "url": "https://www.snowflakeaz.gov/town-hall/job-opportunities",
        "state": "enabled"
    },
    {
        "name": "City of Prescott",
        "url": "https://www.prescott-az.gov/human-resources/hr-careers",
        "state": "enabled"
    },
    {
        "name": "Flagstaff",
        "url": "https://www.flagstaff.az.gov/4887/Join-Team-Flagstaff",
        "state": "enabled"
    },
    {
        "name": "Nogales",
        "url": "https://www.nogalesaz.gov/jobs",
        "state": "enabled"
    },
    {
        "name": "El Mirage",
        "url": "https://www.elmirageaz.gov/220/Human-Resources",
        "state": "enabled"
    },
    {
        "name": "Avondale",
        "url": "https://www.avondaleaz.gov/government/departments/human-resources/careers",
        "state": "enabled"
    }
]

# Application Settings
SESSION_TIMEOUT_MINUTES = 60
MAX_RESUME_SIZE_MB = 5
SUPPORTED_RESUME_FORMATS = [".pdf", ".docx", ".txt"]

# Job Matching Settings
TOP_JOBS_TO_DISPLAY = 50
MIN_MATCH_SCORE_THRESHOLD = 40  # Only show jobs with 40%+ match

# RAG Settings
EMBEDDING_CHUNK_SIZE = 500
EMBEDDING_CHUNK_OVERLAP = 50
VECTOR_DB_PATH = "./chroma_db"

# UI Settings
MATCH_SCORE_COLORS = {
    "strong": "#4CAF50",  # Green (80%+)
    "good": "#FF9800",    # Orange (60-79%)
    "fair": "#F44336"     # Red (<60%)
}

AREAS_OF_INTEREST = [
    "Public Administration",
    "Engineering & Public Works",
    "Information Technology",
    "Public Safety (Police/Fire)",
    "Urban Planning & Development",
    "Finance & Budgeting",
    "Human Resources",
    "Parks & Recreation",
    "Library Services",
    "Community Services",
    "Legal Services",
    "Environmental Services"
]

DEGREE_OPTIONS = [
    "High School Diploma/GED",
    "Some College",
    "Associate's Degree",
    "Bachelor's Degree",
    "Master's Degree",
    "Doctoral Degree (PhD/JD/MD)"
]

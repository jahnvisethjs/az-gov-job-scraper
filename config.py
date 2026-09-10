"""
Configuration file for Arizona city job sites and application settings.
"""
import os
from typing import List, Dict

# =============================================================================
# LLM Provider Configuration
# =============================================================================

# ASU AI Platform Configuration (Primary and Only Provider)
ASU_AI_ENABLED = os.getenv("ASU_AI_ENABLED", "true").lower() == "true"
ASU_AI_API_KEY = os.getenv("ASU_AI_API_KEY", "")
ASU_AI_BASE_URL = os.getenv("ASU_AI_BASE_URL", "https://api-main.aiml.asu.edu")

# ASU AI Text Generation Model
ASU_AI_MODEL = os.getenv("ASU_AI_MODEL", "gpt-4o")

# ASU AI Embeddings Configuration
ASU_AI_EMBEDDINGS_PROVIDER = os.getenv("ASU_AI_EMBEDDINGS_PROVIDER", "openai")
ASU_AI_EMBEDDINGS_MODEL = os.getenv("ASU_AI_EMBEDDINGS_MODEL", "te3s")  # text-embedding-3-small abbreviation
ASU_AI_EMBEDDINGS_DIMENSIONS = int(os.getenv("ASU_AI_EMBEDDINGS_DIMENSIONS", "1024"))

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

# Cache Settings
JOB_CACHE_HOURS = int(os.getenv("JOB_CACHE_HOURS", "6"))  # How long scraped jobs stay fresh
CACHE_DIR = os.getenv("CACHE_DIR", "./data/cache")  # Cache directory path
EMBEDDING_BATCH_WORKERS = int(os.getenv("EMBEDDING_BATCH_WORKERS", "2"))  # Parallel embedding workers

# Job Matching Settings
TOP_JOBS_TO_DISPLAY = 50
MIN_MATCH_SCORE_THRESHOLD = 0  # Temporarily set to 0 to see all jobs and their scores

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

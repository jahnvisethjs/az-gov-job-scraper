"""Shared embedding text and scoring for runtime matching and evaluation."""

import math
from typing import Dict


def prepare_job_text(job: Dict) -> str:
    """
    Prepare job data for embedding by combining key fields.

    Args:
        job: Job dictionary with title, description, requirements, etc.

    Returns:
        Formatted text for embedding
    """
    parts = []

    if job.get("title"):
        parts.append(f"Title: {job['title']}")

    if job.get("department"):
        parts.append(f"Department: {job['department']}")

    if job.get("location") or job.get("city"):
        parts.append(f"Location: {job.get('location') or job.get('city')}")

    if job.get("description"):
        parts.append(f"Description: {job['description']}")

    if job.get("requirements"):
        parts.append(f"Requirements: {job['requirements']}")

    if job.get("job_type"):
        parts.append(f"Type: {job['job_type']}")

    return "\n\n".join(parts)


def prepare_resume_text(profile: Dict) -> str:
    """
    Prepare resume/profile data for embedding.

    Args:
        profile: User profile with resume_parsed data

    Returns:
        Formatted text for embedding
    """
    parts = []

    if profile.get("target_job_title"):
        parts.append(f"Target role: {profile['target_job_title']}")

    if profile.get("target_location"):
        parts.append(f"Preferred location: {profile['target_location']}")

    # Add interests
    if profile.get("interests"):
        parts.append(f"Interests: {', '.join(profile['interests'])}")

    # Add education
    if profile.get("degree"):
        parts.append(f"Education: {profile['degree']}")

    # Parse resume data
    resume_data = profile.get("resume_parsed") or {}

    # Use extracted text when structured parsing was unavailable.
    if not resume_data and profile.get("resume_text"):
        parts.append(f"Resume: {profile['resume_text']}")

    # Add skills
    if resume_data.get("skills"):
        parts.append(f"Skills: {', '.join(resume_data['skills'])}")

    # Add experience
    if resume_data.get("experience"):
        exp_texts = []
        for exp in resume_data["experience"]:
            exp_text = f"{exp.get('title', '')} at {exp.get('company', '')}"
            if exp.get("description"):
                exp_text += f": {exp['description']}"
            exp_texts.append(exp_text)
        parts.append(f"Experience:\n" + "\n".join(exp_texts))

    # Add education details
    if resume_data.get("education"):
        edu_texts = []
        for edu in resume_data["education"]:
            edu_text = f"{edu.get('degree', '')} in {edu.get('field', '')} from {edu.get('institution', '')}"
            edu_texts.append(edu_text)
        parts.append(f"Education Details:\n" + "\n".join(edu_texts))

    # Add projects
    if resume_data.get("projects"):
        proj_texts = []
        for proj in resume_data["projects"]:
            proj_text = f"{proj.get('name', '')}: {proj.get('description', '')}"
            if proj.get("technologies"):
                proj_text += f" (Technologies: {', '.join(proj['technologies'])})"
            proj_texts.append(proj_text)
        parts.append(f"Projects:\n" + "\n".join(proj_texts))

    return "\n\n".join(parts)


def calculate_keyword_overlap(job: Dict, profile: Dict) -> float:
    """
    Calculate keyword overlap score between job and resume.

    Args:
        job: Job dictionary
        profile: User profile dictionary

    Returns:
        Keyword overlap score (0.0 to 1.0)
    """
    # Extract keywords from job
    job_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('requirements', '')}".lower()

    # Extract keywords from profile
    resume_data = profile.get("resume_parsed") or {}
    profile_keywords = set()

    # Add skills as keywords
    if resume_data.get("skills"):
        profile_keywords.update([s.lower() for s in resume_data["skills"]])

    # Add interests
    if profile.get("interests"):
        profile_keywords.update([i.lower() for i in profile["interests"]])

    # Simple keyword matching
    total_keywords = len(profile_keywords)

    if total_keywords == 0:
        return 0.0

    matches = sum(1 for keyword in profile_keywords if keyword in job_text)

    return matches / total_keywords


def combine_match_score(
    semantic_similarity: float,
    keyword_score: float,
    semantic_weight: float = 0.7,
) -> float:
    """Return the existing hybrid heuristic, on its 0–100 scale.

    Cosine similarity can be negative. This is not a hiring probability.
    Alternative weights are for offline evaluation, not runtime tuning.
    """
    if not all(math.isfinite(value) for value in (semantic_similarity, keyword_score, semantic_weight)):
        raise ValueError("Scoring inputs must be finite")
    if not -1 <= semantic_similarity <= 1 or not 0 <= keyword_score <= 1:
        raise ValueError("Similarity or keyword overlap is outside its valid range")
    if not 0 <= semantic_weight <= 1:
        raise ValueError("Semantic weight must be between zero and one")
    return (semantic_weight * semantic_similarity + (1 - semantic_weight) * keyword_score) * 100

"""
RAG Engine for semantic job matching using ChromaDB and Google Gemini embeddings.
"""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Tuple
import google.generativeai as genai
from config import (
    GEMINI_API_KEY,
    GEMINI_EMBEDDING_MODEL,
    VECTOR_DB_PATH,
    MIN_MATCH_SCORE_THRESHOLD
)
import os
from pathlib import Path


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
    
    # Add interests
    if profile.get("interests"):
        parts.append(f"Interests: {', '.join(profile['interests'])}")
    
    # Add education
    if profile.get("degree"):
        parts.append(f"Education: {profile['degree']}")
    
    # Parse resume data
    resume_data = profile.get("resume_parsed", {})
    
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
    job_keywords = set()
    
    job_text = f"{job.get('title', '')} {job.get('description', '')} {job.get('requirements', '')}".lower()
    
    # Extract keywords from profile
    resume_data = profile.get("resume_parsed", {})
    profile_keywords = set()
    
    # Add skills as keywords
    if resume_data.get("skills"):
        profile_keywords.update([s.lower() for s in resume_data["skills"]])
    
    # Add interests
    if profile.get("interests"):
        profile_keywords.update([i.lower() for i in profile["interests"]])
    
    # Simple keyword matching (can be improved with NLP)
    matches = 0
    total_keywords = len(profile_keywords)
    
    if total_keywords == 0:
        return 0.0
    
    for keyword in profile_keywords:
        if keyword in job_text:
            matches += 1
    
    return matches / total_keywords


class JobRAG:
    """RAG engine for semantic job matching."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize RAG engine with ChromaDB and Gemini.
        
        Args:
            api_key: Gemini API key (defaults to config)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY
        
        if not self.api_key:
            raise ValueError("Gemini API key is required")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize ChromaDB
        db_path = Path(VECTOR_DB_PATH)
        db_path.mkdir(parents=True, exist_ok=True)
        
        self.chroma_client = chromadb.PersistentClient(
            path=str(db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="jobs",
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using Gemini.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        result = genai.embed_content(
            model=GEMINI_EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_document"
        )
        return result["embedding"]
    
    def add_jobs(self, jobs: List[Dict]) -> int:
        """
        Add jobs to vector database.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            Number of jobs added
        """
        if not jobs:
            return 0
        
        # Prepare data for ChromaDB
        documents = []
        embeddings = []
        ids = []
        metadatas = []
        
        for i, job in enumerate(jobs):
            # Prepare text for embedding
            job_text = prepare_job_text(job)
            documents.append(job_text)
            
            # Generate embedding
            embedding = self.generate_embedding(job_text)
            embeddings.append(embedding)
            
            # Create unique ID
            job_id = job.get("job_id") or f"{job['city']}_{i}"
            ids.append(job_id)
            
            # Store metadata (all job fields)
            metadatas.append(job)
        
        # Add to ChromaDB
        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )
        
        return len(jobs)
    
    def search_jobs(
        self,
        profile: Dict,
        top_k: int = 50
    ) -> List[Tuple[Dict, float]]:
        """
        Search for matching jobs using semantic similarity.
        
        Args:
            profile: User profile dictionary
            top_k: Number of top results to return
            
        Returns:
            List of (job_dict, score) tuples sorted by score
        """
        # Prepare resume text for embedding
        resume_text = prepare_resume_text(profile)
        
        # Generate embedding for resume
        resume_embedding = self.generate_embedding(resume_text)
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[resume_embedding],
            n_results=top_k
        )
        
        # Process results
        matched_jobs = []
        
        if results["metadatas"] and len(results["metadatas"]) > 0:
            metadatas = results["metadatas"][0]  # First query result
            distances = results["distances"][0] if results.get("distances") else []
            
            for i, job_metadata in enumerate(metadatas):
                # Convert cosine distance to similarity (1 - distance)
                semantic_similarity = 1.0 - distances[i] if distances else 0.5
                
                # Calculate keyword overlap
                keyword_score = calculate_keyword_overlap(job_metadata, profile)
                
                # Combined score: 70% semantic, 30% keyword
                final_score = (0.7 * semantic_similarity) + (0.3 * keyword_score)
                
                # Convert to 0-100 scale
                final_score = final_score * 100
                
                matched_jobs.append((job_metadata, final_score))
        
        # Sort by score descending
        matched_jobs.sort(key=lambda x: x[1], reverse=True)
        
        # Filter by threshold
        matched_jobs = [
            (job, score) for job, score in matched_jobs
            if score >= MIN_MATCH_SCORE_THRESHOLD
        ]
        
        return matched_jobs
    
    def clear_jobs(self):
        """Clear all jobs from the database."""
        # Delete and recreate collection
        try:
            self.chroma_client.delete_collection("jobs")
            self.collection = self.chroma_client.get_or_create_collection(
                name="jobs",
                metadata={"hnsw:space": "cosine"}
            )
        except Exception:
            pass  # Collection might not exist
    
    def get_job_count(self) -> int:
        """Get the number of jobs in the database."""
        return self.collection.count()

"""
RAG Engine for semantic job matching using:
- ASU AI text-embedding-3-small for vector embeddings (1024 dimensions)
- ASU AI Claude Opus 4.7 for text generation (resume parsing, tailoring advice)
- ChromaDB for vector storage and similarity search
"""
import chromadb
from chromadb.config import Settings
from dataclasses import dataclass
from typing import Callable, List, Dict, Optional, Tuple
import hashlib
from config import (
    ASU_AI_API_KEY,
    ASU_AI_BASE_URL,
    ASU_AI_EMBEDDINGS_DIMENSIONS,
    ASU_AI_EMBEDDINGS_MODEL,
    ASU_AI_EMBEDDINGS_PROVIDER,
    VECTOR_DB_PATH,
    MIN_MATCH_SCORE_THRESHOLD,
    EMBEDDING_BATCH_WORKERS
)
import os
from pathlib import Path
from rag.asu_ai_provider import ASUAIProvider
from job_identity import deduplicate_jobs


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
    
    # Simple keyword matching
    total_keywords = len(profile_keywords)
    
    if total_keywords == 0:
        return 0.0
    
    matches = sum(1 for keyword in profile_keywords if keyword in job_text)
    
    return matches / total_keywords


EMBEDDING_HASH_KEY = "_embedding_content_hash"


@dataclass(frozen=True)
class IndexUpdate:
    """Summary of an incremental job-index synchronization."""

    total: int
    embedded: int
    unchanged: int
    removed: int


def _job_embedding_hash(job: Dict) -> str:
    """Hash the text and model settings that determine a job embedding."""
    source = "\n".join([
        ASU_AI_EMBEDDINGS_PROVIDER,
        ASU_AI_EMBEDDINGS_MODEL,
        str(ASU_AI_EMBEDDINGS_DIMENSIONS),
        prepare_job_text(job),
    ])
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def _serialize_job_metadata(job: Dict, content_hash: str) -> Dict:
    """Flatten a job for ChromaDB metadata storage."""
    import json

    metadata = {}
    for key, value in job.items():
        if isinstance(value, dict):
            metadata[key] = json.dumps(value)
        elif isinstance(value, (str, int, float, bool)) or value is None:
            metadata[key] = value
        else:
            metadata[key] = str(value)
    metadata[EMBEDDING_HASH_KEY] = content_hash
    return metadata


class JobRAG:
    """RAG engine for semantic job matching using ASU AI."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize RAG engine with ChromaDB and ASU AI.
        
        Args:
            api_key: ASU AI API key (defaults to config or environment)
        """
        self.api_key = api_key or os.getenv("ASU_AI_API_KEY") or ASU_AI_API_KEY
        self.base_url = ASU_AI_BASE_URL
        
        if not self.api_key:
            raise ValueError("ASU AI API key is required")
        
        # Initialize ASU AI provider for both text generation AND embeddings
        self.llm_provider = ASUAIProvider(api_key=self.api_key)
        
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
        Generate embedding using ASU AI text-embedding-3-small.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector (1024 dimensions)
        """
        from config import ASU_AI_EMBEDDINGS_MODEL, ASU_AI_EMBEDDINGS_PROVIDER, ASU_AI_EMBEDDINGS_DIMENSIONS
        
        return self.llm_provider.generate_embedding_sync(
            text=text,
            model=ASU_AI_EMBEDDINGS_MODEL,
            provider=ASU_AI_EMBEDDINGS_PROVIDER,
            dimensions=ASU_AI_EMBEDDINGS_DIMENSIONS
        )
    
    def generate_embedding_sync(self, text: str) -> List[float]:
        """Alias for generate_embedding (already synchronous)."""
        return self.generate_embedding(text)
    
    def add_jobs(
        self,
        jobs: List[Dict],
        *,
        scope_cities: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> IndexUpdate:
        """Incrementally synchronize jobs with the vector database.

        Existing embeddings survive new ``JobRAG`` instances. Only new jobs,
        jobs whose embedded text changed, or jobs affected by embedding-model
        configuration changes are sent to the embeddings API.

        Args:
            jobs: Complete job set for the supplied city scope.
            scope_cities: Cities represented by ``jobs``. Jobs from other
                previously indexed cities are preserved.
            progress_callback: Optional callback receiving completed and total.

        Returns:
            Incremental update statistics.
        """
        jobs = deduplicate_jobs(jobs)
        existing = self.collection.get(include=["metadatas"])
        existing_metadatas = existing.get("metadatas") or []
        existing_by_id = {
            job_id: metadata or {}
            for job_id, metadata in zip(existing.get("ids") or [], existing_metadatas)
        }

        incoming = {}
        for job in jobs:
            content_hash = _job_embedding_hash(job)
            incoming[job["job_id"]] = {
                "job": job,
                "hash": content_hash,
                "metadata": _serialize_job_metadata(job, content_hash),
            }

        incoming_ids = set(incoming)
        if scope_cities is None:
            managed_existing_ids = set(existing_by_id)
        else:
            managed_cities = set(scope_cities)
            managed_existing_ids = {
                job_id
                for job_id, metadata in existing_by_id.items()
                if metadata.get("city") in managed_cities
            }

        stale_ids = sorted(managed_existing_ids - incoming_ids)
        if stale_ids:
            self.collection.delete(ids=stale_ids)

        changed_ids = [
            job_id
            for job_id, item in incoming.items()
            if existing_by_id.get(job_id, {}).get(EMBEDDING_HASH_KEY) != item["hash"]
        ]
        changed_id_set = set(changed_ids)
        unchanged_ids = [job_id for job_id in incoming if job_id not in changed_id_set]

        # Metadata such as application URLs can change without affecting the
        # text embedding, so refresh it without calling the embeddings API.
        if unchanged_ids:
            self.collection.update(
                ids=unchanged_ids,
                metadatas=[incoming[job_id]["metadata"] for job_id in unchanged_ids],
            )

        if changed_ids:
            documents = [prepare_job_text(incoming[job_id]["job"]) for job_id in changed_ids]
            print(
                f"[RAG] Embedding {len(documents)} new or changed jobs "
                f"with {EMBEDDING_BATCH_WORKERS} workers..."
            )
            embeddings = self.llm_provider.generate_embeddings_batch(
                texts=documents,
                model=ASU_AI_EMBEDDINGS_MODEL,
                provider=ASU_AI_EMBEDDINGS_PROVIDER,
                dimensions=ASU_AI_EMBEDDINGS_DIMENSIONS,
                max_workers=EMBEDDING_BATCH_WORKERS,
                progress_callback=progress_callback,
            )
            self.collection.upsert(
                documents=documents,
                embeddings=embeddings,
                ids=changed_ids,
                metadatas=[incoming[job_id]["metadata"] for job_id in changed_ids],
            )
        else:
            print(f"[RAG] Reusing {len(unchanged_ids)} existing job embeddings.")

        return IndexUpdate(
            total=len(jobs),
            embedded=len(changed_ids),
            unchanged=len(unchanged_ids),
            removed=len(stale_ids),
        )
    
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
        resume_embedding = self.generate_embedding_sync(resume_text)
        
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
            
            for i, stored_metadata in enumerate(metadatas):
                job_metadata = dict(stored_metadata)
                job_metadata.pop(EMBEDDING_HASH_KEY, None)
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


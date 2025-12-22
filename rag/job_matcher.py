"""
Job Matcher and Tailoring Advisor for personalized job recommendations.
"""
from typing import List, Dict, Tuple
from .rag_engine import JobRAG
from scrapers import ScraperRegistry
import asyncio
import os
from config import (
    ASU_AI_API_KEY,
    TOP_JOBS_TO_DISPLAY
)


class JobMatcher:
    """Orchestrates job scraping, matching, and ranking workflow."""
    
    def __init__(self, api_key: str = None):
        """
        Initialize job matcher.
        
        Args:
            api_key: ASU AI API key (defaults to config)
        """
        self.api_key = api_key or os.getenv("ASU_AI_API_KEY") or ASU_AI_API_KEY
        self.rag_engine = JobRAG(api_key=self.api_key)
    
    async def match_jobs_to_profile(
        self,
        profile: Dict,
        cities: List[str],
        progress_callback=None
    ) -> List[Dict]:
        """
        Complete workflow: scrape → embed → match → rank.
        
        Args:
            profile: User profile dictionary
            cities: List of city names to scrape
            progress_callback: Optional callback function for progress updates
            
        Returns:
            List of matched jobs with scores, sorted by relevance
        """
        all_jobs = []
        
        # Step 1: Scrape jobs from selected cities
        if progress_callback:
            progress_callback(f"Scraping jobs from {len(cities)} cities...")
        
        for i, city in enumerate(cities):
            try:
                if progress_callback:
                    progress_callback(f"Scraping {city} ({i+1}/{len(cities)})...")
                
                scraper = ScraperRegistry.get_scraper(city)
                jobs = await scraper.scrape_with_retry(max_retries=2)
                
                # Convert JobData objects to dictionaries
                jobs_dict = [job.to_dict() for job in jobs]
                all_jobs.extend(jobs_dict)
                
                if progress_callback:
                    progress_callback(f"Found {len(jobs)} jobs from {city}")
                
            except Exception as e:
                if progress_callback:
                    progress_callback(f"Error scraping {city}: {e}")
                continue
        
        if not all_jobs:
            return []
        
        # Step 2: Add jobs to vector database
        if progress_callback:
            progress_callback(f"Indexing {len(all_jobs)} jobs in vector database...")
        
        # Clear previous jobs
        self.rag_engine.clear_jobs()
        
        # Add new jobs
        self.rag_engine.add_jobs(all_jobs)
        
        # Step 3: Semantic search and matching
        if progress_callback:
            progress_callback("Finding best matches...")
        
        matched_jobs = self.rag_engine.search_jobs(profile, top_k=100)
        
        # Step 4: Format results
        results = []
        for job, score in matched_jobs:
            job["match_score"] = round(score, 1)
            results.append(job)
        
        if progress_callback:
            progress_callback(f"Found {len(results)} matching jobs!")
        
        return results
    
    def rank_by_score(self, jobs: List[Dict]) -> List[Dict]:
        """
        Sort jobs by match score (descending).
        
        Args:
            jobs: List of jobs with match_score field
            
        Returns:
            Sorted list of jobs
        """
        return sorted(jobs, key=lambda x: x.get("match_score", 0), reverse=True)
    
    def filter_by_threshold(self, jobs: List[Dict], threshold: float) -> List[Dict]:
        """
        Filter jobs below score threshold.
        
        Args:
            jobs: List of jobs with match_score field
            threshold: Minimum score to keep
            
        Returns:
            Filtered list of jobs
        """
        return [job for job in jobs if job.get("match_score", 0) >= threshold]


class TailoringAdvisor:
    """Generate personalized resume tailoring advice using ASU AI."""
    
    def __init__(self, api_key: str = None):
        """
        Initialize tailoring advisor.
        
Args:
            api_key: ASU AI API key (defaults to config)
        """
        from config import ASU_AI_API_KEY, ASU_AI_MODEL
        from .asu_ai_provider import ASUAIProvider
        
        self.api_key = api_key or os.getenv("ASU_AI_API_KEY") or ASU_AI_API_KEY
        self.provider = ASUAIProvider(api_key=self.api_key, model=ASU_AI_MODEL)
    
    def generate_advice(self, job: Dict, profile: Dict) -> Dict[str, any]:
        """
        Generate personalized resume tailoring advice.
        
        Args:
            job: Job dictionary with title, description, requirements
            profile: User profile with resume_parsed data
            
        Returns:
            Dictionary with tailoring advice:
            {
                "skill_gaps": List of missing skills,
                "keywords": List of keywords to add,
               "improvements": List of improvement suggestions,
                "strengths": List of matching strengths
            }
        """
        # Prepare prompt
        resume_data = profile.get("resume_parsed", {})
        
        user_skills = resume_data.get("skills", [])
        user_experience = resume_data.get("experience", [])
        
        prompt = f"""
You are a career advisor helping a job seeker tailor their resume for a specific government job.

**Job Details:**
- Title: {job.get('title', 'N/A')}
- Department: {job.get('department', 'N/A')}
- Description: {job.get('description', 'N/A')[:500]}
- Requirements: {job.get('requirements', 'N/A')[:500]}

**Candidate's Profile:**
- Skills: {', '.join(user_skills) if user_skills else 'N/A'}
- Education: {profile.get('degree', 'N/A')}
- Interests: {', '.join(profile.get('interests', [])) if profile.get('interests') else 'N/A'}

Analyze the match and provide:
1. **Skill Gaps**: List 3-5 skills mentioned in the job that the candidate lacks
2. **Keywords to Add**: 5-7 important keywords from the job description the candidate should include
3. **Resume Improvements**: 3-5 specific suggestions to strengthen their application
4. **Matching Strengths**: 2-3 things the candidate already has that align well

Format your response as JSON:
{{
    "skill_gaps": ["skill1", "skill2", ...],
    "keywords": ["keyword1", "keyword2", ...],
    "improvements": ["improvement1", "improvement2", ...],
    "strengths": ["strength1", "strength2", ...]
}}
"""
        
        try:
            # Use ASU AI provider (synchronous)
            response_text = self.provider.generate_content_sync(prompt)
            
            # Extract JSON from response
            text = response_text.strip()
            
           # Remove markdown code blocks if present
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            # Parse JSON
            import json
            advice = json.loads(text)
            
            return advice
            
        except Exception as e:
            # Fallback: return basic advice
            return {
                "skill_gaps": ["Unable to analyze - please review job requirements"],
                "keywords": ["Check job description for key terms"],
                "improvements": ["Review job requirements carefully", "Align your resume with job description"],
                "strengths": ["Your experience and education"],
                "error": str(e)
            }
    
    def identify_gaps(self, job: Dict, profile: Dict) -> List[str]:
        """
        Identify skill/qualification gaps.
        
        Args:
            job: Job dictionary
            profile: User profile
            
        Returns:
            List of missing skills/qualifications
        """
        advice = self.generate_advice(job, profile)
        return advice.get("skill_gaps", [])
    
    def suggest_keywords(self, job: Dict, profile: Dict) -> List[str]:
        """
        Suggest keywords to add to resume.
        
        Args:
            job: Job dictionary
            profile: User profile
            
        Returns:
            List of recommended keywords
        """
        advice = self.generate_advice(job, profile)
        return advice.get("keywords", [])

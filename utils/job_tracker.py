"""
Job Tracking Utility - Track job applications and their status.

Stores job tracking data locally in JSON format.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class JobTracker:
    """
    Track job applications with status, notes, and deadlines.
    
    Storage: ~/.job_scraper/tracked_jobs.json
    """
    
    STATUSES = ["Saved", "Applied", "Interview", "Rejected", "Offer", "Accepted"]
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize job tracker.
        
        Args:
            storage_path: Custom storage path (defaults to ~/.job_scraper/tracked_jobs.json)
        """
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            home = Path.home()
            self.storage_dir = home / ".job_scraper"
            self.storage_dir.mkdir(exist_ok=True)
            self.storage_path = self.storage_dir / "tracked_jobs.json"
        
        self.jobs = self._load_jobs()
    
    def _load_jobs(self) -> List[Dict]:
        """Load jobs from storage."""
        if self.storage_path.exists():
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_jobs(self):
        """Save jobs to storage."""
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(self.jobs, f, indent=2, ensure_ascii=False)
    
    def add_job(
        self,
        job: Dict,
        status: str = "Saved",
        notes: str = "",
        deadline: Optional[str] = None
    ) -> Dict:
        """
        Add a job to tracking.
        
        Args:
            job: Job dictionary (must have 'title' and 'url')
            status: Application status (default: "Saved")
            notes: Optional notes
            deadline: Optional deadline (YYYY-MM-DD format)
            
        Returns:
            Tracked job dictionary
        """
        # Generate unique ID
        job_id = f"{job.get('city', 'unknown')}_{job.get('title', 'job')}_{datetime.now().timestamp()}"
        
        tracked_job = {
            "id": job_id,
            "job_data": job,
            "status": status,
            "notes": notes,
            "deadline": deadline,
            "added_date": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "history": [
                {
                    "status": status,
                    "timestamp": datetime.now().isoformat(),
                    "note": "Job added to tracking"
                }
            ]
        }
        
        self.jobs.append(tracked_job)
        self._save_jobs()
        
        return tracked_job
    
    def update_status(self, job_id: str, new_status: str, note: str = "") -> bool:
        """
        Update job application status.
        
        Args:
            job_id: Job tracking ID  
            new_status: New status
            note: Optional note about the status change
            
        Returns:
            True if update successful
        """
        for job in self.jobs:
            if job["id"] == job_id:
                job["status"] = new_status
                job["last_updated"] = datetime.now().isoformat()
                
                # Add to history
                job["history"].append({
                    "status": new_status,
                    "timestamp": datetime.now().isoformat(),
                    "note": note
                })
                
                self._save_jobs()
                return True
        
        return False
    
    def add_note(self, job_id: str, note: str) -> bool:
        """Add a note to a tracked job."""
        for job in self.jobs:
            if job["id"] == job_id:
                job["notes"] = note
                job["last_updated"] = datetime.now().isoformat()
                self._save_jobs()
                return True
        
        return False
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a job from tracking."""
        initial_length = len(self.jobs)
        self.jobs = [j for j in self.jobs if j["id"] != job_id]
        
        if len(self.jobs) < initial_length:
            self._save_jobs()
            return True
        
        return False
    
    def get_jobs_by_status(self, status: str) -> List[Dict]:
        """Get all jobs with a specific status."""
        return [j for j in self.jobs if j["status"] == status]
    
    def get_all_jobs(self) -> List[Dict]:
        """Get all tracked jobs."""
        return self.jobs
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get a specific tracked job by ID."""
        for job in self.jobs:
            if job["id"] == job_id:
                return job
        return None
    
    def is_job_tracked(self, job_url: str) -> bool:
        """Check if a job is already being tracked."""
        for tracked in self.jobs:
            if tracked.get("job_data", {}).get("url") == job_url:
                return True
        return False
    
    def get_statistics(self) -> Dict:
        """Get tracking statistics."""
        stats = {
            "total": len(self.jobs),
            "by_status": {}
        }
        
        for status in self.STATUSES:
            stats["by_status"][status] = len(self.get_jobs_by_status(status))
        
        return stats

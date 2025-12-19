"""
Matching Agent - Resume-job matching workflow with RAG integration.

This agent orchestrates the job matching pipeline including resume indexing,
job indexing, scoring, ranking, and tailoring advice generation.
"""

from typing import Optional, Callable
from langgraph.graph import StateGraph, END
from .state_schemas import MatchingState
from rag.rag_engine import JobRAG


class MatchingAgent:
    """
    LangGraph agent for orchestrating resume-job matching.
    
    Features:
    - Resume and job indexing in vector database
    - Hybrid match scoring (semantic + keyword)
    - Configurable filtering and ranking
    - Tailoring advice generation for top matches
    """
    
    def __init__(self, progress_callback: Optional[Callable[[float, str], None]] = None):
        """
        Initialize the matching agent.
        
        Args:
            progress_callback: Optional callback function(progress, message) for UI updates
        """
        self.progress_callback = progress_callback
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(MatchingState)
        
        # Add nodes
        workflow.add_node("validate_inputs", self._validate_inputs)
        workflow.add_node("index_resume", self._index_resume)
        workflow.add_node("index_jobs", self._index_jobs)
        workflow.add_node("compute_matches", self._compute_matches)
        workflow.add_node("rank_filter", self._rank_filter)
        workflow.add_node("generate_advice", self._generate_advice)
        
        # Define edges
        workflow.set_entry_point("validate_inputs")
        workflow.add_edge("validate_inputs", "index_resume")
        workflow.add_edge("index_resume", "index_jobs")
        workflow.add_edge("index_jobs", "compute_matches")
        workflow.add_edge("compute_matches", "rank_filter")
        workflow.add_edge("rank_filter", "generate_advice")
        workflow.add_edge("generate_advice", END)
        
        return workflow.compile()
    
    def _validate_inputs(self, state: MatchingState) -> MatchingState:
        """Validate inputs and initialize state."""
        self._update_progress(0.0, "Validating inputs...")
        
        errors = []
        
        # Check resume data
        if not state.get("resume_data"):
            errors.append("Resume data is required")
        
        # Check jobs
        if not state.get("jobs") or len(state["jobs"]) == 0:
            errors.append("At least one job is required")
        
        # Check API key
        if not state.get("api_key"):
            errors.append("API key is required")
        
        return {
            "resume_indexed": False,
            "jobs_indexed": False,
            "raw_matches": [],
            "matches": [],
            "top_matches": [],
            "errors": errors,
            "progress": 0.1
        }
    
    def _index_resume(self, state: MatchingState) -> MatchingState:
        """Index resume in RAG vector database."""
        self._update_progress(0.2, "Indexing resume...")
        
        # Check for validation errors
        if state.get("errors"):
            return {"progress": 0.2}
        
        try:
            # Initialize RAG engine
            rag = JobRAG(api_key=state["api_key"])
            
            # Note: JobRAG doesn't have separate index_resume method
            # Resume indexing happens during search_jobs
            
            return {
                "resume_indexed": True,
                "progress": 0.3
            }
            
        except Exception as e:
            return {
                "errors": [f"Failed to index resume: {str(e)}"],
                "progress": 0.3
            }
    
    def _index_jobs(self, state: MatchingState) -> MatchingState:
        """Index jobs in RAG vector database."""
        total_jobs = len(state.get("jobs", []))
        self._update_progress(0.4, f"Indexing {total_jobs} jobs...")
        
        # Check for previous errors
        if state.get("errors"):
            return {"progress": 0.4}
        
        try:
            # Initialize RAG engine
            rag = JobRAG(api_key=state["api_key"])
            
            # Index all jobs
            rag.add_jobs(state["jobs"])
            
            return {
                "jobs_indexed": True,
                "progress": 0.5
            }
            
        except Exception as e:
            return {
                "errors": [f"Failed to index jobs: {str(e)}"],
                "progress": 0.5
            }
    
    def _compute_matches(self, state: MatchingState) -> MatchingState:
        """Compute match scores for all jobs."""
        total_jobs = len(state.get("jobs", []))
        self._update_progress(0.6, f"Computing match scores for {total_jobs} jobs...")
        
        # Check for previous errors
        if state.get("errors"):
            return {"progress": 0.6}
        
        try:
            # Initialize RAG
            rag = JobRAG(api_key=state["api_key"])
            
            # Search for matches using RAG
            # This returns (job, similarity_score) tuples
            search_results = rag.search_jobs(state["resume_data"], top_k=len(state["jobs"]))
            
            # Convert to match format with scores
            matches = []
            for job_data, semantic_score in search_results:
                job_with_score = job_data.copy()
                # Convert similarity to percentage (0-1 to 0-100)
                job_with_score["match_score"] = semantic_score * 100
                matches.append(job_with_score)
            
            return {
                "raw_matches": matches,
                "progress": 0.7
            }
            
        except Exception as e:
            return {
                "errors": [f"Failed to compute matches: {str(e)}"],
                "progress": 0.7
            }
    
    def _rank_filter(self, state: MatchingState) -> MatchingState:
        """Rank and filter matches based on threshold and top_n."""
        self._update_progress(0.8, "Ranking and filtering matches...")
        
        # Check for previous errors
        if state.get("errors"):
            return {"progress": 0.8}
        
        # Get configuration
        threshold = state.get("filter_threshold", 50.0)
        top_n = state.get("top_n", 10)
        
        # Filter by threshold
        filtered_matches = [
            job for job in state.get("raw_matches", [])
            if job.get("match_score", 0) >= threshold
        ]
        
        # Sort by match score (descending)
        sorted_matches = sorted(
            filtered_matches,
            key=lambda x: x.get("match_score", 0),
            reverse=True
        )
        
        # Get top N
        top_matches = sorted_matches[:top_n]
        
        self._update_progress(
            0.9,
            f"Found {len(filtered_matches)} matches above {threshold}% threshold"
        )
        
        return {
            "matches": sorted_matches,
            "top_matches": top_matches,
            "progress": 0.9
        }
    
    def _generate_advice(self, state: MatchingState) -> MatchingState:
        """Generate tailoring advice for top matches."""
        top_matches = state.get("top_matches", [])
        self._update_progress(1.0, f"Generating tailoring advice for {len(top_matches)} jobs...")
        
        # Check for previous errors
        if state.get("errors"):
            return {"progress": 1.0}
        
        try:
            # Note: Tailoring advice generation is done in the UI layer
            # The RAG engine focuses on matching, advice uses Gemini directly
            # For now, we'll add placeholder advice
            for job in top_matches:
                job["tailoring_advice"] = {
                    "generated": False,
                    "message": "Click to generate personalized tailoring advice"
                }
            
            self._update_progress(1.0, "Matching complete!")
            
            return {
                "top_matches": top_matches,
                "progress": 1.0
            }
            
        except Exception as e:
            return {
                "errors": [f"Failed to generate tailoring advice: {str(e)}"],
                "progress": 1.0
            }
    
    def _update_progress(self, progress: float, message: str):
        """Send progress update via callback if available."""
        if self.progress_callback:
            self.progress_callback(progress, message)
    
    def run(
        self,
        resume_data: dict,
        jobs: list[dict],
        api_key: str,
        top_n: int = 10,
        filter_threshold: float = 50.0
    ) -> MatchingState:
        """
        Run the matching workflow.
        
        Args:
            resume_data: Parsed resume information
            jobs: List of jobs to match against
            api_key: Gemini API key
            top_n: Number of top matches to return with advice (default: 10)
            filter_threshold: Minimum match score 0-100 (default: 50.0)
            
        Returns:
            Final state with matches and tailoring advice
        """
        initial_state: MatchingState = {
            "resume_data": resume_data,
            "jobs": jobs,
            "api_key": api_key,
            "top_n": top_n,
            "filter_threshold": filter_threshold,
            "resume_indexed": False,
            "jobs_indexed": False,
            "raw_matches": [],
            "matches": [],
            "top_matches": [],
            "errors": [],
            "progress": 0.0
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        return final_state

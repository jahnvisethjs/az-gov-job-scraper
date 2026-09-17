"""Resume-tailoring application service."""

from typing import Dict

from rag import TailoringAdvisor


def generate_tailoring_advice(job: Dict, profile: Dict, api_key: str) -> Dict:
    """Generate advice without exposing the advisor implementation to the UI."""
    return TailoringAdvisor(api_key).generate_advice(job, profile)

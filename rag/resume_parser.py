"""
Resume parser using ASU AI (gpt-4o) to extract structured data from resume text.
"""
import json
from typing import Dict
import asyncio
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.asu_ai_provider import ASUAIProvider


class ResumeParser:
    """Parse resume text into structured data using ASU AI (gpt-4o)."""
    
    def __init__(self, api_key: str = None, model_name: str = "gpt-4o"):
        """
        Initialize resume parser with ASU AI.
        
        Args:
            api_key: ASU AI API key (optional, uses environment variable if not provided)
            model_name: Model to use (default: gpt-4o)
        """
        self.provider = ASUAIProvider(api_key=api_key, model=model_name)
        self.model_name = model_name
    
    async def parse_resume(self, resume_text: str) -> Dict:
        """
        Extract structured data from resume text.
        
        Args:
            resume_text: Raw resume text extracted from PDF/DOCX
            
        Returns:
            Dictionary with structured resume data:
            {
                "skills": List[str],
                "experience": List[{
                    "title": str,
                    "company": str,
                    "duration": str,
                    "description": str
                }],
                "education": List[{
                    "degree": str,
                    "field": str,
                    "institution": str,
                    "year": str
                }],
                "projects": List[{
                    "name": str,
                    "description": str,
                    "technologies": List[str]
                }],
                "certifications": List[str],
                "summary": str
            }
        """
        prompt = f"""
You are a resume parser. Extract structured information from this resume.

Return ONLY a valid JSON object (no markdown, no code blocks) with this exact structure:

{{
  "skills": ["skill1", "skill2", ...],
  "experience": [
    {{
      "title": "Job Title",
      "company": "Company Name",
      "duration": "Start - End (e.g., 2020 - 2023)",
      "description": "Key responsibilities and achievements"
    }}
  ],
  "education": [
    {{
      "degree": "Degree Type (e.g., Bachelor of Science)",
      "field": "Field of Study",
      "institution": "University Name",
      "year": "Graduation Year"
    }}
  ],
  "projects": [
    {{
      "name": "Project Name",
      "description": "What the project does",
      "technologies": ["tech1", "tech2"]
    }}
  ],
  "certifications": ["cert1", "cert2"],
  "summary": "Brief professional summary or objective"
}}

Instructions:
- Extract ALL skills mentioned (technical and soft skills)
- Include all work experience, internships, and relevant positions
- List all education (degrees, certifications, courses)
- Extract notable projects if mentioned
- If a section is not present in the resume, use an empty list []
- Be thorough - extract as much detail as possible

Resume Text:
{resume_text[:10000]}

Return ONLY the JSON object:
"""
        
        try:
            response = await self.provider.generate_content(prompt)
            
            # Extract JSON from response
            response_text = response.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            # Parse JSON
            parsed_data = json.loads(response_text)
            
            # Validate structure
            required_keys = ["skills", "experience", "education", "projects", "certifications", "summary"]
            for key in required_keys:
                if key not in parsed_data:
                    parsed_data[key] = [] if key != "summary" else ""
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Response was: {response_text[:500]}")
            # Return minimal structure on error
            return {
                "skills": [],
                "experience": [],
                "education": [],
                "projects": [],
                "certifications": [],
                "summary": "Error parsing resume",
                "error": str(e)
            }
        except Exception as e:
            print(f"Resume parsing error: {e}")
            return {
                "skills": [],
                "experience": [],
                "education": [],
                "projects": [],
                "certifications": [],
                "summary": "Error parsing resume",
                "error": str(e)
            }
    
    def parse_resume_sync(self, resume_text: str) -> Dict:
        """Synchronous wrapper for parse_resume."""
        return asyncio.run(self.parse_resume(resume_text))


# Legacy function for backward compatibility
def parse_resume(resume_text: str, api_key: str = None) -> Dict:
    """
    Parse resume (legacy function for backward compatibility).
    
    Args:
        resume_text: Resume text to parse
        api_key: ASU AI API key
        
    Returns:
        Parsed resume dictionary
    """
    parser = ResumeParser(api_key=api_key)
    return parser.parse_resume_sync(resume_text)


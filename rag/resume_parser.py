"""
Resume parser using Gemini AI to extract structured data from resume text.
"""
import json
from typing import Dict, Optional
import google.generativeai as genai
from utils.rate_limiter import get_rate_limiter
import asyncio


class ResumeParser:
    """Parse resume text into structured data using Gemini."""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        """
        Initialize resume parser with Gemini API.
        
        Args:
            api_key: Gemini API key
            model_name: Gemini model to use
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.rate_limiter = get_rate_limiter()
    
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
        # Wait for rate limit
        await self.rate_limiter.wait_if_needed()
        
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
            response = await self.model.generate_content_async(prompt)
            
            # Extract JSON from response
            response_text = response.text.strip()
            
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

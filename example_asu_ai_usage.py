"""
Example script demonstrating how to use the ASU AI Provider.

This shows how to:
1. Initialize the ASU AI provider
2. Generate text responses
3. Use it for resume parsing
4. Use it for job matching recommendations
"""
import asyncio
import os
from rag.asu_ai_provider import ASUAIProvider


async def example_basic_usage():
    """Example 1: Basic text generation"""
    print("=" * 60)
    print("Example 1: Basic Text Generation")
    print("=" * 60)
    
    # Initialize provider (reads from environment variables or config.py)
    provider = ASUAIProvider()
    
    # Generate simple response
    prompt = "What are the key skills needed for a software engineer?"
    response = await provider.generate_content(prompt)
    
    print(f"Prompt: {prompt}")
    print(f"Response: {response}\n")


async def example_resume_parsing():
    """Example 2: Resume parsing use case"""
    print("=" * 60)
    print("Example 2: Resume Parsing")
    print("=" * 60)
    
    provider = ASUAIProvider()
    
    # Sample resume text
    resume_text = """
    John Doe
    Software Engineer
    
    Experience:
    - 5 years of Python development
    - Built web applications with Django and Flask
    - Experience with cloud platforms (AWS, Azure)
    
    Skills: Python, JavaScript, SQL, Docker, Git
    
    Education: Bachelor's in Computer Science, ASU
    """
    
    # Create parsing prompt (similar to your resume_parser.py)
    prompt = f"""
    Extract structured information from this resume and return it in JSON format:
    
    {resume_text}
    
    Return a JSON object with these fields:
    - skills: list of technical skills
    - experience_years: approximate years of experience
    - education: highest education level
    - key_strengths: list of 3-5 key strengths
    """
    
    response = await provider.generate_content(prompt)
    print(f"Parsed Resume Data:\n{response}\n")


async def example_job_matching():
    """Example 3: Job matching recommendations"""
    print("=" * 60)
    print("Example 3: Job Matching Advice")
    print("=" * 60)
    
    provider = ASUAIProvider()
    
    job_description = "Software Engineer - City IT Department. Required: Python, cloud experience, 3+ years."
    candidate_profile = "5 years Python, AWS/Azure, Django, web development"
    
    prompt = f"""
    As a career advisor, provide tailored advice for this candidate applying to this job.
    
    Job: {job_description}
    Candidate: {candidate_profile}
    
    Provide:
    1. Match score (0-100)
    2. Top 3 strengths to highlight
    3. Any gaps to address
    """
    
    response = await provider.generate_content(prompt)
    print(f"Matching Advice:\n{response}\n")


async def example_different_models():
    """Example 4: Using different models"""
    print("=" * 60)
    print("Example 4: Testing Different Models")
    print("=" * 60)
    
    provider = ASUAIProvider()
    
    prompt = "Explain what a REST API is in one sentence."
    
    # Test with different models (adjust based on available models)
    models_to_test = ["gpt-4o-mini", "gpt-4o"]
    
    for model in models_to_test:
        try:
            response = await provider.generate_content(prompt, model=model)
            print(f"Model: {model}")
            print(f"Response: {response}\n")
        except Exception as e:
            print(f"Model: {model}")
            print(f"Error: {e}\n")


async def example_provider_info():
    """Example 5: Get provider information"""
    print("=" * 60)
    print("Example 5: Provider Information")
    print("=" * 60)
    
    provider = ASUAIProvider()
    info = provider.get_usage_info()
    
    print(f"Provider: {info['provider']}")
    print(f"Base URL: {info['base_url']}")
    print(f"Default Model: {info['model']}")
    print(f"API Key Configured: {info['has_api_key']}\n")


async def main():
    """Run all examples"""
    # Set environment variable if not already set
    if not os.getenv("ASU_AI_API_KEY"):
        print("WARNING: ASU_AI_API_KEY not set in environment.")
        print("Please set it in your .env file or export it:\n")
        print("export ASU_AI_API_KEY=your_token_here\n")
        return
    
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "ASU AI Provider Usage Examples" + " " * 17 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\n")
    
    # Run examples
    await example_provider_info()
    await example_basic_usage()
    await example_resume_parsing()
    await example_job_matching()
    # await example_different_models()  # Uncomment to test different models


if __name__ == "__main__":
    asyncio.run(main())

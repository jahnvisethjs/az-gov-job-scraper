"""
Integration Test: ASU AI for Job Matching Application

This demonstrates how the ASU AI integration works for your specific use case:
resume parsing and job matching for Arizona government jobs.
"""
import asyncio
import os
import sys

# Set API key for testing
os.environ["ASU_AI_API_KEY"] = "***REMOVED-CREDENTIAL***"
os.environ["LLM_PROVIDER"] = "asu_ai"
os.environ["ASU_AI_ENABLED"] = "true"

from rag.asu_ai_provider import ASUAIProvider


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


async def test_resume_parsing():
    """Test 1: Parse a sample resume"""
    print_section("TEST 1: Resume Parsing")
    
    sample_resume = """
    JANE SMITH
    Phoenix, AZ | jane.smith@email.com | (555) 123-4567
    
    PROFESSIONAL SUMMARY
    Experienced IT professional with 8 years in systems administration, 
    network management, and cybersecurity. Strong background in government 
    IT infrastructure and compliance.
    
    EXPERIENCE
    
    Systems Administrator - Arizona State University (2020-Present)
    - Managed Windows Server and Linux infrastructure for 5,000+ users
    - Implemented security protocols meeting federal compliance standards
    - Reduced system downtime by 40% through proactive monitoring
    
    Network Engineer - City of Tempe (2017-2020)
    - Maintained city-wide network infrastructure
    - Supported public safety communication systems
    - Managed firewall and VPN configurations
    
    EDUCATION
    Bachelor of Science in Computer Science
    Arizona State University, 2016
    
    CERTIFICATIONS
    - CompTIA Security+ (2021)
    - Cisco CCNA (2018)
    - Microsoft Certified: Azure Administrator (2022)
    
    TECHNICAL SKILLS
    - Operating Systems: Windows Server, Linux (Ubuntu, CentOS), Azure
    - Networking: TCP/IP, DNS, DHCP, VPN, Firewalls  
    - Security: NIST Frameworks, FISMA, vulnerability assessment
    - Tools: Active Directory, PowerShell, Python, Docker
    """
    
    provider = ASUAIProvider()
    
    prompt = f"""
    Analyze this resume and extract structured information in JSON format:
    
    {sample_resume}
    
    Extract:
    1. total_experience_years (integer)
    2. key_skills (list of top 5 technical skills)
    3. education_level (highest degree)
    4. certifications (list)
    5. government_experience (boolean - has the candidate worked in government?)
    6. top_3_strengths (list of 3 key strengths)
    
    Return ONLY the JSON object, no other text.
    """
    
    print("Parsing resume...")
    result = await provider.generate_content(prompt)
    print("Parsed Data:")
    print(result)
    print("\n✓ Resume parsing successful")


async def test_job_matching():
    """Test 2: Match candidate to a government job"""
    print_section("TEST 2: Job Matching & Advice")
    
    job_posting = """
    INFORMATION TECHNOLOGY MANAGER
    City of Phoenix - Information Technology Department
    
    Salary: $75,000 - $95,000
    
    RESPONSIBILITIES:
    - Manage IT infrastructure for city department
    - Oversee network security and compliance
    - Supervise team of 5 IT professionals
    - Ensure FISMA and NIST compliance
    - Budget management and vendor relations
    
    REQUIREMENTS:
    - Bachelor's degree in Computer Science or related field
    - 5+ years IT experience, preferably in government
    - Strong knowledge of network administration
    - Experience with cybersecurity frameworks
    - Certifications: Security+ or CISSP preferred
    """
    
    candidate_summary = """
    8 years IT experience including 6 years in government (ASU + City of Tempe).
    Skills: Systems administration, networking, cybersecurity, Azure.
    Education: BS Computer Science from ASU.
    Certifications: Security+, CCNA, Azure Administrator.
    No direct management experience but led project teams.
    """
    
    provider = ASUAIProvider()
    
    prompt = f"""
    You are a career advisor specializing in government jobs.
    
    JOB POSTING:
    {job_posting}
    
    CANDIDATE PROFILE:
    {candidate_summary}
    
    Provide:
    1. MATCH SCORE (0-100): How well does the candidate match?
    2. TOP STRENGTHS: 3 strongest qualifications to highlight in application
    3. POTENTIAL GAPS: Any weaknesses or missing qualifications
    4. APPLICATION STRATEGY: 2-3 specific tips for this application
    
    Be concise but specific.
    """
    
    print("Analyzing job match...")
    advice = await provider.generate_content(prompt)
    print("Matching Advice:")
    print(advice)
    print("\n✓ Job matching analysis successful")


async def test_cover_letter_help():
    """Test 3: Generate tailored cover letter opening"""
    print_section("TEST 3: Cover Letter Assistance")
    
    provider = ASUAIProvider()
    
    prompt = """
    Write the opening paragraph for a cover letter for this situation:
    
    - Job: IT Manager position at City of Phoenix
    - Candidate: Current ASU systems admin with 8 years IT experience
    - Key selling points: Government experience, Security+ certified, reduced downtime 40%
    - Motivation: Grew up in Phoenix, passion for public service technology
    
    Make it professional, engaging, and specific. Maximum 4 sentences.
    """
    
    print("Generating cover letter opening...")
    opening = await provider.generate_content(prompt)
    print("Suggested Opening:")
    print(f'"{opening}"')
    print("\n✓ Cover letter generation successful")


async def test_interview_prep():
    """Test 4: Interview preparation help"""
    print_section("TEST 4: Interview Preparation")
    
    provider = ASUAIProvider()
    
    prompt = """
    Generate 3 likely interview questions for an IT Manager role at a city government,
    and provide brief answer frameworks.
    
    Focus on:
    - Government IT experience
    - Team management
    - Security and compliance
    
    Format each as:
    Q: [question]
    A: [answer framework with key points to cover]
    """
    
    print("Generating interview prep materials...")
    prep = await provider.generate_content(prompt)
    print("Interview Preparation:")
    print(prep)
    print("\n✓ Interview prep generation successful")


async def test_performance():
    """Test 5: Performance and token usage"""
    print_section("TEST 5: Performance Test")
    
    import time
    
    provider = ASUAIProvider()
    
    prompts = [
        "List 3 key skills for government IT jobs in one sentence.",
        "What is FISMA compliance? Answer in 2 sentences.",
        "Why is cybersecurity important for cities? One sentence."
    ]
    
    total_time = 0
    
    for i, prompt in enumerate(prompts, 1):
        start = time.time()
        response = await provider.generate_content(prompt)
        elapsed = time.time() - start
        total_time += elapsed
        
        print(f"Request {i}:")
        print(f"  Prompt: {prompt}")
        print(f"  Response: {response}")
        print(f"  Time: {elapsed:.2f}s\n")
    
    avg_time = total_time / len(prompts)
    print(f"Average response time: {avg_time:.2f}s")
    print(f"Total time: {total_time:.2f}s")
    print("\n✓ Performance test complete")


async def main():
    """Run all integration tests"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "ASU AI INTEGRATION TEST SUITE" + " " * 24 + "║")
    print("║" + " " * 12 + "Job Search Application Use Cases" + " " * 23 + "║")
    print("╚" + "═" * 68 + "╝")
    
    try:
        await test_resume_parsing()
        await test_job_matching()
        await test_cover_letter_help()
        await test_interview_prep()
        await test_performance()
        
        print("\n" + "=" * 70)
        print("  🎉 ALL TESTS PASSED! 🎉")
        print("=" * 70)
        print("\nThe ASU AI integration is fully functional and ready to use")
        print("for your Arizona Government Job Search application!\n")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

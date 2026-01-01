import os
import json
from dotenv import load_dotenv
from utils import analyze_resume, get_llm
from suggestions import generate_tailoring_suggestions

load_dotenv()

# 1. HARDCODED INPUTS (From Context)
# Resume from Step 446 (truncated/summarized for test but contains key sections)
resume_text = """
Sai Vishruth V
United States | +1(469) 629-6350 | valandassaivishruth@gmail.com

PROFESSIONAL SUMMARY
Lead Full-Stack Engineer driving scalable, cloud native solutions...

PROFESSIONAL EXPERIENCES
HCA HealthCare Aug 2024 - Present
Senior Software engineer
• Architected and delivered enterprise healthcare platforms using Java 17+, Kotlin...
• Designed cloud-native microservices with Spring Cloud, Kafka, Redis, PostgreSQL...
• Built Java Spring Boot microservices from scratch including API contracts...
• Implemented BDD and TDD practices using Cucumber, JUnit, Mockito... (Note: No Agile keyword here)

Capital One May 2021 - Jul 2023
Senior Software engineer
• Engineered low-latency Java microservices...

SKILLS
Languages: Java, Kotlin, Go, Python...
Cloud Platforms: AWS (EC2, EKS...), Azure (AKS...), Google Cloud
"""

jd_text = """
Software Engineer
San Antonio, TX
Requirement:
- Hands-on experience as a full stack engineer with Java, Spring Framework, Angular Framework
- Experience with Cloud AWS-hosted applications
- Experience working in an agile environment
- Experience with Data Science using Python
- Experience building AI solutions using AWS Bedrock
"""

print("--- 1. RUNNING ANALYSIS ---")
api_key = os.getenv("OPENAI_API_KEY")
analysis = analyze_resume(resume_text, jd_text, api_key)

print(f"Overall Score: {analysis.get('overall_relevance_score')}")
print("Missing Basic:", analysis['keyword_gap_analysis']['missing_jd_keywords'])

print("\n--- 2. GENERATING SUGGESTIONS ---")

# Mock the "Gap" inputs for suggestions
basic_gaps = [item for item in analysis['basic_qualification_match'] if item['match_status'] != 'Full']
preferred_gaps = [item for item in analysis['preferred_qualification_match'] if item['match_status'] != 'Full']
role_data = analysis['role_alignment']

suggestions = generate_tailoring_suggestions(
    resume_text, 
    basic_gaps, 
    preferred_gaps, 
    role_data, 
    api_key
)

print("\n--- 3. SUGGESTIONS OUTPUT ---")
print(json.dumps(suggestions, indent=2))

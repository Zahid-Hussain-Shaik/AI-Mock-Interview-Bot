"""
Interview question generation service using Claude API.
"""

import logging

logger = logging.getLogger(__name__)

# Predefined role-specific focus areas for richer question generation
ROLE_FOCUS_AREAS = {
    "Software Engineer": {
        "technical": [
            "data structures and algorithms", "system design", "OOP principles",
            "database design", "API development", "testing strategies",
            "code optimization", "concurrency", "version control"
        ],
        "behavioral": [
            "teamwork", "debugging under pressure", "code reviews",
            "mentoring", "handling technical debt"
        ],
    },
    "Frontend Developer": {
        "technical": [
            "HTML/CSS/JavaScript", "React/Vue/Angular", "responsive design",
            "web performance", "accessibility (a11y)", "state management",
            "browser APIs", "CSS architecture", "build tools"
        ],
        "behavioral": [
            "design collaboration", "UX advocacy", "cross-browser issues",
            "rapid prototyping", "user feedback iteration"
        ],
    },
    "Backend Developer": {
        "technical": [
            "API design (REST/GraphQL)", "database optimization", "microservices",
            "authentication/authorization", "caching strategies", "message queues",
            "containerization", "CI/CD pipelines", "security best practices"
        ],
        "behavioral": [
            "incident response", "system reliability", "documentation",
            "cross-team collaboration", "handling production issues"
        ],
    },
    "Full Stack Developer": {
        "technical": [
            "frontend frameworks", "backend APIs", "database design",
            "deployment and DevOps", "full application architecture",
            "performance optimization", "security", "testing across the stack"
        ],
        "behavioral": [
            "prioritization", "end-to-end ownership", "context switching",
            "stakeholder communication", "rapid learning"
        ],
    },
    "Data Scientist": {
        "technical": [
            "statistical analysis", "machine learning algorithms",
            "data visualization", "Python/R/SQL", "feature engineering",
            "model evaluation", "A/B testing", "deep learning fundamentals"
        ],
        "behavioral": [
            "communicating findings to non-technical stakeholders",
            "handling ambiguous problems", "data ethics",
            "cross-functional collaboration"
        ],
    },
    "DevOps Engineer": {
        "technical": [
            "CI/CD pipelines", "infrastructure as code", "containerization (Docker/K8s)",
            "monitoring and alerting", "cloud platforms (AWS/GCP/Azure)",
            "networking", "security hardening", "incident management"
        ],
        "behavioral": [
            "on-call culture", "post-mortems", "automation mindset",
            "cross-team enablement", "change management"
        ],
    },
    "Product Manager": {
        "technical": [
            "product strategy", "roadmap planning", "user research",
            "data-driven decisions", "A/B testing", "competitive analysis",
            "technical understanding", "metrics and KPIs"
        ],
        "behavioral": [
            "stakeholder management", "prioritization frameworks",
            "conflict resolution", "cross-functional leadership",
            "handling ambiguity"
        ],
    },
    "ML Engineer": {
        "technical": [
            "model training and deployment", "MLOps pipelines",
            "feature stores", "model monitoring", "distributed training",
            "data preprocessing at scale", "model optimization",
            "experiment tracking"
        ],
        "behavioral": [
            "research-to-production handoff", "collaboration with data scientists",
            "handling model failures", "documentation of experiments"
        ],
    },
    "Data Analyst": {
        "technical": [
            "SQL and database querying", "data visualization tools",
            "statistical analysis", "Excel/Sheets advanced functions",
            "ETL processes", "dashboard creation", "data cleaning"
        ],
        "behavioral": [
            "presenting insights", "attention to detail",
            "working with stakeholders", "prioritizing analyses"
        ],
    },
    "Cloud Architect": {
        "technical": [
            "cloud platform design (AWS/GCP/Azure)", "network architecture",
            "security and compliance", "cost optimization", "high availability",
            "disaster recovery", "serverless architectures", "multi-cloud strategies"
        ],
        "behavioral": [
            "technical leadership", "vendor management",
            "communicating architecture decisions", "risk assessment"
        ],
    },
}

EXPERIENCE_DESCRIPTORS = {
    "Entry Level": {
        "years": "0-2 years",
        "depth": "foundational knowledge and eagerness to learn",
        "complexity": "straightforward scenarios with some problem-solving",
    },
    "Mid Level": {
        "years": "3-5 years",
        "depth": "solid practical experience and independent problem-solving",
        "complexity": "moderate complexity with real-world trade-off discussions",
    },
    "Senior": {
        "years": "6-10 years",
        "depth": "deep expertise, architectural thinking, and mentoring ability",
        "complexity": "complex scenarios requiring system-level thinking and leadership",
    },
    "Lead/Principal": {
        "years": "10+ years",
        "depth": "strategic vision, organizational impact, and technical authority",
        "complexity": "highly complex, open-ended problems requiring broad expertise",
    },
}


def generate_questions(claude_client, role, experience_level, min_q=8, max_q=12, cv_text=None, jd_text=None):
    """
    Generate a set of interview questions tailored to the role, experience level,
    and optionally the candidate's CV/resume and job description.
    Returns a list of question dicts with id, text, category, and difficulty.
    """
    focus = ROLE_FOCUS_AREAS.get(role, ROLE_FOCUS_AREAS["Software Engineer"])
    exp_info = EXPERIENCE_DESCRIPTORS.get(experience_level, EXPERIENCE_DESCRIPTORS["Mid Level"])

    # Build CV/JD context block
    context_block = ""
    if cv_text:
        # Truncate to avoid token limits
        cv_snippet = cv_text[:3000]
        context_block += f"""

CANDIDATE'S RESUME/CV:
{cv_snippet}

IMPORTANT: Use the candidate's resume to personalize questions. Ask about specific 
technologies, projects, and experiences mentioned in their CV. Probe deeper into 
their claimed skills and accomplishments."""

    if jd_text:
        jd_snippet = jd_text[:2000]
        context_block += f"""

TARGET JOB DESCRIPTION:
{jd_snippet}

IMPORTANT: Align questions with the requirements and responsibilities listed in 
this job description. Test whether the candidate meets the specific qualifications 
and can handle the described responsibilities."""

    system_prompt = f"""You are an expert technical interviewer with 15+ years of experience 
conducting interviews at top tech companies (Google, Meta, Amazon, Microsoft). 

Your task is to generate a set of realistic interview questions for a {role} position 
at the {experience_level} level ({exp_info['years']} of experience).
{context_block}

REQUIREMENTS:
1. Generate between {min_q} and {max_q} questions (aim for {max_q}).
2. Mix question categories with these approximate proportions:
   - Technical questions (~40%): Test domain knowledge and problem-solving in {', '.join(focus['technical'][:5])}
   - Behavioral questions (~30%): Explore past experiences related to {', '.join(focus['behavioral'][:3])}
   - Situational questions (~20%): Present hypothetical scenarios relevant to the role
   - Problem-solving questions (~10%): Test analytical thinking and approach
3. Arrange questions in INCREASING difficulty order:
   - Start with warm-up / introductory questions
   - Progress to moderate depth
   - End with challenging, thought-provoking questions
4. Questions should match {experience_level} expectations: {exp_info['depth']}
5. Complexity should involve: {exp_info['complexity']}
6. Each question should be clear, specific, and answerable in 2-4 minutes of speaking.
7. Avoid generic questions. Make them specific to the {role} domain.
{"8. If a resume/CV was provided, personalize at least 30% of questions to the candidate's background." if cv_text else ""}
{"9. If a job description was provided, ensure questions test the specific skills and requirements listed." if jd_text else ""}

OUTPUT FORMAT — Return ONLY a valid JSON array (no markdown, no explanation):
[
  {{
    "id": 1,
    "text": "The full question text here",
    "category": "technical" | "behavioral" | "situational" | "problem-solving",
    "difficulty": "easy" | "medium" | "hard"
  }},
  ...
]"""

    user_message = (
        f"Generate interview questions for a {experience_level} {role} position. "
    )
    if cv_text:
        user_message += "The candidate has provided their resume — personalize questions accordingly. "
    if jd_text:
        user_message += "A job description has been provided — align questions with its requirements. "
    user_message += "Return only the JSON array."

    logger.info("Generating questions for %s %s", experience_level, role)
    questions = claude_client.call_json(system_prompt, user_message)

    # Validate structure
    if not isinstance(questions, list):
        raise ValueError("Expected a list of questions from Claude")

    validated = []
    for i, q in enumerate(questions):
        validated.append({
            "id": i + 1,
            "text": q.get("text", ""),
            "category": q.get("category", "technical"),
            "difficulty": q.get("difficulty", "medium"),
        })

    if len(validated) < min_q:
        raise ValueError(
            f"Claude generated only {len(validated)} questions, minimum is {min_q}"
        )

    logger.info("Generated %d questions successfully", len(validated))
    return validated[:max_q]

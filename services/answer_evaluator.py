"""
Answer evaluation service using Claude API.
Produces structured feedback for each interview answer.
"""

import logging

logger = logging.getLogger(__name__)


def evaluate_answer(claude_client, question, answer, role, experience_level):
    """
    Evaluate a candidate's answer to an interview question.
    
    Returns a dict with:
        - score (int, 1-10)
        - strengths (list of strings)
        - weaknesses (list of strings)
        - improvements (list of strings)
        - summary (string, 2-3 sentence assessment)
    """
    if not answer or not answer.strip():
        return {
            "score": 0,
            "strengths": [],
            "weaknesses": ["No answer was provided."],
            "improvements": ["Attempt to answer every question, even if unsure. Sharing your thought process is valuable."],
            "summary": "No answer was provided for this question. In a real interview, it's always better to share your thought process than to remain silent.",
        }

    system_prompt = f"""You are a senior technical interviewer evaluating a candidate's response 
for a {role} position at the {experience_level} level.

EVALUATION CRITERIA:
1. **Relevance** — Does the answer directly address the question asked?
2. **Depth** — Is the response detailed enough for a {experience_level} candidate?
3. **Technical Accuracy** — Are the technical claims and concepts correct?
4. **Communication** — Is the answer well-structured and clearly communicated?
5. **Practical Experience** — Does the answer demonstrate real-world understanding?
6. **Problem-Solving** — Does the candidate show strong analytical skills?

SCORING GUIDELINES (be strict and realistic):
- 9-10: Exceptional — Would impress at top tech companies. Thorough, insightful, with specific examples.
- 7-8: Strong — Demonstrates solid knowledge with good examples. Minor gaps only.
- 5-6: Adequate — Shows basic understanding but lacks depth, specifics, or practical insight.
- 3-4: Below Average — Significant gaps in knowledge or relevance. Needs major improvement.
- 1-2: Poor — Answer is largely incorrect, irrelevant, or extremely vague.

IMPORTANT:
- Be fair but strict. Do not inflate scores.
- Provide specific, actionable feedback — not generic advice.
- Reference specific parts of the candidate's answer in your feedback.
- Strengths and weaknesses should each have 2-4 specific points.
- Improvements should be concrete and actionable.

OUTPUT FORMAT — Return ONLY valid JSON (no markdown, no explanation):
{{
    "score": <integer 1-10>,
    "strengths": ["specific strength 1", "specific strength 2", ...],
    "weaknesses": ["specific weakness 1", "specific weakness 2", ...],
    "improvements": ["specific actionable suggestion 1", "specific actionable suggestion 2", ...],
    "summary": "A 2-3 sentence overall assessment of the answer quality."
}}"""

    user_message = f"""QUESTION:
{question['text']}

Category: {question.get('category', 'general')}
Difficulty: {question.get('difficulty', 'medium')}

CANDIDATE'S ANSWER:
{answer}

Evaluate this answer and return the JSON evaluation."""

    logger.info("Evaluating answer for question %s", question.get("id", "?"))
    evaluation = claude_client.call_json(system_prompt, user_message)

    # Validate and sanitize the evaluation
    validated = {
        "score": _clamp(int(evaluation.get("score", 5)), 1, 10),
        "strengths": _ensure_list(evaluation.get("strengths", [])),
        "weaknesses": _ensure_list(evaluation.get("weaknesses", [])),
        "improvements": _ensure_list(evaluation.get("improvements", [])),
        "summary": str(evaluation.get("summary", "Evaluation completed.")),
    }

    logger.info("Evaluation complete — score: %d/10", validated["score"])
    return validated


def _clamp(value, min_val, max_val):
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))


def _ensure_list(value):
    """Ensure value is a list of strings."""
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value]
    return []

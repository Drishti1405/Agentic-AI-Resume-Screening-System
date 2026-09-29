import os
from typing import Dict, Any, Optional, List

def generate_explanation(
    name: str, 
    role: str, 
    domain_name: str,
    scores: Dict[str, float], 
    matcher_reasoning: str,
    strengths: List[str],
    skill_gaps: List[str],
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates recruiter-friendly narrative explanations, skill gap analysis, and interview recommendations.
    """
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
        
    final = round(scores.get("final_score", 0.0), 1)
    tech = round(scores.get("technical_score", 0.0), 1)
    exp = round(scores.get("experience_score", 0.0), 1)
    cert = round(scores.get("certification_score", 0.0), 1)

    default_questions = [
        f"Can you discuss your hands-on experience with key {domain_name} tools and methodologies?",
        f"Walk us through a major project or case where you demonstrated leadership and problem-solving.",
        f"How do you ensure compliance and quality standards in your day-to-day work?"
    ]

    if not api_key:
        if final >= 80:
            summary = f"{name} is an outstanding candidate for the {role} position ({domain_name}), standing in the top percentile bracket for domain skill proficiency and experience alignment."
        elif final >= 65:
            summary = f"{name} shows solid competency for the {role} role with upper percentile skill alignment and reliable background fit."
        else:
            summary = f"{name} possesses foundational background but exhibits lower percentile standing and key requirement gaps for the {role} position."
        
        return {
            "explanation": summary,
            "strengths": strengths or [f"Good foundational alignment for {domain_name} role."],
            "skill_gaps": skill_gaps or ["Verify depth in secondary domain tools."],
            "interview_recommendations": default_questions
        }

    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        from pydantic import BaseModel, Field

        class ExplainerSchema(BaseModel):
            explanation: str = Field(description="Recruiter summary explaining fit and score rationale in 2 impactful sentences")
            strengths: List[str] = Field(description="Top 2-3 candidate strengths for this role")
            skill_gaps: List[str] = Field(description="Top 2-3 candidate skill, certification, or experience gaps")
            interview_recommendations: List[str] = Field(description="3 targeted interview questions for recruiters/hiring managers")

        EXPLAINER_PROMPT = ChatPromptTemplate.from_messages([
            ("system", "You are an executive talent recruiter. Generate a structured recruiter evaluation summary for candidate fit, including strengths, gaps, and interview questions."),
            ("user", "Role: {role} ({domain_name})\nCandidate Name: {name}\nFinal Score: {final_score}/100\nCategory Scores: {scores}\nReasoning: {reasoning}\nIdentified Strengths: {strengths}\nIdentified Gaps: {gaps}")
        ])

        llm = ChatOpenAI(model="gpt-4o", temperature=0.7, api_key=api_key)
        structured_llm = llm.with_structured_output(ExplainerSchema)
        
        chain = EXPLAINER_PROMPT | structured_llm
        result = chain.invoke({
            "name": name,
            "role": role,
            "domain_name": domain_name,
            "final_score": final,
            "scores": scores,
            "reasoning": matcher_reasoning,
            "strengths": strengths,
            "gaps": skill_gaps
        })
        return result.model_dump()
    except Exception as e:
        print(f"LLM explanation failed: {e}. Using narrative fallback.")
        return {
            "explanation": f"{name} presents a {final}% match score for the {role} role ({domain_name}) with key skill alignment at {tech}%.",
            "strengths": strengths or ["Demonstrates relevant domain exposure."],
            "skill_gaps": skill_gaps or ["Clarify specific certifications in interview."],
            "interview_recommendations": default_questions
        }

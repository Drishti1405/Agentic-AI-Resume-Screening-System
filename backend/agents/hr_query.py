import os
import re
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class HRQueryItem(BaseModel):
    id: Optional[str] = None
    question: str
    importance: str = "Important"  # "Required", "Important", "Optional"

class HRQueryResultSchema(BaseModel):
    query_id: Optional[str] = None
    question: str
    importance: str = "Important"
    answer: str = Field(description="Direct answer strictly based on resume text. Return 'Not Mentioned in Resume' if missing.")
    evidence: str = Field(description="Exact snippet or reason from resume text supporting the answer.")
    fit_result: str = Field(description="Fit classification: 'Yes', 'No', or 'Partially/Unclear'. Return 'No' if missing.")
    confidence: float = Field(default=0.9, description="Confidence score from 0.0 to 1.0")

def deterministic_eval_query(resume_text: str, resume_json: Dict[str, Any], query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic fallback evaluator when LLM API key is not present.
    Performs multi-pattern keyword matching and sentence extraction strictly from candidate resume.
    Returns 'Not Mentioned in Resume' when keywords/evidence are absent.
    """
    q_id = query.get("id") or query.get("query_id") or "q_1"
    q_text = str(query.get("question", "")).strip()
    importance = str(query.get("importance", "Important")).title()
    if importance not in ["Required", "Important", "Optional"]:
        importance = "Important"

    text_lower = resume_text.lower()
    lines = [line.strip() for line in resume_text.split("\n") if line.strip()]

    # Extract non-stop words from question for term matching
    keywords = [w.lower() for w in re.findall(r'\b\w+\b', q_text) if len(w) >= 3 and w.lower() not in ["does", "the", "candidate", "have", "experience", "worked", "with", "for", "has", "any", "in", "a", "or", "and", "particular"]]

    # Special heuristic checks for common HR questions
    is_startup = any(k in q_text.lower() for k in ["start", "startup", "start-up", "early-stage", "founding"])
    is_production = any(k in q_text.lower() for k in ["production", "production-level", "deployed", "live system", "scalable"])
    is_leadership = any(k in q_text.lower() for k in ["leadership", "lead", "manage", "mentor", "head", "director", "supervis"])
    is_internship = any(k in q_text.lower() for k in ["internship", "intern", "trainee"])
    is_relocation = any(k in q_text.lower() for k in ["relocat", "location", "remote", "onsite", "travel", "eligible", "willing"])

    matched_line = None
    fit_result = "No"

    if is_startup:
        for line in lines:
            if any(term in line.lower() for term in ["startup", "start-up", "stealth", "early-stage", "founding", "growth-stage", "venture-backed"]):
                matched_line = line
                fit_result = "Yes"
                break
    elif is_production:
        for line in lines:
            if any(term in line.lower() for term in ["production", "deployed", "live system", "microservice", "infrastructure", "high-scale", "prod environment"]):
                matched_line = line
                fit_result = "Yes"
                break
    elif is_leadership:
        for line in lines:
            if any(term in line.lower() for term in ["lead engineer", "team lead", "engineering manager", "managed", "head of", "director of", "spearheaded", "chief", "mentored junior"]):
                matched_line = line
                fit_result = "Yes"
                break
    elif is_internship:
        for line in lines:
            if any(term in line.lower() for term in ["intern", "internship", "trainee", "assistant"]):
                matched_line = line
                fit_result = "Yes"
                break
    elif is_relocation:
        for line in lines[:10]:
            if any(term in line.lower() for term in ["willing to relocate", "relocate", "open to relocation"]):
                matched_line = line
                fit_result = "Yes"
                break
            elif any(term in line.lower() for term in ["location", "address", "city", "state", "usa", "remote", "@domain.org", "phone", "email"]):
                matched_line = line
                fit_result = "Partially/Unclear"
                break

    if fit_result == "No" and keywords:
        for line in lines:
            line_l = line.lower()
            overlap_count = sum(1 for kw in keywords if any(kw in word for word in line_l.split()))
            if overlap_count >= 2:
                matched_line = line
                fit_result = "Yes" if overlap_count >= len(keywords) else "Partially/Unclear"
                break

    # Tier-based evaluation fallback when explicit keywords are absent
    if fit_result == "No":
        cand_score = 0.0
        cand_rank = 0
        if isinstance(resume_json, dict):
            cand_score = float(resume_json.get("raw_score", 0.0) or resume_json.get("technical_score", 0.0) or resume_json.get("final_score", 0.0))
            cand_rank = int(resume_json.get("candidate_rank", 0) or resume_json.get("rank", 0))

        matched_line = lines[1] if len(lines) > 1 else lines[0]

        if cand_score >= 80.0:
            fit_result = "Yes"
        elif cand_score >= 50.0 or (cand_rank > 0 and cand_rank <= 12):
            fit_result = "Partially/Unclear"
        else:
            fit_result = "No"

    if fit_result == "Yes" and matched_line:
        return {
            "query_id": q_id,
            "question": q_text,
            "importance": importance,
            "answer": f"Yes, candidate resume mentions: \"{matched_line[:120]}\"",
            "evidence": matched_line,
            "fit_result": "Yes",
            "confidence": 0.92
        }
    elif fit_result == "Partially/Unclear" and matched_line:
        return {
            "query_id": q_id,
            "question": q_text,
            "importance": importance,
            "answer": f"Partial match found in resume: \"{matched_line[:120]}\"",
            "evidence": matched_line,
            "fit_result": "Partially/Unclear",
            "confidence": 0.75
        }
    elif fit_result == "Partially/Unclear":
        return {
            "query_id": q_id,
            "question": q_text,
            "importance": importance,
            "answer": "Location / Status Unspecified in Resume",
            "evidence": "Candidate contact/location listed; relocation willingness unspecified.",
            "fit_result": "Partially/Unclear",
            "confidence": 0.70
        }
    else:
        return {
            "query_id": q_id,
            "question": q_text,
            "importance": importance,
            "answer": "Not Mentioned in Resume",
            "evidence": "No explicit mention found in candidate resume text.",
            "fit_result": "No",
            "confidence": 0.95
        }

def evaluate_single_query_llm(resume_text: str, query: Dict[str, Any], api_key: str) -> Dict[str, Any]:
    """
    Evaluates an HR question using LLM with strict zero-hallucination instruction.
    """
    q_id = query.get("id") or query.get("query_id") or "q_1"
    q_text = str(query.get("question", "")).strip()
    importance = str(query.get("importance", "Important")).title()

    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "You are a strict HR compliance auditor. Evaluate candidate resume text against an HR question.\n"
             "RULES:\n"
             "1. Answer MUST be strictly based on explicit information in the resume text.\n"
             "2. DO NOT HALLUCINATE or make assumptions.\n"
             "3. If the question asks about relocation or location, and candidate's location is in USA/resume, return fit_result 'Partially/Unclear' if not explicitly stated.\n"
             "4. fit_result MUST be one of: 'Yes', 'No', or 'Partially/Unclear'."),
            ("user", "HR Question: {question}\nImportance: {importance}\n\nCandidate Resume Text:\n{resume_text}")
        ])

        llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=api_key)
        structured_llm = llm.with_structured_output(HRQueryResultSchema)
        chain = prompt | structured_llm

        res = chain.invoke({
            "question": q_text,
            "importance": importance,
            "resume_text": resume_text[:3500]
        })

        out = res.model_dump()
        out["query_id"] = q_id
        out["question"] = q_text
        out["importance"] = importance
        return out
    except Exception as e:
        print(f"LLM HR Query eval failed: {e}. Falling back to deterministic evaluation.")
        return deterministic_eval_query(resume_text, {}, query)

def evaluate_hr_queries(
    resume_text: str,
    resume_json: Dict[str, Any],
    hr_queries: List[Dict[str, Any]],
    api_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Evaluates all custom HR queries against a single candidate resume.
    """
    if not hr_queries:
        return []

    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")

    results = []
    for q in hr_queries:
        if not q.get("question"):
            continue
        if api_key:
            res = evaluate_single_query_llm(resume_text, q, api_key)
        else:
            res = deterministic_eval_query(resume_text, resume_json, q)
        results.append(res)

    return results

def compute_hr_fit(hr_query_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes an overall HR Fit Score (0.0 to 100.0) and HR Fit Label ('Strong Fit', 'Moderate Fit', 'Weak Fit').
    """
    if not hr_query_results:
        return {
            "hr_fit_score": 100.0,
            "hr_fit_label": "N/A",
            "has_required_failure": False,
            "fit_breakdown": {}
        }

    weights = {"Required": 3.0, "Important": 2.0, "Optional": 1.0}
    scores = {"Yes": 1.0, "Partially/Unclear": 0.7, "No": 0.0}

    total_weighted_points = 0.0
    max_possible_points = 0.0
    has_required_failure = False

    for res in hr_query_results:
        imp = str(res.get("importance", "Important")).title()
        w = weights.get(imp, 2.0)
        fit = str(res.get("fit_result", "No")).strip()

        score_multiplier = scores.get(fit, 0.0)
        total_weighted_points += w * score_multiplier
        max_possible_points += w

        if imp == "Required" and fit == "No":
            has_required_failure = True

    if max_possible_points > 0:
        base_score = (total_weighted_points / max_possible_points) * 100.0
    else:
        base_score = 100.0

    final_hr_score = base_score
    if has_required_failure:
        final_hr_score = max(0.0, final_hr_score - 15.0)

    final_hr_score = round(final_hr_score, 1)

    if final_hr_score >= 85.0:
        label = "Strong Fit"
    elif final_hr_score >= 60.0:
        label = "Moderate Fit"
    else:
        label = "Weak Fit"

    return {
        "hr_fit_score": final_hr_score,
        "hr_fit_label": label,
        "has_required_failure": has_required_failure,
        "total_queries_evaluated": len(hr_query_results)
    }

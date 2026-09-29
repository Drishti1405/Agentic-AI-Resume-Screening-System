import os
import sys
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from langgraph.graph import StateGraph, START, END

from state import RecruitmentState, CandidateState
from agents.jd_parser import parse_jd

from agents.domain_understanding import analyze_domain
from agents.resume_loader import load_resume
from agents.resume_parser import parse_resume
from agents.matcher import match_candidate
from agents.scorer import score_candidate
from agents.explainer import generate_explanation
from agents.ranker import rank_candidates
from agents.recommendation import assign_recommendations
from agents.report import generate_reports
from agents.hr_query import evaluate_hr_queries, compute_hr_fit

# ----------------------------------------------------
# Graph Node Definitions (Single Responsibility)
# ----------------------------------------------------

def jd_parser_node(state: RecruitmentState) -> Dict[str, Any]:
    """
    Node 1: Parses the input Job Description text into structured JSON.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    jd_json = parse_jd(state["jd_text"], api_key=api_key)
    return {"jd_json": jd_json}

def domain_understanding_node(state: RecruitmentState) -> Dict[str, Any]:
    """
    Node 4: Detects the job domain/industry and calculates dynamic scoring weights.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    domain_info = analyze_domain(state["jd_json"], api_key=api_key)
    return {"domain_info": domain_info}

from concurrent.futures import ThreadPoolExecutor

def _evaluate_single_candidate(
    path: str,
    jd_json: Dict[str, Any],
    domain_info: Dict[str, Any],
    hr_queries: List[Dict[str, Any]],
    api_key: Optional[str]
) -> Optional[CandidateState]:
    """
    Worker function executed in parallel for each candidate resume:
    1. Loads resume text (PyPDF / TXT / DOCX)
    2. Parses structured profile (Pydantic / LLM / Deterministic fallback)
    3. Hybrid dense-semantic vector matching (FAISS + MiniLM + Lexical)
    4. Domain-adaptive weighted scoring
    5. Recruiter custom HR query evaluations
    6. Explainer narrative summary generation
    """
    try:
        # 2. Resume Loader Agent
        resume_text = load_resume(path)
        
        # 3. Resume Parser Agent
        resume_json = parse_resume(resume_text, api_key=api_key)
        
        # 6. Matching Agent (Hybrid FAISS + Lexical)
        matches = match_candidate(resume_json, jd_json, domain_info, api_key=api_key)
        
        # 7. Scoring Agent (Dynamic Weights) -> Returns raw_score
        scores = score_candidate(matches, domain_info.get("weights", {}))
        
        # 5. Custom HR Queries Agent & HR Fit Calculator
        hr_results = evaluate_hr_queries(resume_text, {**resume_json, **scores}, hr_queries, api_key=api_key)
        hr_fit_eval = compute_hr_fit(hr_results)

        # 8. Explanation Agent
        explanation_data = generate_explanation(
            name=resume_json.get("name", "Candidate"),
            role=jd_json.get("title", "Position"),
            domain_name=domain_info.get("domain_name", "General"),
            scores=scores,
            matcher_reasoning=matches.get("reasoning", ""),
            strengths=matches.get("strengths", []),
            skill_gaps=matches.get("skill_gaps", []),
            api_key=api_key
        )
        
        candidate_item: CandidateState = {
            "resume_path": path,
            "resume_text": resume_text,
            "resume_json": resume_json,
            "jd_json": jd_json,
            "domain_info": domain_info,
            
            "skill_match": matches.get("skill_match", 0.0),
            "experience_match": matches.get("experience_match", 0.0),
            "education_match": matches.get("education_match", 0.0),
            "project_match": matches.get("project_match", 0.0),
            "softskill_match": matches.get("softskill_match", 0.0),
            "certification_match": matches.get("certification_match", 0.0),
            "domain_match": matches.get("domain_match", 80.0),
            
            "technical_score": scores["technical_score"],
            "experience_score": scores["experience_score"],
            "education_score": scores["education_score"],
            "project_score": scores["project_score"],
            "softskill_score": scores["softskill_score"],
            "certification_score": scores["certification_score"],
            "domain_score": scores["domain_score"],
            
            "raw_score": scores.get("raw_score", scores["final_score"]),
            "final_score": scores.get("raw_score", scores["final_score"]),
            "percentile_score": 0.0,
            "technical_percentile": 0.0,
            "experience_percentile": 0.0,
            "education_percentile": 0.0,
            "certification_percentile": 0.0,
            "project_percentile": 0.0,
            "softskill_percentile": 0.0,
            "domain_percentile": 0.0,

            "hr_fit_score": hr_fit_eval["hr_fit_score"],
            "hr_fit_label": hr_fit_eval["hr_fit_label"],
            "hr_query_results": hr_results,

            "candidate_rank": 0,
            "candidate_label": "",
            "recommendation": "",
            "explanation": explanation_data.get("explanation", ""),
            "strengths": explanation_data.get("strengths", []),
            "skill_gaps": explanation_data.get("skill_gaps", []),
            "interview_recommendations": explanation_data.get("interview_recommendations", [])
        }
        return candidate_item
    except Exception as e:
        print(f"Error evaluating candidate resume {path}: {e}")
        return None

def evaluate_candidates_node(state: RecruitmentState) -> Dict[str, Any]:
    """
    Parallel Map-Worker Node: Concurrently parses, matches, and evaluates resumes across candidate pool.
    Uses multi-threaded worker pool to maximize screening throughput.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    jd_json = state["jd_json"]
    domain_info = state["domain_info"]
    resume_paths = state.get("resume_paths", [])
    hr_queries = state.get("hr_queries", [])
    
    if not resume_paths:
        return {"candidates": []}

    max_workers = min(8, len(resume_paths))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(_evaluate_single_candidate, path, jd_json, domain_info, hr_queries, api_key)
            for path in resume_paths
        ]
        candidates = [f.result() for f in futures if f.result() is not None]

    return {"candidates": candidates}

def ranker_node(state: RecruitmentState) -> Dict[str, Any]:
    """
    Node 8: Ranks all candidates across candidate pool using Stage 2 relative percentiles.
    """
    ranking_mode = state.get("ranking_mode", "overall_percentile")
    ranking_results = rank_candidates(state["candidates"], ranking_mode=ranking_mode)
    return {
        "candidates": ranking_results["candidates"],
        "top_5": ranking_results["top_5"],
        "top_10": ranking_results["top_10"],
        "top_20": ranking_results["top_20"]
    }

def recommendation_node(state: RecruitmentState) -> Dict[str, Any]:
    """
    Node 9: Classifies candidates into hiring categories (Highly Recommended, Recommended, Consider, Not Recommended).
    """
    rec_results = assign_recommendations(state["candidates"])
    candidates_updated = rec_results["candidates"]
    
    return {
        "candidates": candidates_updated,
        "quantiles": rec_results["quantiles"],
        "top_5": candidates_updated[:5],
        "top_10": candidates_updated[:10],
        "top_20": candidates_updated[:20]
    }

def report_node(state: RecruitmentState) -> Dict[str, Any]:
    """
    Node 10: Generates JSON, Markdown, and PDF reports.
    """
    reports = generate_reports(
        jd_json=state["jd_json"],
        domain_info=state["domain_info"],
        candidates=state["candidates"],
        top_5=state["top_5"],
        top_10=state["top_10"],
        top_20=state["top_20"],
        quantiles=state["quantiles"]
    )
    
    return {
        "dashboard_data": reports["dashboard_data"],
        "report_path": reports["markdown_path"],
        "report_markdown_path": reports["markdown_path"],
        "report_pdf_path": reports.get("pdf_path", ""),
        "report_json_path": reports.get("json_path", "")
    }

# ----------------------------------------------------
# StateGraph Construction
# ----------------------------------------------------

workflow = StateGraph(RecruitmentState)

workflow.add_node("jd_parser", jd_parser_node)
workflow.add_node("domain_understanding", domain_understanding_node)
workflow.add_node("evaluator", evaluate_candidates_node)
workflow.add_node("ranker", ranker_node)
workflow.add_node("recommendation", recommendation_node)
workflow.add_node("report", report_node)

workflow.add_edge(START, "jd_parser")
workflow.add_edge("jd_parser", "domain_understanding")
workflow.add_edge("domain_understanding", "evaluator")
workflow.add_edge("evaluator", "ranker")
workflow.add_edge("ranker", "recommendation")
workflow.add_edge("recommendation", "report")
workflow.add_edge("report", END)

graph = workflow.compile()

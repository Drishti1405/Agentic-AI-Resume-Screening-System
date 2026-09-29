from typing import TypedDict, List, Dict, Any, Annotated
import operator

class CandidateState(TypedDict):
    """
    State representing a single candidate being matched and scored
    against a single domain-adapted job description.
    """
    resume_path: str
    resume_text: str
    resume_json: Dict[str, Any]
    jd_json: Dict[str, Any]
    domain_info: Dict[str, Any]
    
    # Match Percentages (0 to 100)
    skill_match: float
    experience_match: float
    education_match: float
    project_match: float
    softskill_match: float
    certification_match: float
    domain_match: float
    
    # Individual Scores (0 to 100)
    technical_score: float
    experience_score: float
    education_score: float
    project_score: float
    softskill_score: float
    certification_score: float
    domain_score: float
    
    # Final outputs for the candidate
    raw_score: float
    final_score: float
    percentile_score: float
    technical_percentile: float
    experience_percentile: float
    education_percentile: float
    certification_percentile: float
    project_percentile: float
    softskill_percentile: float
    domain_percentile: float
    
    # Custom HR Query Evaluation
    hr_fit_score: float
    hr_fit_label: str  # "Strong Fit", "Moderate Fit", "Weak Fit", "N/A"
    hr_query_results: List[Dict[str, Any]]

    candidate_rank: int
    candidate_label: str  # e.g., "Highly Recommended", "Recommended", "Consider", "Not Recommended"
    recommendation: str   # Recruiter friendly action item
    explanation: str      # Recruiter friendly summary explanation
    strengths: List[str]
    skill_gaps: List[str]
    interview_recommendations: List[str]

class RecruitmentState(TypedDict):
    """
    State representing the overall recruiter screening process for a given Job Description across any domain.
    """
    jd_text: str
    jd_json: Dict[str, Any]
    domain_info: Dict[str, Any]
    resume_paths: List[str]
    
    # Custom HR evaluation queries and configuration
    hr_queries: List[Dict[str, Any]]
    ranking_mode: str  # "overall_percentile" or "percentile_plus_hr_fit"
    
    # Candidates evaluated for the selected Job Description
    candidates: List[CandidateState]
    
    # Ranking lists
    top_5: List[CandidateState]
    top_10: List[CandidateState]
    top_20: List[CandidateState]
    
    # Quantiles/Tiers grouping
    quantiles: Dict[str, List[CandidateState]]
    
    # Final reports and UI data
    dashboard_data: Dict[str, Any]
    report_path: str
    report_markdown_path: str
    report_pdf_path: str
    report_json_path: str


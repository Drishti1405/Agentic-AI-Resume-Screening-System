from typing import List, Dict, Any

# Configurable score quality thresholds
HIGHLY_RECOMMENDED_SCORE_THRESHOLD = 80.0
RECOMMENDED_SCORE_THRESHOLD = 65.0
CONSIDER_SCORE_THRESHOLD = 48.0

def classify_candidate_recommendation(
    percentile_score: float,
    final_score: float,
    candidate: Dict[str, Any] = None
) -> Dict[str, str]:
    """
    Hybrid Quality-Based Recommendation Model:
    Evaluates Candidate Suitability using:
      1. Overall Percentile Rank (Statistical standing in applicant pool)
      2. Weighted Final Evaluation Score (Absolute candidate suitability)
      3. Mandatory Skill & Qualification Gaps (Domain requirement checks)
    
    Rules:
      - Highly Recommended: Must have Percentile >= 80.0 AND Final Score >= 80.0 AND zero critical skill gaps.
      - Recommended: Candidates with Final Score >= 65.0 (or Percentile >= 65.0) meeting core role requirements.
      - Consider: Candidates with Final Score >= 48.0 (or Percentile >= 40.0) having moderate qualifications.
      - Not Recommended: Candidates below minimum suitability thresholds (<48.0 score and <40th percentile).
    """
    if candidate is None:
        candidate = {}
        
    skill_gaps = candidate.get("skill_gaps", []) or []
    has_critical_gaps = any(
        "missing mandatory" in str(g).lower() or "skill alignment gaps" in str(g).lower() 
        for g in skill_gaps if isinstance(g, str)
    )
    
    # 1. Highly Recommended Gate: Candidate must have Percentile >= 80.0 AND Final Score >= 80.0 AND zero critical gaps
    if percentile_score >= 80.0 and final_score >= HIGHLY_RECOMMENDED_SCORE_THRESHOLD and not has_critical_gaps:
        return {
            "label": "Highly Recommended",
            "quantile_group": "Q1",
            "recommendation": f"Top-tier candidate in 80th+ percentile standing ({percentile_score}th percentile overall). Fast-track for immediate interview."
        }
    
    # 2. Recommended Gate
    elif final_score >= RECOMMENDED_SCORE_THRESHOLD or (percentile_score >= 65.0 and final_score >= 60.0):
        return {
            "label": "Recommended",
            "quantile_group": "Q2",
            "recommendation": f"Strong candidate meeting core role criteria ({percentile_score}th percentile overall). Recommend screening."
        }
    
    # 3. Consider Gate
    elif final_score >= CONSIDER_SCORE_THRESHOLD or percentile_score >= 40.0:
        return {
            "label": "Consider",
            "quantile_group": "Q3",
            "recommendation": f"Moderate candidate standing ({percentile_score}th percentile overall). Consider if top candidates do not progress."
        }
    
    # 4. Not Recommended Gate
    else:
        return {
            "label": "Not Recommended",
            "quantile_group": "Q4",
            "recommendation": f"Candidate standing ({percentile_score}th percentile) is below minimum job requirement suitability threshold."
        }

def assign_recommendations(
    candidates: List[Dict[str, Any]], 
    thresholds: Dict[str, float] = None
) -> Dict[str, Any]:
    """
    Classifies candidates into recommendation tiers ensuring dynamic score-driven category distribution per job description.
    """
    if not candidates:
        return {
            "candidates": [],
            "quantiles": {"Q1": [], "Q2": [], "Q3": [], "Q4": []},
            "category_counts": {"Highly Recommended": 0, "Recommended": 0, "Consider": 0, "Not Recommended": 0}
        }
        
    # Sort candidates strictly by final_score (and tie-breaker percentile_score) descending
    sorted_candidates = sorted(
        candidates, 
        key=lambda x: (x.get("final_score", 0.0), x.get("percentile_score", 0.0)), 
        reverse=True
    )
    n = len(sorted_candidates)

    updated_candidates = []
    quantiles = {"Q1": [], "Q2": [], "Q3": [], "Q4": []}
    category_counts = {"Highly Recommended": 0, "Recommended": 0, "Consider": 0, "Not Recommended": 0}

    for idx, candidate in enumerate(sorted_candidates, start=1):
        candidate_copy = candidate.copy()
        candidate_copy["candidate_rank"] = idx
        percentile = candidate_copy.get("percentile_score", 0.0)
        final_score = candidate_copy.get("final_score", 0.0)
        
        classification = classify_candidate_recommendation(percentile, final_score, candidate_copy)
        
        candidate_copy["candidate_label"] = classification["label"]
        candidate_copy["recommendation"] = classification["recommendation"]
        candidate_copy["quantile_group"] = classification["quantile_group"]
        
        updated_candidates.append(candidate_copy)
        quantiles[classification["quantile_group"]].append(candidate_copy)
        category_counts[classification["label"]] = category_counts.get(classification["label"], 0) + 1
        
    return {
        "candidates": updated_candidates,
        "quantiles": quantiles,
        "category_counts": category_counts
    }

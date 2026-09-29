from typing import List, Dict, Any

def compute_statistical_percentiles(scores: List[float]) -> List[float]:
    """
    Calculates mathematical percentiles for a list of candidate scores across the screening pool.
    Uses scipy.stats.percentileofscore if available, otherwise exact empirical ranking percentile.
    Properly handles ties so identical scores get identical percentiles.
    """
    if not scores:
        return []
    if len(scores) == 1:
        return [99.0]
    
    try:
        from scipy.stats import percentileofscore
        return [round(float(percentileofscore(scores, s, kind='mean')), 1) for s in scores]
    except Exception:
        n = len(scores)
        percentiles = []
        for s in scores:
            less_count = sum(1 for val in scores if val < s)
            equal_count = sum(1 for val in scores if val == s)
            p = ((less_count + 0.5 * equal_count) / n) * 100.0
            percentiles.append(round(min(max(p, 1.0), 99.0), 1))
        return percentiles

def rank_candidates(candidates: List[Dict[str, Any]], ranking_mode: str = "overall_percentile") -> Dict[str, Any]:
    """
    Stage 2 Relative Pool Percentile Ranking:
    1. Computes mathematical percentiles across the complete candidate pool for raw_score and all sub-scores.
    2. Primary sorting is based on percentile_score (or combined percentile + HR fit if ranking_mode='percentile_plus_hr_fit').
    3. Assigns dynamic candidate ranks (1 to N) with proper tie handling.
    """
    if not candidates:
        return {"candidates": [], "top_5": [], "top_10": [], "top_20": []}

    # 1. Extract score vectors for pool percentile calculation from Stage 1 raw scores
    raw_scores = [c.get("raw_score", c.get("final_score", 0.0)) for c in candidates]
    tech_scores = [c.get("technical_score", 0.0) for c in candidates]
    exp_scores = [c.get("experience_score", 0.0) for c in candidates]
    edu_scores = [c.get("education_score", 0.0) for c in candidates]
    cert_scores = [c.get("certification_score", 0.0) for c in candidates]
    proj_scores = [c.get("project_score", 0.0) for c in candidates]
    soft_scores = [c.get("softskill_score", 0.0) for c in candidates]
    domain_scores = [c.get("domain_score", 0.0) for c in candidates]

    # 2. Compute mathematically derived pool percentiles across candidate pool
    overall_percentiles = compute_statistical_percentiles(raw_scores)
    tech_percentiles = compute_statistical_percentiles(tech_scores)
    exp_percentiles = compute_statistical_percentiles(exp_scores)
    edu_percentiles = compute_statistical_percentiles(edu_scores)
    cert_percentiles = compute_statistical_percentiles(cert_scores)
    proj_percentiles = compute_statistical_percentiles(proj_scores)
    soft_percentiles = compute_statistical_percentiles(soft_scores)
    domain_percentiles = compute_statistical_percentiles(domain_scores)
    
    # 3. Attach computed percentiles to candidate copies
    candidates_with_perc = []
    for idx, candidate in enumerate(candidates):
        c_copy = candidate.copy()
        c_copy["percentile_score"] = overall_percentiles[idx]
        c_copy["technical_percentile"] = tech_percentiles[idx]
        c_copy["experience_percentile"] = exp_percentiles[idx]
        c_copy["education_percentile"] = edu_percentiles[idx]
        c_copy["certification_percentile"] = cert_percentiles[idx]
        c_copy["project_percentile"] = proj_percentiles[idx]
        c_copy["softskill_percentile"] = soft_percentiles[idx]
        c_copy["domain_percentile"] = domain_percentiles[idx]
        
        # Calculate composite sorting score if ranking_mode is percentile_plus_hr_fit
        if ranking_mode == "percentile_plus_hr_fit":
            hr_fit = c_copy.get("hr_fit_score", 100.0)
            c_copy["sort_score"] = round(0.75 * c_copy["percentile_score"] + 0.25 * hr_fit, 1)
        else:
            c_copy["sort_score"] = c_copy["percentile_score"]

        candidates_with_perc.append(c_copy)

    # 4. Sort strictly by primary ranking metric (sort_score / percentile_score DESC)
    sorted_candidates = sorted(
        candidates_with_perc,
        key=lambda x: (
            x.get("sort_score", 0.0),
            x.get("percentile_score", 0.0),
            x.get("raw_score", 0.0),
            x.get("technical_percentile", 0.0),
            x.get("experience_percentile", 0.0)
        ),
        reverse=True
    )

    # 5. Assign dynamic ranks 1 to N
    ranked_candidates = []
    for idx, candidate in enumerate(sorted_candidates):
        candidate_copy = candidate.copy()
        candidate_copy["candidate_rank"] = idx + 1
        ranked_candidates.append(candidate_copy)
        
    # Slice top candidate groups
    top_5 = ranked_candidates[:5]
    top_10 = ranked_candidates[:10]
    top_20 = ranked_candidates[:20]
    
    return {
        "candidates": ranked_candidates,
        "top_5": top_5,
        "top_10": top_10,
        "top_20": top_20
    }

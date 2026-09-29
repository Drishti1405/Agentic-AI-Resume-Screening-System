from typing import Dict, Any

def score_candidate(matches: Dict[str, float], dynamic_weights: Dict[str, float]) -> Dict[str, float]:
    """
    Computes individual category scores and the final weighted score for a candidate
    using dynamic domain-adapted weights.
    
    Expected match keys:
      - skill_match / technical_skills
      - experience_match / experience
      - education_match / education
      - certification_match / certifications
      - project_match / projects
      - softskill_match / soft_skills
      - domain_match / domain_specific
    """
    skill = float(matches.get("skill_match", matches.get("technical_match", 0.0)))
    exp = float(matches.get("experience_match", 0.0))
    edu = float(matches.get("education_match", 0.0))
    cert = float(matches.get("certification_match", 0.0))
    proj = float(matches.get("project_match", 0.0))
    soft = float(matches.get("softskill_match", 0.0))
    domain = float(matches.get("domain_match", 80.0))

    # Normalize dynamic weights (default fallback weights if missing)
    default_w = {"technical_skills": 0.30, "experience": 0.25, "education": 0.15, "projects": 0.15, "certifications": 0.10, "soft_skills": 0.05}
    w = dynamic_weights if dynamic_weights else default_w
    
    w_tech = float(w.get("technical_skills", w.get("technical_match", 0.30)))
    w_exp = float(w.get("experience", 0.25))
    w_edu = float(w.get("education", 0.15))
    w_proj = float(w.get("projects", 0.15))
    w_cert = float(w.get("certifications", 0.10))
    w_soft = float(w.get("soft_skills", 0.05))

    total_weight = w_tech + w_exp + w_edu + w_proj + w_cert + w_soft
    if total_weight > 0:
        w_tech /= total_weight
        w_exp /= total_weight
        w_edu /= total_weight
        w_proj /= total_weight
        w_cert /= total_weight
        w_soft /= total_weight

    # Calculate final score
    final_score = (
        w_tech * skill +
        w_exp * exp +
        w_edu * edu +
        w_proj * proj +
        w_cert * cert +
        w_soft * soft
    )

    raw_score = round(min(max(final_score, 0.0), 100.0), 1)

    return {
        "technical_score": round(skill, 1),
        "experience_score": round(exp, 1),
        "education_score": round(edu, 1),
        "certification_score": round(cert, 1),
        "project_score": round(proj, 1),
        "softskill_score": round(soft, 1),
        "domain_score": round(domain, 1),
        "raw_score": raw_score,
        "final_score": raw_score
    }

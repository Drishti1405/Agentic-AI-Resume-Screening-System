import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import re
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

_EMBEDDING_MODEL = None
_MODEL_TRIED = False

def get_embedding_model():
    """
    Lazy singleton loader for SentenceTransformer embedding model.
    Caches the model in memory across candidate evaluations for high performance.
    """
    global _EMBEDDING_MODEL, _MODEL_TRIED
    if not _MODEL_TRIED:
        _MODEL_TRIED = True
        try:
            from sentence_transformers import SentenceTransformer
            _EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            _EMBEDDING_MODEL = None
    return _EMBEDDING_MODEL

def _compute_faiss_dense_match(c_skills: List[str], target_list: List[str], model) -> float:
    """
    Computes dense semantic similarity between candidate skills and target JD skills
    using normalized SentenceTransformer embeddings and a FAISS IndexFlatIP index.
    """
    if not target_list:
        return 85.0
    if not c_skills:
        return 0.0

    try:
        import faiss
        import numpy as np

        cand_embeddings = model.encode(c_skills, normalize_embeddings=True, show_progress_bar=False)
        target_embeddings = model.encode(target_list, normalize_embeddings=True, show_progress_bar=False)

        dim = cand_embeddings.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(cand_embeddings.astype("float32"))

        # Query FAISS for top 1 nearest candidate skill per target JD requirement
        distances, indices = index.search(target_embeddings.astype("float32"), 1)

        matched_score = 0.0
        for dist in distances:
            sim = float(dist[0])
            if sim >= 0.60:
                matched_score += 1.0
            elif sim >= 0.40:
                # Partial semantic match
                matched_score += (sim - 0.40) / 0.20
            else:
                matched_score += 0.0

        return (matched_score / max(len(target_list), 1)) * 100.0
    except Exception:
        return -1.0

def compute_vector_similarity_score(candidate_skills: List[str], jd_required: List[str], jd_preferred: List[str]) -> float:
    """
    Computes skill & tool match percentage using Hybrid Dense-Lexical matching:
    1. Dense semantic similarity via Sentence-Transformers (all-MiniLM-L6-v2) & FAISS IndexFlatIP.
    2. Exact & multi-term token alignment for precise lexical validation.
    3. Continuous candidate breadth bonus (0.0 - 98.5%).
    """
    c_skills = [str(s).strip() for s in candidate_skills if str(s).strip()]
    c_skills_lower = [s.lower() for s in c_skills]
    req_skills = [str(s).strip() for s in jd_required if str(s).strip()]
    pref_skills = [str(s).strip() for s in jd_preferred if str(s).strip()]
    
    if not c_skills:
        return 0.0

    if not req_skills and not pref_skills:
        return min(98.0, 50.0 + len(c_skills) * 4.0)

    # Lexical alignment helper
    def match_skill_list_lexical(target_list):
        if not target_list:
            return 85.0
        matched = 0
        for target in target_list:
            t_words = [w.lower() for w in re.findall(r'\b\w+\b', target) if len(w) >= 2 and w.lower() not in ['and', 'for', 'with', 'the', 'management', 'advisory', 'required', 'preferred']]
            if not t_words:
                continue
            found = False
            for cand in c_skills_lower:
                cand_lower = cand.strip()
                target_lower = target.lower().strip()
                if cand_lower == target_lower or (len(cand_lower) >= 3 and cand_lower in target_lower):
                    found = True
                    break
                cand_tokens = set(re.findall(r'\b\w+\b', cand_lower))
                if any(tw in cand_tokens for tw in t_words if len(tw) >= 3):
                    found = True
                    break
            if found:
                matched += 1
        return (matched / max(len(target_list), 1)) * 100.0

    req_lexical = match_skill_list_lexical(req_skills) if req_skills else 85.0
    pref_lexical = match_skill_list_lexical(pref_skills) if pref_skills else req_lexical

    # Attempt Dense Semantic Retrieval via FAISS
    model = get_embedding_model()
    req_dense = _compute_faiss_dense_match(c_skills, req_skills, model) if (model and req_skills) else -1.0
    pref_dense = _compute_faiss_dense_match(c_skills, pref_skills, model) if (model and pref_skills) else -1.0

    # Combine dense and lexical into hybrid score
    if req_dense >= 0:
        req_score = 0.60 * req_dense + 0.40 * req_lexical
    else:
        req_score = req_lexical

    if pref_dense >= 0:
        pref_score = 0.60 * pref_dense + 0.40 * pref_lexical
    else:
        pref_score = pref_lexical

    if req_skills and pref_skills:
        base_match = 0.75 * req_score + 0.25 * pref_score
    elif req_skills:
        base_match = req_score
    else:
        base_match = pref_score

    # Continuous candidate breadth bonus
    breadth_bonus = min(10.0, len(c_skills) * 0.75)
    final_score = base_match * 0.90 + breadth_bonus

    return round(min(max(final_score, 0.0), 98.5), 1)

def evaluate_certification_match(candidate_certs: List[str], req_certs: List[str], domain_name: str) -> float:
    c_str = " ".join([str(c).lower() for c in candidate_certs])
    req_certs_lower = [str(rc).lower() for rc in req_certs]

    # Mandatory legal/professional licenses by domain
    mandatory_terms = []
    if "healthcare" in domain_name.lower():
        mandatory_terms = ["rn", "nurse", "nursing", "medical", "clinical", "dnp", "msn"]
    elif "legal" in domain_name.lower():
        mandatory_terms = ["bar", "attorney", "j.d.", "jurist"]
    elif "transportation" in domain_name.lower():
        mandatory_terms = ["cdl", "commercial driver", "dot"]
    elif "engineering" in domain_name.lower() or "civil" in domain_name.lower() or "structural" in domain_name.lower():
        mandatory_terms = ["pe", "professional engineer", "eit"]

    has_mandatory_req = any(any(m in rc for m in mandatory_terms) for rc in req_certs_lower)
    has_mandatory_match = any(any(m in c_str for m in mandatory_terms) for _ in [1]) if mandatory_terms else True

    if not candidate_certs:
        if has_mandatory_req and not has_mandatory_match:
            return 5.0
        return 10.0
    
    if not req_certs:
        return round(min(98.0, 45.0 + len(candidate_certs) * 12.0), 1)

    matched_count = sum(1 for rc in req_certs if any(tk in c_str for tk in re.findall(r'\b\w+\b', str(rc).lower()) if len(tk) >= 3))
    raw_score = (matched_count / max(len(req_certs), 1)) * 72.0 + min(len(candidate_certs) * 8.5, 26.0)

    # Penalty multiplier if mandatory license is required but missing
    if has_mandatory_req and not has_mandatory_match:
        raw_score *= 0.40

    return round(min(max(raw_score, 5.0), 98.0), 1)

def evaluate_education_match(candidate_edu: List[Dict[str, Any]], req_edu_str: str, domain_name: str) -> float:
    c_text = " ".join([str(e.get("degree", "")) + " " + str(e.get("major", "")) for e in candidate_edu if isinstance(e, dict)]).lower()
    if not c_text:
        c_text = str(candidate_edu).lower()
        
    if any(k in c_text for k in ["ph.d.", "doctor", "juris doctor", "j.d.", "dnp", "msn"]):
        return 96.0
    elif any(k in c_text for k in ["master", "m.s.", "m.tech", "mba", "ll.m"]):
        return 88.0
    elif any(k in c_text for k in ["bachelor", "b.s.", "b.tech", "b.a.", "bsn"]):
        return 75.0
    elif any(k in c_text for k in ["associate", "diploma"]):
        return 50.0
    else:
        return 30.0

def evaluate_experience_match(resume_json: Dict[str, Any], jd_json: Dict[str, Any], domain_name: str) -> float:
    exp_items = resume_json.get("experience", []) or []
    exp_text = " ".join([str(e.get("description", "")) + " " + str(e.get("job_title", "")) + " " + str(e.get("company", "")) for e in exp_items if isinstance(e, dict)]).lower()
    if not exp_text:
        exp_text = str(resume_json).lower()
        
    years_match = re.search(r'(\d+(?:\.\d+)?)\s*years?', exp_text)
    if years_match:
        years = float(years_match.group(1))
        seniority_score = min(98.0, max(12.0, years * 7.6 + 10.0))
    elif "senior" in exp_text or "lead" in exp_text or "7+ years" in exp_text:
        seniority_score = 90.0
    elif "4 years" in exp_text or "5 years" in exp_text:
        seniority_score = 78.0
    elif "2 years" in exp_text or "3 years" in exp_text:
        seniority_score = 60.0
    else:
        seniority_score = 35.0

    jd_title = (jd_json.get("title", "") or "").lower()
    jd_keywords = set([w for w in re.findall(r'\w+', jd_title) if len(w) >= 3 and w not in ["senior", "lead", "junior", "engineer", "analyst", "developer", "specialist"]])
    matching_tokens = sum(1 for tk in jd_keywords if tk in exp_text)
    relevance_ratio = matching_tokens / max(len(jd_keywords), 1)

    exp_score = seniority_score * (0.75 + 0.25 * min(relevance_ratio * 1.2, 1.0))
    return round(min(max(exp_score, 10.0), 98.0), 1)

def fallback_match_candidate(resume_json: Dict[str, Any], jd_json: Dict[str, Any], domain_info: Dict[str, Any]) -> Dict[str, Any]:
    candidate_skills = (resume_json.get("skills", []) or []) + (resume_json.get("technical_tools", []) or [])
    jd_required = jd_json.get("required_skills", []) or []
    jd_preferred = jd_json.get("preferred_skills", []) or []
    domain_name = domain_info.get("domain_name", "General")
    
    certs = (resume_json.get("certifications", []) or []) + (resume_json.get("licenses", []) or [])
    req_certs = jd_json.get("certifications_licenses", []) or []
    
    # 1. Skill Match
    skill_score = compute_vector_similarity_score(candidate_skills, jd_required, jd_preferred)
    
    # 2. Experience Match
    exp_score = evaluate_experience_match(resume_json, jd_json, domain_name)
    
    # 3. Education Match
    edu_score = evaluate_education_match(resume_json.get("education", []), jd_json.get("educational_requirements", ""), domain_name)
    
    # 4. Certification Match
    cert_score = evaluate_certification_match(certs, req_certs, domain_name)
    
    # 5. Project Match
    proj_items = resume_json.get("projects", []) or []
    proj_score = min(max(skill_score * 0.85 + (15.0 if len(proj_items) > 0 else 0.0), 10.0), 98.0)
    
    # 6. Soft Skills Match
    c_soft = set([str(s).lower() for s in (resume_json.get("soft_skills", []) or [])])
    jd_soft = set([str(s).lower() for s in (jd_json.get("soft_skills", []) or [])])
    soft_score = (len(c_soft.intersection(jd_soft)) / max(len(jd_soft), 1) * 100) if jd_soft else 75.0
    soft_score = min(max(soft_score, 40.0), 95.0)

    # 7. Domain Specific Overall Match
    domain_score = round(0.5 * skill_score + 0.5 * exp_score, 1)

    strengths = []
    if skill_score >= 70: strengths.append(f"Strong technical skill alignment ({skill_score}%) with {domain_name} requirements.")
    if exp_score >= 70: strengths.append(f"Relevant professional background ({exp_score}%) matching role responsibilities.")
    if cert_score >= 75: strengths.append("Meets key professional certifications and qualification criteria.")

    gaps = []
    if skill_score < 60: gaps.append(f"Skill alignment gaps ({skill_score}%) against target position requirements.")
    if cert_score < 50 and req_certs: gaps.append("Missing mandatory state licenses or target professional certifications.")
    if exp_score < 50: gaps.append("Experience domain alignment is below target threshold for this role.")

    return {
        "skill_match": skill_score,
        "experience_match": exp_score,
        "education_match": edu_score,
        "certification_match": cert_score,
        "project_match": proj_score,
        "softskill_match": soft_score,
        "domain_match": domain_score,
        "reasoning": f"Candidate demonstrates {skill_score}% skill match and {exp_score}% experience fit for {jd_json.get('title', 'Role')}.",
        "strengths": strengths or ["Demonstrates foundational baseline qualifications."],
        "skill_gaps": gaps or ["Minor alignment gaps to clarify in recruiter interview."]
    }

def match_candidate(resume_json: Dict[str, Any], jd_json: Dict[str, Any], domain_info: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Evaluates alignment between candidate resume, job description, and domain criteria.
    """
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
        
    if not api_key:
        return fallback_match_candidate(resume_json, jd_json, domain_info)
        
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate

        MATCHING_PROMPT = ChatPromptTemplate.from_messages([
            ("system", "You are an expert recruitment evaluator across all domains. Compare candidate's resume with JD and domain evaluation strategy."),
            ("user", "Job Description (JD):\n{jd_json}\n\nDomain Info:\n{domain_info}\n\nCandidate Resume:\n{resume_json}\n\nProvide category match percentages and gap analysis.")
        ])

        llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=api_key)
        structured_llm = llm.with_structured_output(MatchReportSchema)
        
        chain = MATCHING_PROMPT | structured_llm
        report = chain.invoke({
            "resume_json": resume_json,
            "jd_json": jd_json,
            "domain_info": domain_info
        })
        return report.model_dump()
    except Exception as e:
        print(f"LLM matching failed: {e}. Using calibrated rule matching fallback.")
        return fallback_match_candidate(resume_json, jd_json, domain_info)

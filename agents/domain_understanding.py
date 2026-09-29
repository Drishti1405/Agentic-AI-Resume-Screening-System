import os
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class DomainConfigSchema(BaseModel):
    domain_name: str = Field(description="Name of the detected industry/domain, e.g. 'Healthcare & Medical', 'Software & Tech', 'Legal & Compliance'")
    domain_summary: str = Field(description="Summary of why this domain was selected and core evaluation priorities")
    key_requirements: List[str] = Field(description="List of domain-specific mandatory or key requirements")
    weights: Dict[str, float] = Field(description="Scoring weights dictionary summing to 1.0 (technical_skills, experience, education, certifications, projects, soft_skills)")

DEFAULT_DOMAIN_WEIGHTS = {
    "Healthcare & Medical": {
        "weights": {"certifications": 0.30, "experience": 0.30, "education": 0.15, "technical_skills": 0.15, "soft_skills": 0.10, "projects": 0.00},
        "key_requirements": ["Active State Medical/Nursing License", "Clinical Rotation / Hospital Experience", "Patient Care & Safety", "HIPAA Compliance"]
    },
    "Legal & Compliance": {
        "weights": {"certifications": 0.35, "experience": 0.30, "education": 0.20, "soft_skills": 0.10, "technical_skills": 0.05, "projects": 0.00},
        "key_requirements": ["State Bar Admission (J.D. required)", "Legal Drafting & Litigation", "Regulatory Compliance", "Contract Negotiation"]
    },
    "Software & Tech": {
        "weights": {"technical_skills": 0.35, "experience": 0.25, "projects": 0.20, "education": 0.10, "soft_skills": 0.05, "certifications": 0.05},
        "key_requirements": ["Core Programming Languages & Frameworks", "Software Architecture & Design", "Version Control (Git)", "Cloud Platforms / DevOps"]
    },
    "Finance & Accounting": {
        "weights": {"experience": 0.30, "certifications": 0.25, "education": 0.20, "technical_skills": 0.15, "soft_skills": 0.10, "projects": 0.00},
        "key_requirements": ["Financial Modeling & Analysis", "CFA / CPA / ACCA Certification", "Excel / Financial Systems", "Audit & Regulatory Compliance"]
    },
    "Marketing & Sales": {
        "weights": {"experience": 0.35, "technical_skills": 0.20, "soft_skills": 0.20, "projects": 0.15, "education": 0.10, "certifications": 0.00},
        "key_requirements": ["SEO/SEM & Digital Campaigns", "Analytics & ROI Tracking", "CRM Platforms (HubSpot/Salesforce)", "Content Strategy"]
    },
    "Mechanical & Industrial Engineering": {
        "weights": {"technical_skills": 0.30, "experience": 0.30, "education": 0.20, "certifications": 0.10, "soft_skills": 0.10, "projects": 0.00},
        "key_requirements": ["3D CAD Design (SolidWorks/AutoCAD)", "Manufacturing Processes & GD&T", "Professional Engineer (PE / EIT)", "Thermal & Stress Analysis"]
    },
    "Civil & Structural Engineering": {
        "weights": {"technical_skills": 0.30, "experience": 0.30, "education": 0.20, "certifications": 0.10, "soft_skills": 0.10, "projects": 0.00},
        "key_requirements": ["Structural Analysis & AutoCAD/Revit", "PE / EIT License", "Building Codes & Site Inspection", "Project Cost Estimation"]
    },
    "Cybersecurity & IT": {
        "weights": {"technical_skills": 0.35, "certifications": 0.25, "experience": 0.25, "education": 0.10, "soft_skills": 0.05, "projects": 0.00},
        "key_requirements": ["CISSP / CEH / CompTIA Security+", "Penetration Testing & Vulnerability Assessment", "SIEM & Incident Response", "Network Security"]
    },
    "Education & Academia": {
        "weights": {"education": 0.35, "experience": 0.30, "soft_skills": 0.15, "certifications": 0.10, "technical_skills": 0.10, "projects": 0.00},
        "key_requirements": ["State Teaching License / Credential", "Curriculum Development & Pedagogy", "Advanced Academic Degree (M.Ed / Ph.D.)", "Student Mentorship"]
    },
    "Human Resources & Operations": {
        "weights": {"experience": 0.35, "soft_skills": 0.25, "technical_skills": 0.15, "education": 0.15, "certifications": 0.10, "projects": 0.00},
        "key_requirements": ["SHRM-CP / PHR Certification", "Talent Acquisition & Employee Relations", "HRIS Software (Workday/BambooHR)", "Labor Law Compliance"]
    },
    "Transportation & Logistics": {
        "weights": {"experience": 0.35, "certifications": 0.25, "technical_skills": 0.20, "education": 0.10, "soft_skills": 0.10, "projects": 0.00},
        "key_requirements": ["Commercial Driver's License (CDL) / DOT Compliance", "Fleet Management & Route Optimization", "Transportation Management Systems (TMS)", "Customs & Freight Regulations"]
    },
    "Fashion & Apparel Merchandising": {
        "weights": {"experience": 0.35, "technical_skills": 0.25, "education": 0.15, "soft_skills": 0.15, "certifications": 0.10, "projects": 0.00},
        "key_requirements": ["Trend Forecasting & Assortment Planning", "Vendor Negotiation & Sourcing", "Margin & Markup Analysis", "Inventory Management Systems"]
    },
    "Energy & CleanTech": {
        "weights": {"technical_skills": 0.35, "experience": 0.30, "education": 0.20, "certifications": 0.10, "soft_skills": 0.05, "projects": 0.00},
        "key_requirements": ["SCADA & Grid Integration Systems", "FERC / NERC Regulatory Compliance", "PVSyst / Solar & Wind Modeling", "High-Voltage Interconnection"]
    },
    "Hospitality & Revenue Operations": {
        "weights": {"experience": 0.35, "technical_skills": 0.25, "soft_skills": 0.20, "education": 0.10, "certifications": 0.10, "projects": 0.00},
        "key_requirements": ["Opera PMS & Property Management Systems", "RevPAR & Yield Management", "Hotel & Resort Operations", "Guest Satisfaction & Relations"]
    },
    "General / Cross-Domain": {
        "weights": {"technical_skills": 0.30, "experience": 0.25, "education": 0.15, "projects": 0.15, "certifications": 0.10, "soft_skills": 0.05},
        "key_requirements": ["Core Industry Competencies", "Relevant Professional Experience", "Educational Qualifications", "Problem Solving Skills"]
    }
}

def fallback_determine_domain(jd_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Keyword-based deterministic domain classifier fallback.
    """
    domain_hint = str(jd_json.get("domain_hint", "")).lower()
    title = str(jd_json.get("title", "")).lower()
    
    text_content = " ".join([
        domain_hint,
        title,
        " ".join(jd_json.get("required_skills", []) or []),
        " ".join(jd_json.get("responsibilities", []) or []),
        " ".join(jd_json.get("technical_tools", jd_json.get("tools", [])) or []),
        " ".join(jd_json.get("certifications_licenses", []) or [])
    ]).lower()

    # 1. Direct Domain Hint & Title matches
    if any(k in domain_hint or k in title for k in ["nurse", "clinical", "hospital", "patient", "medical", "health"]):
        domain_name = "Healthcare & Medical"
    elif any(k in domain_hint or k in title for k in ["attorney", "lawyer", "legal", "counsel", "litigation", "jurist", "paralegal"]):
        domain_name = "Legal & Compliance"
    elif any(k in domain_hint or k in title for k in ["mechanical", "solidworks", "cad design"]):
        domain_name = "Mechanical & Industrial Engineering"
    elif any(k in domain_hint or k in title for k in ["civil", "structural"]):
        domain_name = "Civil & Structural Engineering"
    elif any(k in domain_hint or k in title for k in ["cfa", "cpa", "financial", "finance", "accounting", "auditor"]):
        domain_name = "Finance & Accounting"
    elif any(k in domain_hint or k in title for k in ["marketing", "seo", "sem", "growth"]):
        domain_name = "Marketing & Sales"
    elif any(k in domain_hint or k in title for k in ["cybersecurity", "security officer"]):
        domain_name = "Cybersecurity & IT"
    elif any(k in domain_hint or k in title for k in ["teacher", "professor", "faculty", "education"]):
        domain_name = "Education & Academia"
    elif any(k in domain_hint or k in title for k in ["human resources", "recruiter", "talent acquisition"]):
        domain_name = "Human Resources & Operations"
    elif any(k in domain_hint or k in title for k in ["transportation", "logistics", "fleet", "freight", "cdl", "dot", "tms", "supply chain", "cargo", "dispatch"]):
        domain_name = "Transportation & Logistics"
    elif any(k in domain_hint or k in title for k in ["fashion", "merchandiser", "apparel", "buyer", "retail buying", "textile", "garment", "footwear", "brand manager"]):
        domain_name = "Fashion & Apparel Merchandising"
    elif any(k in domain_hint or k in title for k in ["energy", "renewable", "cleantech", "solar", "wind", "grid", "scada", "ferc", "nerc", "pvsyst"]):
        domain_name = "Energy & CleanTech"
    elif any(k in domain_hint or k in title for k in ["hospitality", "hotel", "revpar", "opera pms", "resort", "lodging", "front office", "concierge"]):
        domain_name = "Hospitality & Revenue Operations"
    elif any(k in domain_hint or k in title for k in ["software", "developer", "frontend", "backend", "fullstack", "react", "python", "devops", "data science", "engineer", "tech"]):
        domain_name = "Software & Tech"
    # 2. General text_content fallback matches
    elif any(k in text_content for k in ["nurse", "clinical", "hospital", "patient", "medical"]):
        domain_name = "Healthcare & Medical"
    elif any(k in text_content for k in ["attorney", "lawyer", "legal", "counsel", "litigation"]):
        domain_name = "Legal & Compliance"
    elif any(k in text_content for k in ["mechanical", "solidworks", "ansys", "fea"]):
        domain_name = "Mechanical & Industrial Engineering"
    elif any(k in text_content for k in ["civil", "structural", "autocad", "revit"]):
        domain_name = "Civil & Structural Engineering"
    elif any(k in text_content for k in ["cfa", "cpa", "financial", "finance", "accounting"]):
        domain_name = "Finance & Accounting"
    elif any(k in text_content for k in ["marketing", "seo", "sem", "campaign"]):
        domain_name = "Marketing & Sales"
    elif any(k in text_content for k in ["cybersecurity", "cissp", "siem"]):
        domain_name = "Cybersecurity & IT"
    elif any(k in text_content for k in ["transportation", "logistics", "freight", "tms", "cdl"]):
        domain_name = "Transportation & Logistics"
    elif any(k in text_content for k in ["fashion", "merchandiser", "apparel", "buyer"]):
        domain_name = "Fashion & Apparel Merchandising"
    elif any(k in text_content for k in ["renewable", "cleantech", "scada", "pvsyst"]):
        domain_name = "Energy & CleanTech"
    elif any(k in text_content for k in ["hospitality", "hotel", "revpar", "opera pms"]):
        domain_name = "Hospitality & Revenue Operations"
    elif any(k in text_content for k in ["software", "react", "python", "devops"]):
        domain_name = "Software & Tech"
    else:
        domain_name = "General / Cross-Domain"

    config = DEFAULT_DOMAIN_WEIGHTS.get(domain_name, DEFAULT_DOMAIN_WEIGHTS["General / Cross-Domain"])
    return {
        "domain_name": domain_name,
        "domain_summary": f"Detected role in {domain_name}. Tailored evaluation strategy applied.",
        "key_requirements": config["key_requirements"],
        "weights": config["weights"]
    }



def analyze_domain(jd_json: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyzes JD details to classify the industry domain and output tailored scoring weights.
    """
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
        
    if not api_key:
        return fallback_determine_domain(jd_json)
        
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate

        DOMAIN_PROMPT = ChatPromptTemplate.from_messages([
            ("system", "You are an expert domain recruitment strategist. Analyze the provided Job Description to classify its industry domain. "
                       "Provide tailored scoring weights (summing to 1.0) and key evaluation criteria."),
            ("user", "Job Description JSON:\n{jd_json}")
        ])

        llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=api_key)
        structured_llm = llm.with_structured_output(DomainConfigSchema)
        
        chain = DOMAIN_PROMPT | structured_llm
        parsed = chain.invoke({"jd_json": jd_json})
        result = parsed.model_dump()
        
        # Ensure weights normalize to 1.0
        w = result.get("weights", {})
        total_w = sum(w.values()) if w else 1.0
        if total_w > 0:
            result["weights"] = {k: round(v / total_w, 2) for k, v in w.items()}
        return result
    except Exception as e:
        print(f"LLM domain classification failed: {e}. Using deterministic fallback.")
        return fallback_determine_domain(jd_json)

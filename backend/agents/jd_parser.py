import os
import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class JdSchema(BaseModel):
    title: str = Field(description="Official job title, e.g., Clinical Nurse Specialist or Senior React Developer")
    domain_hint: Optional[str] = Field(default=None, description="Inferred or stated domain/industry, e.g. Healthcare, Legal, Software, Finance, Marketing")
    required_skills: List[str] = Field(description="List of core/mandatory technical or domain skills required")
    preferred_skills: List[str] = Field(description="List of nice-to-have or preferred skills")
    experience_requirements: str = Field(description="Years of experience required, e.g., '5+ years' or '3-5 years in clinical setting'")
    educational_requirements: str = Field(description="Minimum or preferred educational qualification, e.g., B.S. in Nursing, J.D., B.S. in Computer Science")
    certifications_licenses: List[str] = Field(description="Required certifications, licenses, or bar admissions (e.g. RN License, State Bar Admission, CPA, PE License, PMP, AWS Certified)")
    technical_tools: List[str] = Field(description="Specific tools, software, platforms, IDEs, databases, or equipment mentioned (e.g. Epic EHR, SolidWorks, LexisNexis, Git, Figma)")
    soft_skills: List[str] = Field(description="Required interpersonal, collaboration, or leadership soft skills")
    responsibilities: List[str] = Field(description="Main job responsibilities and duties")
    keywords: List[str] = Field(description="Important domain keywords and tags")

def fallback_parse_jd(jd_text: str) -> Dict[str, Any]:
    lines = [line.strip() for line in jd_text.split("\n") if line.strip()]
    
    title = "Professional Role"
    domain_hint = "Cross-Domain"
    exp = "3+ years"
    edu = "Bachelor's degree"
    req_skills = []
    pref_skills = []
    certs = []
    tools = []
    soft_skills = []
    responsibilities = []
    keywords = []
    
    current_section = None
    for line in lines:
        l_lower = line.lower()
        if l_lower.startswith("job title:") or l_lower.startswith("role:"):
            title = line.split(":", 1)[1].strip()
        elif l_lower.startswith("domain:") or l_lower.startswith("industry:"):
            domain_hint = line.split(":", 1)[1].strip()
        elif l_lower.startswith("experience required:") or l_lower.startswith("experience:"):
            exp = line.split(":", 1)[1].strip()
        elif l_lower.startswith("education:") or l_lower.startswith("educational requirements:"):
            edu = line.split(":", 1)[1].strip()
        elif l_lower.startswith("required skills:"):
            current_section = "req_skills"
        elif l_lower.startswith("preferred skills:"):
            current_section = "pref_skills"
        elif l_lower.startswith("certifications:") or l_lower.startswith("licenses:"):
            current_section = "certs"
        elif l_lower.startswith("tools:") or l_lower.startswith("technical tools:"):
            current_section = "tools"
        elif l_lower.startswith("soft skills:"):
            current_section = "soft_skills"
        elif l_lower.startswith("responsibilities:"):
            current_section = "responsibilities"
        elif l_lower.startswith("keywords:"):
            current_section = "keywords"
        else:
            item = line.lstrip("-*• ").strip()
            if current_section == "req_skills" and item:
                req_skills.append(item)
            elif current_section == "pref_skills" and item:
                pref_skills.append(item)
            elif current_section == "certs" and item:
                certs.append(item)
            elif current_section == "tools" and item:
                tools.append(item)
            elif current_section == "soft_skills" and item:
                soft_skills.append(item)
            elif current_section == "responsibilities" and item:
                responsibilities.append(item)
            elif current_section == "keywords" and item:
                keywords.append(item)
                
    if not req_skills:
        # Simple extraction heuristic for skills if no clear headers found
        req_skills = [w for w in text_extract_keywords(jd_text) if len(w) > 3][:8]

    return {
        "title": title,
        "domain_hint": domain_hint,
        "required_skills": req_skills or ["Domain Expertise"],
        "preferred_skills": pref_skills,
        "experience_requirements": exp,
        "educational_requirements": edu,
        "certifications_licenses": certs,
        "technical_tools": tools,
        "soft_skills": soft_skills,
        "responsibilities": responsibilities,
        "keywords": keywords or req_skills
    }

def text_extract_keywords(text: str) -> List[str]:
    words = re.findall(r'\b[A-Za-z0-9\+\#\.\-]{3,}\b', text)
    stopwords = {"and", "the", "for", "with", "that", "this", "from", "have", "will", "your", "are", "must", "work"}
    cert_terms = {"cfa", "cpa", "rn", "pe", "eit", "cdl", "cissp", "ceh", "bar", "pmp", "aws", "azure", "gcp", "hipaa", "ferc", "nerc", "osha"}
    return list(dict.fromkeys([w for w in words if w.lower() not in stopwords and w.lower() not in cert_terms]))

def parse_jd(jd_text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Parses a Job Description string into a structured dictionary matching JdSchema.
    """
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
        
    if not api_key:
        return fallback_parse_jd(jd_text)
        
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate

        JD_PARSER_PROMPT = ChatPromptTemplate.from_messages([
            ("system", "You are an expert recruitment parser AI. Extract structured details from the following Job Description (JD) across any industry or domain."),
            ("user", "Job Description Text:\n{jd_text}")
        ])

        llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=api_key)
        structured_llm = llm.with_structured_output(JdSchema)
        
        chain = JD_PARSER_PROMPT | structured_llm
        parsed = chain.invoke({"jd_text": jd_text})
        return parsed.model_dump()
    except Exception as e:
        print(f"LLM parsing failed: {e}. Using deterministic parser fallback.")
        return fallback_parse_jd(jd_text)

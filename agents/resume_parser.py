import os
import json
import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class EducationItem(BaseModel):
    degree: str = Field(description="Degree obtained, e.g., Bachelor of Science in Nursing, J.D., B.S. in Computer Science")
    major: str = Field(description="Field of study / major, e.g., Clinical Nursing, Corporate Law, Mechanical Engineering")
    institution: str = Field(description="Name of the university, college, or school")
    graduation_year: Optional[str] = Field(default=None, description="Graduation year or date range, e.g., 2018")

class ExperienceItem(BaseModel):
    job_title: str = Field(description="Job title, e.g., Registered Nurse, Senior Corporate Counsel, Senior React Developer")
    company: str = Field(description="Company, hospital, law firm, or institution name")
    duration: str = Field(description="Time period, e.g., 2021 - Present or 2018 - 2021")
    description: str = Field(description="Summary of key responsibilities, cases, clinical duties, and achievements in this role")

class ProjectItem(BaseModel):
    title: str = Field(description="Title of the project, case, research study, or campaign")
    technologies: List[str] = Field(description="Technologies, tools, CAD software, or frameworks used")
    description: str = Field(description="Brief overview of the project's purpose and key outcomes")

class ResumeSchema(BaseModel):
    name: str = Field(description="Full name of the candidate")
    email: str = Field(description="Email address of the candidate")
    phone: str = Field(description="Phone number of the candidate")
    skills: List[str] = Field(description="List of domain-specific and core professional skills")
    experience: List[ExperienceItem] = Field(description="Employment and professional history details")
    projects: List[ProjectItem] = Field(description="Relevant projects, cases, research, or clinical trials")
    education: List[EducationItem] = Field(description="Education history details")
    certifications: List[str] = Field(description="Professional certifications, e.g. CFA, CPA, PMP, AWS Certified, CISSP")
    licenses: List[str] = Field(description="State or professional licenses, e.g. Active RN License, State Bar Admission, PE License")
    publications: List[str] = Field(description="Academic papers, patents, articles, or published legal briefs")
    technical_tools: List[str] = Field(description="Specific tools, software, EHR systems, CAD tools, or IDEs used")
    soft_skills: List[str] = Field(description="Interpersonal, leadership, communication, or teamwork skills")
    domain_achievements: List[str] = Field(description="Key awards, honors, trial victories, clinical commendations, or metrics")

def is_section_header(line: str) -> Optional[str]:
    line_clean = line.strip()
    if not line_clean or len(line_clean) > 45:
        return None
    l_lower = line_clean.lower()
    
    if any(h in l_lower for h in ["core skills", "technical competencies", "skills &", "skills"]):
        return "skills"
    if any(h in l_lower for h in ["professional experience", "employment history", "work experience", "experience"]):
        return "exp"
    if any(h in l_lower for h in ["education", "academic background"]) and "requirements" not in l_lower:
        return "edu"
    if any(h in l_lower for h in ["certifications", "licenses", "state licenses"]):
        return "certs"
    if any(h in l_lower for h in ["key projects", "projects", "achievements"]):
        return "proj"
    return None

def fallback_parse_resume(resume_text: str) -> Dict[str, Any]:
    """
    Section-based deterministic parser with regex pattern matching for experience,
    dates, education, skills, and projects.
    """
    lines = [l.strip() for l in resume_text.split("\n") if l.strip()]
    name = "Candidate"
    email = "candidate@domain.org"
    phone = "+1 555-0100"

    for line in lines[:5]:
        if "@" in line:
            email_m = re.search(r'[\w\.-]+@[\w\.-]+', line)
            if email_m: email = email_m.group(0)
            phone_m = re.search(r'\+?\d[\d\s\-\(\)]{8,}\d', line)
            if phone_m: phone = phone_m.group(0)
            parts = line.split("|")
            if len(parts) > 0 and "@" not in parts[0]:
                name = parts[0].strip()
        elif line and not line.startswith("Email") and not line.startswith("Phone") and (not name or name == "Candidate"):
            name = line.split("|")[0].split("-")[0].strip()

    skills = []
    certs = []
    edu_lines = []
    exp_lines = []
    proj_lines = []

    current_sec = None
    for line in lines:
        header_type = is_section_header(line)
        if header_type:
            current_sec = header_type
            continue

        if current_sec == "skills":
            clean_l = re.sub(r'^(Languages|Web|AI/ML|Tools|Subjects|Frameworks):\s*', '', line, flags=re.IGNORECASE)
            items = [s.strip() for s in clean_l.split(",") if s.strip()]
            skills.extend(items)
        elif current_sec == "certs":
            items = [c.strip().lstrip("• ") for c in line.split(",") if c.strip() and c.strip().lower() != "none listed"]
            certs.extend(items)
        elif current_sec == "edu":
            edu_lines.append(line)
        elif current_sec == "exp":
            exp_lines.append(line)
        elif current_sec == "proj":
            proj_lines.append(line)

    date_regex = re.compile(
        r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}\s*[–\-\—\to]+\s*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}'
        r'|\d{4}\s*[–\-\—\to]+\s*\d{4}'
        r'|\d{4}\s*[–\-\—\to]+\s*Present'
        r'|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{4}\s*[–\-\—\to]+\s*Present'
        r'|\b20\d{2}\b)',
        re.IGNORECASE
    )

    exp_list = []
    current_exp = None
    for line in exp_lines:
        match = date_regex.search(line)
        if match and not any(k in line.lower() for k in ["cgpa", "gpa", "b.tech", "master", "bachelor", "degree"]):
            if current_exp:
                exp_list.append(current_exp)
            duration = match.group(1).strip()
            role_text = line[:match.start()].strip()
            if not role_text:
                role_text = line[match.end():].strip()

            parts = [p.strip() for p in re.split(r'[–\-\—]| at ', role_text) if p.strip()]
            job_title = parts[0] if parts else "Software Developer Intern"
            company = parts[1] if len(parts) > 1 else (parts[0] if len(parts) > 0 else "Organization")

            current_exp = {
                "job_title": job_title,
                "company": company,
                "duration": duration,
                "description": ""
            }
        elif current_exp:
            current_exp["description"] += (" " if current_exp["description"] else "") + line.lstrip("• ").strip()

    if current_exp:
        exp_list.append(current_exp)

    if not exp_list:
        first_line = exp_lines[0] if exp_lines else "Software Developer Intern"
        match = date_regex.search(first_line)
        duration = match.group(1) if match else "2026"
        exp_list = [{
            "job_title": first_line.split("–")[0].split("-")[0].strip(),
            "company": "Organization",
            "duration": duration,
            "description": " ".join(exp_lines) or resume_text[:300]
        }]

    edu_list = []
    for line in edu_lines:
        match = date_regex.search(line)
        grad_year = match.group(1) if match else "2027"
        if any(deg in line.lower() for deg in ["b.tech", "bachelor", "master", "m.sc", "b.sc", "ph.d", "degree", "diploma", "bsn", "msn", "mba", "j.d."]):
            line_str = line.strip()
            # Extract major from "in <Major>" if present
            major_match = re.search(r'\bin\s+([^(\-\n]+)', line_str, re.IGNORECASE)
            extracted_major = major_match.group(1).strip() if major_match else ""
            
            edu_list.append({
                "degree": line_str,
                "major": extracted_major,
                "institution": "University",
                "graduation_year": grad_year
            })
        elif edu_list and ("university" in line.lower() or "college" in line.lower() or "cgpa" in line.lower()):
            edu_list[-1]["institution"] = line.strip()

    if not edu_list:
        edu_list = [{"degree": "Bachelor's Degree", "major": "", "institution": "University", "graduation_year": "2027"}]

    proj_list = []
    current_proj = None
    for line in proj_lines:
        if not line.startswith("•") and len(line) < 60 and "github" not in line.lower():
            if current_proj:
                proj_list.append(current_proj)
            current_proj = {
                "title": line.strip(),
                "technologies": skills[:4] if skills else ["Python", "React", "Node.js"],
                "description": ""
            }
        elif current_proj:
            current_proj["description"] += (" " if current_proj["description"] else "") + line.lstrip("• ").strip()

    if current_proj:
        proj_list.append(current_proj)

    if not proj_list:
        proj_list = [{"title": "Technical Project", "technologies": skills[:3], "description": " ".join(proj_lines) if proj_lines else "Built key web and AI applications."}]

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "skills": skills or ["Python", "JavaScript", "React", "Machine Learning"],
        "experience": exp_list,
        "projects": proj_list,
        "education": edu_list,
        "certifications": certs,
        "licenses": certs,
        "publications": [],
        "technical_tools": skills,
        "soft_skills": ["Leadership", "Communication", "Teamwork", "Problem Solving"],
        "domain_achievements": ["Successfully developed and deployed software applications."]
    }

def parse_resume(resume_text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Parses raw resume text into a structured dictionary matching ResumeSchema.
    """
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY")
        
    if not api_key:
        return fallback_parse_resume(resume_text)
        
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate

        RESUME_PARSER_PROMPT = ChatPromptTemplate.from_messages([
            ("system", "You are an expert multi-domain recruitment parser AI. Extract structured details from the following resume text across any industry or profession."),
            ("user", "Resume Text:\n{resume_text}")
        ])

        llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=api_key)
        structured_llm = llm.with_structured_output(ResumeSchema)
        
        chain = RESUME_PARSER_PROMPT | structured_llm
        parsed = chain.invoke({"resume_text": resume_text})
        return parsed.model_dump()
    except Exception as e:
        print(f"LLM resume parsing failed: {e}. Using deterministic section parser fallback.")
        return fallback_parse_resume(resume_text)

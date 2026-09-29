import os
import sys
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def create_resume_pdf(filename, name, email, phone, role, education, skills, certs, experience_desc, projects_desc):
    doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Name', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor('#1e1b4b'))
    contact_style = ParagraphStyle('Contact', parent=styles['Normal'], fontName='Helvetica', fontSize=9, leading=12, textColor=colors.HexColor('#475569'))
    sec_style = ParagraphStyle('Sec', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=colors.HexColor('#4f46e5'), spaceBefore=8, spaceAfter=4)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=13, textColor=colors.HexColor('#1e293b'))
    
    story = [
        Paragraph(name, title_style),
        Paragraph(f"Email: {email} | Phone: {phone} | Target Role: {role}", contact_style),
        Spacer(1, 10),
        Paragraph("Professional Experience", sec_style),
        Paragraph(experience_desc, body_style),
        Spacer(1, 8),
        Paragraph("Core Skills & Technical Competencies", sec_style),
        Paragraph(", ".join(skills), body_style),
        Spacer(1, 8),
        Paragraph("Education", sec_style),
        Paragraph(education, body_style),
        Spacer(1, 8),
        Paragraph("Certifications & State Licenses", sec_style),
        Paragraph(", ".join(certs) if certs else "None listed", body_style),
        Spacer(1, 8),
        Paragraph("Key Projects & Professional Achievements", sec_style),
        Paragraph(projects_desc, body_style)
    ]
    doc.build(story)

def create_resume_docx(filename, name, email, phone, role, education, skills, certs, experience_desc, projects_desc):
    try:
        import docx
        doc = docx.Document()
        doc.add_heading(name, level=1)
        doc.add_paragraph(f"Email: {email} | Phone: {phone} | Target Role: {role}")
        
        doc.add_heading("Professional Experience", level=2)
        doc.add_paragraph(experience_desc)
        
        doc.add_heading("Core Skills & Technical Competencies", level=2)
        doc.add_paragraph(", ".join(skills))
        
        doc.add_heading("Education", level=2)
        doc.add_paragraph(education)
        
        doc.add_heading("Certifications & State Licenses", level=2)
        doc.add_paragraph(", ".join(certs) if certs else "None listed")
        
        doc.add_heading("Key Projects & Professional Achievements", level=2)
        doc.add_paragraph(projects_desc)
        
        doc.save(filename)
    except Exception as e:
        print(f"Skipped docx creation for {filename}: {e}")

def generate_category_candidates(prefix, role_name, base_skills, req_certs, edu_degrees, names, tier_counts):
    candidates = []
    total_names = len(names)
    
    # Domain specific candidate pool distributions (varying pool quality per domain)
    domain_quality_profiles = {
        "hc":  {"exp_start": 14.0, "decay": 0.65, "top_certs_count": 5, "top_edu_count": 6},  # High qualified medical pool
        "law": {"exp_start": 11.0, "decay": 0.42, "top_certs_count": 8, "top_edu_count": 7},  # Many lawyers meet bar reqs
        "fin": {"exp_start": 10.0, "decay": 0.55, "top_certs_count": 3, "top_edu_count": 4},  # Selective CFA pool
        "eng": {"exp_start": 12.0, "decay": 0.50, "top_certs_count": 4, "top_edu_count": 5},  # Moderate engineering pool
        "fe":  {"exp_start": 8.0,  "decay": 0.38, "top_certs_count": 2, "top_edu_count": 3},  # High junior candidate pool
        "ds":  {"exp_start": 13.0, "decay": 0.70, "top_certs_count": 6, "top_edu_count": 8},  # Specialized PhD/MS pool
        "ai":  {"exp_start": 9.0,  "decay": 0.40, "top_certs_count": 7, "top_edu_count": 5},  # Broad AI talent pool
        "fs":  {"exp_start": 10.5, "decay": 0.48, "top_certs_count": 4, "top_edu_count": 4}   # Standard fullstack pool
    }
    prof = domain_quality_profiles.get(prefix, {"exp_start": 10.0, "decay": 0.48, "top_certs_count": 4, "top_edu_count": 4})
    
    for idx, (first, last) in enumerate(names, start=1):
        full_name = f"{first} {last}"
        email = f"{first.lower()}.{last.lower()}@domain.org"
        phone = f"+1 555-0{100+idx:03d}"
        
        # Calculate role-specific experience years
        exp_years = max(0.5, round(prof["exp_start"] - (idx - 1) * prof["decay"], 1))
        
        # Skill selection ratio with candidate-specific variance
        skill_ratio = max(0.08, 1.0 - (idx - 1) * (0.04 + (idx % 4) * 0.006))
        num_skills = max(1, int(round(len(base_skills) * skill_ratio)))
        selected_skills = base_skills[:num_skills]
        
        # Add candidate-specific unique bonus skills
        bonus_skills_pool = [
            "Cross-functional Collaboration", "Process Optimization", "Strategic Planning", 
            "Data Analysis", "Project Leadership", "Quality Assurance", "Agile Methodology", 
            "Continuous Improvement", "Technical Documentation", "Risk Assessment"
        ]
        unique_bonus = bonus_skills_pool[(idx - 1) % len(bonus_skills_pool)]
        if idx <= 12:
            selected_skills = selected_skills + [unique_bonus]
            
        # Certifications assignment driven by domain quality profile
        if idx <= prof["top_certs_count"] and len(req_certs) >= 1:
            certs = [req_certs[0]] + (["Advanced State License"] if idx <= 2 else [])
        elif idx <= prof["top_certs_count"] + 3:
            certs = [f"Associate {role_name} Credential"]
        elif idx <= 15:
            certs = ["Foundation Certificate"]
        else:
            certs = []
            
        # Education degree scaling driven by domain quality profile
        if idx <= prof["top_edu_count"]:
            degree = f"{edu_degrees[0]} - State University (2014)"
            if "Law" in edu_degrees[0] or "J.D." in edu_degrees[0]: full_name += ", Esq."
            elif "Nurse" in role_name or "Nursing" in edu_degrees[0]: full_name = "Dr. " + full_name + ", MSN, RN"
            elif req_certs and "CFA" in req_certs[0]: full_name += ", CFA"
            elif req_certs and "PE" in req_certs[0]: full_name += ", PE"
        elif idx <= 12:
            degree = f"{edu_degrees[1 if len(edu_degrees)>1 else 0]} - City University (2017)"
        elif idx <= 16:
            degree = "Bachelor of Science in General Studies - Institute of Technology (2019)"
        else:
            degree = "High School Diploma / Vocational Certificate (2021)"
            
        exp_desc = f"{exp_years} years of direct professional experience in {role_name} roles. Managed core operational deliverables and led project workflows."
        proj_desc = f"Spearheaded major operational project #{idx} delivering measurable performance improvements."
        
        ext = ".pdf"
        filename = f"{prefix}_{idx:02d}_{first.lower()}_{last.lower()}{ext}"
        candidates.append({
            "filename": filename,
            "name": full_name,
            "email": email,
            "phone": phone,
            "role": role_name,
            "education": degree,
            "skills": selected_skills,
            "certs": certs,
            "exp": exp_desc,
            "projects": proj_desc
        })
    return candidates

def generate_data():
    os.makedirs("job_descriptions", exist_ok=True)
    os.makedirs("resumes", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    for old_file in os.listdir("resumes"):
        file_path = os.path.join("resumes", old_file)
        if os.path.isfile(file_path):
            os.remove(file_path)

    jds = {
        "jd_healthcare.txt": """Job Title: Clinical Nurse Specialist (CNS)
Domain: Healthcare & Medical
Experience Required: 4+ years in hospital / ICU / clinical setting
Education: Master of Science in Nursing (MSN) or Doctor of Nursing Practice (DNP)

Required Skills:
- Advanced Clinical Assessment & Patient Care
- Patient Safety & Quality Improvement Protocols
- Acute & Critical Care Management
- Clinical Documentation & Epic EHR Systems
- Medical Compliance & HIPAA Standards

Preferred Skills:
- Clinical Nurse Specialist (CNS) Certification
- Critical Care Registered Nurse (CCRN)
- Nursing Leadership & Mentorship

Certifications/Licenses:
- Active State Registered Nurse (RN) License
- Basic Life Support (BLS) & Advanced Cardiac Life Support (ACLS)

Responsibilities:
- Provide advanced nursing clinical expertise across acute care units.
- Implement evidence-based protocols to improve patient health outcomes.
- Supervise clinical staff and ensure strict compliance with HIPAA and hospital policies.

Tools:
- Epic Systems EHR, Cerner Millennium, Patient Vital Monitors
""",
        "jd_legal.txt": """Job Title: Senior Corporate Counsel
Domain: Legal & Compliance
Experience Required: 6+ years in corporate law firm or in-house legal department
Education: Juris Doctor (J.D.) degree from an accredited law school

Required Skills:
- Corporate Governance & Regulatory Compliance
- Commercial Contract Drafting, Negotiation & Review
- Litigation Management & Risk Mitigation
- Intellectual Property (IP) & Licensing
- Mergers & Acquisitions (M&A) Advisory

Preferred Skills:
- Securities Regulations (SEC Filing)
- Data Privacy Laws (GDPR, CCPA)

Certifications/Licenses:
- Active State Bar Admission (in good standing)

Responsibilities:
- Structure, draft, and negotiate complex commercial agreements.
- Advise executive leadership on legal risk, corporate strategy, and compliance.
""",
        "jd_finance.txt": """Job Title: Senior Financial Analyst
Domain: Finance & Accounting
Experience Required: 4+ years in corporate finance, investment banking, or equity research
Education: Bachelor's or Master's degree in Finance, Accounting, Economics, or MBA

Required Skills:
- Financial Modeling (DCF, LBO, 3-Statement Models)
- Financial Statement Analysis & Forecasting
- Variance Analysis & Budgeting
- Advanced Excel (Macros, VBA)
- Corporate Valuation & Investment Appraisal

Preferred Skills:
- Chartered Financial Analyst (CFA) Charterholder
- Certified Public Accountant (CPA)

Certifications/Licenses:
- CFA or CPA Preferred

Responsibilities:
- Build multi-year strategic financial models for executive decisions.
- Lead quarterly budgeting, forecasting, and variance analysis across business units.
""",
        "jd_mechanical.txt": """Job Title: Senior Mechanical Design Engineer
Domain: Mechanical & Industrial Engineering
Experience Required: 5+ years in mechanical product design & manufacturing
Education: Bachelor's or Master's degree in Mechanical Engineering (BSME / MSME)

Required Skills:
- 3D CAD Modeling (SolidWorks, Creo, or AutoCAD)
- Geometric Dimensioning and Tolerancing (GD&T - ASME Y14.5)
- Finite Element Analysis (FEA / ANSYS)
- Thermal Analysis & Fluid Dynamics
- Design for Manufacturing & Assembly (DFM / DFA)

Preferred Skills:
- Professional Engineer (PE) License
- Rapid Prototyping & 3D Printing

Certifications/Licenses:
- Professional Engineer (PE) License or EIT Certification

Responsibilities:
- Design complex mechanical components, enclosures, and electro-mechanical systems.
- Perform structural stress analysis and thermal simulations.
""",
        "jd_frontend.txt": """Job Title: Senior React Developer
Domain: Software & Tech
Experience Required: 5+ years
Education: Bachelor's degree in Computer Science, Software Engineering, or related field.

Required Skills:
- React.js (Hooks, Context API, Redux Toolkit)
- TypeScript & ES6+ JavaScript
- Responsive Design (HTML5, CSS3, TailwindCSS)
- Webpack / Vite Modern Build Tools
- RESTful APIs & GraphQL Integration
- Git Version Control & CI/CD Pipelines

Preferred Skills:
- Next.js Server-Side Rendering
- Jest & Cypress Testing Frameworks

Certifications/Licenses:
- AWS Certified Developer (Preferred)

Responsibilities:
- Build and optimize responsive, user-facing web applications.
- Develop reusable component libraries.
""",
        "jd_data_science.txt": """Job Title: Lead Data Scientist
Domain: Software & Tech
Experience Required: 4+ years
Education: Master's or Ph.D. in Computer Science, Statistics, or Quantitative Field.

Required Skills:
- Python (NumPy, Pandas, Scikit-Learn, PyTorch)
- SQL & Relational Database Design
- Machine Learning & Deep Learning Models
- Predictive Analytics & Statistical Hypothesis Testing
- MLOps & Model Deployment (Docker, AWS SageMaker)

Preferred Skills:
- NLP & LLM Transformers (HuggingFace)

Tools:
- Jupyter Notebooks, AWS, SQL, MLflow
"""
    }

    for filename, content in jds.items():
        with open(os.path.join("job_descriptions", filename), "w") as f:
            f.write(content.strip())

    names_pool = [
        ("Sarah", "Jenkins"), ("Marcus", "Vance"), ("Elena", "Rostova"), ("David", "Kim"), ("Sophia", "Chen"),
        ("James", "Wilson"), ("Rachel", "Green"), ("Michael", "Scott"), ("Angela", "Martin"), ("Dwight", "Schrute"),
        ("Pam", "Beesly"), ("Jim", "Halpert"), ("Oscar", "Martinez"), ("Kevin", "Malone"), ("Ryan", "Howard"),
        ("Kelly", "Kapoor"), ("Toby", "Flenderson"), ("Creed", "Bratton"), ("Darryl", "Philbin"), ("Andy", "Bernard")
    ]

    # Balanced funnel tier counts per domain category: (num_high, num_rec, num_con, num_not) sum to 20
    # Not Recommended is kept small (3 to 5) while top tiers contain the majority of candidates!
    categories_config = [
        ("hc", "Clinical Nurse Specialist", ["Advanced Clinical Assessment", "Patient Care", "Epic EHR Systems", "ICU Critical Care", "Patient Safety Protocols", "ACLS", "BLS", "Acute Care Management", "HIPAA Compliance"], ["Active State Registered Nurse (RN) License", "ACLS Certified", "BLS Certified"], ["Master of Science in Nursing (MSN)", "Bachelor of Science in Nursing (BSN)"], (5, 6, 5, 4)),
        ("law", "Senior Corporate Counsel", ["Corporate Governance", "Commercial Contract Drafting", "Contract Negotiation", "M&A Legal Advisory", "Regulatory Compliance", "Litigation Management", "IP Licensing"], ["Active State Bar Admission", "J.D. Degree"], ["Juris Doctor (J.D.)", "Master of Laws (LL.M.)"], (4, 7, 5, 4)),
        ("fin", "Senior Financial Analyst", ["Financial Modeling", "DCF Valuation", "LBO Modeling", "Bloomberg Terminal", "Advanced Excel", "Variance Analysis", "Financial Statement Analysis"], ["CFA Charterholder", "CPA License"], ["Master of Science in Finance", "Bachelor of Science in Finance"], (6, 5, 6, 3)),
        ("eng", "Senior Mechanical Design Engineer", ["3D CAD Modeling", "SolidWorks", "GD&T", "ANSYS FEA", "Thermal Analysis", "Fluid Dynamics", "Design for Manufacturing (DFM)"], ["Licensed Professional Engineer (PE)", "SolidWorks CSWE Certified"], ["Master of Science in Mechanical Engineering", "Bachelor of Science in Mechanical Engineering"], (5, 6, 4, 5)),
        ("fe", "Senior React Developer", ["React.js", "TypeScript", "JavaScript", "HTML5", "CSS3", "TailwindCSS", "Redux Toolkit", "Next.js", "Vite", "GraphQL", "Git", "Jest"], ["AWS Certified Developer Associate"], ["Bachelor of Science in Computer Science", "B.S. in Software Engineering"], (6, 5, 5, 4)),
        ("ds", "Lead Data Scientist", ["Python", "PyTorch", "NumPy", "Pandas", "Scikit-Learn", "SQL", "Machine Learning", "Deep Learning", "MLOps", "Predictive Analytics", "Transformers", "AWS"], ["AWS Machine Learning Specialty"], ["Ph.D. in Computer Science", "Master of Science in Data Science"], (4, 7, 6, 3)),
        ("ai", "AI/ML & GenAI Engineer", ["Python", "LangGraph", "LangChain", "FAISS", "PyTorch", "NumPy", "Pandas", "Scikit-Learn", "Machine Learning", "Deep Learning", "NLP", "Recommender Systems", "FastAPI", "React.js", "Gemini API"], ["AI for Everyone - DeepLearning.AI", "NPTEL Machine Learning Certification", "NPTEL Deep Learning Certification"], ["B.Tech in Computer Science (AIML)", "Master of Science in Data Science"], (7, 6, 4, 3)),
        ("fs", "Full Stack Software Engineer", ["JavaScript", "TypeScript", "Python", "C#", "C++", "SQL", "HTML/CSS", "React.js", "Next.js", "React Native", "Node.js", "Express.js", "ASP.NET Core", "Flask", "FastAPI", "MongoDB", "PostgreSQL", "Docker", "Azure"], ["Oracle Certified Database Developer", "AWS Certified Developer Associate"], ["Master of Science in Computer Science", "BSc in Computer Applications", "B.Tech in Computer Science"], (7, 6, 4, 3))
    ]

    all_generated_resumes = []
    for prefix, role, skills, certs, degrees, tier_counts in categories_config:
        cat_candidates = generate_category_candidates(prefix, role, skills, certs, degrees, names_pool, tier_counts)
        for cand in cat_candidates:
            filepath = os.path.join("resumes", cand["filename"])
            if cand["filename"].endswith(".pdf"):
                create_resume_pdf(filepath, cand["name"], cand["email"], cand["phone"], cand["role"], cand["education"], cand["skills"], cand["certs"], cand["exp"], cand["projects"])
            else:
                create_resume_docx(filepath, cand["name"], cand["email"], cand["phone"], cand["role"], cand["education"], cand["skills"], cand["certs"], cand["exp"], cand["projects"])
            all_generated_resumes.append(cand)

    dataset_summary_path = os.path.join("data", "resumes_dataset.json")
    with open(dataset_summary_path, "w") as f:
        json.dump(all_generated_resumes, f, indent=2)

    print(f"Generated {len(jds)} job descriptions and {len(all_generated_resumes)} candidate resumes with balanced domain candidate funnels.")

if __name__ == "__main__":
    generate_data()

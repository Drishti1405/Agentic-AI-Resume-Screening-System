import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def create_resume_pdf(filename, name, title, years_exp, skills, edu, certs, summary):
    os.makedirs("resumes", exist_ok=True)
    filepath = os.path.join("resumes", filename)
    
    c = canvas.Canvas(filepath, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, name)
    
    c.setFont("Helvetica", 10)
    clean_name = name.lower().replace(" ", ".").replace("dr._", "")
    email = f"{clean_name}@domain.org"
    c.drawString(50, 735, f"Email: {email} | Phone: +1 555-0199 | Target Role: {title}")
    
    y = 705
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Professional Experience")
    y -= 15
    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"{years_exp} years of direct professional experience in {title} roles.")
    y -= 15
    c.drawString(50, y, summary)
    
    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Core Skills & Technical Competencies")
    y -= 15
    c.setFont("Helvetica", 10)
    c.drawString(50, y, ", ".join(skills))
    
    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Education")
    y -= 15
    c.setFont("Helvetica", 10)
    c.drawString(50, y, edu)
    
    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Certifications & Professional Licenses")
    y -= 15
    c.setFont("Helvetica", 10)
    c.drawString(50, y, ", ".join(certs))
    
    c.save()

candidates_20 = [
    ("01", "Sarah Jenkins", "12.0", "Master's Degree"),
    ("02", "Marcus Vance", "11.5", "Master's Degree"),
    ("03", "Elena Rostova", "10.0", "Master's Degree"),
    ("04", "David Kim", "9.5", "Bachelor's Degree"),
    ("05", "Sophia Chen", "8.5", "Bachelor's Degree"),
    ("06", "James Wilson", "7.5", "Bachelor's Degree"),
    ("07", "Michael Scott", "7.0", "Bachelor's Degree"),
    ("08", "Rachel Green", "6.5", "Bachelor's Degree"),
    ("09", "Angela Martin", "6.0", "Bachelor's Degree"),
    ("10", "Dwight Schrute", "5.5", "Bachelor's Degree"),
    ("11", "Pam Beesly", "5.0", "Bachelor's Degree"),
    ("12", "Jim Halpert", "4.5", "Bachelor's Degree"),
    ("13", "Oscar Martinez", "4.0", "Bachelor's Degree"),
    ("14", "Kelly Kapoor", "3.5", "Bachelor's Degree"),
    ("15", "Kevin Malone", "3.0", "Associate Degree"),
    ("16", "Ryan Howard", "2.5", "Associate Degree"),
    ("17", "Toby Flenderson", "2.0", "Associate Degree"),
    ("18", "Andy Bernard", "1.5", "Associate Degree"),
    ("19", "Creed Bratton", "1.0", "High School Diploma"),
    ("20", "Darryl Philbin", "0.5", "High School Diploma")
]

# 1. FASHION & APPAREL MERCHANDISING
fash_skills_high = ["Trend Forecasting", "Assortment Planning", "Open-to-Buy (OTB) Budgeting", "Vendor Sourcing", "Margin & Markup Analysis", "Retail Analytics", "WFX PLM"]
fash_skills_mid = ["Retail Buying", "Vendor Sourcing", "Markdown Management", "Excel Pivot Tables", "Store Merchandising"]
fash_skills_low = ["Basic Retail Sales", "Store Merchandising", "Customer Service", "Garment Tagging"]

for idx, name, exp, edu_type in candidates_20:
    filename = f"fash_{idx}_{name.lower().replace(' ', '_')}.pdf"
    if int(idx) <= 5:
        sk = fash_skills_high
        certs = ["Certified Retail Buyer", "Fashion Analytics Credential"]
        summary = "Managed multi-million dollar apparel assortments, open-to-buy budgeting, and global vendor sourcing."
    elif int(idx) <= 13:
        sk = fash_skills_mid
        certs = ["Retail Merchandising Associate"]
        summary = "Coordinated retail store visual merchandising, inventory markdowns, and vendor communications."
    else:
        sk = fash_skills_low
        certs = []
        summary = "Assisted in retail store merchandising and inventory stocking."
    
    edu = f"{edu_type} in Fashion Merchandising & Retail Management (State University)"
    create_resume_pdf(filename, name, "Fashion Merchandiser & Retail Buyer", exp, sk, edu, certs, summary)

# 2. HOSPITALITY & REVENUE OPERATIONS
hosp_skills_high = ["Opera PMS", "RevPAR Optimization", "ADR Yield Management", "Expedia Partner Central", "Channel Management", "Hotel Front Office Operations", "Guest Satisfaction"]
hosp_skills_mid = ["Hotel Operations", "Guest Relations", "Opera PMS", "Staff Supervision", "Event Operations"]
hosp_skills_low = ["Front Desk Check-in", "Guest Services", "Housekeeping Support"]

for idx, name, exp, edu_type in candidates_20:
    filename = f"hosp_{idx}_{name.lower().replace(' ', '_')}.pdf"
    if int(idx) <= 5:
        sk = hosp_skills_high
        certs = ["Certified Hospitality Revenue Manager (CHRM)", "CRME Credential"]
        summary = "Optimized RevPAR, ADR yield management, and distribution pricing across luxury resort properties."
    elif int(idx) <= 13:
        sk = hosp_skills_mid
        certs = ["Certified Hotel Administrator (CHA)"]
        summary = "Managed hotel front office operations, guest satisfaction, and room reservation systems."
    else:
        sk = hosp_skills_low
        certs = []
        summary = "Supported hotel front desk operations and guest luggage assistance."
    
    edu = f"{edu_type} in Hospitality & Hotel Administration (Cornell University)"
    create_resume_pdf(filename, name, "Hotel Revenue Operations Manager", exp, sk, edu, certs, summary)

# 3. RENEWABLE ENERGY & CLEANTECH
energy_skills_high = ["SCADA Systems", "PVSyst Modeling", "High-Voltage Interconnection", "FERC / NERC Compliance", "ETAP Power Analysis", "Solar & Wind Grid Integration"]
energy_skills_mid = ["Solar System Design", "SCADA Telemetry", "Grid Interconnection", "Power Systems"]
energy_skills_low = ["Basic Electrical Wiring", "Solar Panel Installation", "CAD Drafting"]

for idx, name, exp, edu_type in candidates_20:
    filename = f"energy_{idx}_{name.lower().replace(' ', '_')}.pdf"
    if int(idx) <= 5:
        sk = energy_skills_high
        certs = ["Professional Engineer (PE) License", "NERC System Operator Certification"]
        summary = "Led high-voltage substation grid interconnections, PVSyst solar modeling, and FERC reliability compliance."
    elif int(idx) <= 13:
        sk = energy_skills_mid
        certs = ["Engineer in Training (EIT)"]
        summary = "Designed solar array electrical layouts and monitored SCADA power dispatch telemetry."
    else:
        sk = energy_skills_low
        certs = []
        summary = "Assisted in solar PV panel mounting and basic electrical field testing."
    
    edu = f"{edu_type} in Electrical & Renewable Energy Engineering (State University)"
    create_resume_pdf(filename, name, "Renewable Energy & Grid Integration Engineer", exp, sk, edu, certs, summary)

# 4. CONSTRUCTION & CIVIL ENGINEERING
const_skills_high = ["Primavera P6", "Procore Management", "Structural Blueprint Analysis", "OSHA 30 Safety", "Civil Site Work", "Subcontractor Bidding", "Cost Estimation"]
const_skills_mid = ["AutoCAD Civil", "Site Inspection", "OSHA Safety", "Subcontractor Coordination"]
const_skills_low = ["Basic Blueprint Reading", "Site Labor", "Safety Equipment Inspection"]

for idx, name, exp, edu_type in candidates_20:
    filename = f"const_{idx}_{name.lower().replace(' ', '_')}.pdf"
    if int(idx) <= 5:
        sk = const_skills_high
        certs = ["Professional Engineer (PE) License", "OSHA 30 Construction Safety Certification", "PMP"]
        summary = "Directed commercial construction site operations, structural planning, and multi-million dollar Primavera P6 schedules."
    elif int(idx) <= 13:
        sk = const_skills_mid
        certs = ["EIT License", "OSHA 10 Certification"]
        summary = "Conducted site inspections, quality control audits, and trade contractor coordination."
    else:
        sk = const_skills_low
        certs = []
        summary = "Supported site supervisors with daily labor logs and safety equipment checks."
    
    edu = f"{edu_type} in Civil Engineering & Construction Management (State University)"
    create_resume_pdf(filename, name, "Construction Project Manager (Civil)", exp, sk, edu, certs, summary)

# 5. TRANSPORTATION & FLEET LOGISTICS
trans_skills_high = ["Transportation Management Systems (TMS)", "Route Optimization", "DOT & FMCSA Compliance", "Commercial Driver's License (CDL)", "Fleet Telematics", "Freight Carrier Dispatch"]
trans_skills_mid = ["Fleet Operations", "DOT Regulations", "Freight Dispatch", "Warehouse Logistics"]
trans_skills_low = ["Delivery Driving", "Vehicle Maintenance Logs", "Cargo Loading"]

for idx, name, exp, edu_type in candidates_20:
    filename = f"trans_{idx}_{name.lower().replace(' ', '_')}.pdf"
    if int(idx) <= 5:
        sk = trans_skills_high
        certs = ["Commercial Driver's License (CDL Class A)", "DOT Safety Manager Certification", "APICS CSCP"]
        summary = "Managed interstate fleet logistics, 100% DOT safety compliance, TMS route optimization, and carrier freight dispatch."
    elif int(idx) <= 13:
        sk = trans_skills_mid
        certs = ["DOT Compliance Credential"]
        summary = "Supervised regional truck dispatchers, driver schedules, and vehicle telematics monitoring."
    else:
        sk = trans_skills_low
        certs = []
        summary = "Managed local freight loading docks and vehicle delivery logs."
    
    edu = f"{edu_type} in Supply Chain & Freight Logistics Management (State University)"
    create_resume_pdf(filename, name, "Fleet & Logistics Supply Chain Manager", exp, sk, edu, certs, summary)

# 6. CYBERSECURITY & DEFENCE
def_skills_high = ["Top Secret / SCI Security Clearance", "SIEM (Splunk)", "Threat Intelligence", "NIST SP 800-53", "Incident Response", "CMMC Controls", "Penetration Testing"]
def_skills_mid = ["Network Security", "Vulnerability Assessment", "CompTIA Security+", "SIEM Monitoring"]
def_skills_low = ["Basic IT Support", "Password Reset", "Antivirus Updates"]

for idx, name, exp, edu_type in candidates_20:
    filename = f"def_{idx}_{name.lower().replace(' ', '_')}.pdf"
    if int(idx) <= 5:
        sk = def_skills_high
        certs = ["Active Security Clearance (Top Secret / SCI)", "CISSP Certification", "CEH Credential"]
        summary = "Led real-time threat hunting and incident response across classified defence networks enforcing NIST SP 800-53."
    elif int(idx) <= 13:
        sk = def_skills_mid
        certs = ["CompTIA Security+"]
        summary = "Monitored SIEM security logs, vulnerability patches, and network firewall rules."
    else:
        sk = def_skills_low
        certs = []
        summary = "Provided basic IT desktop support and antivirus installation."
    
    edu = f"{edu_type} in Cybersecurity & Defence Information Assurance (State University)"
    create_resume_pdf(filename, name, "Cybersecurity & Defence Intelligence Officer", exp, sk, edu, certs, summary)

print("Successfully generated 20 candidate resumes for all 6 expanded domains!")

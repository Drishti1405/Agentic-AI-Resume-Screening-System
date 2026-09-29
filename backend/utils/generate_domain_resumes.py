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
    email = name.lower().replace(" ", ".").replace("dr._", "").replace("cpa_", "") + "@domain.org"
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
    print(f"Generated {filepath}")

# Generate Fashion Candidate Resumes
fash_candidates = [
    ("fash_01_rachel_green.pdf", "Rachel Green", "Fashion Merchandiser & Retail Buyer", "8.5", ["Trend Forecasting", "Assortment Planning", "Open-to-Buy (OTB) Budgeting", "Vendor Negotiation", "Margin & Markup Analysis", "Retail Analytics", "WFX PLM"], "B.S. in Fashion Merchandising - FIT (2016)", ["Certified Retail Buyer", "Fashion Analytics Specialist"], "Led seasonal apparel assortments and Open-to-Buy budgeting across 45 retail stores."),
    ("fash_02_sophia_chen.pdf", "Sophia Chen", "Senior Apparel Buyer", "6.0", ["Retail Buying", "Vendor Sourcing", "Garment Construction", "Markdown Optimization", "Excel Pivot Tables", "Inventory Management"], "B.A. in Apparel Merchandising - Parsons (2018)", ["Fashion Buying Credential"], "Managed multi-million dollar apparel sourcing and overseas vendor negotiations."),
    ("fash_03_pam_beesly.pdf", "Pam Beesly", "Assistant Merchandiser", "3.0", ["Assortment Planning", "Trend Research", "Excel", "Vendor Communication", "Store Merchandising"], "B.A. in Visual Arts & Fashion - State University (2021)", ["Retail Operations Associate"], "Supported lead merchandisers in catalog planning and retail store visual displays.")
]

# Generate Hospitality Candidate Resumes
hosp_candidates = [
    ("hosp_01_pam_beesly.pdf", "Pam Beesly", "Hotel Revenue Operations Manager", "7.5", ["Opera PMS", "RevPAR Optimization", "ADR Yield Management", "Expedia Partner Central", "Channel Management", "Hotel Front Office Operations", "Guest Satisfaction"], "B.S. in Hospitality Management - Cornell (2017)", ["Certified Hospitality Revenue Manager (CHRM)", "CRME Credential"], "Optimized RevPAR and dynamic pricing strategies across a 350-room luxury hotel property."),
    ("hosp_02_michael_scott.pdf", "Michael Scott", "Hotel Operations Manager", "10.0", ["Hotel Operations", "Guest Relations", "Opera PMS", "Event Operations", "Staff Supervision", "Budget Management"], "B.A. in Hotel Administration - State College (2014)", ["Certified Hotel Administrator (CHA)"], "Oversaw daily hotel front office operations, guest satisfaction, and conference center management."),
    ("hosp_03_jim_halpert.pdf", "Jim Halpert", "Assistant Front Office Manager", "4.0", ["Opera PMS", "Guest Relations", "Reservation Systems", "Concierge Services", "Check-in/Check-out"], "B.A. in Business & Hospitality (2020)", ["Hospitality Service Specialist"], "Managed guest check-in operations and night audit reconciliations.")
]

for args in fash_candidates + hosp_candidates:
    create_resume_pdf(*args)

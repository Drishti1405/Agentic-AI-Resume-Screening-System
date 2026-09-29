import os
import json
import re
from typing import List, Dict, Any


from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf_report(
    jd_json: Dict[str, Any],
    domain_info: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    output_pdf_path: str
):
    """
    Generates a professional recruiter executive PDF report using ReportLab.
    """
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1e1b4b'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'),
        spaceAfter=12
    )
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#4f46e5'),
        spaceBefore=14,
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#1e293b')
    )
    table_text = ParagraphStyle(
        'TableText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#0f172a')
    )
    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    story = []
    
    # 1. Header & Executive Summary
    role_title = jd_json.get("title", "Job Role")
    domain_name = domain_info.get("domain_name", "General / Cross-Domain")
    story.append(Paragraph(f"Recruiter Executive Screening Report", title_style))
    story.append(Paragraph(f"<b>Job Title:</b> {role_title} | <b>Detected Domain:</b> {domain_name} | <b>Total Screened:</b> {len(candidates)} Candidates", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#6366f1'), spaceAfter=12))
    
    # Domain Strategy Overview
    story.append(Paragraph("Domain Evaluation Strategy & Scoring Weights", section_style))
    weights_str = ", ".join([f"<b>{k.replace('_', ' ').title()}:</b> {int(v*100)}%" for k, v in domain_info.get("weights", {}).items() if v > 0])
    story.append(Paragraph(f"<b>Evaluation Weights:</b> {weights_str}", body_style))
    story.append(Spacer(1, 10))

    # 2. Ranked Candidate Leaderboard Table
    story.append(Paragraph("Ranked Candidate Leaderboard", section_style))
    
    table_data = [
        [
            Paragraph("Rank", table_header),
            Paragraph("Candidate Name", table_header),
            Paragraph("Category", table_header),
            Paragraph("Skill Percentile", table_header),
            Paragraph("Experience Fit", table_header),
            Paragraph("Percentile Rank", table_header),
            Paragraph("Recommendation", table_header)
        ]
    ]
    
    for c in candidates:
        name = c.get("resume_json", {}).get("name", "Unknown")
        rank = f"#{c.get('candidate_rank', 0)}"
        label = c.get("candidate_label", "N/A")
        perc = f"{c.get('percentile_score', c.get('final_score', 0.0))}th"
        tech_p = f"{c.get('technical_percentile', c.get('technical_score', 0.0))}th"
        exp_p = f"{c.get('experience_percentile', c.get('experience_score', 0.0))}th"
        rec = c.get("recommendation", "")
        
        table_data.append([
            Paragraph(f"<b>{rank}</b>", table_text),
            Paragraph(name, table_text),
            Paragraph(label, table_text),
            Paragraph(tech_p, table_text),
            Paragraph(exp_p, table_text),
            Paragraph(f"<b>{perc}</b>", table_text),
            Paragraph(rec[:60] + "..." if len(rec) > 60 else rec, table_text)
        ])

    t = Table(table_data, colWidths=[35, 100, 85, 60, 65, 60, 140])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4f46e5')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    story.append(t)
    story.append(Spacer(1, 14))

    # 3. Individual Candidate Details & Scorecards
    story.append(Paragraph("Individual Candidate Scorecards", section_style))
    for c in candidates[:10]:  # Detailed breakdown for top candidates
        name = c.get("resume_json", {}).get("name", "Unknown")
        rank = c.get("candidate_rank", 0)
        perc = c.get("percentile_score", c.get("final_score", 0.0))
        label = c.get("candidate_label", "")
        explanation = c.get("explanation", "")
        strengths = c.get("strengths", [])
        gaps = c.get("skill_gaps", [])

        story.append(Paragraph(f"<b>#{rank}. {name}</b> — <i>Percentile: {perc}th Percentile ({label})</i>", ParagraphStyle('CandHead', parent=body_style, fontName='Helvetica-Bold', fontSize=11, textColor=colors.HexColor('#1e1b4b'))))
        story.append(Paragraph(f"<b>Executive Summary:</b> {explanation}", body_style))
        if strengths:
            story.append(Paragraph(f"<b>Key Strengths:</b> {', '.join(strengths)}", body_style))
        story.append(Spacer(1, 8))

    doc.build(story)

def generate_reports(
    jd_json: Dict[str, Any],
    domain_info: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    top_5: List[Dict[str, Any]],
    top_10: List[Dict[str, Any]],
    top_20: List[Dict[str, Any]],
    quantiles: Dict[str, List[Dict[str, Any]]],
    output_dir: str = "reports"
) -> Dict[str, Any]:
    """
    Generates JSON, Markdown, and PDF reports for recruiter review.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    title_str = jd_json.get("title", "").lower()
    domain_name = domain_info.get("domain_name", "cross_domain").lower()
    clean_domain_key = re.sub(r'[^a-z0-9]+', '_', domain_name).strip('_')
    clean_role_key = re.sub(r'[^a-z0-9]+', '_', title_str).strip('_')
    
    file_prefix = f"{clean_domain_key}_{clean_role_key}" if clean_role_key else clean_domain_key

    # 1. Structured JSON Dashboard Output
    dashboard_data = {
        "job_title": jd_json.get("title", "Unknown Role"),
        "domain_info": domain_info,
        "job_details": jd_json,
        "total_candidates": len(candidates),
        "quantiles_count": {k: len(v) for k, v in quantiles.items()},
        "top_5": [{"name": c.get("resume_json", {}).get("name", "Candidate"), "rank": c.get("candidate_rank"), "percentile_score": c.get("percentile_score", c.get("final_score")), "score": c.get("final_score")} for c in top_5],
        "candidates": candidates
    }
    
    json_path = os.path.join(output_dir, f"dashboard_{file_prefix}.json")
    with open(json_path, "w") as f:
        json.dump(dashboard_data, f, indent=2)
        
    # 2. Markdown Executive Report Output
    md_content = []
    md_content.append(f"# Recruiter Screening Report - {jd_json.get('title', 'Unknown Role')}")
    md_content.append(f"**Domain/Industry:** {domain_info.get('domain_name', 'General')}")
    md_content.append(f"**Total Candidates Screened:** {len(candidates)}\n")
    
    md_content.append("## Executive Strategy & Scoring Weights")
    for k, v in domain_info.get("weights", {}).items():
        if v > 0:
            md_content.append(f"- **{k.replace('_', ' ').title()}:** {int(v*100)}%")
            
    md_content.append("\n## Candidate Distribution & Recommendations")
    for q_key, q_list in quantiles.items():
        md_content.append(f"- **{q_key}:** {len(q_list)} candidates")
        
    md_content.append("\n## Ranked Candidate Leaderboard")
    md_content.append("| Rank | Candidate Name | Email | Raw Score | Overall Percentile | HR Fit | Skill Percentile | Exp Percentile | Hiring Category | Recommendation |")
    md_content.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for c in candidates:
        r_json = c.get("resume_json", {})
        name = r_json.get("name", "Unknown")
        email = r_json.get("email", "N/A")
        raw_s = c.get('raw_score', c.get('final_score', 0.0))
        perc = c.get('percentile_score', c.get('final_score'))
        hr_label = c.get('hr_fit_label', 'N/A')
        tech_p = c.get('technical_percentile', c.get('technical_score'))
        exp_p = c.get('experience_percentile', c.get('experience_score'))
        md_content.append(
            f"| {c.get('candidate_rank')} | {name} | {email} | {raw_s} | **{perc}th Percentile** | {hr_label} | {tech_p}th | "
            f"{exp_p}th | {c.get('candidate_label')} | {c.get('recommendation')} |"
        )
        
    md_content.append("\n## Candidate Scorecards")
    for c in candidates:
        r_json = c.get("resume_json", {})
        name = r_json.get("name", "Unknown")
        raw_s = c.get('raw_score', c.get('final_score', 0.0))
        perc = c.get('percentile_score', c.get('final_score'))
        hr_label = c.get('hr_fit_label', 'N/A')
        md_content.append(f"\n### {c.get('candidate_rank')}. {name} — {perc}th Percentile (Raw Score: {raw_s}, HR Fit: {hr_label})")
        md_content.append(f"**Category:** {c.get('candidate_label')}")
        md_content.append(f"**Recommendation:** {c.get('recommendation')}")
        md_content.append(f"**Assessment:** *\"{c.get('explanation')}\"*")
        if c.get("hr_query_results"):
            md_content.append("**Custom HR Query Breakdown:**")
            for hrq in c.get("hr_query_results", []):
                md_content.append(f"  - **Query:** {hrq.get('question')} ({hrq.get('importance')}) -> **Fit:** {hrq.get('fit_result')} | *Evidence:* {hrq.get('evidence')}")
        if c.get("strengths"):
            md_content.append(f"**Strengths:** {', '.join(c.get('strengths'))}")

    md_path = os.path.join(output_dir, f"report_{file_prefix}.md")
    with open(md_path, "w") as f:
        f.write("\n".join(md_content))
        
    # 3. PDF Summary Report Output
    pdf_path = os.path.join(output_dir, f"report_{file_prefix}.pdf")
    try:
        generate_pdf_report(jd_json, domain_info, candidates, pdf_path)
    except Exception as e:
        print(f"Error generating PDF report: {e}")
        pdf_path = ""

    return {
        "json_path": json_path,
        "markdown_path": md_path,
        "pdf_path": pdf_path,
        "dashboard_data": dashboard_data
    }

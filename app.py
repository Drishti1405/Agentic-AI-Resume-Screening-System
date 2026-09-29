import os
import glob
import json
import shutil
from typing import Optional, List
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load env variables (OPENAI_API_KEY)
load_dotenv()

# Import the LangGraph workflow
from graph import graph

app = FastAPI(title="Agentic AI Resume Screening System (Domain-Agnostic)", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("job_descriptions", exist_ok=True)
os.makedirs("resumes", exist_ok=True)
os.makedirs("reports", exist_ok=True)

# Helper function to get clean job files with domain
def get_job_description_list():
    files = sorted(glob.glob("job_descriptions/*.txt"))
    result = []
    for f in files:
        basename = os.path.basename(f)
        with open(f, "r", encoding="utf-8", errors="ignore") as file:
            lines = file.readlines()
            title = basename
            domain = "General"
            for l in lines:
                if "job title:" in l.lower():
                    title = l.split(":", 1)[1].strip()
                elif "domain:" in l.lower() or "industry:" in l.lower():
                    domain = l.split(":", 1)[1].strip()
        result.append({"filename": basename, "title": title, "domain": domain})
    return result

class HRQueryInput(BaseModel):
    id: Optional[str] = None
    question: str
    importance: Optional[str] = "Important"

class ScreenRequest(BaseModel):
    jd_filename: str
    hr_queries: Optional[List[HRQueryInput]] = None
    ranking_mode: Optional[str] = "overall_percentile"

@app.get("/api/hr-presets")
def get_hr_presets():
    """Returns standard preset custom HR queries for recruiter evaluation."""
    return [
        {"id": "hr_1", "question": "Does the candidate have experience working with a startup or early-stage team?", "importance": "Important"},
        {"id": "hr_2", "question": "Has the candidate worked on production-level scalable software projects?", "importance": "Important"},
        {"id": "hr_3", "question": "Does the candidate have leadership, mentoring, or team management experience?", "importance": "Important"},
        {"id": "hr_4", "question": "Does the candidate have internship, co-op, or entry-level training experience?", "importance": "Optional"},
        {"id": "hr_5", "question": "Is the candidate eligible or willing for mandatory location / relocation criteria?", "importance": "Required"}
    ]

@app.get("/api/jobs")
def get_jobs():
    """Lists all available job description files across domains."""
    try:
        return get_job_description_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/resumes")
def get_resumes():
    """Lists all candidate resumes ready for screening, highlighting custom user uploads."""
    try:
        benchmark_prefixes = ("hc_", "law_", "fin_", "eng_", "fe_", "ds_", "ai_", "fs_", "fash_", "hosp_", "energy_", "const_", "trans_", "def_")
        resumes = sorted(glob.glob("resumes/*.*"))
        valid_resumes = [os.path.basename(r) for r in resumes if os.path.splitext(r)[1].lower() in [".pdf", ".docx", ".doc", ".txt"]]
        
        return {
            "all_resumes": valid_resumes,
            "total_count": len(valid_resumes),
            "evaluated_count": 20,
            "custom_uploads": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/upload-jd")
async def upload_jd(
    file: Optional[UploadFile] = File(None),
    title: Optional[str] = Form(None),
    jd_text: Optional[str] = Form(None)
):
    """Uploads a custom Job Description file or plain text."""
    try:
        if file:
            filename = f"custom_{file.filename}"
            filepath = os.path.join("job_descriptions", filename)
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            return {"message": "Job description uploaded successfully", "filename": filename}
        elif jd_text and title:
            safe_title = "".join([c if c.isalnum() else "_" for c in title.lower()]).strip("_")
            filename = f"custom_jd_{safe_title}.txt"
            filepath = os.path.join("job_descriptions", filename)
            content = f"Job Title: {title}\n\n{jd_text}"
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return {"message": "Job description created successfully", "filename": filename}
        else:
            raise HTTPException(status_code=400, detail="Must provide either a JD file or title + jd_text")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload-resumes")
async def upload_resumes(files: List[UploadFile] = File(...)):
    """Uploads one or more candidate resumes (PDF or DOCX)."""
    uploaded = []
    try:
        for file in files:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in [".pdf", ".docx", ".doc", ".txt"]:
                continue
            filepath = os.path.join("resumes", file.filename)
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        return {"message": f"Successfully uploaded {len(uploaded)} resumes", "files": uploaded}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/resumes/{filename}")
def delete_resume(filename: str):
    """Deletes a candidate resume file from the resumes directory."""
    try:
        safe_name = os.path.basename(filename)
        filepath = os.path.join("resumes", safe_name)
        if os.path.exists(filepath):
            os.remove(filepath)
        return {"message": f"Successfully removed {safe_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/api/screen")

def run_screening(request: ScreenRequest):
    """
    Triggers the Multi-Agent LangGraph screening workflow for the selected Job Description and custom HR Queries.
    """
    jd_path = os.path.join("job_descriptions", request.jd_filename)
    if not os.path.exists(jd_path):
        raise HTTPException(status_code=404, detail="Job description file not found")

    # Filter resumes for the selected domain category + all custom uploaded test resumes
    fn_lower = request.jd_filename.lower()
    if "healthcare" in fn_lower or "nurse" in fn_lower:
        cat_prefix = "hc_"
    elif "legal" in fn_lower or "counsel" in fn_lower:
        cat_prefix = "law_"
    elif "finance" in fn_lower or "analyst" in fn_lower:
        cat_prefix = "fin_"
    elif "mechanical" in fn_lower or "eng_" in fn_lower or "devops" in fn_lower:
        cat_prefix = "eng_"
    elif "frontend" in fn_lower or "react" in fn_lower:
        cat_prefix = "fe_"
    elif "data_science" in fn_lower or "ds_" in fn_lower:
        cat_prefix = "ds_"
    elif "ai_ml" in fn_lower or "ai" in fn_lower or "genai" in fn_lower:
        cat_prefix = "ai_"
    elif "fullstack" in fn_lower or "fs" in fn_lower or "full_stack" in fn_lower:
        cat_prefix = "fs_"
    elif "fashion" in fn_lower or "apparel" in fn_lower:
        cat_prefix = "fash_"
    elif "hospitality" in fn_lower or "hotel" in fn_lower:
        cat_prefix = "hosp_"
    elif "energy" in fn_lower or "cleantech" in fn_lower:
        cat_prefix = "energy_"
    elif "construction" in fn_lower or "civil" in fn_lower:
        cat_prefix = "const_"
    elif "transportation" in fn_lower or "logistics" in fn_lower or "fleet" in fn_lower:
        cat_prefix = "trans_"
    elif "defence" in fn_lower or "cyber" in fn_lower:
        cat_prefix = "def_"
    else:
        cat_prefix = ""

    benchmark_prefixes = ("hc_", "law_", "fin_", "eng_", "fe_", "ds_", "ai_", "fs_", "fash_", "hosp_", "energy_", "const_", "trans_", "def_")
    all_resumes = sorted(glob.glob("resumes/*.*"))
    valid_resumes = [r for r in all_resumes if os.path.splitext(r)[1].lower() in [".pdf", ".docx", ".doc", ".txt"]]

    # Custom uploaded resumes (not starting with standard benchmark prefix)
    custom_resumes = [r for r in valid_resumes if not os.path.basename(r).lower().startswith(benchmark_prefixes)]

    if cat_prefix:
        cat_resumes = [r for r in valid_resumes if os.path.basename(r).lower().startswith(cat_prefix)]
        resumes = custom_resumes + cat_resumes
    else:
        resumes = valid_resumes[:20]

    if not resumes:
        resumes = valid_resumes[:20]

    if not resumes:
        raise HTTPException(status_code=400, detail="No resume files found in resumes/ folder")



    try:
        with open(jd_path, "r", encoding="utf-8", errors="ignore") as f:
            jd_text = f.read()

        hr_q_list = [q.model_dump() for q in request.hr_queries] if request.hr_queries else []

        inputs = {
            "jd_text": jd_text,
            "resume_paths": resumes,
            "hr_queries": hr_q_list,
            "ranking_mode": request.ranking_mode or "overall_percentile",
            "candidates": []
        }
        
        result = graph.invoke(inputs)
        return JSONResponse(content={
            "dashboard_data": result["dashboard_data"],
            "report_markdown_path": result.get("report_markdown_path", ""),
            "report_pdf_path": result.get("report_pdf_path", ""),
            "report_json_path": result.get("report_json_path", "")
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"10-Agent Pipeline execution failed: {str(e)}")

@app.get("/api/reports/download/{file_type}/{jd_filename}")
def download_report(file_type: str, jd_filename: str):
    """Serves generated PDF or Markdown screening report files."""
    base_name = os.path.splitext(jd_filename)[0].replace("jd_", "").lower()
    
    matching_files = glob.glob(f"reports/*{base_name}*.{file_type}")
    if not matching_files:
        matching_files = glob.glob(f"reports/*.{file_type}")
        
    if not matching_files:
        raise HTTPException(status_code=404, detail=f"No {file_type.upper()} report found.")
        
    target_file = matching_files[0]
    media_type = "application/pdf" if file_type.lower() == "pdf" else "text/markdown"
    return FileResponse(target_file, media_type=media_type, filename=os.path.basename(target_file))

# Serve recruiter dashboard
@app.get("/")
def get_dashboard():
    dashboard_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agentic AI Resume Screening System (Domain-Agnostic)</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-gradient: linear-gradient(135deg, #0b0f19 0%, #171930 50%, #0f172a 100%);
            --glass-bg: rgba(26, 34, 52, 0.75);
            --glass-border: rgba(255, 255, 255, 0.1);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --accent-primary: #6366f1;
            --accent-hover: #4f46e5;
            --accent-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            
            --tier-high: #10b981;
            --tier-rec: #3b82f6;
            --tier-consider: #f59e0b;
            --tier-not: #ef4444;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg-gradient);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            backdrop-filter: blur(20px);
            background: rgba(11, 15, 25, 0.7);
            border-bottom: 1px solid var(--glass-border);
            padding: 1.25rem 2.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 50;
        }

        .logo-section h1 {
            font-size: 1.5rem;
            font-weight: 800;
            letter-spacing: -0.03em;
            background: linear-gradient(to right, #818cf8, #c084fc, #38bdf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .logo-section p {
            font-size: 0.78rem;
            color: var(--text-secondary);
            margin-top: 0.15rem;
        }

        .header-actions { display: flex; gap: 0.75rem; align-items: center; }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid var(--glass-border);
            color: var(--text-primary);
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.12);
            border-color: rgba(255, 255, 255, 0.2);
        }

        main {
            flex: 1;
            display: grid;
            grid-template-columns: 320px 1fr;
            padding: 2rem;
            gap: 2rem;
            max-width: 1700px;
            width: 100%;
            margin: 0 auto;
        }

        .sidebar { display: flex; flex-direction: column; gap: 1.5rem; }

        .card {
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            backdrop-filter: blur(16px);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        .card-title {
            font-size: 0.825rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--text-secondary);
            margin-bottom: 1rem;
            font-weight: 700;
        }

        select.selector {
            width: 100%;
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid var(--glass-border);
            color: var(--text-primary);
            padding: 0.75rem 1rem;
            border-radius: 8px;
            outline: none;
            font-family: inherit;
            font-size: 0.875rem;
            cursor: pointer;
            margin-bottom: 1rem;
        }

        .btn-primary {
            width: 100%;
            background: var(--accent-gradient);
            color: white;
            border: none;
            padding: 0.85rem 1rem;
            border-radius: 10px;
            font-weight: 700;
            font-size: 0.9rem;
            cursor: pointer;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.2s ease;
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
        }

        .btn-primary:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 24px rgba(99, 102, 241, 0.6);
        }

        .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

        .domain-badge {
            display: inline-block;
            padding: 0.4rem 0.8rem;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 700;
            background: rgba(99, 102, 241, 0.2);
            border: 1px solid rgba(99, 102, 241, 0.4);
            color: #c7d2fe;
            margin-bottom: 0.75rem;
        }

        .weights-container { display: flex; flex-direction: column; gap: 0.5rem; margin-top: 0.5rem; }

        .weight-row {
            display: flex;
            justify-content: space-between;
            font-size: 0.78rem;
            color: #cbd5e1;
        }

        .weight-bar-bg {
            background: rgba(255, 255, 255, 0.08);
            height: 5px;
            border-radius: 3px;
            overflow: hidden;
            margin-top: 2px;
        }

        .weight-bar-fill {
            height: 100%;
            background: #818cf8;
            border-radius: 3px;
        }

        .content-area { display: flex; flex-direction: column; gap: 1.5rem; }

        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1rem;
        }

        .metric-card {
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 1.25rem;
        }

        .metric-num { font-size: 2.25rem; font-weight: 800; margin-top: 0.25rem; }

        .tier-tag {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            white-space: nowrap;
            padding: 0.35rem 0.65rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
            line-height: 1.2;
            min-width: 145px;
            text-align: center;
            box-sizing: border-box;
        }

        .tier-high { background: rgba(16, 185, 129, 0.15); color: var(--tier-high); border: 1px solid rgba(16, 185, 129, 0.3); }
        .tier-rec { background: rgba(59, 130, 246, 0.15); color: var(--tier-rec); border: 1px solid rgba(59, 130, 246, 0.3); }
        .tier-consider { background: rgba(245, 158, 11, 0.15); color: var(--tier-consider); border: 1px solid rgba(245, 158, 11, 0.3); }
        .tier-not { background: rgba(239, 68, 68, 0.15); color: var(--tier-not); border: 1px solid rgba(239, 68, 68, 0.3); }

        .candidate-table-wrapper { overflow-x: auto; margin-top: 1rem; }

        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.875rem; }
        th { color: var(--text-secondary); font-weight: 600; padding: 1rem; border-bottom: 1px solid var(--glass-border); }
        td { padding: 1rem; border-bottom: 1px solid rgba(255, 255, 255, 0.04); vertical-align: middle; }
        tr.table-row { cursor: pointer; transition: background 0.15s ease; }
        tr.table-row:hover { background: rgba(255, 255, 255, 0.04); }

        .score-pill { font-size: 0.85rem; font-weight: 700; color: #a5b4fc; }

        /* Candidate Search Bar Styling */
        .search-container {
            display: flex;
            gap: 0.75rem;
            align-items: center;
            margin-top: 0.5rem;
            margin-bottom: 0.75rem;
            flex-wrap: wrap;
        }

        .search-input-wrapper {
            flex: 1;
            min-width: 260px;
            position: relative;
        }

        .search-input {
            width: 100%;
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid var(--glass-border);
            color: var(--text-primary);
            padding: 0.55rem 1rem 0.55rem 2.4rem;
            border-radius: 8px;
            outline: none;
            font-family: inherit;
            font-size: 0.85rem;
            transition: all 0.2s;
        }

        .search-input:focus {
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.25);
        }

        .search-icon {
            position: absolute;
            left: 0.8rem;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-secondary);
            font-size: 0.9rem;
            pointer-events: none;
        }

        .filter-badge {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--glass-border);
            color: var(--text-secondary);
            padding: 0.45rem 0.85rem;
            border-radius: 8px;
            font-size: 0.78rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }

        .filter-badge:hover {
            background: rgba(255, 255, 255, 0.1);
            color: var(--text-primary);
        }

        .filter-badge.active {
            background: rgba(99, 102, 241, 0.25);
            border-color: rgba(99, 102, 241, 0.6);
            color: #a5b4fc;
        }

        .match-count-badge {
            font-size: 0.78rem;
            color: var(--text-secondary);
            font-weight: 600;
        }

        /* Modal styling */
        .modal-overlay {
            position: fixed; top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(11, 15, 25, 0.88);
            backdrop-filter: blur(12px);
            z-index: 100;
            display: none; justify-content: center; align-items: center;
            padding: 2rem;
        }

        .modal-content {
            background: #171930;
            border: 1px solid var(--glass-border);
            width: 100%; max-width: 960px; max-height: 88vh;
            border-radius: 20px; display: flex; flex-direction: column; overflow: hidden;
            box-shadow: 0 25px 60px rgba(0, 0, 0, 0.6);
        }

        .modal-header {
            padding: 1.5rem 2rem; border-bottom: 1px solid var(--glass-border);
            display: flex; justify-content: space-between; align-items: center;
            background: rgba(26, 34, 52, 0.5);
        }

        .modal-body { padding: 2rem; overflow-y: auto; display: flex; flex-direction: column; gap: 1.5rem; }
        .close-btn { background: none; border: none; color: var(--text-secondary); font-size: 1.5rem; cursor: pointer; }
        .close-btn:hover { color: white; }

        .section-title {
            font-size: 0.95rem; font-weight: 700; color: #a5b4fc; margin-bottom: 0.5rem;
            border-bottom: 1.5px solid rgba(165, 180, 252, 0.15); padding-bottom: 0.3rem;
        }

        .pill-container { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.4rem; }
        .pill { background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.1); padding: 0.3rem 0.6rem; border-radius: 6px; font-size: 0.78rem; }
        .pill-strength { background: rgba(16, 185, 129, 0.15); border-color: rgba(16, 185, 129, 0.3); color: #6ee7b7; }
        .pill-gap { background: rgba(239, 68, 68, 0.15); border-color: rgba(239, 68, 68, 0.3); color: #fca5a5; }

        .scores-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 0.75rem; }
        .score-card { background: rgba(11, 15, 25, 0.5); border: 1px solid var(--glass-border); border-radius: 8px; padding: 0.75rem; text-align: center; }
        .score-card p { font-size: 0.72rem; color: var(--text-secondary); }
        .score-card h3 { font-size: 1.25rem; font-weight: 700; margin-top: 0.25rem; }

        .spinner {
            border: 3px solid rgba(255, 255, 255, 0.1); width: 18px; height: 18px; border-radius: 50%;
            border-left-color: white; animation: spin 0.8s linear infinite; display: none;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        .no-data { text-align: center; color: var(--text-secondary); padding: 3.5rem; font-style: italic; }

        /* ========================================================
           Aesthetic Professional Reloader & Shimmer System
           ======================================================== */
        .btn-reload {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(168, 85, 247, 0.2) 100%);
            border: 1px solid rgba(165, 180, 252, 0.35);
            color: #f1f5f9;
            padding: 0.5rem 1rem;
            border-radius: 9px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            backdrop-filter: blur(10px);
            box-shadow: 0 4px 14px -2px rgba(99, 102, 241, 0.25);
        }
        .btn-reload:hover {
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.35) 0%, rgba(168, 85, 247, 0.35) 100%);
            border-color: rgba(199, 210, 254, 0.6);
            transform: translateY(-1px);
            box-shadow: 0 6px 20px -2px rgba(99, 102, 241, 0.4);
            color: #ffffff;
        }
        .btn-reload:active { transform: translateY(0); }
        .btn-reload .reload-svg {
            transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .btn-reload:hover .reload-svg {
            transform: rotate(180deg);
        }
        .btn-reload.is-reloading .reload-svg {
            animation: spinReload 0.85s linear infinite;
        }

        .btn-icon-reload {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: var(--text-secondary);
            padding: 0.3rem 0.65rem;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            transition: all 0.2s;
        }
        .btn-icon-reload:hover {
            background: rgba(99, 102, 241, 0.15);
            border-color: rgba(99, 102, 241, 0.4);
            color: #c7d2fe;
        }
        .btn-icon-reload:hover .reload-svg {
            transform: rotate(180deg);
            transition: transform 0.5s ease;
        }

        @keyframes spinReload {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Reloader Overlay */
        .reloader-overlay {
            position: fixed;
            inset: 0;
            background: rgba(8, 12, 22, 0.82);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .reloader-overlay.active {
            opacity: 1;
            pointer-events: auto;
        }

        .reloader-card {
            background: linear-gradient(145deg, rgba(22, 30, 50, 0.95) 0%, rgba(13, 19, 36, 0.98) 100%);
            border: 1px solid rgba(99, 102, 241, 0.35);
            box-shadow: 0 25px 65px -15px rgba(0, 0, 0, 0.7), 0 0 50px rgba(99, 102, 241, 0.2);
            border-radius: 24px;
            padding: 2.25rem 2.5rem;
            max-width: 520px;
            width: 90%;
            text-align: center;
            position: relative;
            overflow: hidden;
            transform: scale(0.94);
            transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        .reloader-overlay.active .reloader-card {
            transform: scale(1);
        }

        .reloader-top-glow {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #6366f1, #a855f7, #38bdf8, #6366f1);
            background-size: 200% 100%;
            animation: moveGradient 2s linear infinite;
        }
        @keyframes moveGradient {
            0% { background-position: 0% 50%; }
            100% { background-position: 200% 50%; }
        }

        /* Radar Orbit Visual */
        .radar-box {
            position: relative;
            width: 90px;
            height: 90px;
            margin: 0 auto 1.5rem;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .radar-ring {
            position: absolute;
            border-radius: 50%;
            pointer-events: none;
        }
        .radar-ring-1 {
            width: 90px;
            height: 90px;
            border: 2px dashed rgba(99, 102, 241, 0.4);
            animation: radarRotate 3s linear infinite;
        }
        .radar-ring-2 {
            width: 68px;
            height: 68px;
            border: 2px solid transparent;
            border-top-color: #38bdf8;
            border-right-color: #a855f7;
            animation: radarCounter 1.8s cubic-bezier(0.4, 0, 0.2, 1) infinite;
        }
        .radar-ring-3 {
            width: 48px;
            height: 48px;
            background: radial-gradient(circle, rgba(99, 102, 241, 0.4) 0%, rgba(168, 85, 247, 0.1) 70%);
            border: 1px solid rgba(165, 180, 252, 0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            animation: pulseGlow 1.8s ease-in-out infinite;
        }
        .radar-center-icon {
            color: #ffffff;
            filter: drop-shadow(0 0 6px rgba(129, 140, 248, 0.8));
        }

        @keyframes radarRotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @keyframes radarCounter {
            0% { transform: rotate(360deg); }
            100% { transform: rotate(0deg); }
        }
        @keyframes pulseGlow {
            0%, 100% { transform: scale(0.96); box-shadow: 0 0 15px rgba(99, 102, 241, 0.3); }
            50% { transform: scale(1.05); box-shadow: 0 0 25px rgba(168, 85, 247, 0.6); }
        }

        .reloader-title {
            font-size: 1.25rem;
            font-weight: 800;
            background: linear-gradient(135deg, #f8fafc 0%, #cbd5e1 50%, #818cf8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.35rem;
            letter-spacing: -0.02em;
        }
        .reloader-subtitle {
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-bottom: 1.25rem;
        }

        /* Progress Bar */
        .reloader-progress-wrap {
            margin-bottom: 1.25rem;
        }
        .reloader-progress-header {
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: #a5b4fc;
            margin-bottom: 0.45rem;
            font-weight: 600;
        }
        .reloader-bar {
            width: 100%;
            height: 7px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 999px;
            overflow: hidden;
            position: relative;
        }
        .reloader-bar-fill {
            height: 100%;
            width: 15%;
            background: linear-gradient(90deg, #6366f1 0%, #a855f7 50%, #38bdf8 100%);
            border-radius: 999px;
            transition: width 0.35s ease;
            box-shadow: 0 0 12px rgba(99, 102, 241, 0.7);
            position: relative;
        }
        .reloader-bar-fill::after {
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
            animation: barSweep 1.5s infinite;
        }
        @keyframes barSweep {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }

        /* Step Checklist */
        .reloader-steps {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            text-align: left;
            background: rgba(11, 15, 25, 0.5);
            border: 1px solid var(--glass-border);
            border-radius: 14px;
            padding: 0.85rem 1rem;
            margin-bottom: 0.5rem;
        }
        .reloader-step-item {
            display: flex;
            align-items: center;
            gap: 0.65rem;
            font-size: 0.78rem;
            color: #64748b;
            transition: all 0.25s ease;
        }
        .reloader-step-item.active {
            color: #f8fafc;
            font-weight: 600;
        }
        .reloader-step-item.completed {
            color: #94a3b8;
        }
        .step-icon-badge {
            width: 18px;
            height: 18px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.65rem;
            font-weight: 700;
            background: rgba(255, 255, 255, 0.08);
            color: #64748b;
            border: 1px solid rgba(255, 255, 255, 0.1);
            flex-shrink: 0;
            transition: all 0.25s;
        }
        .reloader-step-item.active .step-icon-badge {
            background: rgba(99, 102, 241, 0.25);
            color: #a5b4fc;
            border-color: #6366f1;
            box-shadow: 0 0 10px rgba(99, 102, 241, 0.5);
            animation: pulseGlow 1.2s infinite;
        }
        .reloader-step-item.completed .step-icon-badge {
            background: rgba(16, 185, 129, 0.2);
            color: #34d399;
            border-color: rgba(16, 185, 129, 0.4);
        }

        /* Skeleton Shimmer Loaders */
        .skeleton-grid {
            display: flex;
            flex-direction: column;
            gap: 1rem;
            width: 100%;
        }
        .skeleton-card {
            background: rgba(26, 34, 52, 0.45);
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 12px;
            padding: 1.25rem;
            position: relative;
            overflow: hidden;
        }
        .skeleton-card::before {
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.05) 50%, transparent 100%);
            animation: shimmerSweep 1.6s infinite;
        }
        @keyframes shimmerSweep {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        .skeleton-pill {
            background: rgba(255, 255, 255, 0.08);
            border-radius: 6px;
        }
    </style>
</head>
<body>
    <header>
        <div class="logo-section">
            <h1>Domain-Agnostic Resume Screening System (LangGraph)</h1>
            <p>Enterprise Multi-Agent Candidate Evaluation Pipeline (LangGraph & FastAPI)</p>
        </div>
        <div class="header-actions">
            <button class="btn-reload" id="btn-header-reload" onclick="triggerPipelineReload()" title="Re-screen and refresh candidate rankings with multi-agent pipeline">
                <svg class="reload-svg" viewBox="0 0 24 24" width="15" height="15" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" fill="none">
                    <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-1.19"/>
                </svg>
                <span>⚡ Reload Pipeline</span>
            </button>
            <button class="btn-secondary" onclick="openUploadModal()">+ Upload JD / Resumes</button>
            <button class="btn-secondary" id="btn-dl-pdf" onclick="downloadReport('pdf')" style="display:none;">📄 Download PDF Report</button>
            <button class="btn-secondary" id="btn-dl-md" onclick="downloadReport('md')" style="display:none;">📝 Download Markdown Report</button>
        </div>
    </header>

    <main>
        <div class="sidebar">
            <div class="card">
                <h3 class="card-title">Select Job Role & Domain</h3>
                <select class="selector" id="jd-select">
                    <option value="">Loading job descriptions...</option>
                </select>
                <button class="btn-primary" id="run-btn" disabled>
                    <span class="spinner" id="run-spinner"></span>
                    <span id="btn-text">Run Diagnostics</span>
                </button>
            </div>

            <!-- Custom HR Evaluation Queries Card -->
            <div class="card" id="hr-query-card">
                <h3 class="card-title">Custom HR Evaluation</h3>
                <div style="margin-bottom:0.75rem;">
                    <div style="font-size:0.75rem; color:var(--text-secondary); margin-bottom:0.4rem;">Add Custom Requirement / Question:</div>
                    <input type="text" id="hr-q-input" class="search-input" placeholder="e.g. Has experience working with a startup?" style="padding:0.45rem 0.75rem; font-size:0.8rem; margin-bottom:0.45rem;">
                    <div style="display:flex; gap:0.4rem; margin-bottom:0.5rem;">
                        <select id="hr-q-importance" class="selector" style="margin-bottom:0; padding:0.4rem; font-size:0.78rem; flex:1;">
                            <option value="Important">Important</option>
                            <option value="Required">Required (Mandatory)</option>
                            <option value="Optional">Optional</option>
                        </select>
                        <button class="btn-secondary" onclick="addCustomHRQuery()" style="padding:0.4rem 0.85rem; font-size:0.78rem; white-space:nowrap;">+ Add</button>
                    </div>
                </div>

                <div style="font-size:0.75rem; color:#a5b4fc; margin-bottom:0.35rem; font-weight:600;">Quick Presets:</div>
                <div style="display:flex; flex-wrap:wrap; gap:0.35rem; margin-bottom:0.75rem;">
                    <button class="pill" onclick="addHRPreset('Does the candidate have experience working with a startup or early-stage team?', 'Important')" style="cursor:pointer; font-size:0.75rem; background:rgba(99, 102, 241, 0.18); border:1px solid rgba(99, 102, 241, 0.45); color:#c7d2fe; font-weight:600;">+ Startup Exp</button>
                    <button class="pill" onclick="addHRPreset('Has the candidate worked on production-level scalable software projects?', 'Important')" style="cursor:pointer; font-size:0.75rem; background:rgba(14, 165, 233, 0.18); border:1px solid rgba(14, 165, 233, 0.45); color:#7dd3fc; font-weight:600;">+ Production Project</button>
                    <button class="pill" onclick="addHRPreset('Does the candidate have leadership, mentoring, or team management experience?', 'Important')" style="cursor:pointer; font-size:0.75rem; background:rgba(245, 158, 11, 0.18); border:1px solid rgba(245, 158, 11, 0.45); color:#fde047; font-weight:600;">+ Leadership</button>
                    <button class="pill" onclick="addHRPreset('Is the candidate eligible or willing for mandatory location / relocation criteria?', 'Required')" style="cursor:pointer; font-size:0.75rem; background:rgba(239, 68, 68, 0.18); border:1px solid rgba(239, 68, 68, 0.45); color:#fca5a5; font-weight:600;">+ Relocation (Req)</button>
                </div>

                <div style="font-size:0.75rem; color:var(--text-secondary); margin-bottom:0.4rem; display:flex; justify-content:space-between;">
                    <span>Active HR Queries:</span>
                    <span id="hr-q-count" style="font-weight:700; color:#a5b4fc;">0</span>
                </div>
                <div id="hr-query-list" style="display:flex; flex-direction:column; gap:0.35rem; max-height:160px; overflow-y:auto;">
                    <div style="font-size:0.75rem; color:#94a3b8; font-style:italic;">No custom queries added. Click quick presets above or type a question.</div>
                </div>

                <div style="margin-top:0.75rem; border-top:1px solid var(--glass-border); padding-top:0.6rem;">
                    <div style="font-size:0.75rem; color:#a5b4fc; margin-bottom:0.3rem;">Ranking Methodology:</div>
                    <select id="ranking-mode-select" class="selector" style="margin-bottom:0; font-size:0.78rem; padding:0.45rem;">
                        <option value="overall_percentile">Overall Percentile (Default)</option>
                        <option value="percentile_plus_hr_fit">Percentile + HR Fit (75% / 25%)</option>
                    </select>
                </div>
            </div>

            <div class="card" id="domain-card" style="display:none;">
                <h3 class="card-title">Detected Domain Strategy</h3>
                <div class="domain-badge" id="domain-name-badge">Software & Tech</div>
                <p id="domain-summary-text" style="font-size: 0.78rem; color: var(--text-secondary); margin-bottom: 0.75rem;"></p>
                <h4 style="font-size: 0.75rem; color: #a5b4fc; margin-bottom: 0.4rem;">Dynamic Evaluation Weights:</h4>
                <div class="weights-container" id="weights-list"></div>
            </div>

            <div class="card">
                <h3 class="card-title">Screening Candidate Pool</h3>
                <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.9rem; font-weight:600;">
                    <span style="color:var(--text-secondary);">Total Resumes Evaluated</span>
                    <span id="stat-pool" style="color:#a5b4fc; font-weight:700;">20 Resumes</span>
                </div>
            </div>

        </div>

        <div class="content-area">
            <div class="metrics-grid" id="metrics-summary" style="display: none;">
                <div class="card metric-card" style="border-top: 4px solid var(--tier-high);">
                    <h3 class="card-title" style="margin-bottom: 0;">Highly Recommended</h3>
                    <div class="metric-num" style="color: var(--tier-high);" id="count-high">0</div>
                </div>
                <div class="card metric-card" style="border-top: 4px solid var(--tier-rec);">
                    <h3 class="card-title" style="margin-bottom: 0;">Recommended</h3>
                    <div class="metric-num" style="color: var(--tier-rec);" id="count-rec">0</div>
                </div>
                <div class="card metric-card" style="border-top: 4px solid var(--tier-consider);">
                    <h3 class="card-title" style="margin-bottom: 0;">Consider</h3>
                    <div class="metric-num" style="color: var(--tier-consider);" id="count-consider">0</div>
                </div>
                <div class="card metric-card" style="border-top: 4px solid var(--tier-not);">
                    <h3 class="card-title" style="margin-bottom: 0;">Not Recommended</h3>
                    <div class="metric-num" style="color: var(--tier-not);" id="count-not">0</div>
                </div>
            </div>

            <div class="card" style="flex: 1; display: flex; flex-direction: column;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                    <div style="display:flex; align-items:center; gap:0.65rem;">
                        <h3 class="card-title" style="margin-bottom: 0;">Candidate Screening Leaderboard</h3>
                        <button class="btn-icon-reload" onclick="triggerPipelineReload()" title="Refresh & re-evaluate candidates">
                            <svg class="reload-svg" viewBox="0 0 24 24" width="13" height="13" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" fill="none">
                                <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-1.19"/>
                            </svg>
                            <span>Reload</span>
                        </button>
                    </div>
                    <span class="match-count-badge" id="match-counter"></span>
                </div>

                <div class="search-container">
                    <div class="search-input-wrapper">
                        <span class="search-icon">🔍</span>
                        <input type="text" id="candidate-search-input" class="search-input" placeholder="Search candidate name, skills, custom resume filename..." oninput="filterAndRenderCandidates()" />
                    </div>
                    <button class="btn-secondary" id="search-btn" onclick="filterAndRenderCandidates()" style="display: inline-flex; align-items: center; gap: 0.3rem;">
                        🔍 Search
                    </button>
                    <button class="btn-secondary" id="clear-search-btn" onclick="clearCandidateSearch()" style="display: none;">
                        ✖ Clear
                    </button>
                    <button class="filter-badge active" id="filter-all-btn" onclick="setCandidateFilterType('all')">
                        All Candidates
                    </button>
                    <button class="filter-badge" id="filter-custom-btn" onclick="setCandidateFilterType('custom')">
                        📄 Custom Resumes Only
                    </button>
                </div>

                <div class="candidate-table-wrapper" id="results-container">
                    <div class="no-data">Select a job description and click "Run Diagnostics" to evaluate candidates across detected domain criteria.</div>
                </div>
            </div>
        </div>
    </main>

    <!-- Upload Modal -->
    <div class="modal-overlay" id="upload-modal">
        <div class="modal-content" style="max-width: 600px;">
            <div class="modal-header">
                <h3>Upload Custom JD or Candidate Resumes</h3>
                <button class="close-btn" onclick="closeUploadModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div>
                    <h4 class="section-title">Upload Candidate Resumes (PDF or DOCX)</h4>
                    <input type="file" id="resume-files" multiple accept=".pdf,.docx,.doc" style="margin-top: 0.5rem; color: white;">
                    <button class="btn-secondary" onclick="uploadResumes()" style="margin-top: 0.75rem; width:100%;">Upload Resumes</button>
                </div>
                <hr style="border: 0.5px solid var(--glass-border);">
                <div>
                    <h4 class="section-title">Upload Custom Job Description (Text File)</h4>
                    <input type="file" id="jd-file" accept=".txt" style="margin-top: 0.5rem; color: white;">
                    <button class="btn-secondary" onclick="uploadJDFile()" style="margin-top: 0.75rem; width:100%;">Upload Job Description</button>
                </div>
            </div>
        </div>
    </div>

    <!-- Candidate Details Modal -->
    <div class="modal-overlay" id="details-modal">
        <div class="modal-content">
            <div class="modal-header">
                <div>
                    <h2 id="modal-name" style="font-weight: 800;">Candidate Name</h2>
                    <p id="modal-contact" style="font-size: 0.8rem; color: var(--text-secondary);"></p>
                </div>
                <div style="display:flex; align-items:center; gap:0.75rem;">
                    <button id="modal-delete-btn" style="background:rgba(239, 68, 68, 0.2); border:1px solid rgba(239, 68, 68, 0.4); color:#fca5a5; border-radius:6px; font-size:0.8rem; padding:0.4rem 0.85rem; cursor:pointer; font-weight:600; display:inline-flex; align-items:center; gap:0.3rem;">
                        🗑️ Remove Resume
                    </button>
                    <button class="close-btn" onclick="closeDetailsModal()">&times;</button>
                </div>
            </div>

            <div class="modal-body">
                <div>
                    <h3 class="section-title">Hiring Recommendation & Action Item</h3>
                    <p id="modal-rec" style="font-weight: 700; color: #818cf8; font-size: 1rem;"></p>
                </div>
                <div>
                    <h3 class="section-title">Executive Evaluation Assessment</h3>
                    <p id="modal-explanation" style="font-style: italic; color: #e2e8f0; line-height: 1.5;"></p>
                </div>
                <div>
                    <h3 class="section-title">Category Match Scorecard</h3>
                    <div class="scores-grid" id="modal-scores"></div>
                </div>
                <div id="modal-hr-query-section" style="display:none;">
                    <h3 class="section-title">Custom HR Query Evaluation & Resume Evidence</h3>
                    <div id="modal-hr-queries-table" style="overflow-x:auto;"></div>
                </div>
                <div>
                    <h3 class="section-title">Identified Candidate Strengths</h3>
                    <div class="pill-container" id="modal-strengths"></div>
                </div>
                <div>
                    <h3 class="section-title">Technical & Domain Skills</h3>
                    <div class="pill-container" id="modal-skills"></div>
                </div>
                <div>
                    <h3 class="section-title">Certifications & Professional Licenses</h3>
                    <div class="pill-container" id="modal-certs"></div>
                </div>
                <div>
                    <h3 class="section-title">Education & Experience Summary</h3>
                    <div id="modal-education"></div>
                    <div id="modal-experience" style="margin-top: 1rem;"></div>
                </div>
            </div>
        </div>
    </div>

    <!-- Aesthetic Multi-Agent Reloader Overlay -->
    <div class="reloader-overlay" id="agent-reloader-overlay">
        <div class="reloader-card">
            <div class="reloader-top-glow"></div>
            
            <div class="radar-box">
                <div class="radar-ring radar-ring-1"></div>
                <div class="radar-ring radar-ring-2"></div>
                <div class="radar-ring radar-ring-3">
                    <svg class="radar-center-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
                        <circle cx="12" cy="12" r="3"/>
                    </svg>
                </div>
            </div>

            <h3 class="reloader-title" id="reloader-main-title">Multi-Agent Screening Pipeline</h3>
            <p class="reloader-subtitle" id="reloader-status-subtitle">Orchestrating autonomous LangGraph workflow...</p>

            <div class="reloader-progress-wrap">
                <div class="reloader-progress-header">
                    <span id="reloader-phase-text">Phase 1 / 5: Domain Classification</span>
                    <span id="reloader-percent-text">15%</span>
                </div>
                <div class="reloader-bar">
                    <div class="reloader-bar-fill" id="reloader-bar-fill" style="width: 15%;"></div>
                </div>
            </div>

            <div class="reloader-steps">
                <div class="reloader-step-item active" id="step-item-1">
                    <span class="step-icon-badge" id="step-badge-1">1</span>
                    <span>JD Parser & Domain Strategy Agent</span>
                </div>
                <div class="reloader-step-item" id="step-item-2">
                    <span class="step-icon-badge" id="step-badge-2">2</span>
                    <span>Concurrent Profile Extraction & Verification</span>
                </div>
                <div class="reloader-step-item" id="step-item-3">
                    <span class="step-icon-badge" id="step-badge-3">3</span>
                    <span>FAISS Dense Embeddings & Vector Similarity</span>
                </div>
                <div class="reloader-step-item" id="step-item-4">
                    <span class="step-icon-badge" id="step-badge-4">4</span>
                    <span>Scipy Empirical Pool Percentile Ranker</span>
                </div>
                <div class="reloader-step-item" id="step-item-5">
                    <span class="step-icon-badge" id="step-badge-5">5</span>
                    <span>Hiring Quartiles & Recruiter Narrative Synthesis</span>
                </div>
            </div>

            <div style="margin-top: 1rem; display: flex; justify-content: center;">
                <span style="font-size: 0.72rem; color: #64748b; display: inline-flex; align-items: center; gap: 0.35rem;">
                    <span style="display:inline-block; width:6px; height:6px; border-radius:50%; background:#10b981;"></span>
                    LangGraph Dynamic State Workflow Active
                </span>
            </div>
        </div>
    </div>

    <script>
        const jdSelect = document.getElementById('jd-select');
        const runBtn = document.getElementById('run-btn');
        const runSpinner = document.getElementById('run-spinner');
        const btnText = document.getElementById('btn-text');
        const resultsContainer = document.getElementById('results-container');
        const metricsSummary = document.getElementById('metrics-summary');
        
        const countHigh = document.getElementById('count-high');
        const countRec = document.getElementById('count-rec');
        const countConsider = document.getElementById('count-consider');
        const countNot = document.getElementById('count-not');
        const statPool = document.getElementById('stat-pool');

        const domainCard = document.getElementById('domain-card');
        const domainNameBadge = document.getElementById('domain-name-badge');
        const domainSummaryText = document.getElementById('domain-summary-text');
        const weightsList = document.getElementById('weights-list');

        let allCandidates = [];
        let currentSelectedJD = "";
        let activeHRQueries = [];
        let totalSystemResumes = 280;

        async function fetchJobs() {
            try {
                const response = await fetch('/api/jobs');
                const data = await response.json();
                jdSelect.innerHTML = '<option value="">-- Select Job Description --</option>';
                data.forEach(job => {
                    const opt = document.createElement('option');
                    opt.value = job.filename;
                    opt.textContent = `[${job.domain}] ${job.title}`;
                    jdSelect.appendChild(opt);
                });
                jdSelect.addEventListener('change', () => {
                    runBtn.disabled = !jdSelect.value;
                });

                const rRes = await fetch('/api/resumes');
                const rData = await rRes.json();
                totalSystemResumes = Array.isArray(rData) ? rData.length : (rData.total_count || 280);
                if (statPool) statPool.textContent = `20 evaluated out of ${totalSystemResumes} Resumes`;
                if (data && data.length > 0) {
                    const defaultJob = data.find(j => j.filename.includes('react') || j.filename.includes('devops')) || data[0];
                    jdSelect.value = defaultJob.filename;
                    runBtn.disabled = false;
                    runScreeningPipeline();
                }
            } catch (err) {
                console.error(err);
            }
        }

        function addCustomHRQuery() {
            const input = document.getElementById('hr-q-input');
            const impSelect = document.getElementById('hr-q-importance');
            const text = (input ? input.value : '').trim();
            const imp = impSelect ? impSelect.value : 'Important';
            if (!text) return alert('Please enter a custom HR question or requirement.');
            
            const newQ = { id: 'hr_' + Date.now(), question: text, importance: imp };
            activeHRQueries.push(newQ);
            if (input) input.value = '';
            renderHRQueries();
        }

        function addHRPreset(question, importance) {
            if (activeHRQueries.some(q => q.question.toLowerCase() === question.toLowerCase())) {
                showToast("✓ Requirement already added to active queries");
                return;
            }
            activeHRQueries.push({ id: 'hr_' + Date.now(), question: question, importance: importance });
            renderHRQueries();
            showToast("✓ Added HR query preset");
        }

        function removeHRQuery(id) {
            activeHRQueries = activeHRQueries.filter(q => q.id !== id);
            renderHRQueries();
        }

        function renderHRQueries() {
            const listContainer = document.getElementById('hr-query-list');
            const countSpan = document.getElementById('hr-q-count');
            if (countSpan) countSpan.textContent = activeHRQueries.length;
            
            if (!listContainer) return;
            if (activeHRQueries.length === 0) {
                listContainer.innerHTML = `<div style="font-size:0.75rem; color:#94a3b8; font-style:italic;">No custom queries added. Click quick presets above or type a question.</div>`;
                return;
            }

            let html = "";
            activeHRQueries.forEach(q => {
                let badgeColor = "background:rgba(99, 102, 241, 0.2); color:#c7d2fe; border:1px solid rgba(99, 102, 241, 0.4);";
                if (q.importance === "Required") badgeColor = "background:rgba(239, 68, 68, 0.2); color:#fca5a5; border:1px solid rgba(239, 68, 68, 0.4);";
                else if (q.importance === "Optional") badgeColor = "background:rgba(255, 255, 255, 0.08); color:#cbd5e1; border:1px solid rgba(255, 255, 255, 0.12);";

                html += `
                    <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(15,23,42,0.6); padding:0.35rem 0.6rem; border-radius:6px; border:1px solid var(--glass-border);">
                        <div style="font-size:0.76rem; color:#e2e8f0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; max-width:180px;" title="${q.question}">
                            <span style="font-size:0.68rem; padding:0.1rem 0.35rem; border-radius:4px; margin-right:0.3rem; ${badgeColor}">${q.importance}</span>
                            ${q.question}
                        </div>
                        <button onclick="removeHRQuery('${q.id}')" style="background:none; border:none; color:#fca5a5; font-size:0.9rem; cursor:pointer; font-weight:700; padding:0 0.2rem;">&times;</button>
                    </div>
                `;
            });
            listContainer.innerHTML = html;
        }

        // ========================================================
        // Aesthetic Reloader Controller & Shimmer Skeletons
        // ========================================================
        let reloaderInterval = null;

        function renderSkeletonCards() {
            return `
                <div class="skeleton-grid">
                    ${[1, 2, 3].map(i => `
                        <div class="skeleton-card">
                            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
                                <div style="display:flex; gap:0.65rem; align-items:center;">
                                    <div class="skeleton-pill" style="width:34px; height:24px;"></div>
                                    <div class="skeleton-pill" style="width:160px; height:22px;"></div>
                                </div>
                                <div class="skeleton-pill" style="width:110px; height:26px; border-radius:12px;"></div>
                            </div>
                            <div class="skeleton-pill" style="width:55%; height:14px; margin-bottom:0.75rem;"></div>
                            <div class="skeleton-pill" style="width:90%; height:14px; margin-bottom:1.25rem;"></div>
                            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(100px, 1fr)); gap:0.65rem;">
                                <div class="skeleton-pill" style="height:48px; border-radius:8px;"></div>
                                <div class="skeleton-pill" style="height:48px; border-radius:8px;"></div>
                                <div class="skeleton-pill" style="height:48px; border-radius:8px;"></div>
                                <div class="skeleton-pill" style="height:48px; border-radius:8px;"></div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        function showAestheticReloader(jobTitle = "") {
            const overlay = document.getElementById('agent-reloader-overlay');
            const subTitle = document.getElementById('reloader-status-subtitle');
            const phaseText = document.getElementById('reloader-phase-text');
            const percentText = document.getElementById('reloader-percent-text');
            const barFill = document.getElementById('reloader-bar-fill');
            const reloadBtn = document.getElementById('btn-header-reload');
            
            if (reloadBtn) reloadBtn.classList.add('is-reloading');
            if (subTitle && jobTitle) subTitle.textContent = `Screening & evaluating candidates for ${jobTitle}...`;
            
            // Reset steps
            for (let i = 1; i <= 5; i++) {
                const s = document.getElementById(`step-item-${i}`);
                const b = document.getElementById(`step-badge-${i}`);
                if (s) { s.classList.remove('active', 'completed'); }
                if (b) { b.textContent = i; }
            }
            const s1 = document.getElementById('step-item-1');
            if (s1) s1.classList.add('active');

            if (barFill) barFill.style.width = '15%';
            if (percentText) percentText.textContent = '15%';
            if (phaseText) phaseText.textContent = 'Phase 1 / 5: Domain Classification';

            if (overlay) overlay.classList.add('active');

            // Smooth progressive animation across LangGraph stages
            const stages = [
                { progress: 34, phase: 'Phase 2 / 5: Concurrent Profile Extraction', step: 2 },
                { progress: 60, phase: 'Phase 3 / 5: FAISS Dense Vector Similarity', step: 3 },
                { progress: 80, phase: 'Phase 4 / 5: Scipy Empirical Pool Percentiles', step: 4 },
                { progress: 94, phase: 'Phase 5 / 5: Recruiter Synthesis & Quartiles', step: 5 }
            ];

            let stageIdx = 0;
            clearInterval(reloaderInterval);
            reloaderInterval = setInterval(() => {
                if (stageIdx < stages.length) {
                    const st = stages[stageIdx];
                    if (barFill) barFill.style.width = `${st.progress}%`;
                    if (percentText) percentText.textContent = `${st.progress}%`;
                    if (phaseText) phaseText.textContent = st.phase;

                    for (let k = 1; k < st.step; k++) {
                        const prev = document.getElementById(`step-item-${k}`);
                        const prevB = document.getElementById(`step-badge-${k}`);
                        if (prev) { prev.classList.remove('active'); prev.classList.add('completed'); }
                        if (prevB) { prevB.textContent = '✓'; }
                    }
                    const curr = document.getElementById(`step-item-${st.step}`);
                    if (curr) curr.classList.add('active');
                    stageIdx++;
                }
            }, 420);
        }

        function hideAestheticReloader() {
            clearInterval(reloaderInterval);
            const overlay = document.getElementById('agent-reloader-overlay');
            const percentText = document.getElementById('reloader-percent-text');
            const barFill = document.getElementById('reloader-bar-fill');
            const phaseText = document.getElementById('reloader-phase-text');
            const reloadBtn = document.getElementById('btn-header-reload');

            if (reloadBtn) reloadBtn.classList.remove('is-reloading');

            if (barFill) barFill.style.width = '100%';
            if (percentText) percentText.textContent = '100%';
            if (phaseText) phaseText.textContent = '✓ Multi-Agent Pipeline Completed';

            for (let i = 1; i <= 5; i++) {
                const s = document.getElementById(`step-item-${i}`);
                const b = document.getElementById(`step-badge-${i}`);
                if (s) { s.classList.remove('active'); s.classList.add('completed'); }
                if (b) { b.textContent = '✓'; }
            }

            setTimeout(() => {
                if (overlay) overlay.classList.remove('active');
            }, 360);
        }

        function triggerPipelineReload() {
            runScreeningPipeline();
        }

        async function runScreeningPipeline() {
            const val = jdSelect.value;
            if (!val) return;
            currentSelectedJD = val;

            const selectedText = jdSelect.options[jdSelect.selectedIndex] ? jdSelect.options[jdSelect.selectedIndex].text : '';
            const rankingModeSelect = document.getElementById('ranking-mode-select');
            const rankingMode = rankingModeSelect ? rankingModeSelect.value : 'overall_percentile';

            runBtn.disabled = true;
            runSpinner.style.display = 'inline-block';
            btnText.textContent = 'Evaluating Multi-Agent Pipeline...';
            
            // Show shimmering skeleton placeholders & modal reloader
            resultsContainer.innerHTML = renderSkeletonCards();
            metricsSummary.style.display = 'none';
            showAestheticReloader(selectedText);

            try {
                const response = await fetch('/api/screen', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        jd_filename: val,
                        hr_queries: activeHRQueries,
                        ranking_mode: rankingMode
                    })
                });
                
                if (!response.ok) {
                    const errDetail = await response.json();
                    throw new Error(errDetail.detail || "Server error");
                }
                
                const resData = await response.json();
                renderResults(resData.dashboard_data);
                
                if (activeHRQueries.length > 0) {
                    showToast(`✓ Evaluated ${activeHRQueries.length} custom HR queries against candidate resumes!`);
                } else {
                    showToast(`✓ Candidate screening diagnostics completed successfully!`);
                }

                document.getElementById('btn-dl-pdf').style.display = 'inline-block';
                document.getElementById('btn-dl-md').style.display = 'inline-block';
            } catch (err) {
                resultsContainer.innerHTML = `<div class="no-data" style="color:var(--tier-not);">Pipeline Execution Error: ${err.message}</div>`;
            } finally {
                runBtn.disabled = false;
                runSpinner.style.display = 'none';
                btnText.textContent = 'Run Diagnostics';
                hideAestheticReloader();
            }
        }

        runBtn.addEventListener('click', runScreeningPipeline);

        function renderResults(data) {
            allCandidates = data.candidates;
            if (statPool) statPool.textContent = `${allCandidates.length || 20} evaluated out of ${totalSystemResumes || 280} Resumes`;
            
            // Domain Card
            const dInfo = data.domain_info || {};
            domainNameBadge.textContent = dInfo.domain_name || "General";
            domainSummaryText.textContent = dInfo.domain_summary || "";
            
            let weightsHtml = "";
            const weights = dInfo.weights || {};
            for (const [k, v] of Object.entries(weights)) {
                if (v > 0) {
                    const pct = Math.round(v * 100);
                    const title = k.replace('_', ' ').toUpperCase();
                    weightsHtml += `
                        <div>
                            <div class="weight-row">
                                <span>${title}</span>
                                <span>${pct}%</span>
                            </div>
                            <div class="weight-bar-bg">
                                <div class="weight-bar-fill" style="width: ${pct}%;"></div>
                            </div>
                        </div>
                    `;
                }
            }
            weightsList.innerHTML = weightsHtml;
            domainCard.style.display = 'block';

            // Metrics Summary
            const counts = data.quantiles_count || {};
            countHigh.textContent = counts["Q1"] || 0;
            countRec.textContent = counts["Q2"] || 0;
            countConsider.textContent = counts["Q3"] || 0;
            countNot.textContent = counts["Q4"] || 0;
            metricsSummary.style.display = 'grid';

            filterAndRenderCandidates();
        }

        let activeFilterType = 'all';

        function setCandidateFilterType(type) {
            activeFilterType = type;
            const btnAll = document.getElementById('filter-all-btn');
            const btnCustom = document.getElementById('filter-custom-btn');
            if (btnAll) btnAll.classList.toggle('active', type === 'all');
            if (btnCustom) btnCustom.classList.toggle('active', type === 'custom');
            filterAndRenderCandidates();
        }

        function clearCandidateSearch() {
            const input = document.getElementById('candidate-search-input');
            if (input) input.value = '';
            const clearBtn = document.getElementById('clear-search-btn');
            if (clearBtn) clearBtn.style.display = 'none';
            filterAndRenderCandidates();
        }

        function filterAndRenderCandidates() {
            const searchInput = document.getElementById('candidate-search-input');
            const query = searchInput ? (searchInput.value || '').trim().toLowerCase() : '';
            const clearBtn = document.getElementById('clear-search-btn');
            if (clearBtn) clearBtn.style.display = query ? 'inline-block' : 'none';

            if (!allCandidates || allCandidates.length === 0) return;

            const benchmarkPrefixes = ["hc_", "law_", "fin_", "eng_", "fe_", "ds_", "ai_", "fs_"];

            const filtered = allCandidates.filter(c => {
                const rName = (c.resume_json ? c.resume_json.name : '').toLowerCase();
                const rEmail = (c.resume_json ? c.resume_json.email : '').toLowerCase();
                const rPath = (c.resume_path || '').toLowerCase();
                const rFilename = rPath.split('/').pop() || '';
                const hrLabel = (c.hr_fit_label || '').toLowerCase();
                const skills = (c.resume_json && Array.isArray(c.resume_json.skills) ? c.resume_json.skills.join(' ') : '').toLowerCase();

                const isCustom = !benchmarkPrefixes.some(prefix => rFilename.startsWith(prefix));

                if (activeFilterType === 'custom' && !isCustom) {
                    return false;
                }

                if (!query) return true;

                return rName.includes(query) ||
                       rEmail.includes(query) ||
                       rFilename.includes(query) ||
                       rPath.includes(query) ||
                       hrLabel.includes(query) ||
                       skills.includes(query) ||
                       (c.candidate_label || '').toLowerCase().includes(query);
            });

            renderCandidateTable(filtered, query);
        }

        function renderCandidateTable(candidatesToDisplay, searchFilterQuery = '') {
            const container = document.getElementById('results-container');
            const matchCounter = document.getElementById('match-counter');

            if (matchCounter) {
                if (searchFilterQuery || activeFilterType === 'custom') {
                    matchCounter.textContent = `Showing ${candidatesToDisplay.length} of ${allCandidates.length} candidates`;
                } else {
                    matchCounter.textContent = `Total Candidates: ${allCandidates.length}`;
                }
            }

            if (!candidatesToDisplay || candidatesToDisplay.length === 0) {
                container.innerHTML = `
                    <div class="no-data">
                        ${searchFilterQuery ? `No candidates found matching "<strong>${searchFilterQuery}</strong>"` : 'No custom uploaded resumes found for this screening pool.'}
                    </div>
                `;
                return;
            }

            let html = `
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Candidate Name</th>
                            <th>Skill Percentile</th>
                            <th>Exp Percentile</th>
                            <th>Cert Percentile</th>
                            <th>Percentile Rank</th>
                            <th>Category Tier</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            candidatesToDisplay.forEach(c => {
                let tierClass = "tier-not";
                if (c.candidate_label === "Highly Recommended") tierClass = "tier-high";
                else if (c.candidate_label === "Recommended") tierClass = "tier-rec";
                else if (c.candidate_label === "Consider") tierClass = "tier-consider";

                let hrClass = "tier-not";
                const hrLabel = c.hr_fit_label || "";
                if (hrLabel === "Strong Fit") hrClass = "tier-high";
                else if (hrLabel === "Moderate Fit") hrClass = "tier-rec";
                else if (hrLabel === "Weak Fit") hrClass = "tier-not";

                const rName = c.resume_json ? c.resume_json.name : "Candidate";
                const rEmail = c.resume_json ? c.resume_json.email : "";
                const safeName = (rName || "").replace(/'/g, "");

                const perc = c.percentile_score !== undefined ? c.percentile_score : c.final_score;
                const techP = c.technical_percentile !== undefined ? c.technical_percentile : c.technical_score;
                const expP = c.experience_percentile !== undefined ? c.experience_percentile : c.experience_score;
                const certP = c.certification_percentile !== undefined ? c.certification_percentile : c.certification_score;

                const showHRBadge = hrLabel && (activeHRQueries.length > 0 || (c.hr_query_results && c.hr_query_results.length > 0));

                html += `
                    <tr class="table-row" onclick="showDetails(${c.candidate_rank})">
                        <td><strong>#${c.candidate_rank}</strong></td>
                        <td>
                            <div style="font-weight: 700;">${rName}</div>
                            <div style="font-size: 0.75rem; color: var(--text-secondary);">${rEmail}</div>
                            ${showHRBadge ? `<div style="margin-top:0.25rem;"><span class="tier-tag ${hrClass}" style="font-size:0.68rem; padding:0.12rem 0.4rem; min-width:auto;">HR Fit: ${hrLabel}</span></div>` : ''}
                        </td>
                        <td><span style="font-weight:600;">${techP}th</span></td>
                        <td><span style="font-weight:600;">${expP}th</span></td>
                        <td><span style="font-weight:600;">${certP}th</span></td>
                        <td><span class="score-pill">${perc}th Percentile</span></td>
                        <td><span class="tier-tag ${tierClass}" style="white-space: nowrap;">${c.candidate_label}</span></td>
                        <td onclick="event.stopPropagation();">
                            <button onclick="removeCandidateFromWebpage('${c.resume_path || ''}', '${safeName}')" style="background:rgba(239, 68, 68, 0.18); border:1px solid rgba(239, 68, 68, 0.4); color:#fca5a5; border-radius:6px; font-size:0.75rem; padding:0.25rem 0.55rem; cursor:pointer; font-weight:600; display:inline-flex; align-items:center; gap:0.3rem;">
                                🗑️ Remove
                            </button>
                        </td>
                    </tr>
                `;
            });

            html += "</tbody></table>";
            container.innerHTML = html;
        }

        function showToast(message, isError = false) {
            let toast = document.getElementById('toast-notification');
            if (!toast) {
                toast = document.createElement('div');
                toast.id = 'toast-notification';
                toast.style.cssText = 'position:fixed; bottom:24px; right:24px; z-index:9999; padding:12px 20px; border-radius:8px; font-weight:600; font-size:0.85rem; color:#fff; box-shadow:0 10px 25px rgba(0,0,0,0.5); transition:all 0.3s ease; transform:translateY(100px); opacity:0; backdrop-filter:blur(10px);';
                document.body.appendChild(toast);
            }
            toast.style.background = isError ? 'rgba(239, 68, 68, 0.9)' : 'rgba(16, 185, 129, 0.9)';
            toast.style.border = isError ? '1px solid #f87171' : '1px solid #34d399';
            toast.innerText = message;
            toast.style.transform = 'translateY(0)';
            toast.style.opacity = '1';

            setTimeout(() => {
                toast.style.transform = 'translateY(100px)';
                toast.style.opacity = '0';
            }, 3000);
        }

        async function deleteCustomResume(filename) {
            try {
                await fetch(`/api/resumes/${encodeURIComponent(filename)}`, { method: 'DELETE' });
                showToast(`✓ Removed ${filename}`);
                fetchJobs();
            } catch (err) {
                console.error(err);
                showToast(`⚠ Failed to remove file: ${err.message}`, true);
            }
        }

        async function removeCandidateFromWebpage(resumePath, candidateName) {
            if (!resumePath) {
                showToast("⚠ Resume file path not available", true);
                return;
            }
            const filename = (resumePath || "").split('/').pop().split(String.fromCharCode(92)).pop();
            if (!filename) return;
            
            try {
                closeDetailsModal();
                
                await fetch(`/api/resumes/${encodeURIComponent(filename)}`, { method: 'DELETE' });
                
                allCandidates = allCandidates.filter(c => {
                    const p = (c.resume_path || "").split('/').pop().split(String.fromCharCode(92)).pop();
                    return p !== filename;
                });
                
                allCandidates.forEach((c, idx) => c.candidate_rank = idx + 1);
                
                const qCounts = { "Q1": 0, "Q2": 0, "Q3": 0, "Q4": 0 };
                allCandidates.forEach(c => {
                    if (c.candidate_label === "Highly Recommended") qCounts["Q1"]++;
                    else if (c.candidate_label === "Recommended") qCounts["Q2"]++;
                    else if (c.candidate_label === "Consider") qCounts["Q3"]++;
                    else if (c.candidate_label === "Not Recommended") qCounts["Q4"]++;
                });
                
                renderResults({
                    candidates: allCandidates,
                    quantiles_count: qCounts,
                    domain_info: {
                        domain_name: domainNameBadge.textContent,
                        domain_summary: domainSummaryText.textContent
                    }
                });
                
                showToast(`✓ Removed ${candidateName || filename} from screening pool`);
                fetchJobs();
            } catch (err) {
                console.error(err);
                showToast(`⚠ Failed to remove candidate: ${err.message}`, true);
            }
        }

        window.showDetails = function(rank) {
            const c = allCandidates.find(x => x.candidate_rank === rank);
            if (!c) return;

            const rJson = c.resume_json || {};
            const rName = rJson.name || "Candidate";
            document.getElementById('modal-name').textContent = rName;
            document.getElementById('modal-contact').textContent = `Email: ${rJson.email || 'N/A'} | Phone: ${rJson.phone || 'N/A'}`;
            document.getElementById('modal-rec').textContent = c.recommendation || "";
            document.getElementById('modal-explanation').textContent = c.explanation || "";

            const modalDeleteBtn = document.getElementById('modal-delete-btn');
            if (modalDeleteBtn) {
                modalDeleteBtn.onclick = () => removeCandidateFromWebpage(c.resume_path, rName);
            }

            const rawS = c.raw_score !== undefined ? c.raw_score : c.final_score;
            const perc = c.percentile_score !== undefined ? c.percentile_score : c.final_score;
            const techP = c.technical_percentile !== undefined ? c.technical_percentile : c.technical_score;
            const expP = c.experience_percentile !== undefined ? c.experience_percentile : c.experience_score;
            const eduP = c.education_percentile !== undefined ? c.education_percentile : c.education_score;
            const certP = c.certification_percentile !== undefined ? c.certification_percentile : c.certification_score;
            const projP = c.project_percentile !== undefined ? c.project_percentile : c.project_score;

            const hrFitScore = c.hr_fit_score !== undefined ? c.hr_fit_score : 100.0;
            const hrFitLabel = c.hr_fit_label || "N/A";

            // Scorecards
            document.getElementById('modal-scores').innerHTML = `
                <div class="score-card" style="border-top: 3px solid #818cf8;"><p>Overall Percentile</p><h3 style="color:#a5b4fc;">${perc}th</h3></div>
                <div class="score-card"><p>Raw Score</p><h3>${rawS}</h3></div>
                <div class="score-card"><p>HR Fit</p><h3>${hrFitScore}%</h3></div>
                <div class="score-card"><p>Technical Skills</p><h3>${techP}th</h3></div>
                <div class="score-card"><p>Experience Fit</p><h3>${expP}th</h3></div>
                <div class="score-card"><p>Education</p><h3>${eduP}th</h3></div>
                <div class="score-card"><p>Certifications</p><h3>${certP}th</h3></div>
                <div class="score-card"><p>Project Fit</p><h3>${projP}th</h3></div>
            `;

            // Custom HR Query Breakdown Table
            const hrResults = c.hr_query_results || [];
            const hrSec = document.getElementById('modal-hr-query-section');
            const hrTab = document.getElementById('modal-hr-queries-table');
            if (hrSec && hrTab) {
                if (hrResults.length > 0) {
                    hrSec.style.display = 'block';
                    let hrTableHtml = `
                        <table style="font-size:0.8rem; border:1px solid var(--glass-border); border-radius:8px; margin-top:0.4rem;">
                            <thead>
                                <tr style="background:rgba(255,255,255,0.04);">
                                    <th style="padding:0.6rem;">HR Question / Requirement</th>
                                    <th style="padding:0.6rem;">Importance</th>
                                    <th style="padding:0.6rem;">Resume Answer</th>
                                    <th style="padding:0.6rem;">Evidence / Reason</th>
                                    <th style="padding:0.6rem;">Fit Result</th>
                                </tr>
                            </thead>
                            <tbody>
                    `;
                    hrResults.forEach(hrq => {
                        let fitBadge = "color:#fca5a5; background:rgba(239,68,68,0.2); border:1px solid rgba(239,68,68,0.4);";
                        if (hrq.fit_result === "Yes") fitBadge = "color:#6ee7b7; background:rgba(16,185,129,0.2); border:1px solid rgba(16,185,129,0.4);";
                        else if (hrq.fit_result === "Partially/Unclear") fitBadge = "color:#fde047; background:rgba(245,158,11,0.2); border:1px solid rgba(245,158,11,0.4);";

                        let impBadge = "color:#cbd5e1;";
                        if (hrq.importance === "Required") impBadge = "color:#fca5a5; font-weight:700;";

                        hrTableHtml += `
                            <tr>
                                <td style="padding:0.6rem; font-weight:600; color:#f8fafc;">${hrq.question}</td>
                                <td style="padding:0.6rem;"><span style="${impBadge}">${hrq.importance}</span></td>
                                <td style="padding:0.6rem; color:#e2e8f0;">${hrq.answer}</td>
                                <td style="padding:0.6rem; font-style:italic; color:#94a3b8;">${hrq.evidence}</td>
                                <td style="padding:0.6rem;"><span style="padding:0.2rem 0.5rem; border-radius:4px; font-weight:700; font-size:0.75rem; ${fitBadge}">${hrq.fit_result}</span></td>
                            </tr>
                        `;
                    });
                    hrTableHtml += `</tbody></table>`;
                    hrTab.innerHTML = hrTableHtml;
                } else {
                    hrSec.style.display = 'none';
                }
            }

            // Strengths
            let strHtml = "";
            (c.strengths || []).forEach(s => strHtml += `<span class="pill pill-strength">✓ ${s}</span>`);
            document.getElementById('modal-strengths').innerHTML = strHtml || '<p style="color:#94a3b8; font-size:0.8rem;">None recorded</p>';

            // Skills
            let skHtml = "";
            (rJson.skills || []).forEach(s => skHtml += `<span class="pill">${s}</span>`);
            document.getElementById('modal-skills').innerHTML = skHtml || '<p style="color:#94a3b8;">None listed</p>';

            // Certs & Licenses
            let certsHtml = "";
            const certList = (rJson.certifications || []).concat(rJson.licenses || []);
            certList.forEach(ct => certsHtml += `<span class="pill" style="background:rgba(16, 185, 129, 0.15); color:#6ee7b7;">📜 ${ct}</span>`);
            document.getElementById('modal-certs').innerHTML = certsHtml || '<p style="color:#94a3b8;">None listed</p>';

            // Education
            let eduHtml = "";
            (rJson.education || []).forEach(e => {
                if (typeof e === 'object') {
                    const deg = e.degree || '';
                    const maj = e.major || '';
                    const showMajor = maj && !deg.toLowerCase().includes(maj.toLowerCase()) ? ` in ${maj}` : '';
                    eduHtml += `<div style="background:rgba(15,23,42,0.4); padding:8px; border-radius:6px; margin-top:4px;">🎓 <strong>${deg}${showMajor}</strong> (${e.institution || ''})</div>`;
                }
            });
            document.getElementById('modal-education').innerHTML = eduHtml;

            // Experience
            let expHtml = "";
            (rJson.experience || []).forEach(e => {
                if (typeof e === 'object') {
                    expHtml += `<div style="margin-top:8px;"><strong>${e.job_title || ''}</strong> at ${e.company || ''} (${e.duration || ''})<p style="font-size:0.8rem; color:#cbd5e1;">${e.description || ''}</p></div>`;
                }
            });
            document.getElementById('modal-experience').innerHTML = expHtml;

            document.getElementById('details-modal').style.display = 'flex';
        }

        function closeDetailsModal() { document.getElementById('details-modal').style.display = 'none'; }
        function openUploadModal() { document.getElementById('upload-modal').style.display = 'flex'; }
        function closeUploadModal() { document.getElementById('upload-modal').style.display = 'none'; }

        async function uploadResumes() {
            const files = document.getElementById('resume-files').files;
            if (!files.length) return alert('Select files first');
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) formData.append('files', files[i]);
            const res = await fetch('/api/upload-resumes', { method: 'POST', body: formData });
            const data = await res.json();
            alert(data.message);
            closeUploadModal();
            fetchJobs();
        }

        async function uploadJDFile() {
            const file = document.getElementById('jd-file').files[0];
            if (!file) return alert('Select a text file first');
            const formData = new FormData();
            formData.append('file', file);
            const res = await fetch('/api/upload-jd', { method: 'POST', body: formData });
            const data = await res.json();
            alert(data.message);
            closeUploadModal();
            fetchJobs();
        }

        function downloadReport(type) {
            if (!currentSelectedJD) return;
            window.open(`/api/reports/download/${type}/${currentSelectedJD}`, '_blank');
        }

        fetchJobs();
    </script>
</body>
</html>
"""
    return HTMLResponse(content=dashboard_html)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8050, reload=True)


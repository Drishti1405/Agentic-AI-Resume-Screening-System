import os
import glob
import json
import shutil
from typing import Optional, List
from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables (OPENAI_API_KEY, etc.)
load_dotenv()

# Import the LangGraph workflow
from graph import graph

app = FastAPI(
    title="Agentic AI Resume Screening API",
    description="Multi-Agent Candidate Screening & Evaluation Engine using LangGraph, FAISS, and Scipy",
    version="2.1.0"
)

# Enable CORS for decoupled frontend (e.g. localhost:3000, localhost:5173, production domains)
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

@app.get("/")
def root_status():
    """Health check & API info endpoint."""
    return {
        "status": "online",
        "service": "Agentic AI Resume Screening System Backend",
        "version": "2.1.0",
        "documentation": "/docs",
        "total_jobs": len(get_job_description_list()),
        "total_resumes": len(glob.glob("resumes/*.*"))
    }

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
        resumes = sorted(glob.glob("resumes/*.*"))
        valid_resumes = [os.path.basename(r) for r in resumes if os.path.splitext(r)[1].lower() in [".pdf", ".docx", ".doc", ".txt"]]
        
        return {
            "all_resumes": valid_resumes,
            "total_count": len(valid_resumes),
            "evaluated_count": min(len(valid_resumes), 20),
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
            uploaded.append(file.filename)
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
        raise HTTPException(status_code=500, detail=f"Multi-Agent Pipeline execution failed: {str(e)}")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

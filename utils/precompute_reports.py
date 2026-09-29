import os
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph import graph

def precompute():
    os.makedirs("reports", exist_ok=True)
    jd_files = sorted(glob.glob("job_descriptions/*.txt"))
    
    all_resumes = sorted(glob.glob("resumes/*.*"))

    for jd_path in jd_files:
        jd_filename = os.path.basename(jd_path)
        
        # Filter resumes relevant to the domain or use all resumes
        if "healthcare" in jd_filename:
            resumes = [r for r in all_resumes if "hc_" in r]
        elif "legal" in jd_filename:
            resumes = [r for r in all_resumes if "law_" in r]
        elif "finance" in jd_filename:
            resumes = [r for r in all_resumes if "fin_" in r]
        elif "mechanical" in jd_filename or "devops" in jd_filename:
            resumes = [r for r in all_resumes if "eng_" in r]
        elif "frontend" in jd_filename:
            resumes = [r for r in all_resumes if "fe_" in r]
        elif "data_science" in jd_filename:
            resumes = [r for r in all_resumes if "ds_" in r]
        elif "ai_ml" in jd_filename or "ai" in jd_filename:
            resumes = [r for r in all_resumes if "ai_" in r]
        elif "fullstack" in jd_filename or "fs" in jd_filename:
            resumes = [r for r in all_resumes if "fs_" in r]
        elif "fashion" in jd_filename:
            resumes = [r for r in all_resumes if "fash_" in r]
        elif "hospitality" in jd_filename:
            resumes = [r for r in all_resumes if "hosp_" in r]
        elif "energy" in jd_filename:
            resumes = [r for r in all_resumes if "energy_" in r]
        elif "construction" in jd_filename or "civil" in jd_filename:
            resumes = [r for r in all_resumes if "const_" in r]
        elif "transportation" in jd_filename or "logistics" in jd_filename:
            resumes = [r for r in all_resumes if "trans_" in r]
        elif "defence" in jd_filename or "cyber" in jd_filename:
            resumes = [r for r in all_resumes if "def_" in r]
        else:
            resumes = all_resumes[:20]

        if not resumes or len(resumes) < 10:
            resumes = all_resumes[:20]

        with open(jd_path, "r", encoding="utf-8", errors="ignore") as f:
            jd_text = f.read()

        print(f"Pre-computing screening pipeline for {jd_filename} against {len(resumes)} candidate resumes...")
        sample_hr_queries = [
            {"question": "Does the candidate have experience working with a startup or early-stage team?", "importance": "Important"},
            {"question": "Does the candidate have leadership, mentoring, or team management experience?", "importance": "Important"},
            {"question": "Has the candidate worked on production-level scalable software projects?", "importance": "Important"}
        ]

        inputs = {
            "jd_text": jd_text,
            "resume_paths": resumes,
            "hr_queries": sample_hr_queries,
            "ranking_mode": "overall_percentile",
            "candidates": []
        }
        
        result = graph.invoke(inputs)
        print(f"Successfully generated reports for {jd_filename}")
        print(f"  - Markdown: {result.get('report_markdown_path')}")
        print(f"  - PDF: {result.get('report_pdf_path')}\n")

if __name__ == "__main__":
    precompute()

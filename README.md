# Agentic Technical Recruiter using LangGraph

This project is a prototype of an **Agentic AI Resume Screening System** built using **LangGraph**, **FastAPI**, **LangChain**, and **Sentence Transformers / FAISS**. It simulates an experienced technical recruiter that parses multiple PDF resumes and text Job Descriptions, runs semantic vector and LLM matching, calculates weighted scores, ranks candidates, maps them to quartiles (Highly Likely, Most Likely, Likely, Not Likely), and presents them on a gorgeous recruiter dashboard.

---

## Folder Structure

```
project/
├── app.py                     # FastAPI server & Recruiter Dashboard
├── graph.py                   # LangGraph workflow structure
├── state.py                   # State variables (parent & child subgraph)
├── requirements.txt           # Project dependencies
├── README.md                  # This file
├── agents/                    # Agent implementations
│   ├── resume_loader.py       # Reads PDF files via PyPDF
│   ├── resume_parser.py       # Extracts structured Pydantic JSON via LLM
│   ├── jd_parser.py           # Extracts structured Job requirements via LLM
│   ├── matcher.py             # Computes similarity via Sentence Transformers & FAISS
│   ├── scorer.py              # Computes final weighted recruiter score
│   ├── ranker.py              # Sorts and slices top candidates
│   ├── quantile.py            # Assigns quartile recommendations
│   ├── explainer.py           # Generates recruiter summaries
│   └── report.py              # Outputs Markdown reports & JSON data
├── utils/
│   └── generate_mock_data.py  # Generates 20 mock resumes (PDFs) & 3 JDs
├── resumes/                   # PDF Resume folder (pre-populated by generator)
├── job_descriptions/          # Job Description text folder
└── reports/                   # Output reports and cached dashboard JSONs
```

---

## Architecture details

The system is architected as a parallel map-reduce workflow in LangGraph:
1. **JD Parser Node**: Runs first to convert job description text to structural JSON.
2. **Conditional Map Route**: Triggers a parallel worker subgraph for each candidate resume.
3. **Subgraph Nodes (per candidate)**:
   - **Resume Loader**: Extracts text from PDF.
   - **Resume Parser**: Extracts structured entities (skills, experience, etc.) using `gpt-4o`.
   - **Matcher**: Uses `all-MiniLM-L6-v2` embeddings in a local `FAISS` index to match candidate skills against JD required/preferred skills. It then couples this score with a multi-criteria LLM evaluation.
   - **Scorer**: Computes the final weighted score:
     $$\text{Final Score} = 0.40 \times \text{Technical} + 0.20 \times \text{Experience} + 0.15 \times \text{Projects} + 0.10 \times \text{Education} + 0.10 \times \text{Soft Skills} + 0.05 \times \text{Certifications}$$
   - **Explainer**: Generates a 1-2 sentence narrative explanation.
4. **Reduce / Aggregation**: Once all candidates complete the sub-branch, the results merge into the parent state.
5. **Ranker Node**: Sorts and ranks the candidates.
6. **Quantile Node**: Calculates quartiles (Highly Likely, Most Likely, Likely, Not Likely) across the candidate pool.
7. **Report Node**: Generates reports in `reports/` and prepares dashboard structures.

---

## Setup Instructions

### 1. Prerequisites
Ensure you have Python 3.9+ and `uv` (fast package manager) installed.
If `uv` is not installed, install it:
- **macOS/Linux**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Windows**: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

### 2. Install Dependencies
Create a virtual environment and install the requirements:
```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 3. Configure API Keys
Create a file named `.env` in the root of the project directory and insert your OpenAI API key:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Generate Mock Data
Generate the 20 sample resumes as PDF files (using reportlab) and the 3 Job Descriptions (Frontend, Data Science, DevOps):
```bash
python3 utils/generate_mock_data.py
```
This will populate the `resumes/` and `job_descriptions/` folders automatically.

### 5. Launch the Recruiter Dashboard
Run the FastAPI application server:
```bash
uvicorn app:app --host 0.0.0.0 --port 8005 --reload
```

Open your browser and navigate to:
```
http://localhost:8005
```

---

## Features of the Recruiter Dashboard
- **Job Role Selector**: Screen candidates for any of the 3 loaded job roles.
- **Glassmorphism Dark Mode Theme**: Visual gauges, progress bars, and clean typography.
- **Category Match Percentages**: Clear breakdown showing why a candidate was ranked.
- **Detail Modal**: Clicking on any candidate reveals their contact details, recruiter narrative assessment, full experience summary, and exact parsed skills.
- **Auto-generated Reports**: Markdown files containing leaderboard summaries are saved in `reports/` on each run.

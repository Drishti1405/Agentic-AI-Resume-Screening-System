# Backend — Agentic AI Resume Screening Engine

FastAPI-powered multi-agent recruitment screening service built with **LangGraph**, **Sentence-Transformers & FAISS**, and **Scipy**.

---

## 📁 Architecture
- `main.py`: FastAPI server exposing candidate evaluation REST APIs.
- `graph.py`: LangGraph state machine orchestrating domain analysis, multi-agent parsing, matching, and ranking.
- `state.py`: TypedDict state schemas (`RecruitmentState`, `CandidateState`).
- `agents/`: Dedicated single-responsibility agents:
  - `jd_parser.py`: Extracts structured JSON criteria from Job Descriptions.
  - `domain_understanding.py`: Infers role industry & calculates dynamic weighting matrix.
  - `resume_loader.py`: Ingests PDF/DOCX resumes.
  - `resume_parser.py`: Pydantic structured profile extraction with regex fallbacks.
  - `matcher.py`: Dense semantic vector search via **FAISS** + **all-MiniLM-L6-v2** embeddings + lexical alignment.
  - `scorer.py`: Weighted multi-category score calculation.
  - `hr_query.py`: Custom recruiter question evaluation & evidence extraction.
  - `ranker.py`: Continuous empirical percentiles via `scipy.stats.percentileofscore`.
  - `recommendation.py`: Quartile mapping (Highly Recommended, Recommended, Consider, Not Recommended).
  - `explainer.py`: Recruiter narrative summaries & interview question recommendations.
  - `report.py`: Automated generation of JSON, Markdown, and PDF candidate reports.

---

## 🚀 Running Locally

```bash
# 1. Activate environment
source ../.venv/bin/activate   # or create your own: python3 -m venv .venv

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the FastAPI server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive Swagger API docs available at: `http://localhost:8000/docs`

---

## 🐳 Docker Deployment

```bash
docker build -t resume-screener-backend .
docker run -p 8000:8000 -e OPENAI_API_KEY=your_key_here resume-screener-backend
```

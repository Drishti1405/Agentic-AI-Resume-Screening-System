import os
import pypdf

def load_resume_text_from_pdf(resume_path: str) -> str:
    reader = pypdf.PdfReader(resume_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()

def load_resume_text_from_docx(resume_path: str) -> str:
    try:
        import docx
        doc = docx.Document(resume_path)
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text.strip())
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        full_text.append(cell.text.strip())
        return "\n".join(full_text)
    except ImportError:
        # Fallback if python-docx not available
        with open(resume_path, "rb") as f:
            raw = f.read().decode("utf-8", errors="ignore")
        return raw

def load_resume(resume_path: str) -> str:
    """
    Reads a PDF, DOCX, or TXT resume file and extracts clean text content.
    """
    if not os.path.exists(resume_path):
        raise FileNotFoundError(f"Resume file not found at: {resume_path}")
        
    ext = os.path.splitext(resume_path)[1].lower()
    
    try:
        if ext == ".pdf":
            text = load_resume_text_from_pdf(resume_path)
        elif ext in [".docx", ".doc"]:
            text = load_resume_text_from_docx(resume_path)
        else:
            with open(resume_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
                
        # Clean extracted text
        cleaned_text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
        return cleaned_text
    except Exception as e:
        raise RuntimeError(f"Error reading resume file {resume_path}: {e}")

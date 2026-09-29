FROM python:3.9-slim

# Prevent Python from writing .pyc and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV KMP_DUPLICATE_LIB_OK=TRUE
ENV OMP_NUM_THREADS=1

WORKDIR /app

# Install system dependencies needed for compiling packages and PDF processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Ensure storage directories exist
RUN mkdir -p resumes job_descriptions reports data

# Expose port for FastAPI application
EXPOSE 8005

# Launch the FastAPI Recruiter Dashboard
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8005"]

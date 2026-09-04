# Base image with Python and standard dependencies
FROM python:3.12-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-serve.txt .
RUN pip install --no-cache-dir -r requirements-serve.txt

# Copy source code and config
COPY src/ ./src/
COPY config/ ./config/
COPY app/ ./app/

# Set Python path
ENV PYTHONPATH=/app

# --- API TARGET ---
FROM base as api
EXPOSE 8000
CMD ["uvicorn", "src.serving.main:app", "--host", "0.0.0.0", "--port", "8000"]

# --- FRONTEND TARGET ---
FROM base as frontend
EXPOSE 8501
CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]

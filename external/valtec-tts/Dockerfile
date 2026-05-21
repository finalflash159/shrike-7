# Valtec Vietnamese TTS - Docker Image
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsndfile1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
# Install CPU-only PyTorch first, then other requirements (excluding torch from requirements)
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir $(grep -v '^torch' requirements.txt | grep -v '^torchaudio') && \
    pip install --no-cache-dir gradio==5.38.0

# Copy application code
COPY . .

# Create outputs directory
RUN mkdir -p /app/outputs

# Expose Gradio port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860')" || exit 1

# Default command - run Gradio demo
CMD ["python", "app.py"]

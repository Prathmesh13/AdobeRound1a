# High-Performance PDF Processing System
# Optimized for AMD64 architecture with strict performance constraints
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for PyMuPDF
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies directly
RUN pip install --no-cache-dir PyMuPDF==1.26.3

# Copy application code
COPY *.py ./

# Create input and output directories
RUN mkdir -p /app/input /app/output

# Set environment variables for optimal performance
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV INPUT_DIR=/app/input
ENV OUTPUT_DIR=/app/output
ENV MAX_WORKERS=8
ENV MAX_MEMORY_MB=200
ENV TIMEOUT_SECONDS=10
ENV MAX_PAGES_FOR_ANALYSIS=50

# Run the PDF processing system
CMD ["python", "process_pdfs.py"]
# PDF Processing System - Git Repository Setup Guide

## 📋 Repository Structure

Your Git repository should contain these files:

```
pdf-processor/
├── README.md                   # Main documentation
├── SETUP.md                    # This setup guide
├── Dockerfile                  # Docker container configuration
├── pyproject.toml             # Python dependencies
├── process_pdfs.py            # Main entry point
├── pdf_processor.py           # Core PDF processing
├── title_extractor.py         # Title extraction module
├── outline_extractor.py       # Outline extraction module
├── json_validator.py          # Schema validation
├── utils.py                   # Utility functions
├── config.py                  # Configuration management
├── input/                     # Input PDF directory (create empty)
├── output/                    # Output JSON directory (create empty)
└── .gitignore                 # Git ignore file
```

## 🚀 Quick Start Steps

### 1. Clone and Setup Repository

```bash
# Clone your repository
git clone <your-repo-url>
cd pdf-processor

# Create required directories
mkdir -p input output

# Verify all files are present
ls -la
```

### 2. Add Sample PDFs

```bash
# Place your test PDF files in the input directory
cp /path/to/your/test-files/*.pdf input/
```

### 3. Build Docker Image

```bash
# Build the Docker image (AMD64 platform required)
docker build --platform linux/amd64 -t pdf-processor .
```

### 4. Run Docker Container

```bash
# Run the processing system
docker run --rm \
    -v $(pwd)/input:/app/input:ro \
    -v $(pwd)/output:/app/output \
    --network none \
    pdf-processor
```

## 📁 File Contents Required

All Python files (`*.py`) and the `Dockerfile` are already configured. You need to create:

### `.gitignore` File
```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.log
.DS_Store
*.swp
*.swo
*~
.vscode/
.idea/
```

### `pyproject.toml` File
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "pdf-processor"
version = "1.0.0"
description = "High-performance PDF processing system for title and outline extraction"
authors = [{name = "Your Name", email = "your.email@example.com"}]
dependencies = [
    "PyMuPDF>=1.26.0",
]
requires-python = ">=3.11"

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "black>=22.0.0",
    "flake8>=4.0.0",
]
```

## 🔧 Docker Commands Reference

### Build Commands
```bash
# Standard build
docker build --platform linux/amd64 -t pdf-processor .

# Build with custom tag
docker build --platform linux/amd64 -t your-repo/pdf-processor:v1.0 .

# Build with no cache (if needed)
docker build --no-cache --platform linux/amd64 -t pdf-processor .
```

### Run Commands
```bash
# Basic run (processes PDFs from input/ to output/)
docker run --rm \
    -v $(pwd)/input:/app/input:ro \
    -v $(pwd)/output:/app/output \
    --network none \
    pdf-processor

# Run with custom directories
docker run --rm \
    -v /path/to/your/pdfs:/app/input:ro \
    -v /path/to/output:/app/output \
    --network none \
    pdf-processor

# Run with environment variables
docker run --rm \
    -e MAX_WORKERS=8 \
    -e MAX_MEMORY_MB=150 \
    -e TIMEOUT_SECONDS=5 \
    -v $(pwd)/input:/app/input:ro \
    -v $(pwd)/output:/app/output \
    --network none \
    pdf-processor
```

## 📊 Expected Output

After running, you'll find:
- `output/*.json` - Individual PDF processing results
- `output/processing_summary.json` - Overall processing statistics

### Sample JSON Output Structure
```json
{
  "title": "Document Title Here",
  "outline": [
    {
      "level": "h1",
      "text": "Chapter 1: Introduction",
      "page": 1
    },
    {
      "level": "h2", 
      "text": "1.1 Overview",
      "page": 1
    }
  ]
}
```

## ⚡ Performance Specifications

- **Processing Speed**: ≤10 seconds for 50-page PDFs (typically 0.05s per file)
- **Memory Usage**: ≤200MB total system memory
- **Architecture**: AMD64 CPU-only (no GPU required)
- **Network**: No internet access required during processing
- **Concurrency**: Multi-threaded processing with configurable worker count

## 🛠️ Configuration Options

Set these environment variables when running Docker:

- `MAX_WORKERS`: Thread pool size (default: 4)
- `MAX_MEMORY_MB`: Memory limit in MB (default: 200)
- `TIMEOUT_SECONDS`: Per-file timeout (default: 10)
- `MAX_PAGES_FOR_ANALYSIS`: Page limit for processing (default: 50)
- `LOG_LEVEL`: Logging verbosity (default: INFO)

## 🔍 Troubleshooting

### Common Issues

1. **Permission denied on output directory**
   ```bash
   chmod 755 output/
   ```

2. **Docker build fails**
   ```bash
   # Clean Docker cache
   docker system prune -a
   # Rebuild
   docker build --no-cache --platform linux/amd64 -t pdf-processor .
   ```

3. **No PDFs found**
   ```bash
   # Verify input directory
   ls -la input/
   # Ensure files have .pdf extension
   ```

## 📈 Testing Your Setup

1. Add test PDFs to `input/` directory
2. Run the Docker command
3. Check `output/` for JSON files
4. Verify `processing_summary.json` shows successful results

The system is optimized for high-performance batch processing and meets all submission requirements for containerized PDF processing systems.
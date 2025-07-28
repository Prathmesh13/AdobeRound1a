"""
Configuration settings for the PDF processing system.
"""

import os
from pathlib import Path


class Config:
    """Configuration class for PDF processing system."""
    
    # Directory paths
    INPUT_DIR = os.getenv("INPUT_DIR", "./input")
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")
    
    # Performance settings
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))  # Thread pool size
    MAX_MEMORY_MB = int(os.getenv("MAX_MEMORY_MB", "200"))  # Memory limit
    TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "10"))  # Per-file timeout
    
    # Processing settings
    MAX_PAGES_FOR_ANALYSIS = int(os.getenv("MAX_PAGES_FOR_ANALYSIS", "50"))
    MAX_OUTLINE_ITEMS = int(os.getenv("MAX_OUTLINE_ITEMS", "100"))
    
    # Title extraction settings
    TITLE_MAX_LENGTH = int(os.getenv("TITLE_MAX_LENGTH", "500"))
    TITLE_MIN_LENGTH = int(os.getenv("TITLE_MIN_LENGTH", "3"))
    
    # Outline extraction settings
    OUTLINE_TEXT_MAX_LENGTH = int(os.getenv("OUTLINE_TEXT_MAX_LENGTH", "1000"))
    OUTLINE_TEXT_MIN_LENGTH = int(os.getenv("OUTLINE_TEXT_MIN_LENGTH", "2"))
    
    # Logging settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "pdf_processing.log")
    
    # Debug settings
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    SAVE_INTERMEDIATE_RESULTS = os.getenv("SAVE_INTERMEDIATE_RESULTS", "false").lower() == "true"
    
    @classmethod
    def validate(cls):
        """Validate configuration settings."""
        # Ensure directories exist or can be created
        input_path = Path(cls.INPUT_DIR)
        output_path = Path(cls.OUTPUT_DIR)
        
        if not input_path.exists():
            raise ValueError(f"Input directory does not exist: {cls.INPUT_DIR}")
        
        # Create output directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Validate numeric settings
        if cls.MAX_WORKERS < 1:
            raise ValueError("MAX_WORKERS must be >= 1")
        
        if cls.TIMEOUT_SECONDS < 1:
            raise ValueError("TIMEOUT_SECONDS must be >= 1")
        
        if cls.MAX_MEMORY_MB < 50:
            raise ValueError("MAX_MEMORY_MB must be >= 50")
    
    @classmethod
    def get_summary(cls) -> dict:
        """Get configuration summary for logging."""
        return {
            "input_dir": cls.INPUT_DIR,
            "output_dir": cls.OUTPUT_DIR,
            "max_workers": cls.MAX_WORKERS,
            "max_memory_mb": cls.MAX_MEMORY_MB,
            "timeout_seconds": cls.TIMEOUT_SECONDS,
            "max_pages_for_analysis": cls.MAX_PAGES_FOR_ANALYSIS,
            "max_outline_items": cls.MAX_OUTLINE_ITEMS,
            "debug": cls.DEBUG
        }

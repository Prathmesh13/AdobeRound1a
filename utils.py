"""
Utility functions for PDF processing.
"""

import re
import logging
from typing import Optional, List, Any

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """
    Clean and normalize text content.
    
    Args:
        text: Raw text string
        
    Returns:
        Cleaned text
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove non-printable characters except common ones
    text = re.sub(r'[^\x20-\x7E\u00A0-\uFFFF]', '', text)
    
    # Remove common PDF artifacts
    text = re.sub(r'\.{3,}', '...', text)  # Multiple dots
    text = re.sub(r'\s*\.\s*\.\s*\.', '...', text)  # Spaced dots
    
    return text.strip()


def normalize_level(level: int) -> str:
    """
    Convert numeric level to h1, h2, h3, etc.
    
    Args:
        level: Numeric level (1, 2, 3, ...)
        
    Returns:
        Normalized level string (h1, h2, h3, ...)
    """
    # Clamp level between 1 and 6
    level = max(1, min(6, level))
    return f"h{level}"


def detect_heading_level(text: str, font_size: float, flags: int, avg_font_size: float) -> str:
    """
    Detect the heading level based on text content and formatting.
    
    Args:
        text: Text content
        font_size: Font size
        flags: Text formatting flags
        avg_font_size: Average font size on page
        
    Returns:
        Heading level (h1, h2, h3, etc.)
    """
    text_lower = text.lower()
    
    # Check for explicit level indicators
    if re.match(r'^\d+\.\d+\.\d+', text):  # 1.1.1 format
        return "h3"
    elif re.match(r'^\d+\.\d+', text):  # 1.1 format
        return "h2"
    elif re.match(r'^\d+\.?', text):  # 1. format
        return "h1"
    elif re.match(r'^[IVX]+\.?', text):  # Roman numerals
        return "h1"
    elif re.match(r'^[A-Z]\.', text):  # A. format
        return "h2"
    
    # Check for keyword indicators
    if 'chapter' in text_lower or 'part' in text_lower:
        return "h1"
    elif 'section' in text_lower:
        return "h2"
    elif 'subsection' in text_lower:
        return "h3"
    
    # Use font size relative to average
    size_ratio = font_size / avg_font_size if avg_font_size > 0 else 1.0
    
    if size_ratio >= 1.8:
        return "h1"
    elif size_ratio >= 1.5:
        return "h2"
    elif size_ratio >= 1.2:
        return "h3"
    else:
        return "h4"


def is_likely_title(text: str) -> bool:
    """
    Determine if text is likely to be a document title.
    
    Args:
        text: Text to analyze
        
    Returns:
        True if likely a title
    """
    if not text or len(text) < 3:
        return False
    
    text_lower = text.lower()
    
    # Too long to be a title
    if len(text) > 200:
        return False
    
    # Common non-title patterns
    non_title_patterns = [
        r'^\d+$',  # Just numbers
        r'^page\s+\d+',  # "Page 1"
        r'^\d+\s*of\s*\d+',  # "1 of 10"
        r'^(table|figure|chart|diagram)',  # Captions
        r'^(see|refer|note|example)',  # References
        r'^(http|www|ftp)',  # URLs
        r'@',  # Email addresses
    ]
    
    for pattern in non_title_patterns:
        if re.search(pattern, text_lower):
            return False
    
    # Common title indicators
    title_indicators = [
        r'^(chapter|section|part)\s+\d+',  # "Chapter 1"
        r'^\d+\.?\s+[A-Z]',  # "1. Title" or "1 Title"
        r'^[IVX]+\.?\s+[A-Z]',  # Roman numerals
    ]
    
    for pattern in title_indicators:
        if re.search(pattern, text):
            return True
    
    # General characteristics of titles
    # - Starts with capital letter
    # - Not all caps (unless short)
    # - Contains letters
    if (text[0].isupper() and 
        re.search(r'[a-zA-Z]', text) and 
        (not text.isupper() or len(text) <= 50)):
        return True
    
    return False


def filter_outline_items(outline: List[dict], max_items: int = 100) -> List[dict]:
    """
    Filter and limit outline items for performance.
    
    Args:
        outline: List of outline items
        max_items: Maximum number of items to keep
        
    Returns:
        Filtered outline list
    """
    if len(outline) <= max_items:
        return outline
    
    # Keep items with preference for higher levels (h1, h2 over h3, h4, etc.)
    level_priority = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
    
    # Sort by level priority, then by page
    outline.sort(key=lambda x: (level_priority.get(x["level"], 6), x["page"]))
    
    return outline[:max_items]


def validate_page_number(page: int, max_pages: int) -> int:
    """
    Validate and clamp page number to valid range.
    
    Args:
        page: Page number to validate
        max_pages: Maximum valid page number
        
    Returns:
        Valid page number
    """
    return max(1, min(page, max_pages))


def estimate_processing_time(page_count: int) -> float:
    """
    Estimate processing time based on page count.
    
    Args:
        page_count: Number of pages in PDF
        
    Returns:
        Estimated processing time in seconds
    """
    # Base processing time plus per-page factor
    base_time = 0.5  # seconds
    per_page = 0.1   # seconds per page
    
    return base_time + (page_count * per_page)

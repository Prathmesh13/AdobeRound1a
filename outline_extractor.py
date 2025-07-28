"""
Outline extraction module for PDF documents.
Extracts hierarchical document structure from bookmarks and content analysis.
"""

import fitz
import re
import logging
from typing import List, Dict, Any, Optional, Tuple

from utils import clean_text, normalize_level, detect_heading_level

logger = logging.getLogger(__name__)


class OutlineExtractor:
    """Extracts document outlines from PDF files."""
    
    def __init__(self):
        # Heading patterns for content-based extraction
        self.heading_patterns = [
            r'^(\d+\.?\s+.+)',  # "1. Heading" or "1 Heading"
            r'^([IVX]+\.?\s+.+)',  # Roman numerals
            r'^([A-Z]\.?\s+.+)',  # "A. Heading"
            r'^(Chapter\s+\d+.+)',  # "Chapter 1 Title"
            r'^(Section\s+\d+.+)',  # "Section 1 Title"
            r'^(\d+\.\d+\s+.+)',  # "1.1 Subheading"
            r'^(\d+\.\d+\.\d+\s+.+)',  # "1.1.1 Sub-subheading"
        ]
        
        # Level indicators
        self.level_indicators = {
            'chapter': 'h1',
            'section': 'h2',
            'subsection': 'h3',
            'part': 'h1',
            'appendix': 'h2'
        }
    
    def extract_outline(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        """
        Extract document outline using multiple strategies.
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            List of outline items with level, text, and page
        """
        # Strategy 1: PDF bookmarks/TOC
        outline = self._extract_from_bookmarks(doc)
        if outline:
            logger.debug(f"Outline extracted from bookmarks: {len(outline)} items")
            return outline
        
        # Strategy 2: Content analysis
        outline = self._extract_from_content(doc)
        if outline:
            logger.debug(f"Outline extracted from content: {len(outline)} items")
            return outline
        
        logger.warning("No outline found")
        return []
    
    def _extract_from_bookmarks(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        """Extract outline from PDF bookmarks/table of contents."""
        try:
            toc = doc.get_toc()
            
            if not toc:
                return []
            
            outline = []
            
            for item in toc:
                level, title, page = item
                
                # Clean and validate
                clean_title = clean_text(title)
                if not clean_title or len(clean_title) < 2:
                    continue
                
                # Normalize level to h1, h2, h3, etc.
                normalized_level = normalize_level(level)
                
                # Ensure page is valid
                page_num = max(1, min(page, doc.page_count))
                
                outline.append({
                    "level": normalized_level,
                    "text": clean_title,
                    "page": page_num
                })
            
            return outline
            
        except Exception as e:
            logger.debug(f"Error extracting outline from bookmarks: {str(e)}")
            return []
    
    def _extract_from_content(self, doc: fitz.Document) -> List[Dict[str, Any]]:
        """Extract outline by analyzing document content."""
        try:
            outline = []
            
            # Analyze text formatting to find headings
            for page_num in range(doc.page_count):
                page = doc[page_num]
                headings = self._find_headings_on_page(page, page_num + 1)
                outline.extend(headings)
            
            # Filter and refine the outline
            outline = self._refine_outline(outline)
            
            return outline
            
        except Exception as e:
            logger.debug(f"Error extracting outline from content: {str(e)}")
            return []
    
    def _find_headings_on_page(self, page: fitz.Page, page_num: int) -> List[Dict[str, Any]]:
        """Find potential headings on a single page."""
        headings = []
        
        try:
            # Get text with formatting
            page_dict = page.get_text("dict")
            
            # Collect all text spans with their properties
            text_spans = []
            for block in page_dict.get("blocks", []):
                if "lines" not in block:
                    continue
                
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span.get("text", "").strip()
                        if text:
                            text_spans.append({
                                "text": text,
                                "font": span.get("font", ""),
                                "size": span.get("size", 0),
                                "flags": span.get("flags", 0),
                                "bbox": span.get("bbox", []),
                                "y": span.get("bbox", [0, 0, 0, 0])[1]
                            })
            
            # Sort by vertical position
            text_spans.sort(key=lambda x: x["y"])
            
            # Find potential headings
            avg_font_size = self._calculate_average_font_size(text_spans)
            
            for span in text_spans:
                text = span["text"]
                font_size = span["size"]
                flags = span["flags"]
                
                # Check if this looks like a heading
                if self._is_likely_heading(text, font_size, flags, avg_font_size):
                    level = detect_heading_level(text, font_size, flags, avg_font_size)
                    
                    headings.append({
                        "level": level,
                        "text": clean_text(text),
                        "page": page_num
                    })
            
        except Exception as e:
            logger.debug(f"Error finding headings on page {page_num}: {str(e)}")
        
        return headings
    
    def _calculate_average_font_size(self, text_spans: List[Dict[str, Any]]) -> float:
        """Calculate the average font size on the page."""
        if not text_spans:
            return 12.0
        
        total_size = sum(span["size"] for span in text_spans)
        return total_size / len(text_spans)
    
    def _is_likely_heading(self, text: str, font_size: float, flags: int, avg_font_size: float) -> bool:
        """Determine if text is likely a heading."""
        # Must be reasonably short
        if len(text) < 3 or len(text) > 200:
            return False
        
        # Font size significantly larger than average
        if font_size > avg_font_size * 1.2:
            return True
        
        # Bold text that's not too long
        if (flags & 2**4) and len(text) < 100:  # Bold flag
            return True
        
        # Matches heading patterns
        for pattern in self.heading_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        
        # Contains level indicators
        lower_text = text.lower()
        for indicator in self.level_indicators:
            if indicator in lower_text:
                return True
        
        return False
    
    def _refine_outline(self, outline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Refine and clean up the extracted outline."""
        if not outline:
            return []
        
        # Remove duplicates
        seen = set()
        refined = []
        
        for item in outline:
            key = (item["text"].lower(), item["page"])
            if key not in seen:
                seen.add(key)
                refined.append(item)
        
        # Sort by page number
        refined.sort(key=lambda x: x["page"])
        
        # Ensure reasonable hierarchy
        refined = self._fix_hierarchy(refined)
        
        return refined
    
    def _fix_hierarchy(self, outline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fix the hierarchical levels to ensure proper nesting."""
        if not outline:
            return []
        
        # Convert level strings to numbers for processing
        level_map = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
        reverse_map = {1: "h1", 2: "h2", 3: "h3", 4: "h4", 5: "h5", 6: "h6"}
        
        # Track current level
        current_level = 1
        
        for item in outline:
            level_num = level_map.get(item["level"], 1)
            
            # Don't allow jumps of more than 1 level
            if level_num > current_level + 1:
                level_num = current_level + 1
            
            item["level"] = reverse_map.get(level_num, "h1")
            current_level = level_num
        
        return outline

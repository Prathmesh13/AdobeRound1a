"""
Title extraction module for PDF documents.
Attempts multiple strategies to find the document title.
"""

import fitz
import re
import logging
from typing import Optional, List, Dict, Any

from utils import clean_text, is_likely_title

logger = logging.getLogger(__name__)


class TitleExtractor:
    """Extracts document titles from PDF files using multiple strategies."""
    
    def __init__(self):
        # Common title indicators
        self.title_patterns = [
            r'^title\s*:?\s*(.+)$',
            r'^(.+)\s*-\s*title$',
            r'^(.{10,100})$',  # Reasonable title length
        ]
        
        # Words to ignore in titles
        self.ignore_words = {
            'page', 'chapter', 'section', 'table', 'figure',
            'contents', 'index', 'appendix', 'bibliography',
            'abstract', 'introduction', 'conclusion'
        }
    
    def extract_title(self, doc: fitz.Document) -> str:
        """
        Extract title using multiple strategies.
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            Extracted title or empty string if not found
        """
        # Strategy 1: PDF metadata
        title = self._extract_from_metadata(doc)
        if title:
            logger.debug(f"Title found in metadata: '{title}'")
            return title
        
        # Strategy 2: Document outline/bookmarks
        title = self._extract_from_outline(doc)
        if title:
            logger.debug(f"Title found in outline: '{title}'")
            return title
        
        # Strategy 3: First page analysis
        title = self._extract_from_first_page(doc)
        if title:
            logger.debug(f"Title found on first page: '{title}'")
            return title
        
        # Strategy 4: Largest font text
        title = self._extract_by_font_size(doc)
        if title:
            logger.debug(f"Title found by font size: '{title}'")
            return title
        
        logger.warning("No title found, returning empty string")
        return ""
    
    def _extract_from_metadata(self, doc: fitz.Document) -> Optional[str]:
        """Extract title from PDF metadata."""
        try:
            metadata = doc.metadata or {}
            title = metadata.get("title", "").strip()
            
            if title and len(title) > 3:
                return clean_text(title)
                
        except Exception as e:
            logger.debug(f"Error extracting title from metadata: {str(e)}")
        
        return None
    
    def _extract_from_outline(self, doc: fitz.Document) -> Optional[str]:
        """Extract title from document outline if it has a root title."""
        try:
            outline = doc.get_toc()
            
            if outline and len(outline) > 0:
                # Look for a potential document title in the first outline item
                first_item = outline[0]
                level, title, page = first_item
                
                # If it's level 1 and seems like a title
                if level == 1 and is_likely_title(title):
                    return clean_text(title)
                    
        except Exception as e:
            logger.debug(f"Error extracting title from outline: {str(e)}")
        
        return None
    
    def _extract_from_first_page(self, doc: fitz.Document) -> Optional[str]:
        """Extract title by analyzing the first page."""
        try:
            if doc.page_count == 0:
                return None
            
            page = doc[0]
            text_blocks = self._get_text_blocks_with_formatting(page)
            
            # Look for title-like text in the first page
            candidates = []
            
            for block in text_blocks:
                text = block["text"].strip()
                
                # Skip very short or very long text
                if len(text) < 5 or len(text) > 200:
                    continue
                
                # Skip common non-title text
                if any(word.lower() in text.lower() for word in self.ignore_words):
                    continue
                
                # Check if it looks like a title
                if is_likely_title(text):
                    candidates.append({
                        "text": text,
                        "font_size": block.get("size", 0),
                        "y_position": block.get("bbox", [0, 0, 0, 0])[1],
                        "score": self._calculate_title_score(block)
                    })
            
            # Sort by score and return the best candidate
            candidates.sort(key=lambda x: x["score"], reverse=True)
            
            if candidates:
                return clean_text(candidates[0]["text"])
                
        except Exception as e:
            logger.debug(f"Error extracting title from first page: {str(e)}")
        
        return None
    
    def _extract_by_font_size(self, doc: fitz.Document) -> Optional[str]:
        """Find title by looking for the largest font text."""
        try:
            max_font_size = 0
            title_candidates = []
            
            # Check first 3 pages
            for page_num in range(min(3, doc.page_count)):
                page = doc[page_num]
                text_blocks = self._get_text_blocks_with_formatting(page)
                
                for block in text_blocks:
                    font_size = block.get("size", 0)
                    text = block["text"].strip()
                    
                    if font_size > max_font_size and len(text) > 5 and is_likely_title(text):
                        max_font_size = font_size
                        title_candidates = [text]
                    elif font_size == max_font_size and len(text) > 5 and is_likely_title(text):
                        title_candidates.append(text)
            
            # Return the first (topmost) candidate with the largest font
            if title_candidates:
                return clean_text(title_candidates[0])
                
        except Exception as e:
            logger.debug(f"Error extracting title by font size: {str(e)}")
        
        return None
    
    def _get_text_blocks_with_formatting(self, page: fitz.Page) -> List[Dict[str, Any]]:
        """Extract text blocks with formatting information."""
        blocks = []
        
        try:
            page_dict = page.get_text("dict")
            
            for block in page_dict.get("blocks", []):
                if "lines" not in block:
                    continue
                
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span.get("text", "").strip()
                        if text:
                            blocks.append({
                                "text": text,
                                "font": span.get("font", ""),
                                "size": span.get("size", 0),
                                "flags": span.get("flags", 0),
                                "bbox": span.get("bbox", []),
                                "color": span.get("color", 0)
                            })
        except Exception as e:
            logger.debug(f"Error getting text blocks: {str(e)}")
        
        return blocks
    
    def _calculate_title_score(self, block: Dict[str, Any]) -> float:
        """Calculate a score for how likely a text block is to be a title."""
        score = 0.0
        text = block["text"]
        font_size = block.get("size", 0)
        y_pos = block.get("bbox", [0, 0, 0, 0])[1]
        flags = block.get("flags", 0)
        
        # Font size factor
        score += font_size * 2
        
        # Position factor (higher on page = more likely title)
        score += max(0, 800 - y_pos) / 10
        
        # Bold text gets bonus
        if flags & 2**4:  # Bold flag
            score += 20
        
        # Length factor (reasonable title length)
        if 10 <= len(text) <= 100:
            score += 30
        
        # Title case bonus
        if text.istitle():
            score += 15
        
        # All caps penalty (unless short)
        if text.isupper() and len(text) > 20:
            score -= 10
        
        return score

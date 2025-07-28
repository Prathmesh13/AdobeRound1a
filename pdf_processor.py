"""
Core PDF processing module for extracting titles and outlines.
Uses PyMuPDF (fitz) for high-performance PDF parsing.
"""

import fitz  # PyMuPDF
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from title_extractor import TitleExtractor
from outline_extractor import OutlineExtractor
from utils import clean_text, normalize_level

logger = logging.getLogger(__name__)


class PDFProcessor:
    """High-performance PDF processor for title and outline extraction."""
    
    def __init__(self):
        self.title_extractor = TitleExtractor()
        self.outline_extractor = OutlineExtractor()
    
    def process_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Process a PDF file and extract title and outline.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing title and outline data
        """
        logger.debug(f"Opening PDF: {pdf_path}")
        
        try:
            # Open PDF document
            with fitz.open(str(pdf_path)) as doc:
                # Validate document
                if doc.is_closed or doc.page_count == 0:
                    raise ValueError("Invalid or empty PDF document")
                
                logger.debug(f"PDF opened successfully: {doc.page_count} pages")
                
                # Extract title
                title = self.title_extractor.extract_title(doc)
                
                # Extract outline
                outline = self.outline_extractor.extract_outline(doc)
                
                # Construct result
                result = {
                    "title": title,
                    "outline": outline
                }
                
                logger.debug(f"Extraction complete: title='{title}', outline_items={len(outline)}")
                return result
                
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            # Return empty structure on error
            return {
                "title": "",
                "outline": []
            }
    
    def get_document_info(self, doc: fitz.Document) -> Dict[str, Any]:
        """Extract basic document information."""
        try:
            metadata = doc.metadata or {}
            return {
                "page_count": doc.page_count,
                "title": metadata.get("title", ""),
                "author": metadata.get("author", ""),
                "subject": metadata.get("subject", ""),
                "creator": metadata.get("creator", ""),
                "producer": metadata.get("producer", ""),
                "creation_date": metadata.get("creationDate", ""),
                "modification_date": metadata.get("modDate", "")
            }
        except Exception as e:
            logger.warning(f"Could not extract document info: {str(e)}")
            return {"page_count": doc.page_count}
    
    def extract_text_blocks(self, doc: fitz.Document, max_pages: int = 5) -> List[Dict[str, Any]]:
        """
        Extract text blocks from the first few pages for analysis.
        Used for fallback title extraction and outline detection.
        """
        text_blocks = []
        
        try:
            for page_num in range(min(max_pages, doc.page_count)):
                page = doc[page_num]
                
                # Get text blocks with formatting information
                blocks = page.get_text("dict")["blocks"]
                
                for block in blocks:
                    if "lines" not in block:
                        continue
                    
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span.get("text", "").strip()
                            if text:
                                text_blocks.append({
                                    "text": text,
                                    "page": page_num + 1,
                                    "font": span.get("font", ""),
                                    "size": span.get("size", 0),
                                    "flags": span.get("flags", 0),
                                    "bbox": span.get("bbox", []),
                                    "color": span.get("color", 0)
                                })
                
        except Exception as e:
            logger.warning(f"Error extracting text blocks: {str(e)}")
        
        return text_blocks

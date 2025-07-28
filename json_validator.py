"""
JSON validation module for ensuring output conforms to the required schema.
"""

import json
import logging
from typing import Dict, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class JSONValidator:
    """Validates extracted data against the required JSON schema."""
    
    def __init__(self):
        # Define the expected schema structure
        self.schema = {
            "title": str,
            "outline": list
        }
        
        self.outline_item_schema = {
            "level": str,
            "text": str,
            "page": int
        }
        
        # Valid level values
        self.valid_levels = {"h1", "h2", "h3", "h4", "h5", "h6"}
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate the extracted data against the schema.
        
        Args:
            data: Dictionary containing title and outline data
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check top-level structure
            if not isinstance(data, dict):
                logger.error("Data must be a dictionary")
                return False
            
            # Check required fields
            if "title" not in data or "outline" not in data:
                logger.error("Missing required fields: title or outline")
                return False
            
            # Validate title
            if not self._validate_title(data["title"]):
                return False
            
            # Validate outline
            if not self._validate_outline(data["outline"]):
                return False
            
            logger.debug("Validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            return False
    
    def _validate_title(self, title: Any) -> bool:
        """Validate the title field."""
        if not isinstance(title, str):
            logger.error("Title must be a string")
            return False
        
        # Title can be empty, but if present should be reasonable length
        if len(title) > 500:
            logger.error("Title is too long (>500 characters)")
            return False
        
        return True
    
    def _validate_outline(self, outline: Any) -> bool:
        """Validate the outline field."""
        if not isinstance(outline, list):
            logger.error("Outline must be a list")
            return False
        
        # Empty outline is valid
        if len(outline) == 0:
            return True
        
        # Validate each outline item
        for i, item in enumerate(outline):
            if not self._validate_outline_item(item, i):
                return False
        
        return True
    
    def _validate_outline_item(self, item: Any, index: int) -> bool:
        """Validate a single outline item."""
        if not isinstance(item, dict):
            logger.error(f"Outline item {index} must be a dictionary")
            return False
        
        # Check required fields
        required_fields = ["level", "text", "page"]
        for field in required_fields:
            if field not in item:
                logger.error(f"Outline item {index} missing required field: {field}")
                return False
        
        # Validate level
        level = item["level"]
        if not isinstance(level, str):
            logger.error(f"Outline item {index} level must be a string")
            return False
        
        if level not in self.valid_levels:
            logger.error(f"Outline item {index} has invalid level: {level}")
            return False
        
        # Validate text
        text = item["text"]
        if not isinstance(text, str):
            logger.error(f"Outline item {index} text must be a string")
            return False
        
        if len(text.strip()) == 0:
            logger.error(f"Outline item {index} text cannot be empty")
            return False
        
        if len(text) > 1000:
            logger.error(f"Outline item {index} text is too long (>1000 characters)")
            return False
        
        # Validate page
        page = item["page"]
        if not isinstance(page, int):
            logger.error(f"Outline item {index} page must be an integer")
            return False
        
        if page < 1:
            logger.error(f"Outline item {index} page must be >= 1")
            return False
        
        return True
    
    def sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize and fix common data issues.
        
        Args:
            data: Raw extracted data
            
        Returns:
            Sanitized data
        """
        sanitized = {}
        
        # Sanitize title
        title = data.get("title", "")
        if not isinstance(title, str):
            title = str(title)
        sanitized["title"] = title.strip()[:500]  # Limit length
        
        # Sanitize outline
        outline = data.get("outline", [])
        if not isinstance(outline, list):
            outline = []
        
        sanitized_outline = []
        for item in outline:
            if not isinstance(item, dict):
                continue
            
            sanitized_item = {}
            
            # Sanitize level
            level = item.get("level", "h1")
            if not isinstance(level, str) or level not in self.valid_levels:
                level = "h1"
            sanitized_item["level"] = level
            
            # Sanitize text
            text = item.get("text", "")
            if not isinstance(text, str):
                text = str(text)
            text = text.strip()[:1000]  # Limit length
            if not text:
                continue  # Skip empty text items
            sanitized_item["text"] = text
            
            # Sanitize page
            page = item.get("page", 1)
            if not isinstance(page, int) or page < 1:
                page = 1
            sanitized_item["page"] = page
            
            sanitized_outline.append(sanitized_item)
        
        sanitized["outline"] = sanitized_outline
        
        return sanitized

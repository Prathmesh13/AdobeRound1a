#!/usr/bin/env python3
"""
Main entry point for PDF processing system.
Processes all PDFs from /app/input directory and generates JSON outputs.
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

from pdf_processor import PDFProcessor
from json_validator import JSONValidator
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pdf_processing.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)


class PDFProcessingSystem:
    """High-performance PDF processing system for title and outline extraction."""
    
    def __init__(self):
        self.config = Config()
        self.processor = PDFProcessor()
        self.validator = JSONValidator()
        self.input_dir = Path(self.config.INPUT_DIR)
        self.output_dir = Path(self.config.OUTPUT_DIR)
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def find_pdf_files(self) -> List[Path]:
        """Find all PDF files in the input directory."""
        if not self.input_dir.exists():
            logger.error(f"Input directory does not exist: {self.input_dir}")
            return []
        
        pdf_files = list(self.input_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        return pdf_files
    
    def process_single_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Process a single PDF file and return the results."""
        start_time = time.time()
        
        try:
            logger.info(f"Processing: {pdf_path.name}")
            
            # Extract title and outline
            result = self.processor.process_pdf(pdf_path)
            
            # Validate against schema
            if not self.validator.validate(result):
                logger.error(f"Validation failed for {pdf_path.name}")
                return {"status": "error", "message": "Schema validation failed"}
            
            # Generate output file path
            output_filename = pdf_path.stem + ".json"
            output_path = self.output_dir / output_filename
            
            # Write JSON output
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            processing_time = time.time() - start_time
            logger.info(f"Completed {pdf_path.name} in {processing_time:.2f}s")
            
            return {
                "status": "success",
                "file": pdf_path.name,
                "output": output_filename,
                "processing_time": processing_time,
                "title": result.get("title", ""),
                "outline_items": len(result.get("outline", []))
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Error processing {pdf_path.name}: {str(e)}")
            return {
                "status": "error",
                "file": pdf_path.name,
                "message": str(e),
                "processing_time": processing_time
            }
    
    def process_all_pdfs(self) -> Dict[str, Any]:
        """Process all PDF files using multi-threading."""
        pdf_files = self.find_pdf_files()
        
        if not pdf_files:
            logger.warning("No PDF files found to process")
            return {"total_files": 0, "processed": 0, "errors": 0, "results": []}
        
        start_time = time.time()
        results = []
        
        # Use ThreadPoolExecutor for concurrent processing
        max_workers = min(self.config.MAX_WORKERS, len(pdf_files))
        logger.info(f"Processing {len(pdf_files)} files with {max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(self.process_single_pdf, pdf_file): pdf_file
                for pdf_file in pdf_files
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                result = future.result()
                results.append(result)
        
        total_time = time.time() - start_time
        successful = len([r for r in results if r["status"] == "success"])
        errors = len([r for r in results if r["status"] == "error"])
        
        summary = {
            "total_files": len(pdf_files),
            "processed": successful,
            "errors": errors,
            "total_processing_time": total_time,
            "average_time_per_file": total_time / len(pdf_files) if pdf_files else 0,
            "results": results
        }
        
        logger.info(f"Processing complete: {successful}/{len(pdf_files)} files processed successfully")
        logger.info(f"Total time: {total_time:.2f}s, Average: {summary['average_time_per_file']:.2f}s per file")
        
        return summary
    
    def run(self):
        """Main execution method."""
        logger.info("Starting PDF processing system")
        logger.info(f"Input directory: {self.input_dir}")
        logger.info(f"Output directory: {self.output_dir}")
        
        try:
            summary = self.process_all_pdfs()
            
            # Write processing summary
            summary_path = self.output_dir / "processing_summary.json"
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            # Exit with appropriate code
            if summary["errors"] > 0:
                logger.warning(f"Processing completed with {summary['errors']} errors")
                sys.exit(1)
            else:
                logger.info("All files processed successfully")
                sys.exit(0)
                
        except Exception as e:
            logger.error(f"System error: {str(e)}")
            sys.exit(1)


if __name__ == "__main__":
    system = PDFProcessingSystem()
    system.run()

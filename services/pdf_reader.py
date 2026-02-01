"""
PDF reader service
Extracts text from PDF files
"""

import PyPDF2
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFReader:
    """Extract text from PDF files"""
    
    @staticmethod
    def extract_text(file_path: str) -> Optional[str]:
        """
        Extract text from PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text or None if failed
        """
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
            
            logger.info(f"Extracted {len(text)} characters from {file_path}")
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
            return None
    
    @staticmethod
    def extract_text_from_upload(uploaded_file) -> Optional[str]:
        """
        Extract text from Streamlit uploaded file
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            
        Returns:
            Extracted text or None if failed
        """
        try:
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            logger.info(f"Extracted {len(text)} characters from uploaded file")
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error reading uploaded PDF: {e}")
            return None
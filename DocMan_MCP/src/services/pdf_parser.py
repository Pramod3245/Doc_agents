
import PyPDF2
from typing import Optional

class PDFParser:
    def __init__(self):
        pass
    
    def extract_text_from_pdf(self, file_path: str) -> Optional[str]:
        """
        Extract text content from a PDF file.
        
        Args:
            file_path (str): Path to the PDF file
            
        Returns:
            Optional[str]: Extracted text content or None if extraction fails
        """
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
                
                return text.strip()
                
        except Exception as e:
            print(f"Error extracting text from PDF: {str(e)}")
            return None
    
    def get_pdf_metadata(self, file_path: str) -> Optional[dict]:
        """
        Extract metadata from a PDF file.
        
        Args:
            file_path (str): Path to the PDF file
            
        Returns:
            Optional[dict]: PDF metadata or None if extraction fails
        """
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata = pdf_reader.metadata
                
                return {
                    "title": metadata.get("/Title", ""),
                    "author": metadata.get("/Author", ""),
                    "subject": metadata.get("/Subject", ""),
                    "creator": metadata.get("/Creator", ""),
                    "producer": metadata.get("/Producer", ""),
                    "creation_date": metadata.get("/CreationDate", ""),
                    "modification_date": metadata.get("/ModDate", ""),
                    "page_count": len(pdf_reader.pages)
                }
                
        except Exception as e:
            print(f"Error extracting metadata from PDF: {str(e)}")
            return None


from typing import List, Optional
from src.services.pdf_parser import PDFParser
from src.utils.Summary_agent import SummaryAgent

class SummaryService:
    def __init__(self):
        self.pdf_parser = PDFParser()
        self.summary_agent = SummaryAgent()
    
    def generate_summary(self, file_path: str) -> Optional[str]:
        """
        Generate a summary for a single document.
        
        Args:
            file_path (str): Path to the document file
            
        Returns:
            Optional[str]: Generated summary or None if generation fails
        """
        try:
            # Extract text from PDF
            if file_path.lower().endswith('.pdf'):
                text_content = self.pdf_parser.extract_text_from_pdf(file_path)
            else:
                # For other file types, read as text
                with open(file_path, 'r', encoding='utf-8') as file:
                    text_content = file.read()
            
            if not text_content:
                return "Unable to extract text from the document."
            
            # Generate summary using the summary agent
            summary = self.summary_agent.generate_summary(text_content)
            return summary
            
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return f"Error generating summary: {str(e)}"
    
    def generate_project_summary(self, file_paths: List[str]) -> Optional[str]:
        """
        Generate a consolidated summary for multiple documents in a project.
        
        Args:
            file_paths (List[str]): List of file paths in the project
            
        Returns:
            Optional[str]: Generated project summary or None if generation fails
        """
        try:
            all_summaries = []
            
            for file_path in file_paths:
                summary = self.generate_summary(file_path)
                if summary:
                    all_summaries.append(f"Document: {file_path}\nSummary: {summary}\n")
            
            if not all_summaries:
                return "No summaries could be generated for the project documents."
            
            # Combine all summaries
            combined_text = "\n".join(all_summaries)
            
            # Generate a meta-summary of all document summaries
            project_summary = self.summary_agent.generate_project_summary(combined_text)
            return project_summary
            
        except Exception as e:
            print(f"Error generating project summary: {str(e)}")
            return f"Error generating project summary: {str(e)}"
    
    def get_document_insights(self, file_path: str) -> dict:
        """
        Get detailed insights about a document including summary and metadata.
        
        Args:
            file_path (str): Path to the document file
            
        Returns:
            dict: Document insights including summary, metadata, and statistics
        """
        try:
            insights = {
                "summary": self.generate_summary(file_path),
                "metadata": {},
                "statistics": {}
            }
            
            # Get PDF metadata if it's a PDF file
            if file_path.lower().endswith('.pdf'):
                metadata = self.pdf_parser.get_pdf_metadata(file_path)
                if metadata:
                    insights["metadata"] = metadata
                
                # Get text for statistics
                text_content = self.pdf_parser.extract_text_from_pdf(file_path)
            else:
                with open(file_path, 'r', encoding='utf-8') as file:
                    text_content = file.read()
            
            # Calculate basic statistics
            if text_content:
                insights["statistics"] = {
                    "character_count": len(text_content),
                    "word_count": len(text_content.split()),
                    "line_count": len(text_content.split('\n'))
                }
            
            return insights
            
        except Exception as e:
            print(f"Error getting document insights: {str(e)}")
            return {
                "summary": f"Error analyzing document: {str(e)}",
                "metadata": {},
                "statistics": {}
            }


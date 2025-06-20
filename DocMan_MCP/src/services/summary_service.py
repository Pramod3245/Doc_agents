from typing import List, Optional
from src.services.pdf_parser import PDFParser
from src.utils.Summary_agent import SummaryAgent
from src.utils.otel_tracing import traced_function
from opentelemetry import trace
from opentelemetry.trace.status import Status, StatusCode

tracer = trace.get_tracer(__name__)

class SummaryService:
    def __init__(self):
        self.pdf_parser = PDFParser()
        self.summary_agent = SummaryAgent()
    
    @traced_function()
    def generate_summary(self, file_path: str) -> Optional[str]:
        with tracer.start_as_current_span("generate_summary", attributes={"file_path": file_path}) as span:
            try:
                # Extract text from PDF
                if file_path.lower().endswith('.pdf'):
                    text_content = self.pdf_parser.extract_text_from_pdf(file_path)
                else:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        text_content = file.read()
                
                if not text_content:
                    span.set_status(Status(StatusCode.ERROR, "Unable to extract text from the document."))
                    return "Unable to extract text from the document."
                
                # Generate summary using the summary agent
                summary = self.summary_agent.generate_summary(text_content)
                span.set_status(Status(StatusCode.OK))
                return summary
                
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                print(f"Error generating summary: {str(e)}")
                return f"Error generating summary: {str(e)}"
    
    @traced_function()
    def generate_project_summary(self, file_paths: List[str]) -> Optional[str]:
        with tracer.start_as_current_span("generate_project_summary", attributes={"file_paths": str(file_paths)}) as span:
            try:
                all_summaries = []
                
                for file_path in file_paths:
                    summary = self.generate_summary(file_path)
                    if summary:
                        all_summaries.append(f"Document: {file_path}\nSummary: {summary}\n")
                
                if not all_summaries:
                    span.set_status(Status(StatusCode.ERROR, "No summaries could be generated for the project documents."))
                    return "No summaries could be generated for the project documents."
                
                # Combine all summaries
                combined_text = "\n".join(all_summaries)
                
                # Generate a meta-summary of all document summaries
                project_summary = self.summary_agent.generate_project_summary(combined_text)
                span.set_status(Status(StatusCode.OK))
                return project_summary
            
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                print(f"Error generating project summary: {str(e)}")
                return f"Error generating project summary: {str(e)}"
    
    @traced_function()
    def get_document_insights(self, file_path: str) -> dict:
        with tracer.start_as_current_span("get_document_insights", attributes={"file_path": file_path}) as span:
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
                
                span.set_status(Status(StatusCode.OK))
                return insights
            
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                print(f"Error getting document insights: {str(e)}")
                return {
                    "summary": f"Error analyzing document: {str(e)}",
                    "metadata": {},
                    "statistics": {}
                }


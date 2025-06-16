"""
PDF summarization utilities using Azure OpenAI with proper async handling
"""

from openai import AsyncAzureOpenAI
import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import HTTPException
import PyPDF2
import re
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent.parent / "utils/.env", override=True)

# Azure OpenAI Configuration
# AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
# AZURE_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
# AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
# AZURE_MODEL_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT")


AZURE_ENDPOINT = "https://aoai-farm.bosch-temp.com/api/openai/deployments/askbosch-prod-farm-openai-gpt-4o-mini-2024-07-18/chat/completions?api-version=2024-08-01-preview"
AZURE_VERSION = "2024-08-01-preview"
AZURE_API_KEY = "d8d02862135245e2940d3a1cd7518249"
AZURE_MODEL_NAME = "gpt-4o-mini"

if not all([AZURE_ENDPOINT, AZURE_VERSION, AZURE_API_KEY, AZURE_MODEL_NAME]):
    raise ValueError("Missing required Azure OpenAI configuration")

# Initialize Azure OpenAI Client with timeout settings
client = AsyncAzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_version=AZURE_VERSION,
    api_key=AZURE_API_KEY,
    timeout=60.0  # Set timeout to 60 seconds
)

class SummaryAgent:
    def __init__(self):
        from pydantic_ai import Agent
        from pydantic_ai.models.openai import OpenAIModel
        from pydantic_ai.providers.openai import OpenAIProvider

        model = OpenAIModel(
            AZURE_MODEL_NAME,
            provider=OpenAIProvider(openai_client=client),
        )

        self.summarization_agent = Agent(model)
        self.refinement_agent = Agent(model)
        self.error_handling_agent = Agent(model)
        self.chunk_size = 4000  # Maximum size of text chunks for processing
        self.max_retries = 3

    async def process_with_timeout(self, coro, timeout=300):
        """Process a coroutine with timeout"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=500,
                detail="Summary generation timed out. Please try again with a smaller section or contact support."
            )

    def chunk_text(self, text: str) -> list[str]:
        """Split text into manageable chunks"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 > self.chunk_size:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_summary_for_chunk(self, chunk: str, **kwargs) -> str:
        """Generate summary for a single chunk of text"""
        prompt = (
            f"Summarize the following content. "
            f"Length: {'detailed' if kwargs.get('detailed') else 'concise'}. "
            f"Style: {kwargs.get('style', 'professional')}.\n\n"
            f"Content:\n{chunk}"
        )
        
        result = await self.process_with_timeout(
            self.summarization_agent.run(prompt),
            timeout=120  # 2 minutes timeout per chunk
        )
        return result.output

    async def combine_summaries(self, summaries: list[str], **kwargs) -> str:
        """Combine multiple summaries into a coherent final summary"""
        if len(summaries) == 1:
            return summaries[0]

        combined_text = "\n\n".join(summaries)
        prompt = (
            f"Combine and refine these summaries into a single coherent summary. "
            f"Focus on: {kwargs.get('focus', 'main points')}. "
            f"Style: {kwargs.get('style', 'professional')}.\n\n"
            f"{combined_text}"
        )

        result = await self.process_with_timeout(
            self.refinement_agent.run(prompt),
            timeout=120
        )
        return result.output

    def extract_page_content(self, pdf_path: str, page_number: int) -> str:
        """Extract content from a specific page of the PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                if not (0 <= page_number < len(pdf_reader.pages)):
                    raise ValueError(f"Page number {page_number} is out of range")
                return pdf_reader.pages[page_number].extract_text()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error extracting page content: {str(e)}")

    def extract_section_content(self, pdf_path: str, section_text: str) -> str:
        """Extract content from a section containing specific text"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                full_text = ""
                for page in pdf_reader.pages:
                    full_text += page.extract_text() + "\n"

                # Find the section containing the text
                sections = re.split(r'\n(?=[A-Z][^a-z]*\n)', full_text)
                matching_sections = []
                for section in sections:
                    if section_text.lower() in section.lower():
                        matching_sections.append(section)
                
                if not matching_sections:
                    raise ValueError(f"Section containing '{section_text}' not found")
                
                # Return the most relevant section if multiple matches found
                return max(matching_sections, key=len)
                
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error extracting section content: {str(e)}")

    def extract_document_content(self, pdf_path: str) -> str:
        """Extract all content from the PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return "\n".join(page.extract_text() for page in pdf_reader.pages)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error extracting document content: {str(e)}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def summarize_page(self, pdf_path: str, page_number: int, **kwargs) -> Dict[str, Any]:
        """Summarize a specific page with customization options"""
        try:
            content = self.extract_page_content(pdf_path, page_number)
            chunks = self.chunk_text(content)
            chunk_summaries = []

            # Process each chunk with timeout
            for chunk in chunks:
                summary = await self.generate_summary_for_chunk(chunk, **kwargs)
                chunk_summaries.append(summary)

            # Combine summaries if needed
            final_summary = await self.combine_summaries(chunk_summaries, **kwargs)

            return {
                "page_number": page_number + 1,
                "summary": final_summary,
                "metadata": {
                    "content_length": len(content),
                    "summary_length": len(final_summary),
                    "chunks_processed": len(chunks)
                }
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error in page summarization: {str(e)}"
            )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def summarize_section(self, pdf_path: str, section_text: str, **kwargs) -> Dict[str, Any]:
        """Summarize a specific section with customization options"""
        try:
            content = self.extract_section_content(pdf_path, section_text)
            chunks = self.chunk_text(content)
            chunk_summaries = []

            # Process each chunk with timeout
            for chunk in chunks:
                summary = await self.generate_summary_for_chunk(chunk, **kwargs)
                chunk_summaries.append(summary)

            # Combine summaries if needed
            final_summary = await self.combine_summaries(chunk_summaries, **kwargs)

            return {
                "section_identifier": section_text,
                "summary": final_summary,
                "metadata": {
                    "content_length": len(content),
                    "summary_length": len(final_summary),
                    "chunks_processed": len(chunks)
                }
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error in section summarization: {str(e)}"
            )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def summarize_document(self, pdf_path: str, **kwargs) -> Dict[str, Any]:
        """Summarize entire document with customization options"""
        try:
            content = self.extract_document_content(pdf_path)
            chunks = self.chunk_text(content)
            chunk_summaries = []

            # Process chunks in parallel with timeout
            tasks = [self.generate_summary_for_chunk(chunk, **kwargs) for chunk in chunks]
            chunk_summaries = await asyncio.gather(*tasks)

            # Combine all summaries
            final_summary = await self.combine_summaries(chunk_summaries, **kwargs)

            # Additional refinement for coherence
            refinement_prompt = (
                f"Refine and structure the following summary to make it more coherent and focused "
                f"on {kwargs.get('focus', 'main points')}:\n\n{final_summary}"
            )
            
            refined_result = await self.process_with_timeout(
                self.refinement_agent.run(refinement_prompt),
                timeout=120
            )

            return {
                "summary": refined_result.output,
                "metadata": {
                    "content_length": len(content),
                    "summary_length": len(refined_result.output),
                    "chunks_processed": len(chunks)
                }
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error in document summarization: {str(e)}"
            )
import os
import re
import time
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import asyncio
import json
import faiss
import pickle
import numpy as np
from pathlib import Path
from pydantic import BaseModel, Field
from openai import AsyncAzureOpenAI

# --- Configuration ---
load_dotenv()

AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_CHAT_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")

FAISS_INDEX_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "vector_store/faiss_index.bin")
FAISS_METADATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "vector_store/faiss_metadata.pkl")

# --- Pydantic Models ---
class DocumentChunk(BaseModel):
    page_content: str = Field(..., description="The textual content of the chunk.")
    metadata: Dict[str, Any] = Field(..., description="Metadata associated with the chunk, e.g., page number, source filename, chunk index.")
    embedding: Optional[List[float]] = Field(default=None, description="The embedding vector for the chunk content.")

class TranslationIntent(BaseModel):
    task_type: str = Field(..., description="Type of translation task: 'document', 'page', 'section', 'unclear', 'unspecified_language'.")
    target_language: str = Field(..., description="The target language for translation (e.g., 'Spanish', 'French', 'unspecified').")
    filename: Optional[str] = Field(None, description="The specific PDF filename if the request is for a document, page, or section.")
    page_number: Optional[int] = Field(None, description="The page number if the request is for a specific page.")
    section_name: Optional[str] = Field(None, description="The name of the section if the request is for a specific section (case-insensitive for general text matching).")
    message: Optional[str] = Field(None, description="A message if the intent is unclear or language is unspecified, or for error handling.")

class TranslationPlan(BaseModel):
    steps: List[str] = Field(..., description="A list of step-by-step instructions for translating the content.")
    extracted_content_type: str = Field(..., description="The type of content to be extracted: 'document_chunks', 'page_content', 'section_content'.")
    target_language: str = Field(..., description="The target language for translation.")
    filename: Optional[str] = Field(None, description="The specific PDF filename related to the plan.")
    page_number: Optional[int] = Field(None, description="The page number related to the plan.")
    section_name: Optional[str] = Field(None, description="The section name related to the plan.")

class TranslationResult(BaseModel):
    success: bool = Field(..., description="Whether the translation was successful.")
    translated_content: str = Field(..., description="The translated content or error message.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the translation.")

# --- Initialize Azure OpenAI Client ---
async_openai_client = AsyncAzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_version=AZURE_API_VERSION,
    api_key=AZURE_API_KEY,
)

# --- Agent Models ---
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.exceptions import ModelHTTPError

chat_model = OpenAIModel(
    AZURE_CHAT_DEPLOYMENT_NAME,
    provider=OpenAIProvider(openai_client=async_openai_client),
)

error_handling_agent = Agent(
    name="ErrorHandlingAgent",
    model=chat_model,
    description="Handles errors or unclear requests by providing helpful messages to the user.",
    output_type=str
)

user_intent_agent = Agent(
    name="UserIntentAndLanguageDetectionAgent",
    model=chat_model,
    description="Analyzes user queries to determine the intended translation task and target language.",
    output_type=TranslationIntent
)

translation_planning_agent = Agent(
    name="TranslationPlanningAgent",
    model=chat_model,
    description="Creates a detailed, step-by-step plan for translating the content based on user intent.",
    output_type=TranslationPlan
)

translation_execution_agent = Agent(
    name="TranslationExecutionAgent",
    model=chat_model,
    description="Executes the translation plan by coordinating content retrieval and translation.",
    output_type=TranslationResult
)

# --- FAISS Index with Metadata ---
class FaissIndexWithMetadata:
    def __init__(self, index_path: str, metadata_path: str):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.index: Optional[faiss.Index] = None
        self.document_chunks: Optional[List[DocumentChunk]] = None

    async def load(self):
        print(f"Attempting to load FAISS index from '{self.index_path}' and metadata from '{self.metadata_path}'...")
        try:
            if not os.path.exists(self.index_path) or not os.path.exists(self.metadata_path):
                raise FileNotFoundError("FAISS index or metadata files not found.")

            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, 'rb') as f:
                loaded_chunks = pickle.load(f)
                # Convert loaded chunks to DocumentChunk objects if they aren't already
                self.document_chunks = []
                for chunk in loaded_chunks:
                    if isinstance(chunk, dict):
                        self.document_chunks.append(DocumentChunk(**chunk))
                    elif isinstance(chunk, DocumentChunk):
                        self.document_chunks.append(chunk)
                    else:
                        raise ValueError(f"Unknown chunk type: {type(chunk)}")
                
            for chunk in self.document_chunks:
                if chunk.embedding and isinstance(chunk.embedding, list):
                    chunk.embedding = np.array(chunk.embedding, dtype='float32')
            print("FAISS index and metadata loaded successfully.")
            print(f"Loaded {self.index.ntotal} embeddings and {len(self.document_chunks)} document chunks.")
        except FileNotFoundError as e:
            print(f"Warning: {e}. Please ensure your ingestion script has been run to index documents.")
            raise
        except Exception as e:
            print(f"Error loading FAISS index or metadata: {e}")
            raise

# --- Translation Workflows ---
async def translate_text_chunk(text: str, target_language: str, metadata: Dict[str, Any]) -> str:
    """Helper function to translate a single text chunk with metadata context."""
    try:
        system_prompt = f"""You are a highly skilled and professional translator. Your task is to accurately translate the provided text into {target_language}.

**Context**: This text is from a document with the following metadata:
- Source File: {metadata.get('source_filename', 'Unknown')}
- Page Number: {metadata.get('page_number', 'N/A')}
- Chunk Index: {metadata.get('chunk_index', 'N/A')}

**Formatting Rules**:
1. Output in paragraph format only - no tables, lists, or special formatting.
2. Convert any tables, charts, or structured data into flowing paragraph text.
3. If a table, image, chart, or non-text element is present, include a description like: '[Table from Page X: contains data about...]' or '[Image from Page X: shows...]'.
4. Maintain all information as natural, flowing sentences and paragraphs.
5. Use proper sentence structure and paragraph breaks for readability.
6. Do not use markdown table syntax, bullet points, or numbered lists.
7. Convert any structured data into descriptive sentences.
8. Convert the whole output as markdown format with ### for major headings, ## for page numbers"""

        response = await async_openai_client.chat.completions.create(
            model=AZURE_CHAT_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        return response.choices[0].message.content if response.choices and response.choices[0].message.content else ""
    except Exception as e:
        print(f"An unexpected error occurred during translation of chunk: {e}")
        return f"[Translation Failed for chunk: {str(e)}]"

async def translate_document_workflow(filename: str, target_language: str, faiss_data: FaissIndexWithMetadata) -> str:
    """Translates the entire document by processing its chunks with page and chunk metadata."""
    print(f"Translating entire document: '{filename}' to '{target_language}'")
    all_chunks = get_document_chunks_by_filename(filename, faiss_data)
    
    if not all_chunks:
        return f"Error: No content found for document '{filename}'. Please ensure it was ingested."

    translated_chunks = []
    for i, chunk in enumerate(all_chunks):
        print(f"Translating chunk {i+1}/{len(all_chunks)} (Page {chunk.metadata.get('page_number', 'N/A')}, Chunk {chunk.metadata.get('chunk_index', 'N/A')})...")
        try:
            translated_text = await translate_text_chunk(chunk.page_content, target_language, chunk.metadata)
            # Prepend metadata to the translated text for clarity
            metadata_label = f"[Page {chunk.metadata.get('page_number', 'N/A')}, Chunk {chunk.metadata.get('chunk_index', 'N/A')}]"
            translated_chunks.append(f"{metadata_label}\n{translated_text}")
        except Exception as e:
            print(f"Failed to translate chunk {i+1}: {e}. Skipping this chunk.")
            translated_chunks.append(f"[Page {chunk.metadata.get('page_number', 'N/A')}, Chunk {chunk.metadata.get('chunk_index', 'N/A')}]\n[Translation Failed for chunk {i+1}]")
    
    return "\n\n".join(translated_chunks)

async def translate_page_workflow(filename: str, page_number: int, target_language: str, faiss_data: FaissIndexWithMetadata) -> str:
    """Translates a specific page of the document with page metadata."""
    print(f"Translating page {page_number} of '{filename}' to '{target_language}'")
    page_content = get_page_content(filename, page_number, faiss_data)

    if not page_content:
        return f"Error: No content found for page {page_number} in '{filename}'. Please check page number and filename."

    try:
        metadata = {"source_filename": filename, "page_number": page_number, "chunk_index": "N/A"}
        translated_text = await translate_text_chunk(page_content, target_language, metadata)
        return f"[Page {page_number}]\n{translated_text}"
    except Exception as e:
        print(f"Failed to translate page {page_number}: {e}")
        return f"[Page {page_number}]\nError translating page {page_number} of '{filename}'."

async def translate_section_workflow(filename: str, section_name: str, target_language: str, faiss_data: FaissIndexWithMetadata) -> str:
    """Translates a specific section of the document with section metadata."""
    print(f"Translating section '{section_name}' of '{filename}' to '{target_language}'")
    section_content = get_section_content(filename, section_name, faiss_data)

    if not section_content:
        return f"Error: No content found for section '{section_name}' in '{filename}'. Please provide a more precise section name if possible or ensure it exists."

    try:
        metadata = {"source_filename": filename, "section_name": section_name, "page_number": "N/A", "chunk_index": "N/A"}
        translated_text = await translate_text_chunk(section_content, target_language, metadata)
        return f"[Section: {section_name}]\n{translated_text}"
    except Exception as e:
        print(f"Failed to translate section '{section_name}': {e}")
        return f"[Section: {section_name}]\nError translating section '{section_name}' of '{filename}'."

# --- Content Retrieval Functions ---
def get_document_chunks_by_filename(filename: str, faiss_data: FaissIndexWithMetadata) -> List[DocumentChunk]:
    if not faiss_data.document_chunks:
        print("No document chunks available in FAISS data")
        return []
    
    # Only use the filename (not full path) for matching
    filename_only = Path(filename).name
    print(f"Looking for chunks with filename: {filename_only}")
    
    # Print available filenames for debugging
    available_files = set(chunk.metadata.get("source_filename") for chunk in faiss_data.document_chunks)
    print(f"Available files in chunks: {available_files}")
    
    chunks = sorted(
        [chunk for chunk in faiss_data.document_chunks if chunk.metadata.get("source_filename") == filename_only],
        key=lambda x: (x.metadata.get("page_number", 0), x.metadata.get("chunk_index", 0))
    )
    
    print(f"Found {len(chunks)} chunks for {filename_only}")
    return chunks

def get_page_content(filename: str, page_number: int, faiss_data: FaissIndexWithMetadata) -> str:
    if not faiss_data.document_chunks:
        return ""
    filename_only = Path(filename).name
    page_chunks_sorted = sorted(
        [chunk for chunk in faiss_data.document_chunks
         if chunk.metadata.get("source_filename") == filename_only and chunk.metadata.get("page_number") == page_number],
        key=lambda x: x.metadata.get("chunk_index", 0)
    )
    return " ".join([chunk.page_content for chunk in page_chunks_sorted])

def get_section_content(filename: str, section_name: str, faiss_data: FaissIndexWithMetadata) -> str:
    if not faiss_data.document_chunks:
        return ""
    filename_only = Path(filename).name
    section_content_parts = []
    section_pattern = re.compile(r'\b' + re.escape(section_name) + r'\b', re.IGNORECASE)
    relevant_chunks = []
    found_section_start = False
    for chunk in sorted(faiss_data.document_chunks, key=lambda x: (x.metadata.get("page_number", 0), x.metadata.get("chunk_index", 0))):
        if chunk.metadata.get("source_filename") == filename_only:
            if section_pattern.search(chunk.page_content):
                found_section_start = True
                relevant_chunks.append(chunk)
            elif found_section_start:
                if len(chunk.page_content) < 100 and (chunk.page_content.isupper() or chunk.page_content.istitle()):
                    break
                relevant_chunks.append(chunk)
    for chunk in relevant_chunks:
        section_content_parts.append(chunk.page_content)
    if not section_content_parts:
        return ""
    return " ".join(section_content_parts)

async def execute_translation_plan(plan: TranslationPlan, faiss_data: FaissIndexWithMetadata) -> TranslationResult:
    try:
        if plan.extracted_content_type == "document_chunks":
            if not plan.filename:
                return TranslationResult(
                    success=False,
                    translated_content="Error: Filename is required for document translation.",
                    metadata={"error_type": "missing_filename"}
                )
            translated_content = await translate_document_workflow(plan.filename, plan.target_language, faiss_data)
            
        elif plan.extracted_content_type == "page_content":
            if not plan.filename or plan.page_number is None:
                return TranslationResult(
                    success=False,
                    translated_content="Error: Filename and page number are required for page translation.",
                    metadata={"error_type": "missing_parameters"}
                )
            translated_content = await translate_page_workflow(plan.filename, plan.page_number, plan.target_language, faiss_data)
            
        elif plan.extracted_content_type == "section_content":
            if not plan.filename or not plan.section_name:
                return TranslationResult(
                    success=False,
                    translated_content="Error: Filename and section name are required for section translation.",
                    metadata={"error_type": "missing_parameters"}
                )
            translated_content = await translate_section_workflow(plan.filename, plan.section_name, plan.target_language, faiss_data)
            
        else:
            return TranslationResult(
                success=False,
                translated_content=f"Error: Unknown content type '{plan.extracted_content_type}'.",
                metadata={"error_type": "unknown_content_type"}
            )
        
        success = not translated_content.startswith("Error:")
        saved_filename = ""
        if success:
            saved_filename = save_translation_to_file(translated_content, plan)
        
        return TranslationResult(
            success=success,
            translated_content=translated_content,
            metadata={
                "content_type": plan.extracted_content_type,
                "target_language": plan.target_language,
                "filename": plan.filename,
                "page_number": plan.page_number,
                "section_name": plan.section_name,
                "saved_file": saved_filename
            }
        )
        
    except Exception as e:
        return TranslationResult(
            success=False,
            translated_content=f"Error executing translation plan: {str(e)}",
            metadata={"error_type": "execution_error", "exception": str(e)}
        )

class TranslationAgent:
    def __init__(self):
        self.faiss_data = None

    async def initialize(self):
        if self.faiss_data is None:
            self.faiss_data = FaissIndexWithMetadata(FAISS_INDEX_PATH, FAISS_METADATA_PATH)
            await self.faiss_data.load()

    async def translate_document(self, file_path: str, target_language: str) -> Dict[str, Any]:
        await self.initialize()
        print(f"Translating document: {file_path}")
        
        # Search for the document in all subdirectories of uploads
        uploads_dir = Path(os.path.dirname(os.path.dirname(__file__))) / "uploads"
        found_files = list(uploads_dir.rglob(Path(file_path).name))
        
        if not found_files:
            return {
                "success": False,
                "translation": f"Error: File not found in uploads directory: {file_path}",
                "chunks_processed": 0
            }
            
        actual_file_path = str(found_files[0])
        filename = Path(actual_file_path).name
        print(f"Found file: {actual_file_path}")
        
        chunks_processed = 0
        try:
            # First check if we have chunks for this file
            chunks = get_document_chunks_by_filename(filename, self.faiss_data)
            if not chunks:
                print(f"No chunks found for {filename}, attempting to ingest...")
                # If no chunks found, try to ingest the document
                from ingest_to_vector import extract_chunks_from_pdf, model
                new_chunks = extract_chunks_from_pdf(Path(actual_file_path))
                if new_chunks:
                    # Generate embeddings for new chunks
                    texts_to_embed = [chunk.page_content for chunk in new_chunks]
                    embeddings_np = model.encode(texts_to_embed, convert_to_numpy=True, normalize_embeddings=True)
                    
                    # Add embeddings to chunks
                    for i, chunk in enumerate(new_chunks):
                        chunk.embedding = embeddings_np[i].tolist()
                    
                    # Add to FAISS index
                    if self.faiss_data.index is not None:
                        self.faiss_data.index.add(embeddings_np)
                        self.faiss_data.document_chunks.extend(new_chunks)
                        
                        # Save updated index and metadata
                        faiss.write_index(self.faiss_data.index, FAISS_INDEX_PATH)
                        with open(FAISS_METADATA_PATH, "wb") as f:
                            pickle.dump(self.faiss_data.document_chunks, f)
                            
                        print(f"Successfully ingested and indexed {len(new_chunks)} new chunks")
                        chunks = new_chunks
            
            translated_content = await translate_document_workflow(filename, target_language, self.faiss_data)
            chunks_processed = len(chunks) if chunks else 0
            
            if translated_content.startswith("Error:"):
                return {
                    "success": False,
                    "translation": translated_content,
                    "chunks_processed": chunks_processed
                }
            return {
                "success": True,
                "translation": translated_content,
                "chunks_processed": chunks_processed
            }
        except Exception as e:
            print(f"Translation error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "translation": str(e),
                "chunks_processed": chunks_processed
            }

    async def translate_page(self, file_path: str, page_number: int, target_language: str) -> Dict[str, Any]:
        await self.initialize()
        filename = Path(file_path).name
        try:
            translated_content = await translate_page_workflow(filename, page_number, target_language, self.faiss_data)
            if translated_content.startswith("Error:"):
                return {
                    "success": False,
                    "translation": translated_content,
                    "chunks_processed": 0
                }
            return {
                "success": True,
                "translation": translated_content,
                "chunks_processed": 1
            }
        except Exception as e:
            return {
                "success": False,
                "translation": str(e),
                "chunks_processed": 0
            }

    async def translate_section(self, file_path: str, section_text: str, target_language: str) -> Dict[str, Any]:
        await self.initialize()
        filename = Path(file_path).name
        try:
            translated_content = await translate_section_workflow(filename, section_text, target_language, self.faiss_data)
            if translated_content.startswith("Error:"):
                return {
                    "success": False,
                    "translation": translated_content,
                    "chunks_processed": 0
                }
            return {
                "success": True,
                "translation": translated_content,
                "chunks_processed": 1
            }
        except Exception as e:
            return {
                "success": False,
                "translation": str(e),
                "chunks_processed": 0
            }

import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from pathlib import Path
import traceback
from PyPDF2 import PdfReader
from pydantic import BaseModel, Field # NEW: For DocumentChunk model
from typing import List, Dict, Any, Optional # NEW: For DocumentChunk model
import pickle # NEW: For saving metadata as .pkl

# --- Pydantic Models (Copied from summary_agent.py for consistency) ---
class DocumentChunk(BaseModel):
    page_content: str = Field(..., description="The textual content of the chunk.")
    metadata: Dict[str, Any] = Field(..., description="Metadata associated with the chunk, e.g., page number, source filename, chunk index.")
    embedding: Optional[List[float]] = Field(default=None, description="The embedding vector for the chunk content.")

# --- Configuration ---
PDF_DIR = "./src/uploads"
CHUNK_SIZE = 500  # characters
CHUNK_OVERLAP = 50
MODEL_NAME = "all-MiniLM-L6-v2"
# CORRECTED: FAISS index path to match summary_agent.py
FAISS_INDEX_PATH = "vector_store/faiss_index.bin"
# NEW: Metadata path for pickle file
FAISS_METADATA_PATH = "vector_store/faiss_metadata.pkl"

# Ensure output dir exists
os.makedirs("vector_store", exist_ok=True)

# Load Hugging Face embedder
print("Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)
print(f"Embedding model loaded: {MODEL_NAME} with dimension {model.get_sentence_embedding_dimension()}")


# Helper: Load and chunk PDF, returning DocumentChunk objects
def extract_chunks_from_pdf(file_path: Path) -> List[DocumentChunk]:
    chunks = []
    reader = PdfReader(file_path)
    file_name = file_path.name # Get the filename from the Path object

    for page_num, page in enumerate(reader.pages):
        try:
            text = page.extract_text()
            if not text:
                continue
            
            # Basic clean-up
            text = text.replace("\n", " ").strip()
            
            # Split into chunks with overlap
            current_chunk_index = 0
            start = 0
            while start < len(text):
                end = min(len(text), start + CHUNK_SIZE)
                chunk_text = text[start:end]
                
                # Create DocumentChunk instance with detailed metadata
                chunk = DocumentChunk(
                    page_content=chunk_text,
                    metadata={
                        "source_filename": file_name,
                        "page_number": page_num + 1, # Page numbers are typically 1-indexed
                        "chunk_index": current_chunk_index,
                    }
                )
                chunks.append(chunk)
                
                start += CHUNK_SIZE - CHUNK_OVERLAP
                current_chunk_index += 1
                
        except Exception as e:
            print(f"Warning: Failed to extract page {page_num+1} from {file_name}: {e}")
            traceback.print_exc() # Print full traceback for debugging

    return chunks


# Main
# This list will hold DocumentChunk objects, which will later have embeddings added
document_chunks_for_faiss: List[DocumentChunk] = []
texts_to_embed = [] # This list will hold only the page_content for embedding

print("--- Starting PDF Ingestion ---")
for file in Path(PDF_DIR).glob("*.pdf"):
    print(f"Processing: {file.name}")
    try:
        chunks_from_file = extract_chunks_from_pdf(file)
        document_chunks_for_faiss.extend(chunks_from_file)
        texts_to_embed.extend([chunk.page_content for chunk in chunks_from_file])
    except Exception as e:
        print(f"Failed to process {file.name}: {e}")
        traceback.print_exc()

print(f"Total chunks extracted: {len(document_chunks_for_faiss)}")

if not document_chunks_for_faiss:
    print("No chunks extracted. Exiting without creating FAISS index.")
else:
    # Generate embeddings
    print("Generating embeddings...")
    # normalize_embeddings=True is important for cosine similarity with L2 index
    embeddings_np = model.encode(texts_to_embed, convert_to_numpy=True, normalize_embeddings=True)
    print(f"Generated {embeddings_np.shape[0]} embeddings of dimension {embeddings_np.shape[1]}")

    # Add embeddings back to the DocumentChunk objects
    for i, chunk in enumerate(document_chunks_for_faiss):
        chunk.embedding = embeddings_np[i].tolist() # Store as list in Pydantic model

    # Store in FAISS
    dimension = embeddings_np.shape[1]
    # Using IndexFlatL2 for cosine similarity with L2 normalized vectors (common for BGE)
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_np)
    # CORRECTED: Save with .bin extension
    faiss.write_index(index, FAISS_INDEX_PATH)
    print(f"Embeddings stored in FAISS index at '{FAISS_INDEX_PATH}'")

    # Save metadata separately using pickle
    # CORRECTED: Save as .pkl and use the new path
    with open(FAISS_METADATA_PATH, "wb") as f:
        pickle.dump(document_chunks_for_faiss, f)
    print(f"Metadata (DocumentChunk objects) stored at '{FAISS_METADATA_PATH}'")

print("--- Ingestion Complete ---")
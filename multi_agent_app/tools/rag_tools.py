"""RAG tools for document ingestion and vector search using ChromaDB."""

from __future__ import annotations

import os
from typing import Any

from langchain_core.tools import tool

_vectorstore = None


def _get_vectorstore():
    """Lazy-initialise a ChromaDB vectorstore with a HuggingFace embedding model."""
    global _vectorstore
    if _vectorstore is not None:
        return _vectorstore

    from langchain_chroma import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings

    persist_dir = os.getenv(
        "VECTOR_STORE_DIR", "multi_agent_app/db/vector_store"
    )
    embedding = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    _vectorstore = Chroma(
        collection_name="documents",
        embedding_function=embedding,
        persist_directory=persist_dir,
    )
    return _vectorstore


def ingest_text_file(file_path: str, chunk_size: int = 500) -> int:
    """Read a plain-text file and add its chunks to the vector store.

    Returns the number of chunks added.
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=50
    )
    chunks = splitter.split_text(content)
    vs = _get_vectorstore()
    vs.add_texts(
        texts=chunks,
        metadatas=[{"source": file_path, "chunk": i} for i in range(len(chunks))],
    )
    return len(chunks)


def ingest_pdf(file_path: str, chunk_size: int = 500) -> int:
    """Read a PDF file and add its chunks to the vector store.

    Returns the number of chunks added.
    """
    from langchain_community.document_loaders import PyPDFLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    loader = PyPDFLoader(file_path)
    pages = loader.load()
    full_text = "\n".join(p.page_content for p in pages)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=50
    )
    chunks = splitter.split_text(full_text)
    vs = _get_vectorstore()
    vs.add_texts(
        texts=chunks,
        metadatas=[{"source": file_path, "chunk": i} for i in range(len(chunks))],
    )
    return len(chunks)


@tool
def search_documents(query: str, top_k: int = 5) -> str:
    """Search the internal document vector store for relevant information.

    Args:
        query: Search query string.
        top_k: Number of top results to return.

    Returns:
        Matched document chunks as a formatted string.
    """
    vs = _get_vectorstore()
    docs = vs.similarity_search(query, k=top_k)
    if not docs:
        return "No relevant documents found."
    results = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "unknown")
        results.append(f"[{i}] (source: {source})\n{doc.page_content}")
    return "\n\n".join(results)


def get_rag_tools() -> list[Any]:
    """Return the list of RAG tools."""
    return [search_documents]

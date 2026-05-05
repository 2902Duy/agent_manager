from functools import lru_cache
from pathlib import Path
from typing import Type

from crewai.tools import BaseTool
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_FILE = PROJECT_ROOT / "data.txt"


def load_vector_db() -> Chroma:
    loader = TextLoader(str(DATA_FILE), encoding="utf-8")
    docs = loader.load()

    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return Chroma.from_documents(docs, embeddings)


@lru_cache(maxsize=1)
def get_vector_db() -> Chroma:
    return load_vector_db()


def query_db(query: str) -> str:
    docs = get_vector_db().similarity_search(query, k=3)
    return "\n".join(doc.page_content for doc in docs)


class RagSearchInput(BaseModel):
    """Input schema for RagSearchTool."""

    query: str = Field(..., description="Question or search query to look up in data.txt.")


class RagSearchTool(BaseTool):
    name: str = "rag_search"
    description: str = (
        "Searches the local data.txt knowledge file and returns the most relevant context."
    )
    args_schema: Type[BaseModel] = RagSearchInput

    def _run(self, query: str) -> str:
        return query_db(query)

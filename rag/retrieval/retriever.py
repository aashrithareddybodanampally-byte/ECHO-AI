"""
TF-IDF retriever over knowledge-base chunks (cosine similarity).

Lexical retrieval was chosen over dense embeddings to avoid a vector
database and model download; the knowledge base is small and curated.
"""

from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from rag.ingestion.markdown_loader import Chunk, load_directory

DEFAULT_KB_DIR = Path(__file__).resolve().parents[1] / "knowledge_base"


class TfidfRetriever:
    def __init__(self, chunks: list[Chunk], min_score: float = 0.05):
        if not chunks:
            raise ValueError("Knowledge base is empty")
        self.chunks = chunks
        self.min_score = min_score
        self._vectorizer = TfidfVectorizer(
            stop_words="english", ngram_range=(1, 2), sublinear_tf=True
        )
        self._matrix = self._vectorizer.fit_transform(
            [f"{c.source} {c.content}" for c in chunks]
        )

    @classmethod
    def from_directory(cls, directory: Path = DEFAULT_KB_DIR, **kwargs) -> "TfidfRetriever":
        return cls(load_directory(directory), **kwargs)

    def retrieve(self, query: str, top_k: int) -> list[dict]:
        scores = linear_kernel(self._vectorizer.transform([query]), self._matrix)[0]
        ranked = scores.argsort()[::-1][:top_k]
        return [
            {"source": self.chunks[i].source, "content": self.chunks[i].content,
             "score": round(float(scores[i]), 6)}
            for i in ranked if scores[i] >= self.min_score
        ]

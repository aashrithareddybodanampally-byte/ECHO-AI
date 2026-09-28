import pytest

from rag.ingestion.markdown_loader import chunk_markdown, load_directory
from rag.retrieval.retriever import DEFAULT_KB_DIR, TfidfRetriever


def test_chunk_markdown_by_section():
    chunks = chunk_markdown("# Doc\n\n## A\nfirst  text\n\n## B\nsecond\n", "doc")
    assert [(c.source, c.content) for c in chunks] == [("Doc — A", "first text"), ("Doc — B", "second")]


def test_knowledge_base_loads_and_skips_readme():
    chunks = load_directory(DEFAULT_KB_DIR)
    assert len(chunks) >= 15
    assert all(c.document != "README" for c in chunks)


@pytest.fixture(scope="module")
def retriever():
    return TfidfRetriever.from_directory()


@pytest.mark.parametrize("query,expected_prefix", [
    ("how long should my study breaks be", "Study Techniques"),
    ("I can't fall asleep at night", "Sleep Basics"),
    ("breathing exercise to calm down", "Relaxation Techniques"),
    ("helpline number for a crisis", "Professional Support Resources"),
])
def test_retrieval_relevance(retriever, query, expected_prefix):
    results = retriever.retrieve(query, 3)
    assert results[0]["source"].startswith(expected_prefix)
    assert results == sorted(results, key=lambda r: -r["score"])


def test_retrieval_respects_top_k_and_threshold(retriever):
    assert len(retriever.retrieve("sleep", 2)) <= 2
    assert retriever.retrieve("xylophone quantum zebra", 3) == []

"""
Load and chunk the Markdown knowledge base.

Each document starts with a '# Title' line; each '## Section' becomes one
chunk whose source is "Title — Section".
"""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Chunk:
    source: str
    content: str
    document: str


def chunk_markdown(text: str, document: str) -> list[Chunk]:
    title_match = re.search(r"^# (.+)$", text, flags=re.MULTILINE)
    title = title_match.group(1).strip() if title_match else document
    chunks = []
    for section in re.split(r"^## ", text, flags=re.MULTILINE)[1:]:
        heading, _, body = section.partition("\n")
        body = re.sub(r"\s+", " ", body).strip()
        if body:
            chunks.append(Chunk(source=f"{title} — {heading.strip()}", content=body, document=document))
    return chunks


def load_directory(directory: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(directory.glob("*.md")):
        if path.name.upper() == "README.MD":
            continue
        chunks.extend(chunk_markdown(path.read_text(encoding="utf-8"), path.stem))
    return chunks

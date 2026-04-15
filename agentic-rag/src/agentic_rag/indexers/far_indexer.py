"""
FAR (Federal Aviation Regulations) indexer for Qdrant.

Downloads Title 14 CFR (Code of Federal Regulations) from eCFR API,
generates embeddings, and indexes to Qdrant.

Usage as CLI:
    # Local embeddings (fast, free)
    python -m agentic_rag.indexers.far_indexer --parts 61,91,121

    # OpenAI embeddings
    python -m agentic_rag.indexers.far_indexer --parts 61,91,121 --embedder openai

Usage as module:
    from agentic_rag.indexers import FARIndexer
    indexer = FARIndexer(qdrant_url="http://localhost:6333", embedder="local")
    indexer.index(parts=["91", "121"])
"""

import argparse
import hashlib
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Generator, Literal

import httpx

from .embeddings import get_embedder, Embedder


@dataclass
class FARConfig:
    """Configuration for FAR indexer."""
    ecfr_api_base: str = "https://www.ecfr.gov/api/versioner/v1"
    qdrant_url: str = "http://localhost:6333"
    collection_name: str = "far_regulations"
    index_batch_size: int = 50
    default_parts: list[str] = field(default_factory=lambda: ["1", "61", "91", "121", "135"])
    save_to: str | None = "./data/aviation/far"
    # Use current date for API requests (eCFR requires date in URL)
    ecfr_date: str = field(default_factory=lambda: date.today().isoformat())


class FARIndexer:
    """
    Indexes FAR (Federal Aviation Regulations) to Qdrant.

    Fetches regulations from eCFR API, generates embeddings,
    and indexes to a Qdrant collection.
    """

    def __init__(
        self,
        qdrant_url: str | None = None,
        collection_name: str | None = None,
        embedder: Literal["local", "openai"] | Embedder = "local",
        embedding_model: str | None = None,
        save_to: str | None = "./data/aviation/far",
    ):
        self.config = FARConfig()
        if qdrant_url:
            self.config.qdrant_url = qdrant_url
        if collection_name:
            self.config.collection_name = collection_name
        self.config.save_to = save_to

        # Set up embedder
        if isinstance(embedder, str):
            self.embedder = get_embedder(embedder, model_name=embedding_model)
        else:
            self.embedder = embedder

    def save_data(self, part: str, sections: list[dict]) -> None:
        """Save fetched data to JSON file."""
        if not self.config.save_to:
            return

        save_dir = Path(self.config.save_to)
        save_dir.mkdir(parents=True, exist_ok=True)

        filepath = save_dir / f"part_{part}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(sections, f, indent=2, ensure_ascii=False)
        print(f"  Saved {len(sections)} sections to {filepath}")

    def create_collection(self) -> None:
        """Create the Qdrant collection if it doesn't exist."""
        response = httpx.get(
            f"{self.config.qdrant_url}/collections/{self.config.collection_name}"
        )
        if response.status_code == 200:
            print(f"Collection '{self.config.collection_name}' already exists")
            return

        response = httpx.put(
            f"{self.config.qdrant_url}/collections/{self.config.collection_name}",
            json={
                "vectors": {
                    "size": self.embedder.dimension,
                    "distance": "Cosine"
                }
            },
            timeout=30
        )
        response.raise_for_status()
        print(f"Created collection '{self.config.collection_name}' (dim={self.embedder.dimension})")

    def fetch_part_structure(self, title: int, part: str) -> dict:
        """Fetch the structure (TOC) for a CFR part."""
        url = f"{self.config.ecfr_api_base}/structure/{self.config.ecfr_date}/title-{title}.json"
        params = {"part": part}

        response = httpx.get(url, params=params, timeout=60)
        response.raise_for_status()
        return response.json()

    def fetch_section_content(self, title: int, part: str, section_id: str) -> str:
        """
        Fetch the full text content of a section from eCFR API.

        Uses XML format which provides reliable content.
        """
        url = f"{self.config.ecfr_api_base}/full/{self.config.ecfr_date}/title-{title}.xml"
        params = {"part": part, "section": section_id}

        try:
            response = httpx.get(url, params=params, timeout=30)
            if response.status_code == 200:
                return self._parse_ecfr_xml(response.content)
        except Exception as e:
            print(f"    Warning: Failed to fetch §{section_id}: {e}")

        return ""

    def _parse_ecfr_xml(self, xml_content: bytes) -> str:
        """Parse eCFR XML response and extract text content."""
        try:
            root = ET.fromstring(xml_content)

            # Extract all text from P (paragraph) elements
            paragraphs = []
            for elem in root.iter():
                if elem.tag == "HEAD":
                    # Section header
                    if elem.text:
                        paragraphs.append(elem.text.strip())
                elif elem.tag == "P":
                    # Paragraph text - get all text including nested elements
                    text = "".join(elem.itertext()).strip()
                    if text:
                        paragraphs.append(text)

            return "\n\n".join(paragraphs)
        except ET.ParseError:
            return ""

    def extract_sections_from_structure(
        self,
        structure: dict,
        part: str
    ) -> Generator[dict, None, None]:
        """Extract section information from the part structure."""

        def walk_structure(node: dict, path: list[str] | None = None):
            if path is None:
                path = []

            node_type = node.get("type", "")
            label = node.get("label", "")
            identifier = node.get("identifier", "")
            title = node.get("title", "")

            current_path = path + [label] if label else path

            if node_type == "section" and identifier:
                yield {
                    "section_id": identifier,
                    "part": part,
                    "section_number": identifier.split(".")[-1] if "." in identifier else identifier,
                    "title": title,
                    "path": current_path,
                }

            for child in node.get("children", []):
                yield from walk_structure(child, current_path)

        yield from walk_structure(structure)

    def get_embedding(self, text: str) -> list[float]:
        """Generate embedding for text."""
        return self.embedder.embed(text)

    def index_to_qdrant(self, points: list[dict]) -> None:
        """Index points to Qdrant."""
        response = httpx.put(
            f"{self.config.qdrant_url}/collections/{self.config.collection_name}/points",
            json={"points": points},
            timeout=60
        )
        response.raise_for_status()

    def build_regulation_text(self, section_info: dict, content: str) -> str:
        """Build searchable text for a regulation section."""
        parts = [
            f"14 CFR Part {section_info['part']}",
            f"§{section_info['section_id']} {section_info['title']}",
        ]

        if section_info.get("path"):
            parts.append(f"Path: {' > '.join(section_info['path'])}")

        # Add eCFR URL for reference
        section_id = section_info['section_id']
        ecfr_url = f"https://www.ecfr.gov/current/title-14/section-{section_id}"
        parts.append(f"Reference: {ecfr_url}")

        parts.append("")
        if content:
            parts.append(content)
        else:
            parts.append(f"(See eCFR for full text: {ecfr_url})")

        return "\n".join(parts)

    def process_part(self, part: str, dry_run: bool = False) -> int:
        """Process a single CFR part and index to Qdrant."""
        print(f"\nProcessing Part {part}...")

        try:
            structure = self.fetch_part_structure(14, part)
        except Exception as e:
            print(f"  Failed to fetch structure for Part {part}: {e}")
            return 0

        sections = list(self.extract_sections_from_structure(structure, part))
        print(f"  Found {len(sections)} sections")

        # Fetch content for all sections and save
        sections_with_content = []
        content_count = 0
        print(f"  Fetching section content...")
        for i, section in enumerate(sections):
            content = self.fetch_section_content(14, part, section["section_id"])
            if content:
                content_count += 1
            time.sleep(0.15)  # Rate limiting for eCFR API
            section_data = {**section, "content": content}
            sections_with_content.append(section_data)

            # Progress indicator every 20 sections
            if (i + 1) % 20 == 0:
                print(f"    Progress: {i + 1}/{len(sections)} sections...")

        print(f"  Fetched content for {content_count}/{len(sections)} sections")

        # Save fetched data to JSON
        if self.config.save_to:
            self.save_data(part, sections_with_content)

        if dry_run:
            for section in sections[:5]:
                print(f"    - §{section['section_id']}: {section['title']}")
            if len(sections) > 5:
                print(f"    ... and {len(sections) - 5} more")
            return len(sections)

        points = []
        indexed = 0

        for section in sections_with_content:
            text = self.build_regulation_text(section, section.get("content", ""))

            try:
                embedding = self.get_embedding(text)
            except Exception as e:
                print(f"    Failed to embed §{section['section_id']}: {e}")
                continue

            # Convert section ID to integer for Qdrant
            point_id = int(hashlib.md5(section["section_id"].encode()).hexdigest()[:16], 16)

            point = {
                "id": point_id,
                "vector": embedding,
                "payload": {
                    "text": text,
                    "part": section["part"],
                    "section": section["section_id"],
                    "title": section["title"],
                    "header_l1": f"14 CFR Part {section['part']}",
                    "header_l2": section["path"][0] if section.get("path") else "General",
                    "header_l3": f"§{section['section_id']} {section['title']}",
                }
            }
            points.append(point)

            if len(points) >= self.config.index_batch_size:
                print(f"    Indexing batch of {len(points)} sections...")
                self.index_to_qdrant(points)
                indexed += len(points)
                points = []

        if points:
            print(f"    Indexing final batch of {len(points)} sections...")
            self.index_to_qdrant(points)
            indexed += len(points)

        return indexed

    def index(
        self,
        parts: list[str] | None = None,
        dry_run: bool = False,
    ) -> int:
        """
        Index FAR regulations to Qdrant.

        Args:
            parts: List of CFR parts to index (default: 1, 61, 91, 121, 135)
            dry_run: If True, fetch structure but don't index

        Returns:
            Number of sections indexed
        """
        if parts is None:
            parts = self.config.default_parts

        print(f"FAR Indexer")
        print(f"  Parts: {', '.join(parts)}")
        print(f"  Qdrant URL: {self.config.qdrant_url}")
        print(f"  Collection: {self.config.collection_name}")

        if not dry_run:
            self.create_collection()

        total_indexed = 0
        for part in parts:
            count = self.process_part(part, dry_run)
            total_indexed += count

        print()
        print(f"Done! Indexed {total_indexed} regulation sections to '{self.config.collection_name}'")
        return total_indexed


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Index FAR regulations to Qdrant")
    parser.add_argument(
        "--parts",
        default="1,61,91,121,135",
        help="Comma-separated list of CFR parts to index"
    )
    parser.add_argument(
        "--qdrant-url",
        default="http://localhost:6333",
        help="Qdrant server URL"
    )
    parser.add_argument(
        "--collection",
        default="far_regulations",
        help="Qdrant collection name"
    )
    parser.add_argument(
        "--embedder",
        choices=["local", "openai"],
        default="local",
        help="Embedding provider: 'local' (sentence-transformers) or 'openai' (API)"
    )
    parser.add_argument(
        "--embedding-model",
        help="Embedding model name (default: all-MiniLM-L6-v2 for local, text-embedding-3-small for openai)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch structure but don't index"
    )
    parser.add_argument(
        "--save-to",
        default="./data/aviation/far",
        help="Directory to save fetched data (default: ./data/aviation/far). Use --no-save to disable."
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save fetched data to disk"
    )

    args = parser.parse_args()
    parts = [p.strip() for p in args.parts.split(",")]

    save_to = None if args.no_save else args.save_to

    indexer = FARIndexer(
        qdrant_url=args.qdrant_url,
        collection_name=args.collection,
        embedder=args.embedder,
        embedding_model=args.embedding_model,
        save_to=save_to,
    )
    indexer.index(parts=parts, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

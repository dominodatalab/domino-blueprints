"""
Aviation news indexer for Qdrant.

Fetches aviation news from RSS feeds and indexes to Qdrant.

Usage as CLI:
    # Local embeddings (fast, free)
    python -m agentic_rag.indexers.news_indexer

    # OpenAI embeddings
    python -m agentic_rag.indexers.news_indexer --embedder openai

Usage as module:
    from agentic_rag.indexers import NewsIndexer
    indexer = NewsIndexer(qdrant_url="http://localhost:6333", embedder="local")
    indexer.index()
"""

import argparse
import hashlib
import json
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from html import unescape
from pathlib import Path
from typing import Generator, Literal
import re

import httpx

from .embeddings import get_embedder, Embedder


@dataclass
class NewsSource:
    """Configuration for a news source."""
    name: str
    feed_url: str
    category: str


@dataclass
class NewsConfig:
    """Configuration for news indexer."""
    qdrant_url: str = "http://localhost:6333"
    collection_name: str = "aviation_news"
    index_batch_size: int = 50
    save_to: str | None = "./data/aviation/news"
    sources: list[NewsSource] = field(default_factory=lambda: [
        NewsSource(
            name="AVweb",
            feed_url="https://www.avweb.com/feed/",
            category="General Aviation"
        ),
        NewsSource(
            name="Aviation Week",
            feed_url="https://aviationweek.com/rss.xml",
            category="Industry"
        ),
        NewsSource(
            name="Flying Magazine",
            feed_url="https://www.flyingmag.com/feed/",
            category="General Aviation"
        ),
        NewsSource(
            name="Simple Flying",
            feed_url="https://simpleflying.com/feed/",
            category="Commercial Aviation"
        ),
    ])


class NewsIndexer:
    """
    Indexes aviation news to Qdrant.

    Fetches news from RSS feeds, generates embeddings,
    and indexes to a Qdrant collection.
    """

    def __init__(
        self,
        qdrant_url: str | None = None,
        collection_name: str | None = None,
        embedder: Literal["local", "openai"] | Embedder = "local",
        embedding_model: str | None = None,
        save_to: str | None = "./data/aviation/news",
    ):
        self.config = NewsConfig()
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

    def save_data(self, articles: list[dict], source_name: str | None = None) -> None:
        """Save fetched data to JSON file."""
        if not self.config.save_to:
            return

        save_dir = Path(self.config.save_to)
        save_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{source_name.lower().replace(' ', '_')}.json" if source_name else "all_articles.json"
        filepath = save_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        print(f"  Saved {len(articles)} articles to {filepath}")

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

    def clean_html(self, text: str) -> str:
        """Remove HTML tags and clean up text."""
        if not text:
            return ""
        # Unescape HTML entities
        text = unescape(text)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def parse_rss_feed(self, source: NewsSource) -> Generator[dict, None, None]:
        """Parse an RSS feed and yield article items."""
        try:
            response = httpx.get(
                source.feed_url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; NewsIndexer/1.0)"},
                timeout=30,
                follow_redirects=True
            )
            response.raise_for_status()
        except Exception as e:
            print(f"  Failed to fetch {source.name}: {e}")
            return

        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            print(f"  Failed to parse {source.name} feed: {e}")
            return

        # Handle both RSS and Atom feeds
        namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'content': 'http://purl.org/rss/1.0/modules/content/',
            'dc': 'http://purl.org/dc/elements/1.1/',
        }

        # Try RSS format first
        items = root.findall('.//item')
        if not items:
            # Try Atom format
            items = root.findall('.//atom:entry', namespaces)

        for item in items:
            article = self._parse_item(item, source, namespaces)
            if article:
                yield article

    def _parse_item(self, item: ET.Element, source: NewsSource, namespaces: dict) -> dict | None:
        """Parse a single RSS/Atom item."""
        # Try different tag names for compatibility
        title = (
            self._get_text(item, 'title') or
            self._get_text(item, 'atom:title', namespaces)
        )

        link = (
            self._get_text(item, 'link') or
            self._get_attr(item, 'atom:link', 'href', namespaces)
        )

        description = (
            self._get_text(item, 'description') or
            self._get_text(item, 'content:encoded', namespaces) or
            self._get_text(item, 'atom:content', namespaces) or
            self._get_text(item, 'atom:summary', namespaces)
        )

        pub_date = (
            self._get_text(item, 'pubDate') or
            self._get_text(item, 'dc:date', namespaces) or
            self._get_text(item, 'atom:published', namespaces) or
            self._get_text(item, 'atom:updated', namespaces)
        )

        if not title:
            return None

        # Generate unique ID from URL or title
        id_source = link or title
        article_id = hashlib.md5(id_source.encode()).hexdigest()[:16]

        return {
            "id": article_id,
            "title": self.clean_html(title),
            "link": link,
            "description": self.clean_html(description) if description else "",
            "pub_date": pub_date,
            "source_name": source.name,
            "category": source.category,
        }

    def _get_text(self, element: ET.Element, tag: str, namespaces: dict = None) -> str | None:
        """Get text content of a child element."""
        if namespaces:
            child = element.find(tag, namespaces)
        else:
            child = element.find(tag)
        return child.text if child is not None and child.text else None

    def _get_attr(self, element: ET.Element, tag: str, attr: str, namespaces: dict = None) -> str | None:
        """Get attribute of a child element."""
        if namespaces:
            child = element.find(tag, namespaces)
        else:
            child = element.find(tag)
        return child.get(attr) if child is not None else None

    def build_document_text(self, article: dict) -> str:
        """Build searchable text from an article."""
        parts = [
            f"Aviation News: {article['title']}",
            f"Source: {article['source_name']}",
            f"Category: {article['category']}",
        ]

        if article.get("pub_date"):
            parts.append(f"Published: {article['pub_date']}")

        if article.get("description"):
            parts.append("")
            parts.append(article["description"])

        return "\n".join(parts)

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

    def fetch_all_articles(self) -> Generator[dict, None, None]:
        """Fetch articles from all configured sources."""
        for source in self.config.sources:
            print(f"\nFetching from {source.name}...")
            count = 0
            for article in self.parse_rss_feed(source):
                count += 1
                yield article
            print(f"  Found {count} articles")
            time.sleep(0.5)  # Rate limiting between sources

    def process_and_index(self, articles: list[dict]) -> int:
        """Process articles and index to Qdrant. Returns count indexed."""
        points = []
        indexed = 0

        for article in articles:
            text = self.build_document_text(article)

            try:
                embedding = self.get_embedding(text)
            except Exception as e:
                print(f"  Failed to embed '{article['title'][:50]}...': {e}")
                continue

            # Convert hex string ID to integer for Qdrant
            point_id = int(article["id"], 16)

            point = {
                "id": point_id,
                "vector": embedding,
                "payload": {
                    "text": text,
                    "title": article["title"],
                    "link": article.get("link"),
                    "description": article.get("description", "")[:500],
                    "pub_date": article.get("pub_date"),
                    "source_name": article["source_name"],
                    "category": article["category"],
                    "header_l1": "Aviation News",
                    "header_l2": article["source_name"],
                    "header_l3": article["title"][:100],
                }
            }
            points.append(point)

            if len(points) >= self.config.index_batch_size:
                print(f"  Indexing batch of {len(points)} articles...")
                self.index_to_qdrant(points)
                indexed += len(points)
                points = []
                time.sleep(0.1)

        if points:
            print(f"  Indexing final batch of {len(points)} articles...")
            self.index_to_qdrant(points)
            indexed += len(points)

        return indexed

    def add_source(self, name: str, feed_url: str, category: str = "General") -> None:
        """Add a custom news source."""
        self.config.sources.append(NewsSource(
            name=name,
            feed_url=feed_url,
            category=category
        ))

    def index(
        self,
        sources: list[str] | None = None,
        dry_run: bool = False,
    ) -> int:
        """
        Index aviation news to Qdrant.

        Args:
            sources: List of source names to index (default: all configured sources)
            dry_run: If True, fetch but don't index

        Returns:
            Number of articles indexed
        """
        print(f"Aviation News Indexer")
        print(f"  Qdrant URL: {self.config.qdrant_url}")
        print(f"  Collection: {self.config.collection_name}")
        print(f"  Sources: {', '.join(s.name for s in self.config.sources)}")

        # Filter sources if specified
        if sources:
            self.config.sources = [
                s for s in self.config.sources
                if s.name.lower() in [name.lower() for name in sources]
            ]
            print(f"  Filtered to: {', '.join(s.name for s in self.config.sources)}")

        if not dry_run:
            self.create_collection()

        # Collect all articles
        all_articles = list(self.fetch_all_articles())
        print(f"\nTotal articles collected: {len(all_articles)}")

        # Save fetched data to JSON
        if self.config.save_to:
            self.save_data(all_articles)

        if dry_run:
            print("\n[DRY RUN] Would index the following articles:")
            for article in all_articles[:10]:
                print(f"  - [{article['source_name']}] {article['title'][:60]}...")
            if len(all_articles) > 10:
                print(f"  ... and {len(all_articles) - 10} more")
            return len(all_articles)

        total_indexed = self.process_and_index(all_articles)

        print()
        print(f"Done! Indexed {total_indexed} articles to '{self.config.collection_name}'")
        return total_indexed


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Index aviation news to Qdrant")
    parser.add_argument(
        "--qdrant-url",
        default="http://localhost:6333",
        help="Qdrant server URL"
    )
    parser.add_argument(
        "--collection",
        default="aviation_news",
        help="Qdrant collection name"
    )
    parser.add_argument(
        "--sources",
        help="Comma-separated list of source names to index (default: all)"
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
        help="Fetch but don't index"
    )
    parser.add_argument(
        "--save-to",
        default="./data/aviation/news",
        help="Directory to save fetched data (default: ./data/aviation/news). Use --no-save to disable."
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save fetched data to disk"
    )

    args = parser.parse_args()

    sources = None
    if args.sources:
        sources = [s.strip() for s in args.sources.split(",")]

    save_to = None if args.no_save else args.save_to

    indexer = NewsIndexer(
        qdrant_url=args.qdrant_url,
        collection_name=args.collection,
        embedder=args.embedder,
        embedding_model=args.embedding_model,
        save_to=save_to,
    )
    indexer.index(sources=sources, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

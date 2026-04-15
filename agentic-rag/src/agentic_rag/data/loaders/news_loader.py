# news_loader.py
"""
Load aviation news articles for context.

For demo purposes, we use sample articles or Wikipedia aviation incidents.
In production, this could integrate with news APIs or web scraping.
"""

from pathlib import Path
from typing import Iterator
from dataclasses import dataclass
from datetime import datetime

from agentic_rag.config import get_settings


@dataclass
class NewsArticle:
    """Parsed news article."""
    id: str
    title: str
    source: str
    date: str
    url: str
    text: str
    related_incident_id: str | None = None

    @property
    def header_l1(self) -> str:
        return f"News: {self.source}"

    @property
    def header_l2(self) -> str:
        return self.date

    @property
    def header_l3(self) -> str:
        return self.title


class NewsLoader:
    """Load aviation news articles."""

    def __init__(self, data_dir: Path | None = None):
        settings = get_settings()
        self.data_dir = data_dir or settings.data_dir / "news"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_articles(self) -> Iterator[NewsArticle]:
        """Load news articles from local storage."""
        # Check for JSON files in data directory
        for json_file in self.data_dir.glob("*.json"):
            yield from self._load_json_file(json_file)

        # Check for markdown files
        for md_file in self.data_dir.glob("*.md"):
            yield self._load_markdown_file(md_file)

    def _load_json_file(self, path: Path) -> Iterator[NewsArticle]:
        """Load articles from a JSON file."""
        import json
        with open(path) as f:
            data = json.load(f)

        if isinstance(data, list):
            for item in data:
                yield NewsArticle(**item)
        else:
            yield NewsArticle(**data)

    def _load_markdown_file(self, path: Path) -> NewsArticle:
        """Load a single article from markdown file."""
        content = path.read_text()

        # Parse frontmatter if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                body = parts[2]
                metadata = self._parse_frontmatter(frontmatter)
                return NewsArticle(
                    id=path.stem,
                    text=body.strip(),
                    **metadata
                )

        return NewsArticle(
            id=path.stem,
            title=path.stem.replace("-", " ").title(),
            source="Unknown",
            date=datetime.now().strftime("%Y-%m-%d"),
            url="",
            text=content,
        )

    def _parse_frontmatter(self, frontmatter: str) -> dict:
        """Parse YAML-like frontmatter."""
        metadata = {}
        for line in frontmatter.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                metadata[key.strip()] = value.strip()
        return metadata

    def to_documents(self, articles: Iterator[NewsArticle] | None = None) -> Iterator[dict]:
        """Convert news articles to documents for indexing."""
        articles = articles or self.load_articles()

        for article in articles:
            text = self._format_document_text(article)
            metadata = {
                "source": "news",
                "news_source": article.source,
                "date": article.date,
                "url": article.url,
                "header_l1": article.header_l1,
                "header_l2": article.header_l2,
                "header_l3": article.header_l3,
                "related_incident_id": article.related_incident_id,
            }

            yield {"id": article.id, "text": text, "metadata": metadata}

    def _format_document_text(self, article: NewsArticle) -> str:
        """Format article as document text."""
        parts = [
            f"# {article.title}",
            f"Source: {article.source}",
            f"Date: {article.date}",
            "",
            article.text,
        ]

        if article.url:
            parts.extend(["", f"URL: {article.url}"])

        return "\n".join(parts)

    def create_sample_data(self) -> Iterator[dict]:
        """Create sample news articles for demo purposes."""
        sample_articles = [
            NewsArticle(
                id="news-001",
                title="Small Plane Crashes in Colorado Mountains During Storm",
                source="Aviation Weekly",
                date="2023-03-15",
                url="https://example.com/news/colorado-crash",
                text="""A single-engine Cessna 172 crashed in the Colorado Rocky Mountains yesterday during deteriorating weather conditions. The pilot, flying solo, was attempting to cross a mountain pass when the aircraft went down.

Search and rescue teams located the wreckage this morning. The pilot sustained serious injuries but survived.

Witnesses reported seeing the aircraft flying below the cloud layer before it disappeared into the mountains. Weather at the time included low ceilings, reduced visibility, and moderate turbulence.

The NTSB has dispatched investigators to the scene. Preliminary reports suggest the pilot may have attempted to continue VFR flight into instrument meteorological conditions (IMC).

Local flight instructors noted that the mountain pass where the accident occurred is notorious for rapidly changing weather conditions. "Many pilots have been caught off guard by how quickly the weather can close in," said a local CFI.

The investigation is ongoing.""",
                related_incident_id="CEN23FA001"
            ),
            NewsArticle(
                id="news-002",
                title="FAA Issues Warning About Mountain Flying After Recent Accidents",
                source="Flying Magazine",
                date="2023-03-20",
                url="https://example.com/news/faa-mountain-warning",
                text="""The Federal Aviation Administration has issued a safety advisory following a series of accidents involving general aviation aircraft in mountainous terrain.

The advisory emphasizes the importance of:
- Obtaining thorough weather briefings before mountain flights
- Understanding density altitude effects on aircraft performance
- Having an escape route planned before entering mountain passes
- Maintaining VFR weather minimums appropriate for the terrain

"Mountain flying requires specialized knowledge and skills," the FAA statement reads. "Pilots should seek additional training before attempting flights in mountainous areas."

The advisory comes after three fatal accidents in the past month involving pilots who encountered unexpected weather in mountain terrain. In each case, investigators found that the pilots had limited mountain flying experience.

Flight schools in Colorado and Utah report increased interest in mountain flying courses following the accidents.""",
                related_incident_id=None
            ),
            NewsArticle(
                id="news-003",
                title="Pilot in Colorado Crash Was Not Instrument Rated, Records Show",
                source="Local News 9",
                date="2023-03-25",
                url="https://example.com/news/pilot-records",
                text="""FAA records reveal that the pilot involved in last week's Colorado mountain crash held only a private pilot certificate with no instrument rating.

The pilot, who survived the crash with serious injuries, had approximately 180 total flight hours, with only 12 hours logged in mountainous terrain.

According to the preliminary accident report, the pilot departed from a local airport despite forecasts calling for deteriorating conditions along the planned route. ATC recordings indicate the pilot did not request a weather briefing through Flight Service.

"This is unfortunately a common scenario," said an NTSB spokesperson. "Pilots sometimes underestimate how quickly mountain weather can change and overestimate their ability to navigate through it."

The aircraft, a 1975 Cessna 172M, was destroyed on impact. The pilot remains hospitalized in stable condition.

Aviation safety experts emphasize that attempting to fly VFR into IMC conditions is one of the leading causes of fatal general aviation accidents. Pilots without instrument ratings are prohibited from flying in instrument conditions under FAR Part 91.""",
                related_incident_id="CEN23FA001"
            ),
        ]

        # Write sample data
        import json
        output_path = self.data_dir / "sample_news.json"
        with open(output_path, "w") as f:
            json.dump([{
                "id": a.id,
                "title": a.title,
                "source": a.source,
                "date": a.date,
                "url": a.url,
                "text": a.text,
                "related_incident_id": a.related_incident_id,
            } for a in sample_articles], f, indent=2)

        print(f"Sample news data created at {output_path}")

        # Yield as documents
        for article in sample_articles:
            text = self._format_document_text(article)
            metadata = {
                "source": "news",
                "news_source": article.source,
                "date": article.date,
                "url": article.url,
                "header_l1": article.header_l1,
                "header_l2": article.header_l2,
                "header_l3": article.header_l3,
                "related_incident_id": article.related_incident_id,
            }
            yield {"id": article.id, "text": text, "metadata": metadata}


if __name__ == "__main__":
    loader = NewsLoader()
    print("Creating sample news data...")
    for doc in loader.create_sample_data():
        print(f"Created: {doc['id']} - {doc['metadata']['header_l3']}")

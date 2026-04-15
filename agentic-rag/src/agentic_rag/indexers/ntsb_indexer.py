"""
NTSB accident data indexer for Qdrant.

Loads NTSB aviation accident data from CSV file and indexes to Qdrant.

Download data from: https://data.ntsb.gov/avdata (Access database files)
Or Kaggle: https://www.kaggle.com/datasets/khsamaha/aviation-accident-database-synopses

Usage as CLI:
    # From CSV file
    python -m agentic_rag.indexers.ntsb_indexer --csv-file ./ntsb_data.csv

    # With OpenAI embeddings
    python -m agentic_rag.indexers.ntsb_indexer --csv-file ./ntsb_data.csv --embedder openai

Usage as module:
    from agentic_rag.indexers import NTSBIndexer
    indexer = NTSBIndexer(qdrant_url="http://localhost:6333", embedder="local")
    indexer.index_from_csv("./ntsb_data.csv")
"""

import argparse
import csv
import hashlib
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Generator, Literal

import httpx

from .embeddings import get_embedder, Embedder


@dataclass
class NTSBConfig:
    """Configuration for NTSB indexer."""
    api_url: str = "https://data.ntsb.gov/carol-main-public/api/Query/Main"
    qdrant_url: str = "http://localhost:6333"
    collection_name: str = "ntsb_incidents"
    batch_size: int = 100  # NTSB API max per request
    index_batch_size: int = 50  # Qdrant upsert batch size


class NTSBIndexer:
    """
    Indexes NTSB aviation accident data to Qdrant.

    Fetches data from the NTSB public API, generates embeddings,
    and indexes to a Qdrant collection.
    """

    def __init__(
        self,
        qdrant_url: str | None = None,
        collection_name: str | None = None,
        embedder: Literal["local", "openai"] | Embedder = "local",
        embedding_model: str | None = None,
    ):
        self.config = NTSBConfig()
        if qdrant_url:
            self.config.qdrant_url = qdrant_url
        if collection_name:
            self.config.collection_name = collection_name

        # Set up embedder
        if isinstance(embedder, str):
            self.embedder = get_embedder(embedder, model_name=embedding_model)
        else:
            self.embedder = embedder

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

    def fetch_accidents(
        self,
        start_date: str,
        end_date: str,
    ) -> Generator[list[dict], None, None]:
        """
        Fetch NTSB accidents via pagination.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Yields:
            Batches of accident records
        """
        offset = 0
        total_fetched = 0

        while True:
            payload = {
                "ResultSetSize": self.config.batch_size,
                "ResultSetOffset": offset,
                "QueryFilterCriteria": [
                    {
                        "FieldName": "EventDate",
                        "Operator": ">=",
                        "FieldValue": start_date
                    },
                    {
                        "FieldName": "EventDate",
                        "Operator": "<=",
                        "FieldValue": end_date
                    }
                ]
            }

            print(f"Fetching records {offset} to {offset + self.config.batch_size}...")

            response = httpx.post(
                self.config.api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            response.raise_for_status()

            data = response.json()
            records = data.get("Results", [])

            if not records:
                print(f"No more records. Total fetched: {total_fetched}")
                break

            total_fetched += len(records)
            print(f"Fetched {len(records)} records (total: {total_fetched})")

            yield records

            offset += self.config.batch_size
            time.sleep(0.5)  # Rate limiting

    def build_document_text(self, record: dict) -> str:
        """Build searchable text from an NTSB record."""
        # Handle location - may be combined or separate fields
        location = record.get('Location') or f"{record.get('City', '')}, {record.get('State', '')}".strip(", ")

        parts = [
            "NTSB Aviation Accident Report",
            f"Event ID: {record.get('EventId', 'Unknown')}",
            f"Date: {record.get('EventDate', 'Unknown')}",
            f"Location: {location}",
            f"Country: {record.get('Country', 'USA')}",
        ]

        if record.get("Make") or record.get("Model"):
            parts.append(f"Aircraft: {record.get('Make', '')} {record.get('Model', '')}")
        if record.get("RegistrationNumber"):
            parts.append(f"Registration: {record.get('RegistrationNumber')}")
        if record.get("AircraftCategory"):
            parts.append(f"Category: {record.get('AircraftCategory')}")

        if record.get("HighestInjuryLevel"):
            parts.append(f"Injury Severity: {record.get('HighestInjuryLevel')}")
        if record.get("FatalInjuryCount"):
            parts.append(f"Fatalities: {record.get('FatalInjuryCount')}")
        if record.get("SeriousInjuryCount"):
            parts.append(f"Serious Injuries: {record.get('SeriousInjuryCount')}")

        if record.get("WeatherCondition"):
            parts.append(f"Weather: {record.get('WeatherCondition')}")
        if record.get("BroadPhaseOfFlight"):
            parts.append(f"Phase of Flight: {record.get('BroadPhaseOfFlight')}")

        if record.get("ProbableCause"):
            parts.append(f"\nProbable Cause:\n{record.get('ProbableCause')}")

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

    def _make_point_id(self, event_id: str) -> int:
        """Convert event ID string to a valid Qdrant point ID (positive integer)."""
        # Hash the event ID and take first 16 hex chars to make a 64-bit integer
        hash_hex = hashlib.md5(event_id.encode()).hexdigest()[:16]
        return int(hash_hex, 16)

    def process_and_index(self, records: list[dict]) -> int:
        """Process records and index to Qdrant. Returns count indexed."""
        points = []
        indexed = 0

        for record in records:
            event_id = record.get("EventId")
            if not event_id:
                continue

            text = self.build_document_text(record)

            try:
                embedding = self.get_embedding(text)
            except Exception as e:
                print(f"  Failed to embed {event_id}: {e}")
                continue

            # Handle location - may be combined or separate fields
            location = record.get('Location') or f"{record.get('City', '')}, {record.get('State', '')}".strip(", ")

            # Convert string event ID to integer for Qdrant
            point_id = self._make_point_id(event_id)

            point = {
                "id": point_id,
                "vector": embedding,
                "payload": {
                    "text": text,
                    "event_id": event_id,
                    "event_date": record.get("EventDate"),
                    "location": location,
                    "country": record.get("Country", "USA"),
                    "aircraft": f"{record.get('Make', '')} {record.get('Model', '')}".strip(),
                    "registration": record.get("RegistrationNumber"),
                    "injury_severity": record.get("HighestInjuryLevel"),
                    "fatal_count": record.get("FatalInjuryCount"),
                    "weather_condition": record.get("WeatherCondition"),
                    "phase_of_flight": record.get("BroadPhaseOfFlight"),
                    "probable_cause": record.get("ProbableCause"),
                    "header_l1": "NTSB Aviation Accidents",
                    "header_l2": record.get("AircraftCategory", "General Aviation"),
                    "header_l3": f"{record.get('Make', '')} {record.get('Model', '')} - {record.get('BroadPhaseOfFlight', 'Unknown')}",
                }
            }
            points.append(point)

            if len(points) >= self.config.index_batch_size:
                print(f"  Indexing batch of {len(points)} points...")
                self.index_to_qdrant(points)
                indexed += len(points)
                points = []
                time.sleep(0.1)

        if points:
            print(f"  Indexing final batch of {len(points)} points...")
            self.index_to_qdrant(points)
            indexed += len(points)

        return indexed

    def index(
        self,
        start_date: str = "2020-01-01",
        end_date: str | None = None,
        dry_run: bool = False,
    ) -> int:
        """
        Index NTSB accident data to Qdrant.

        Args:
            start_date: Start date for accidents (YYYY-MM-DD)
            end_date: End date for accidents (YYYY-MM-DD), defaults to today
            dry_run: If True, fetch but don't index

        Returns:
            Number of records indexed
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        print(f"NTSB Indexer")
        print(f"  Date range: {start_date} to {end_date}")
        print(f"  Qdrant URL: {self.config.qdrant_url}")
        print(f"  Collection: {self.config.collection_name}")
        print()

        if not dry_run:
            self.create_collection()

        total_indexed = 0
        for batch in self.fetch_accidents(start_date, end_date):
            if dry_run:
                print(f"  [DRY RUN] Would index {len(batch)} records")
                for record in batch[:3]:
                    print(f"    - {record.get('EventId')}: {record.get('City')}, {record.get('State')} ({record.get('EventDate')})")
            else:
                total_indexed += self.process_and_index(batch)

        print()
        print(f"Done! Indexed {total_indexed} records to '{self.config.collection_name}'")
        return total_indexed

    def load_from_csv(self, csv_path: str) -> Generator[list[dict], None, None]:
        """
        Load NTSB data from a CSV file.

        Expected columns (flexible - uses what's available):
        - EventId or ev_id or NtsbNo
        - EventDate or ev_date
        - City or ev_city
        - State or ev_state
        - Country or ev_country
        - Make or acft_make
        - Model or acft_model
        - RegistrationNumber or regis_no
        - AircraftCategory or acft_category
        - HighestInjuryLevel or inj_tot_f (fatal count)
        - WeatherCondition or wx_cond_basic
        - BroadPhaseOfFlight or phase_flt_spec
        - ProbableCause or narr_cause

        Yields:
            Batches of records
        """
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        # Column name mappings (CSV column -> standard name)
        # Keys are normalized: lowercase with spaces, underscores, dots removed
        column_mappings = {
            # Event ID
            'eventid': 'EventId', 'evid': 'EventId', 'ntsbno': 'EventId',
            'accidentnumber': 'EventId',
            # Date
            'eventdate': 'EventDate', 'evdate': 'EventDate',
            # Location
            'city': 'City', 'evcity': 'City',
            'state': 'State', 'evstate': 'State',
            'country': 'Country', 'evcountry': 'Country',
            'location': 'Location',
            # Aircraft
            'make': 'Make', 'acftmake': 'Make',
            'model': 'Model', 'acftmodel': 'Model',
            'registrationnumber': 'RegistrationNumber', 'regisno': 'RegistrationNumber',
            'aircraftcategory': 'AircraftCategory', 'acftcategory': 'AircraftCategory',
            'aircraftdamage': 'AircraftDamage',
            # Injuries
            'injuryseverity': 'HighestInjuryLevel', 'highestinjurylevel': 'HighestInjuryLevel',
            'totalfatalinjuries': 'FatalInjuryCount', 'fatalinjurycount': 'FatalInjuryCount',
            'injtotf': 'FatalInjuryCount',
            'totalseriousinjuries': 'SeriousInjuryCount',
            'totalminorinjuries': 'MinorInjuryCount',
            'totaluninjured': 'UninjuredCount',
            # Conditions
            'weathercondition': 'WeatherCondition', 'wxcondbasic': 'WeatherCondition',
            'broadphaseofflight': 'BroadPhaseOfFlight', 'phasefltspec': 'BroadPhaseOfFlight',
            # Narrative
            'probablecause': 'ProbableCause', 'narrcause': 'ProbableCause',
            # Other useful fields
            'investigationtype': 'InvestigationType',
            'numberofengines': 'NumberOfEngines',
            'enginetype': 'EngineType',
            'fardescription': 'FARDescription',
            'purposeofflight': 'PurposeOfFlight',
            'amateurbuilt': 'AmateurBuilt',
            'reportstatus': 'ReportStatus',
        }

        batch = []
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            reader = csv.DictReader(f)

            # Build mapping for this file's columns
            field_map = {}
            mapped_cols = []
            for col in reader.fieldnames or []:
                # Normalize: lowercase, remove spaces, underscores, and dots
                col_lower = col.lower().replace(' ', '').replace('_', '').replace('.', '')
                if col_lower in column_mappings:
                    field_map[col] = column_mappings[col_lower]
                    mapped_cols.append(f"{col} -> {column_mappings[col_lower]}")
                elif col.lower().replace(' ', '_') in column_mappings:
                    field_map[col] = column_mappings[col.lower().replace(' ', '_')]
                    mapped_cols.append(f"{col} -> {column_mappings[col.lower().replace(' ', '_')]}")
                else:
                    field_map[col] = col  # Keep original

            print(f"  Mapped columns: {len(mapped_cols)}")
            for m in mapped_cols[:10]:
                print(f"    {m}")
            if len(mapped_cols) > 10:
                print(f"    ... and {len(mapped_cols) - 10} more")

            for row in reader:
                # Normalize row keys
                record = {}
                for orig_col, value in row.items():
                    new_col = field_map.get(orig_col, orig_col)
                    record[new_col] = value

                batch.append(record)

                if len(batch) >= self.config.batch_size:
                    yield batch
                    batch = []

            if batch:
                yield batch

    def index_from_csv(
        self,
        csv_path: str,
        dry_run: bool = False,
    ) -> int:
        """
        Index NTSB data from a CSV file to Qdrant.

        Args:
            csv_path: Path to CSV file
            dry_run: If True, load but don't index

        Returns:
            Number of records indexed
        """
        print(f"NTSB Indexer (CSV)")
        print(f"  CSV file: {csv_path}")
        print(f"  Qdrant URL: {self.config.qdrant_url}")
        print(f"  Collection: {self.config.collection_name}")
        print()

        if not dry_run:
            self.create_collection()

        total_indexed = 0
        for batch in self.load_from_csv(csv_path):
            if dry_run:
                print(f"  [DRY RUN] Would index {len(batch)} records")
                for record in batch[:3]:
                    print(f"    - {record.get('EventId', 'N/A')}: {record.get('City', '')}, {record.get('State', '')} ({record.get('EventDate', '')})")
            else:
                total_indexed += self.process_and_index(batch)

        print()
        print(f"Done! Indexed {total_indexed} records to '{self.config.collection_name}'")
        return total_indexed


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Index NTSB accident data to Qdrant",
        epilog="""
Data sources:
  Download CSV from: https://data.ntsb.gov/avdata
  Or Kaggle: https://www.kaggle.com/datasets/khsamaha/aviation-accident-database-synopses
        """
    )
    parser.add_argument(
        "--csv-file",
        required=True,
        help="Path to NTSB CSV data file (required)"
    )
    parser.add_argument(
        "--qdrant-url",
        default="http://localhost:6333",
        help="Qdrant server URL"
    )
    parser.add_argument(
        "--collection",
        default="ntsb_incidents",
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
        help="Load data but don't index"
    )

    args = parser.parse_args()

    indexer = NTSBIndexer(
        qdrant_url=args.qdrant_url,
        collection_name=args.collection,
        embedder=args.embedder,
        embedding_model=args.embedding_model,
    )
    indexer.index_from_csv(
        csv_path=args.csv_file,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()

# ntsb_loader.py
"""
Load NTSB Aviation Accident Database.

Source: https://www.ntsb.gov/Pages/AviationQueryV2.aspx

The NTSB provides downloadable CSV data with accident reports including:
- Event ID, date, location
- Aircraft info (make, model, registration)
- Injury counts
- Weather conditions
- Probable cause narrative
"""

import csv
import httpx
from pathlib import Path
from typing import Iterator
from dataclasses import dataclass

from agentic_rag.config import get_settings


@dataclass
class NTSBRecord:
    """Parsed NTSB accident record."""
    event_id: str
    event_date: str
    location: str
    country: str
    latitude: float | None
    longitude: float | None
    aircraft_make: str
    aircraft_model: str
    registration: str
    injury_severity: str
    fatal_injuries: int
    serious_injuries: int
    minor_injuries: int
    weather_condition: str
    broad_phase_of_flight: str
    probable_cause: str
    narrative: str

    @property
    def header_l1(self) -> str:
        return f"NTSB Report {self.event_id}"

    @property
    def header_l2(self) -> str:
        return f"{self.event_date} - {self.location}"

    @property
    def header_l3(self) -> str:
        return f"{self.aircraft_make} {self.aircraft_model} ({self.registration})"


class NTSBLoader:
    """Load and parse NTSB accident data."""

    # NTSB data download URL (requires form submission, so we use cached data)
    NTSB_API_URL = "https://data.ntsb.gov/avdata"

    def __init__(self, data_dir: Path | None = None):
        settings = get_settings()
        self.data_dir = data_dir or settings.data_dir / "ntsb"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def download_data(self, years: list[int] | None = None) -> Path:
        """
        Download NTSB data for specified years.

        Note: NTSB requires form submission. For demo purposes,
        we provide sample data or users can manually download.
        """
        # TODO: Implement NTSB data download
        # For now, expect data to be manually placed in data_dir
        output_path = self.data_dir / "accidents.csv"
        if not output_path.exists():
            raise FileNotFoundError(
                f"NTSB data not found at {output_path}. "
                "Please download from https://www.ntsb.gov/Pages/AviationQueryV2.aspx"
            )
        return output_path

    def load_csv(self, csv_path: Path | None = None) -> Iterator[NTSBRecord]:
        """Load and parse NTSB CSV data."""
        csv_path = csv_path or self.data_dir / "accidents.csv"

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield self._parse_row(row)

    def _parse_row(self, row: dict) -> NTSBRecord:
        """Parse a CSV row into an NTSBRecord."""
        return NTSBRecord(
            event_id=row.get("EventId", row.get("ev_id", "")),
            event_date=row.get("EventDate", row.get("ev_date", "")),
            location=row.get("Location", row.get("ev_city", "")),
            country=row.get("Country", row.get("ev_country", "USA")),
            latitude=self._parse_float(row.get("Latitude")),
            longitude=self._parse_float(row.get("Longitude")),
            aircraft_make=row.get("Make", row.get("acft_make", "")),
            aircraft_model=row.get("Model", row.get("acft_model", "")),
            registration=row.get("RegistrationNumber", row.get("regis_no", "")),
            injury_severity=row.get("InjurySeverity", row.get("ev_highest_injury", "")),
            fatal_injuries=self._parse_int(row.get("TotalFatalInjuries", row.get("inj_tot_f", 0))),
            serious_injuries=self._parse_int(row.get("TotalSeriousInjuries", row.get("inj_tot_s", 0))),
            minor_injuries=self._parse_int(row.get("TotalMinorInjuries", row.get("inj_tot_m", 0))),
            weather_condition=row.get("WeatherCondition", row.get("wx_cond_basic", "")),
            broad_phase_of_flight=row.get("BroadPhaseOfFlight", row.get("phase_flt_spec", "")),
            probable_cause=row.get("ProbableCause", row.get("narr_cause", "")),
            narrative=row.get("Narrative", row.get("narr_accp", "")),
        )

    @staticmethod
    def _parse_float(value: str | None) -> float | None:
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None

    @staticmethod
    def _parse_int(value: str | int | None) -> int:
        if not value:
            return 0
        try:
            return int(value)
        except ValueError:
            return 0

    def to_documents(self, records: Iterator[NTSBRecord] | None = None) -> Iterator[dict]:
        """Convert NTSB records to documents for indexing."""
        records = records or self.load_csv()

        for record in records:
            # Create document with full text and metadata
            text = self._format_document_text(record)
            metadata = {
                "source": "ntsb",
                "event_id": record.event_id,
                "event_date": record.event_date,
                "header_l1": record.header_l1,
                "header_l2": record.header_l2,
                "header_l3": record.header_l3,
                "location": record.location,
                "aircraft": f"{record.aircraft_make} {record.aircraft_model}",
                "registration": record.registration,
                "injury_severity": record.injury_severity,
                "weather_condition": record.weather_condition,
                "phase_of_flight": record.broad_phase_of_flight,
            }

            yield {"id": record.event_id, "text": text, "metadata": metadata}

    def _format_document_text(self, record: NTSBRecord) -> str:
        """Format record as readable document text."""
        parts = [
            f"# NTSB Accident Report: {record.event_id}",
            f"Date: {record.event_date}",
            f"Location: {record.location}, {record.country}",
            "",
            "## Aircraft Information",
            f"Make/Model: {record.aircraft_make} {record.aircraft_model}",
            f"Registration: {record.registration}",
            "",
            "## Conditions",
            f"Weather: {record.weather_condition}",
            f"Phase of Flight: {record.broad_phase_of_flight}",
            "",
            "## Injuries",
            f"Severity: {record.injury_severity}",
            f"Fatal: {record.fatal_injuries}, Serious: {record.serious_injuries}, Minor: {record.minor_injuries}",
        ]

        if record.probable_cause:
            parts.extend(["", "## Probable Cause", record.probable_cause])

        if record.narrative:
            parts.extend(["", "## Narrative", record.narrative])

        return "\n".join(parts)


if __name__ == "__main__":
    # CLI for loading data
    loader = NTSBLoader()
    try:
        count = 0
        for doc in loader.to_documents():
            count += 1
            if count <= 3:
                print(f"--- Document {count} ---")
                print(doc["text"][:500])
                print()
        print(f"Total documents: {count}")
    except FileNotFoundError as e:
        print(e)

# constraint_validator.py
"""Extract and validate query constraints against retrieved documents."""

import json
import re
from dataclasses import dataclass, field

from agentic_rag.config import get_settings
from agentic_rag.llm import get_llm_client
from agentic_rag.models import Document


@dataclass
class QueryConstraints:
    """Constraints extracted from user query."""
    location: str | None = None  # City, state, or country
    date: str | None = None  # Specific date or range
    date_range_start: str | None = None
    date_range_end: str | None = None
    aircraft_type: str | None = None  # Make/model
    registration: str | None = None  # N-number
    event_id: str | None = None  # Specific incident ID
    regulation: str | None = None  # Specific FAR section
    keywords: list[str] = field(default_factory=list)  # Other specific terms

    def has_constraints(self) -> bool:
        """Check if any constraints were extracted."""
        return any([
            self.location,
            self.date,
            self.date_range_start,
            self.aircraft_type,
            self.registration,
            self.event_id,
            self.regulation,
        ])


@dataclass
class ValidationResult:
    """Result of constraint validation."""
    is_valid: bool  # Do documents satisfy constraints?
    matched_documents: list[Document]
    unmatched_constraints: list[str]  # Constraints that weren't satisfied
    confidence: str  # high, medium, low
    explanation: str


EXTRACTION_PROMPT = """Extract specific constraints from this aviation safety question.

Question: {question}

Look for:
- Location: city, state, or country names (e.g., "Colorado", "Chicago, IL", "Atlanta")
- Date: specific dates or ranges (e.g., "2023", "January 2022", "last month")
- Aircraft: make/model (e.g., "Cessna 172", "Boeing 737")
- Registration: N-numbers (e.g., "N12345")
- Event ID: NTSB event IDs (e.g., "ERA23FA001")
- Regulation: FAR sections (e.g., "91.103", "Part 61")

Output JSON:
{{
    "location": "string or null",
    "date": "string or null",
    "date_range_start": "string or null",
    "date_range_end": "string or null",
    "aircraft_type": "string or null",
    "registration": "string or null",
    "event_id": "string or null",
    "regulation": "string or null",
    "keywords": ["other", "specific", "terms"]
}}

Only extract explicit constraints mentioned in the question. Do not infer or assume."""


class ConstraintValidator:
    """Extract query constraints and validate against documents."""

    def __init__(self):
        settings = get_settings()
        self.llm = get_llm_client()
        self.model = settings.refinement_model

    def extract_constraints(self, question: str) -> QueryConstraints:
        """Extract constraints from the user's question."""
        response = self.llm.chat(
            messages=[
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(question=question),
                }
            ],
            model=self.model,
            temperature=0,
            json_output=True,
        )

        try:
            result = json.loads(response)
            return QueryConstraints(
                location=result.get("location"),
                date=result.get("date"),
                date_range_start=result.get("date_range_start"),
                date_range_end=result.get("date_range_end"),
                aircraft_type=result.get("aircraft_type"),
                registration=result.get("registration"),
                event_id=result.get("event_id"),
                regulation=result.get("regulation"),
                keywords=result.get("keywords", []),
            )
        except (json.JSONDecodeError, KeyError):
            return QueryConstraints()

    def validate(
        self,
        constraints: QueryConstraints,
        documents: list[Document],
    ) -> ValidationResult:
        """Validate that documents satisfy the query constraints."""
        if not constraints.has_constraints():
            # No specific constraints, all documents are valid
            return ValidationResult(
                is_valid=True,
                matched_documents=documents,
                unmatched_constraints=[],
                confidence="high",
                explanation="No specific constraints to validate.",
            )

        if not documents:
            return ValidationResult(
                is_valid=False,
                matched_documents=[],
                unmatched_constraints=self._list_constraints(constraints),
                confidence="high",
                explanation="No documents retrieved.",
            )

        # Check each constraint
        matched = []
        unmatched_constraints = []

        # Location validation
        if constraints.location:
            location_matches = self._filter_by_location(documents, constraints.location)
            if location_matches:
                matched.extend(location_matches)
            else:
                unmatched_constraints.append(f"location: {constraints.location}")

        # Date validation
        if constraints.date:
            date_matches = self._filter_by_date(documents, constraints.date)
            if date_matches:
                matched.extend(date_matches)
            else:
                unmatched_constraints.append(f"date: {constraints.date}")

        # Aircraft validation
        if constraints.aircraft_type:
            aircraft_matches = self._filter_by_aircraft(documents, constraints.aircraft_type)
            if aircraft_matches:
                matched.extend(aircraft_matches)
            else:
                unmatched_constraints.append(f"aircraft: {constraints.aircraft_type}")

        # Registration validation
        if constraints.registration:
            reg_matches = self._filter_by_registration(documents, constraints.registration)
            if reg_matches:
                matched.extend(reg_matches)
            else:
                unmatched_constraints.append(f"registration: {constraints.registration}")

        # Event ID validation
        if constraints.event_id:
            event_matches = self._filter_by_event_id(documents, constraints.event_id)
            if event_matches:
                matched.extend(event_matches)
            else:
                unmatched_constraints.append(f"event_id: {constraints.event_id}")

        # Regulation validation
        if constraints.regulation:
            reg_matches = self._filter_by_regulation(documents, constraints.regulation)
            if reg_matches:
                matched.extend(reg_matches)
            else:
                unmatched_constraints.append(f"regulation: {constraints.regulation}")

        # Deduplicate matched documents
        seen_ids = set()
        unique_matched = []
        for doc in matched:
            if doc.id not in seen_ids:
                seen_ids.add(doc.id)
                unique_matched.append(doc)

        # If no constraints matched, use original documents but flag the issue
        if not unique_matched and unmatched_constraints:
            return ValidationResult(
                is_valid=False,
                matched_documents=[],
                unmatched_constraints=unmatched_constraints,
                confidence="high",
                explanation=f"No documents match the specified constraints: {', '.join(unmatched_constraints)}. "
                           f"Available data may not include information about these specific criteria.",
            )

        return ValidationResult(
            is_valid=len(unmatched_constraints) == 0,
            matched_documents=unique_matched if unique_matched else documents,
            unmatched_constraints=unmatched_constraints,
            confidence="high" if not unmatched_constraints else "low",
            explanation="All constraints satisfied." if not unmatched_constraints
                       else f"Some constraints not matched: {', '.join(unmatched_constraints)}",
        )

    def _filter_by_location(self, documents: list[Document], location: str) -> list[Document]:
        """Filter documents by location constraint."""
        location_lower = location.lower()
        matches = []

        for doc in documents:
            # Check text content
            if location_lower in doc.text.lower():
                matches.append(doc)
                continue

            # Check metadata
            doc_location = doc.metadata.get("location", "").lower()
            if location_lower in doc_location:
                matches.append(doc)

        return matches

    def _filter_by_date(self, documents: list[Document], date: str) -> list[Document]:
        """Filter documents by date constraint."""
        date_lower = date.lower()
        matches = []

        for doc in documents:
            # Check text content
            if date_lower in doc.text.lower():
                matches.append(doc)
                continue

            # Check metadata for date fields
            event_date = doc.metadata.get("event_date", "").lower()
            publish_date = doc.metadata.get("publish_date", "").lower()

            if date_lower in event_date or date_lower in publish_date:
                matches.append(doc)

        return matches

    def _filter_by_aircraft(self, documents: list[Document], aircraft: str) -> list[Document]:
        """Filter documents by aircraft type constraint."""
        aircraft_lower = aircraft.lower()
        matches = []

        for doc in documents:
            # Check text content
            if aircraft_lower in doc.text.lower():
                matches.append(doc)
                continue

            # Check metadata
            doc_aircraft = doc.metadata.get("aircraft", "").lower()
            if aircraft_lower in doc_aircraft:
                matches.append(doc)

        return matches

    def _filter_by_registration(self, documents: list[Document], registration: str) -> list[Document]:
        """Filter documents by registration constraint."""
        reg_lower = registration.lower()
        matches = []

        for doc in documents:
            if reg_lower in doc.text.lower():
                matches.append(doc)
                continue

            doc_reg = doc.metadata.get("registration", "").lower()
            if reg_lower in doc_reg:
                matches.append(doc)

        return matches

    def _filter_by_event_id(self, documents: list[Document], event_id: str) -> list[Document]:
        """Filter documents by event ID constraint."""
        event_id_lower = event_id.lower()
        matches = []

        for doc in documents:
            if event_id_lower in doc.text.lower():
                matches.append(doc)
                continue

            doc_event_id = doc.metadata.get("event_id", "").lower()
            if event_id_lower in doc_event_id:
                matches.append(doc)

        return matches

    def _filter_by_regulation(self, documents: list[Document], regulation: str) -> list[Document]:
        """Filter documents by regulation constraint."""
        # Normalize regulation format (91.103, §91.103, Part 91.103, etc.)
        reg_normalized = regulation.replace("§", "").replace("Part ", "").strip()
        matches = []

        for doc in documents:
            if reg_normalized in doc.text:
                matches.append(doc)
                continue

            doc_section = doc.metadata.get("section", "")
            if reg_normalized in doc_section:
                matches.append(doc)

        return matches

    def _list_constraints(self, constraints: QueryConstraints) -> list[str]:
        """List all active constraints."""
        active = []
        if constraints.location:
            active.append(f"location: {constraints.location}")
        if constraints.date:
            active.append(f"date: {constraints.date}")
        if constraints.aircraft_type:
            active.append(f"aircraft: {constraints.aircraft_type}")
        if constraints.registration:
            active.append(f"registration: {constraints.registration}")
        if constraints.event_id:
            active.append(f"event_id: {constraints.event_id}")
        if constraints.regulation:
            active.append(f"regulation: {constraints.regulation}")
        return active

# far_loader.py
"""
Load Federal Aviation Regulations (FARs) from eCFR.

Source: https://www.ecfr.gov/current/title-14

Title 14 - Aeronautics and Space contains:
- Part 1: Definitions
- Part 61: Pilot Certification
- Part 91: General Operating Rules
- Part 121: Air Carrier Operations
- Part 135: Commuter and On-Demand Operations
"""

import re
import httpx
from pathlib import Path
from typing import Iterator
from dataclasses import dataclass
from xml.etree import ElementTree

from agentic_rag.config import get_settings


@dataclass
class FARSection:
    """Parsed FAR section."""
    part: str           # e.g., "91"
    subpart: str        # e.g., "B"
    section: str        # e.g., "91.103"
    title: str          # e.g., "Preflight action"
    text: str           # Full section text
    authority: str      # Legal authority citation

    @property
    def header_l1(self) -> str:
        return f"14 CFR Part {self.part}"

    @property
    def header_l2(self) -> str:
        return f"Subpart {self.subpart}" if self.subpart else f"Part {self.part}"

    @property
    def header_l3(self) -> str:
        return f"§{self.section} {self.title}"


class FARLoader:
    """Load and parse FAR regulations from eCFR."""

    # eCFR API base URL
    ECFR_API_URL = "https://www.ecfr.gov/api/versioner/v1/full"

    # Key parts for aviation safety
    RELEVANT_PARTS = ["1", "61", "91", "121", "135"]

    def __init__(self, data_dir: Path | None = None):
        settings = get_settings()
        self.data_dir = data_dir or settings.data_dir / "far"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def download_part(self, part: str) -> Path:
        """Download a specific FAR part from eCFR."""
        output_path = self.data_dir / f"part_{part}.xml"

        if output_path.exists():
            return output_path

        # eCFR API endpoint for Title 14
        url = f"{self.ECFR_API_URL}/2024-01-01/title-14.xml"
        params = {"part": part}

        print(f"Downloading 14 CFR Part {part}...")
        with httpx.Client(timeout=60) as client:
            response = client.get(url, params=params)
            response.raise_for_status()

        output_path.write_bytes(response.content)
        return output_path

    def load_part(self, part: str, xml_path: Path | None = None) -> Iterator[FARSection]:
        """Load and parse a FAR part from XML."""
        xml_path = xml_path or self.data_dir / f"part_{part}.xml"

        if not xml_path.exists():
            # Try downloading
            xml_path = self.download_part(part)

        tree = ElementTree.parse(xml_path)
        root = tree.getroot()

        # Parse sections from XML structure
        for section_elem in root.iter("SECTION"):
            yield self._parse_section(part, section_elem)

    def _parse_section(self, part: str, elem: ElementTree.Element) -> FARSection:
        """Parse an XML section element into FARSection."""
        # Extract section number from SECTNO element
        sectno_elem = elem.find("SECTNO")
        section = sectno_elem.text if sectno_elem is not None else ""

        # Extract title from SUBJECT element
        subject_elem = elem.find("SUBJECT")
        title = subject_elem.text if subject_elem is not None else ""

        # Extract full text from P elements
        paragraphs = []
        for p_elem in elem.findall(".//P"):
            if p_elem.text:
                paragraphs.append(p_elem.text.strip())

        text = "\n\n".join(paragraphs)

        # Try to determine subpart
        subpart = self._extract_subpart(section)

        # Extract authority if present
        auth_elem = elem.find(".//AUTH")
        authority = auth_elem.text if auth_elem is not None else ""

        return FARSection(
            part=part,
            subpart=subpart,
            section=section.replace("§", "").strip(),
            title=title,
            text=text,
            authority=authority,
        )

    def _extract_subpart(self, section: str) -> str:
        """Extract subpart letter from section number."""
        # Section numbers like 91.103 map to subparts
        # This is a simplified mapping - real implementation would use eCFR structure
        match = re.search(r"(\d+)\.(\d+)", section)
        if match:
            part, sec_num = match.groups()
            sec_num = int(sec_num)
            # Rough mapping (varies by part)
            if sec_num < 100:
                return "A"
            elif sec_num < 200:
                return "B"
            elif sec_num < 300:
                return "C"
            else:
                return ""
        return ""

    def load_all_parts(self) -> Iterator[FARSection]:
        """Load all relevant FAR parts."""
        for part in self.RELEVANT_PARTS:
            try:
                yield from self.load_part(part)
            except Exception as e:
                print(f"Error loading Part {part}: {e}")

    def to_documents(self, sections: Iterator[FARSection] | None = None) -> Iterator[dict]:
        """Convert FAR sections to documents for indexing."""
        sections = sections or self.load_all_parts()

        for section in sections:
            if not section.text:
                continue

            text = self._format_document_text(section)
            metadata = {
                "source": "far",
                "part": section.part,
                "subpart": section.subpart,
                "section": section.section,
                "title": section.title,
                "header_l1": section.header_l1,
                "header_l2": section.header_l2,
                "header_l3": section.header_l3,
            }

            yield {"id": section.section, "text": text, "metadata": metadata}

    def _format_document_text(self, section: FARSection) -> str:
        """Format section as readable document text."""
        parts = [
            f"# {section.header_l1}",
            f"## {section.header_l2}",
            f"### {section.header_l3}",
            "",
            section.text,
        ]

        if section.authority:
            parts.extend(["", f"Authority: {section.authority}"])

        return "\n".join(parts)

    def create_sample_data(self) -> None:
        """Create sample FAR data for demo purposes."""
        sample_sections = [
            FARSection(
                part="91",
                subpart="B",
                section="91.103",
                title="Preflight action",
                text="""Each pilot in command shall, before beginning a flight, become familiar with all available information concerning that flight. This information must include:

(a) For a flight under IFR or a flight not in the vicinity of an airport, weather reports and forecasts, fuel requirements, alternatives available if the planned flight cannot be completed, and any known traffic delays of which the pilot in command has been advised by ATC.

(b) For any flight, runway lengths at airports of intended use, and the following takeoff and landing distance information:
(1) For civil aircraft for which an approved Airplane or Rotorcraft Flight Manual containing takeoff and landing distance data is required, the takeoff and landing distance data contained therein.
(2) For civil aircraft other than those specified in paragraph (b)(1) of this section, other reliable information appropriate to the aircraft, relating to aircraft performance under expected values of airport elevation and runway slope, aircraft gross weight, and wind and temperature.""",
                authority="49 U.S.C. 106(f), 106(g), 40103, 40113, 40120, 44101, 44111, 44701, 44709, 44711, 44712, 44715, 44716, 44717, 44722, 46306, 46315, 46316, 46504, 46506-46507, 47122, 47508, 47528-47531, 47534"
            ),
            FARSection(
                part="91",
                subpart="B",
                section="91.155",
                title="Basic VFR weather minimums",
                text="""(a) Except as provided in paragraph (b) of this section and §91.157, no person may operate an aircraft under VFR when the flight visibility is less, or at a distance from clouds that is less, than that prescribed for the corresponding altitude and class of airspace in the following table:

Class B airspace: 3 statute miles visibility, clear of clouds.
Class C airspace: 3 statute miles visibility, 500 feet below, 1,000 feet above, 2,000 feet horizontal from clouds.
Class D airspace: 3 statute miles visibility, 500 feet below, 1,000 feet above, 2,000 feet horizontal from clouds.
Class E airspace (less than 10,000 feet MSL): 3 statute miles visibility, 500 feet below, 1,000 feet above, 2,000 feet horizontal from clouds.
Class E airspace (at or above 10,000 feet MSL): 5 statute miles visibility, 1,000 feet below, 1,000 feet above, 1 statute mile horizontal from clouds.
Class G airspace (1,200 feet or less above the surface, day): 1 statute mile visibility, clear of clouds.
Class G airspace (1,200 feet or less above the surface, night): 3 statute miles visibility, 500 feet below, 1,000 feet above, 2,000 feet horizontal from clouds.""",
                authority="49 U.S.C. 106(f), 106(g), 40103, 40113, 40120, 44101, 44111, 44701, 44709, 44711"
            ),
            FARSection(
                part="61",
                subpart="E",
                section="61.57",
                title="Recent experience: Pilot in command",
                text="""(a) General experience. (1) Except as provided in paragraph (e) of this section, no person may act as a pilot in command of an aircraft carrying passengers or of an aircraft certificated for more than one pilot flight crewmember unless that person has made at least three takeoffs and three landings within the preceding 90 days, and—
(i) The person acted as the sole manipulator of the flight controls; and
(ii) The required takeoffs and landings were performed in an aircraft of the same category, class, and type (if a type rating is required).

(c) Instrument experience. Except as provided in paragraph (e) of this section, a person may act as pilot in command under IFR or weather conditions less than the minimums prescribed for VFR only if:
(1) Use of an airplane, powered-lift, helicopter, or airship for maintaining instrument experience. Within the 6 calendar months preceding the month of the flight, that person performed and logged at least the following tasks and iterations in an airplane, powered-lift, helicopter, or airship, as appropriate, for the instrument rating privileges to be maintained in actual weather conditions, or under simulated conditions using a view-limiting device:
(i) Six instrument approaches.
(ii) Holding procedures and tasks.
(iii) Intercepting and tracking courses through the use of navigational electronic systems.""",
                authority="49 U.S.C. 106(f), 106(g), 40113, 44701-44703, 44707, 44709-44711, 44729, 44903, 45102-45103, 45301-45302"
            ),
        ]

        # Write sample data
        output_path = self.data_dir / "sample_far.txt"
        with open(output_path, "w") as f:
            for section in sample_sections:
                f.write(self._format_document_text(section))
                f.write("\n\n---\n\n")

        print(f"Sample FAR data created at {output_path}")

        # Also yield as documents
        for section in sample_sections:
            text = self._format_document_text(section)
            metadata = {
                "source": "far",
                "part": section.part,
                "subpart": section.subpart,
                "section": section.section,
                "title": section.title,
                "header_l1": section.header_l1,
                "header_l2": section.header_l2,
                "header_l3": section.header_l3,
            }
            yield {"id": section.section, "text": text, "metadata": metadata}


if __name__ == "__main__":
    from agentic_rag.data.indexers.vector_store import get_regulations_store

    loader = FARLoader()
    store = get_regulations_store()

    print("Creating sample FAR data and indexing to Qdrant...")
    docs = list(loader.create_sample_data())
    store.index_documents(iter(docs))
    print(f"Indexed {len(docs)} FAR regulations")

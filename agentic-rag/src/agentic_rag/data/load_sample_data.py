# load_sample_data.py
"""Load sample data into Qdrant for demo purposes."""

from agentic_rag.data.indexers.vector_store import (
    get_incidents_store,
    get_regulations_store,
    get_news_store,
)
from agentic_rag.models import SourceType


SAMPLE_INCIDENTS = [
    {
        "id": "ERA23FA001",
        "text": """# NTSB Accident Report: ERA23FA001
Date: 2023-01-15
Location: Atlanta, GA, USA

## Aircraft Information
Make/Model: Cessna 172S
Registration: N12345

## Conditions
Weather: VMC (Visual Meteorological Conditions)
Phase of Flight: Landing

## Injuries
Severity: Fatal
Fatal: 2, Serious: 0, Minor: 0

## Probable Cause
The pilot's failure to maintain adequate airspeed during the approach, which resulted in an aerodynamic stall and loss of control. Contributing factors included the pilot's lack of recent flight experience and failure to conduct a proper preflight assessment of weather conditions.

## Narrative
The aircraft was on approach to runway 27 when witnesses observed it flying unusually slow. The aircraft pitched nose down and impacted terrain approximately 500 feet short of the runway threshold. Investigation revealed the pilot had not flown in 4 months and had less than 200 total flight hours.""",
        "metadata": {
            "event_id": "ERA23FA001",
            "event_date": "2023-01-15",
            "header_l1": "NTSB Aviation Accidents",
            "header_l2": "General Aviation",
            "header_l3": "Cessna 172S - Stall/Spin",
            "location": "Atlanta, GA",
            "aircraft": "Cessna 172S",
            "registration": "N12345",
            "injury_severity": "Fatal",
            "weather_condition": "VMC",
            "phase_of_flight": "Landing",
        },
    },
    {
        "id": "WPR22LA002",
        "text": """# NTSB Accident Report: WPR22LA002
Date: 2022-06-20
Location: Phoenix, AZ, USA

## Aircraft Information
Make/Model: Piper PA-28-180
Registration: N67890

## Conditions
Weather: VMC
Phase of Flight: Takeoff

## Injuries
Severity: Minor
Fatal: 0, Serious: 0, Minor: 2

## Probable Cause
The pilot's inadequate preflight inspection, which resulted in a fuel exhaustion event during climb. The pilot failed to verify fuel quantity before departure despite the fuel gauges indicating less than half tanks.

## Narrative
Shortly after takeoff, the engine lost power at approximately 500 feet AGL. The pilot attempted to return to the airport but was unable to make the runway. The aircraft landed in a field, sustaining substantial damage. Post-accident examination revealed empty fuel tanks.""",
        "metadata": {
            "event_id": "WPR22LA002",
            "event_date": "2022-06-20",
            "header_l1": "NTSB Aviation Accidents",
            "header_l2": "General Aviation",
            "header_l3": "Piper PA-28 - Fuel Exhaustion",
            "location": "Phoenix, AZ",
            "aircraft": "Piper PA-28-180",
            "registration": "N67890",
            "injury_severity": "Minor",
            "weather_condition": "VMC",
            "phase_of_flight": "Takeoff",
        },
    },
    {
        "id": "CEN21FA003",
        "text": """# NTSB Accident Report: CEN21FA003
Date: 2021-11-30
Location: Chicago, IL, USA

## Aircraft Information
Make/Model: Beechcraft Bonanza A36
Registration: N33456

## Conditions
Weather: IMC (Instrument Meteorological Conditions)
Phase of Flight: Cruise

## Injuries
Severity: Fatal
Fatal: 4, Serious: 0, Minor: 0

## Probable Cause
The non-instrument-rated pilot's decision to continue VFR flight into instrument meteorological conditions, which resulted in spatial disorientation and loss of aircraft control. Contributing factors included inadequate preflight planning and the pilot's overconfidence in personal flying abilities.

## Narrative
The pilot filed a VFR flight plan for a cross-country flight. Weather briefing indicated deteriorating conditions along the route. Radar data showed the aircraft entered clouds and began erratic maneuvers before descending rapidly. The pilot held only a private pilot certificate with no instrument rating. The aircraft impacted terrain in a steep nose-down attitude.""",
        "metadata": {
            "event_id": "CEN21FA003",
            "event_date": "2021-11-30",
            "header_l1": "NTSB Aviation Accidents",
            "header_l2": "General Aviation",
            "header_l3": "Beechcraft Bonanza - VFR into IMC",
            "location": "Chicago, IL",
            "aircraft": "Beechcraft Bonanza A36",
            "registration": "N33456",
            "injury_severity": "Fatal",
            "weather_condition": "IMC",
            "phase_of_flight": "Cruise",
        },
    },
]

SAMPLE_REGULATIONS = [
    {
        "id": "91.103",
        "text": """# 14 CFR Part 91
## Subpart B
### §91.103 Preflight action

Each pilot in command shall, before beginning a flight, become familiar with all available information concerning that flight. This information must include:

(a) For a flight under IFR or a flight not in the vicinity of an airport, weather reports and forecasts, fuel requirements, alternatives available if the planned flight cannot be completed, and any known traffic delays of which the pilot in command has been advised by ATC.

(b) For any flight, runway lengths at airports of intended use, and the following takeoff and landing distance information:
(1) For civil aircraft for which an approved Airplane or Rotorcraft Flight Manual containing takeoff and landing distance data is required, the takeoff and landing distance data contained therein.
(2) For civil aircraft other than those specified in paragraph (b)(1) of this section, other reliable information appropriate to the aircraft, relating to aircraft performance under expected values of airport elevation and runway slope, aircraft gross weight, and wind and temperature.

Authority: 49 U.S.C. 106(f), 106(g), 40103, 40113, 40120, 44101, 44111, 44701, 44709, 44711""",
        "metadata": {
            "part": "91",
            "subpart": "B",
            "section": "91.103",
            "title": "Preflight action",
            "header_l1": "14 CFR Part 91",
            "header_l2": "Subpart B",
            "header_l3": "§91.103 Preflight action",
        },
    },
    {
        "id": "91.155",
        "text": """# 14 CFR Part 91
## Subpart B
### §91.155 Basic VFR weather minimums

(a) Except as provided in paragraph (b) of this section and §91.157, no person may operate an aircraft under VFR when the flight visibility is less, or at a distance from clouds that is less, than that prescribed for the corresponding altitude and class of airspace in the following table:

Class B airspace: 3 statute miles visibility, clear of clouds.
Class C airspace: 3 statute miles visibility, 500 feet below, 1,000 feet above, 2,000 feet horizontal from clouds.
Class D airspace: 3 statute miles visibility, 500 feet below, 1,000 feet above, 2,000 feet horizontal from clouds.
Class E airspace (less than 10,000 feet MSL): 3 statute miles visibility, 500 feet below, 1,000 feet above, 2,000 feet horizontal from clouds.
Class E airspace (at or above 10,000 feet MSL): 5 statute miles visibility, 1,000 feet below, 1,000 feet above, 1 statute mile horizontal from clouds.
Class G airspace (1,200 feet or less above the surface, day): 1 statute mile visibility, clear of clouds.
Class G airspace (1,200 feet or less above the surface, night): 3 statute miles visibility, 500 feet below, 1,000 feet above, 2,000 feet horizontal from clouds.

Authority: 49 U.S.C. 106(f), 106(g), 40103, 40113, 40120, 44101, 44111, 44701, 44709, 44711""",
        "metadata": {
            "part": "91",
            "subpart": "B",
            "section": "91.155",
            "title": "Basic VFR weather minimums",
            "header_l1": "14 CFR Part 91",
            "header_l2": "Subpart B",
            "header_l3": "§91.155 Basic VFR weather minimums",
        },
    },
    {
        "id": "61.57",
        "text": """# 14 CFR Part 61
## Subpart E
### §61.57 Recent experience: Pilot in command

(a) General experience. (1) Except as provided in paragraph (e) of this section, no person may act as a pilot in command of an aircraft carrying passengers or of an aircraft certificated for more than one pilot flight crewmember unless that person has made at least three takeoffs and three landings within the preceding 90 days, and—
(i) The person acted as the sole manipulator of the flight controls; and
(ii) The required takeoffs and landings were performed in an aircraft of the same category, class, and type (if a type rating is required).

(c) Instrument experience. Except as provided in paragraph (e) of this section, a person may act as pilot in command under IFR or weather conditions less than the minimums prescribed for VFR only if:
(1) Within the 6 calendar months preceding the month of the flight, that person performed and logged at least the following tasks in actual weather conditions, or under simulated conditions using a view-limiting device:
(i) Six instrument approaches.
(ii) Holding procedures and tasks.
(iii) Intercepting and tracking courses through the use of navigational electronic systems.

Authority: 49 U.S.C. 106(f), 106(g), 40113, 44701-44703, 44707, 44709-44711""",
        "metadata": {
            "part": "61",
            "subpart": "E",
            "section": "61.57",
            "title": "Recent experience: Pilot in command",
            "header_l1": "14 CFR Part 61",
            "header_l2": "Subpart E",
            "header_l3": "§61.57 Recent experience: Pilot in command",
        },
    },
]

SAMPLE_NEWS = [
    {
        "id": "news_001",
        "text": """# FAA Issues New Safety Directive on Preflight Inspections
Source: Aviation Weekly
Date: 2023-03-15

The Federal Aviation Administration has issued a new Safety Alert for Operators (SAFO) emphasizing the importance of thorough preflight inspections following a series of accidents attributed to inadequate preflight procedures.

The directive highlights several recent incidents where pilots failed to properly check fuel quantities, control surface freedom of movement, and overall aircraft airworthiness before flight. The FAA is urging all pilots to review and strictly adhere to the preflight checklist procedures outlined in their aircraft's Pilot Operating Handbook.

"We've seen a troubling pattern of accidents that could have been prevented with proper preflight procedures," said FAA Administrator John Smith. "This SAFO serves as a reminder that every flight begins with a thorough preflight inspection."

The SAFO specifically references 14 CFR 91.103, which requires pilots to become familiar with all available information concerning their flight before departure.""",
        "metadata": {
            "header_l1": "Aviation News",
            "header_l2": "FAA Safety Directives",
            "header_l3": "Preflight Inspection SAFO",
            "source_name": "Aviation Weekly",
            "publish_date": "2023-03-15",
        },
    },
    {
        "id": "news_002",
        "text": """# Study: VFR-into-IMC Remains Leading Cause of Fatal GA Accidents
Source: AOPA Pilot Magazine
Date: 2023-05-20

A comprehensive study by the Aircraft Owners and Pilots Association (AOPA) Air Safety Institute has confirmed that VFR flight into Instrument Meteorological Conditions (IMC) continues to be the leading cause of fatal general aviation accidents.

The study analyzed over 2,000 accidents over a 10-year period and found that VFR-into-IMC accidents account for approximately 4% of all general aviation accidents but represent nearly 20% of all fatalities. The survival rate for these accidents is less than 10%.

Key findings include:
- Most VFR-into-IMC accidents occur with non-instrument-rated pilots
- Pilots often ignore or underestimate adverse weather reports
- Spatial disorientation typically occurs within 3 minutes of entering clouds
- Go/no-go decision making is the most critical safety factor

The study recommends that all pilots, regardless of certification level, receive spatial disorientation training and practice instrument flying skills regularly.""",
        "metadata": {
            "header_l1": "Aviation News",
            "header_l2": "Safety Studies",
            "header_l3": "VFR into IMC Study",
            "source_name": "AOPA Pilot Magazine",
            "publish_date": "2023-05-20",
        },
    },
]


def load_all_sample_data():
    """Load all sample data into Qdrant."""
    print("Loading sample data into Qdrant...")

    # Load incidents
    print("\n--- Loading NTSB Incidents ---")
    incidents_store = get_incidents_store()
    incidents_store.index_documents(iter(SAMPLE_INCIDENTS))
    print(f"Indexed {len(SAMPLE_INCIDENTS)} incidents")

    # Load regulations
    print("\n--- Loading FAR Regulations ---")
    regulations_store = get_regulations_store()
    regulations_store.index_documents(iter(SAMPLE_REGULATIONS))
    print(f"Indexed {len(SAMPLE_REGULATIONS)} regulations")

    # Load news
    print("\n--- Loading News Articles ---")
    news_store = get_news_store()
    news_store.index_documents(iter(SAMPLE_NEWS))
    print(f"Indexed {len(SAMPLE_NEWS)} news articles")

    print("\n✅ All sample data loaded successfully!")
    print("You can now query the API at http://localhost:8000/api/query")


if __name__ == "__main__":
    load_all_sample_data()

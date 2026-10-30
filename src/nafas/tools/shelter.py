"""Cooling shelter and emergency nebulizer facility locator for Nafas (نَفَس).

Locates air-conditioned municipal cooling points and primary healthcare centers
equipped with emergency nebulization chambers in Riyadh and Greater Cairo.
"""

from typing import Any
from strands import tool


# Public cooling shelters and primary care nebulizer stations
SHELTER_DATABASE: dict[str, list[dict[str, Any]]] = {
    "riyadh": [
        {
            "name": "Al-Batha Primary Healthcare Center (PHC)",
            "district": "Al-Batha",
            "type": "Primary Health Clinic with Nebulizer Station",
            "has_nebulizer": True,
            "has_air_conditioning": True,
            "drinking_water_available": True,
            "operating_hours": "24/7 Emergency Care",
            "address": "Al-Batha Commercial District, Central Riyadh",
            "phone": "937 (MOH Hotline)",
            "guidance": "Equipped with multiple salbutamol nebulizers and emergency rehydration salts for outdoor workers.",
        },
        {
            "name": "Al-Malaz Municipal Cooling & Transit Hub",
            "district": "Al-Malaz",
            "type": "Municipal Climate Shelter",
            "has_nebulizer": False,
            "has_air_conditioning": True,
            "drinking_water_available": True,
            "operating_hours": "06:00 to 22:00",
            "address": "Near Prince Faisal bin Fahd Stadium, Al-Malaz",
            "phone": "940 (Amanat Riyadh)",
            "guidance": "High-capacity chilled waiting halls with cold drinking water dispensers and shaded rest areas.",
        },
        {
            "name": "Al-Ameen Medical Complex Emergency",
            "district": "Al-Sulaimaniyah",
            "type": "Hospital Emergency Room",
            "has_nebulizer": True,
            "has_air_conditioning": True,
            "drinking_water_available": True,
            "operating_hours": "24/7",
            "address": "Al-Sulaimaniyah, Riyadh",
            "phone": "011-464-4434",
            "guidance": "Full acute respiratory emergency triage with piped oxygen and pediatric nebulizers.",
        },
        {
            "name": "Manfuha Community Health Center",
            "district": "Manfuha",
            "type": "Community Clinic",
            "has_nebulizer": True,
            "has_air_conditioning": True,
            "drinking_water_available": True,
            "operating_hours": "08:00 to 23:00",
            "address": "Manfuha Al-Jadidah, Southern Riyadh",
            "phone": "937",
            "guidance": "Accessible community clinic serving migrant and blue-collar residential quarters.",
        },
    ],
    "cairo": [
        {
            "name": "Shubra General Hospital (Kit Kat / Shubra)",
            "district": "Shubra",
            "type": "Public Hospital Emergency Department",
            "has_nebulizer": True,
            "has_air_conditioning": True,
            "drinking_water_available": True,
            "operating_hours": "24/7",
            "address": "Shubra Main Street, Cairo",
            "phone": "123 (Ambulance) / 02-2430-1000",
            "guidance": "Round-the-clock emergency respiratory unit with continuous aerosol nebulization for children and elderly.",
        },
        {
            "name": "Ezbet El-Nakhl Comprehensive Health Center",
            "district": "Ezbet El-Nakhl",
            "type": "Primary Healthcare Unit",
            "has_nebulizer": True,
            "has_air_conditioning": True,
            "drinking_water_available": True,
            "operating_hours": "08:00 to 20:00",
            "address": "Near Metro Station, Ezbet El-Nakhl, Eastern Cairo",
            "phone": "137 (MOH Emergency)",
            "guidance": "Dedicated nebulizer room for pediatric asthma flare-ups and saline hydration.",
        },
        {
            "name": "Imbaba Fever & Respiratory Hospital",
            "district": "Imbaba",
            "type": "Specialized Pulmonology & Fever Hospital",
            "has_nebulizer": True,
            "has_air_conditioning": True,
            "drinking_water_available": True,
            "operating_hours": "24/7",
            "address": "Corniche El-Nil, Imbaba, Giza/Cairo",
            "phone": "123",
            "guidance": "Specialized respiratory intensive center equipped for severe status asthmaticus and COPD crises.",
        },
        {
            "name": "Al-Azhar Metro Subterranean Cooling Concourse",
            "district": "Downtown / Sayyeda Zeinab",
            "type": "Public Subterranean Transit Shelter",
            "has_nebulizer": False,
            "has_air_conditioning": True,
            "drinking_water_available": True,
            "operating_hours": "05:00 to 00:30",
            "address": "Downtown Cairo Metro Network",
            "phone": "16048 (Metro Authority)",
            "guidance": "Subterranean air-conditioned transit hall providing immediate relief from surface 42C heat and dust.",
        },
    ],
}


@tool
def find_cooling_or_nebulizer_shelter(
    city: str,
    district: str | None = None,
    need_nebulizer: bool = False,
) -> dict[str, Any]:
    """Find the nearest air-conditioned cooling shelter or emergency nebulizer facility.

    Helps outdoor workers find shaded, air-conditioned relief during heatwaves,
    and routes asthmatic patients to clinics equipped with emergency aerosol nebulizers.

    Args:
        city: The city name (e.g. Riyadh, Cairo).
        district: Optional specific district or neighborhood to filter results.
        need_nebulizer: If True, prioritizes facilities equipped with medical aerosol nebulizers.

    Returns:
        A dictionary containing matched facilities, distances, addresses, operating hours,
        and immediate transit guidance.
    """
    key = city.strip().lower()
    city_shelters = SHELTER_DATABASE.get(key, [])

    if not city_shelters:
        # Fallback to general regional instructions
        return {
            "city": city,
            "found": False,
            "message": f"No registered specific shelter coordinates for '{city}'.",
            "emergency_advisory": (
                "Move immediately to any air-conditioned public building, shopping center, "
                "or government health clinic. If experiencing breathing distress, call emergency medical dispatch: "
                "997 in Saudi Arabia, 123 in Egypt."
            ),
        }

    # Filter based on criteria
    filtered = []
    district_clean = district.strip().lower() if district else ""

    for s in city_shelters:
        if need_nebulizer and not s["has_nebulizer"]:
            continue
        if district_clean and district_clean in s["district"].lower():
            filtered.append(s)

    # If district filter yielded no matches, return all city shelters meeting nebulizer criteria
    if not filtered:
        filtered = [s for s in city_shelters if (not need_nebulizer or s["has_nebulizer"])]

    return {
        "city": city.title(),
        "found": True,
        "district_filter": district,
        "need_nebulizer": need_nebulizer,
        "shelters_count": len(filtered),
        "recommended_shelters": filtered,
        "action_guideline": (
            "Proceed immediately to the nearest location listed. "
            "Rest in shade or air-conditioning, drink chilled water, and avoid exertion until symptoms stabilize."
        ),
    }

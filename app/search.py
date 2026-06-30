"""Structured station search over the catalog.

Pure filtering used by the `find_chargers` tool. Kept separate from the tool
wrapper so it is testable without the LangChain stack.
"""

from __future__ import annotations

from typing import List, Optional

from .data import STATIONS
from .models import Connector, Station


def find_chargers(
    city: Optional[str] = None,
    min_power_kw: int = 0,
    connector: Optional[Connector] = None,
    amenity: Optional[str] = None,
    operator: Optional[str] = None,
) -> List[Station]:
    """Return catalog stations matching all provided filters, most powerful first."""
    results = []
    for station in STATIONS:
        if city and station.city.lower() != city.lower():
            continue
        if station.max_power_kw < min_power_kw:
            continue
        if connector and connector not in station.connectors:
            continue
        if amenity and amenity.lower() not in [a.lower() for a in station.amenities]:
            continue
        if operator and station.operator.lower() != operator.lower():
            continue
        results.append(station)
    return sorted(results, key=lambda s: s.max_power_kw, reverse=True)

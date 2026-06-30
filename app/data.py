"""Seed catalog of stations, city coordinates, and EV models.

In production this layer would be backed by the OCPI Locations module and a
TimescaleDB-backed live-status feed. Here it is an in-memory fixture so the
demo is fully self-contained and deterministic.
"""

from __future__ import annotations

from typing import Dict, List

from .models import Connector, Station

# City centroids used by the routing engine (lat, lon).
CITIES: Dict[str, tuple[float, float]] = {
    "Paris": (48.8566, 2.3522),
    "Lyon": (45.7640, 4.8357),
    "Bordeaux": (44.8378, -0.5792),
    "Nantes": (47.2184, -1.5536),
    "Dijon": (47.3220, 5.0415),
    "Clermont-Ferrand": (45.7772, 3.0870),
    "Brussels": (50.8503, 4.3517),
    "Lille": (50.6292, 3.0573),
}

# Simplified EV models: usable battery (kWh) and average consumption (kWh/100km).
EV_MODELS: Dict[str, tuple[float, float]] = {
    "Renault Megane E-Tech": (60.0, 16.5),
    "Tesla Model 3": (60.0, 14.0),
    "Peugeot e-208": (51.0, 15.5),
    "Hyundai Ioniq 5": (77.0, 17.0),
    "default": (60.0, 16.0),
}

DEFAULT_USABLE_RANGE_BUFFER_PCT = 10  # never plan to arrive below this SoC


def _s(  # noqa: PLR0913 - a fixture builder; explicit fields are clearest here
    sid: str,
    name: str,
    operator: str,
    city: str,
    lat: float,
    lon: float,
    power: int,
    connectors: List[Connector],
    tariff: float,
    amenities: List[str],
    points: int,
) -> Station:
    """Build one Station fixture (keeps the catalog below compact and readable)."""
    return Station(
        station_id=sid,
        name=name,
        operator=operator,
        city=city,
        lat=lat,
        lon=lon,
        max_power_kw=power,
        connectors=connectors,
        tariff_eur_per_kwh=tariff,
        amenities=amenities,
        num_points=points,
    )


_CCS = [Connector.CCS]
_CCS_T2 = [Connector.CCS, Connector.TYPE2]

STATIONS: List[Station] = [
    _s("ELEC-PAR-01", "Electra Paris Bercy", "Electra", "Paris", 48.8400, 2.3820, 300, _CCS_T2, 0.39, ["café", "toilets", "shopping"], 8),
    _s("ELEC-PAR-02", "Electra Paris La Défense", "Electra", "Paris", 48.8920, 2.2389, 400, _CCS, 0.42, ["café", "restaurant"], 6),
    _s("ELEC-AUX-01", "Electra Auxerre", "Electra", "Auxerre", 47.8000, 3.5700, 300, _CCS_T2, 0.37, ["café", "toilets"], 6),
    _s("ELEC-DIJ-01", "Electra Dijon Toison d'Or", "Electra", "Dijon", 47.3490, 5.0570, 300, _CCS_T2, 0.37, ["café", "supermarket", "toilets"], 8),
    _s("ELEC-ARR-01", "Electra Arras", "Electra", "Arras", 50.2900, 2.7800, 300, _CCS_T2, 0.38, ["café", "toilets"], 6),
    _s("ELEC-LYO-01", "Electra Lyon Part-Dieu", "Electra", "Lyon", 45.7610, 4.8590, 300, _CCS_T2, 0.40, ["café", "shopping", "toilets"], 10),
    _s("ELEC-CLF-01", "Electra Clermont Brezet", "Electra", "Clermont-Ferrand", 45.7900, 3.1500, 300, _CCS, 0.38, ["toilets"], 6),
    _s("ELEC-TRS-01", "Electra Tours Nord", "Electra", "Tours", 47.4200, 0.7000, 300, _CCS_T2, 0.38, ["café", "toilets"], 6),
    _s("ELEC-POI-01", "Electra Poitiers Sud", "Electra", "Poitiers", 46.5500, 0.3400, 300, _CCS, 0.38, ["restaurant", "toilets"], 6),
    _s("ELEC-ANG-01", "Electra Angoulême", "Electra", "Angoulême", 45.6500, 0.1600, 300, _CCS_T2, 0.39, ["café", "toilets"], 6),
    _s("ELEC-BDX-01", "Electra Bordeaux Lac", "Electra", "Bordeaux", 44.8830, -0.5560, 400, _CCS_T2, 0.39, ["café", "restaurant", "toilets"], 8),
    _s("ELEC-NTE-01", "Electra Nantes Atlantis", "Electra", "Nantes", 47.2230, -1.6300, 300, _CCS_T2, 0.38, ["shopping", "café"], 8),
    _s("ELEC-LIL-01", "Electra Lille Euralille", "Electra", "Lille", 50.6380, 3.0760, 300, _CCS_T2, 0.40, ["café", "shopping"], 8),
    _s("ELEC-BRU-01", "Electra Brussels Midi", "Electra", "Brussels", 50.8360, 4.3360, 400, _CCS, 0.43, ["café", "toilets"], 6),
    # Roaming partners (Spark Alliance) — reachable via OCPI, shown for interoperability.
    _s("IONI-MCN-01", "Ionity Mâcon", "Ionity", "Lyon", 46.3060, 4.8330, 350, _CCS, 0.59, ["restaurant", "toilets"], 6),
    _s("FAST-ORL-01", "Fastned Orléans", "Fastned", "Paris", 47.9020, 1.9090, 300, _CCS, 0.55, ["café", "toilets"], 8),
]


def stations_by_id() -> Dict[str, Station]:
    """Index the catalog by station_id for O(1) lookups."""
    return {s.station_id: s for s in STATIONS}

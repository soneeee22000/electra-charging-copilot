"""LangChain tools exposed to the agent.

Thin wrappers over the pure-Python core (search, live status, routing) and the
RAG retriever. Docstrings are written for the model — they are the tool's API
contract, so they are explicit about arguments and when to use each tool.
"""

from __future__ import annotations

from typing import List, Optional

from langchain_core.tools import tool

from .knowledge import retrieve
from .live import live_status
from .models import Connector
from .routing import plan_route
from .search import find_chargers


@tool
def find_charging_stations(
    city: Optional[str] = None,
    min_power_kw: int = 0,
    connector: Optional[str] = None,
    amenity: Optional[str] = None,
) -> str:
    """Find charging stations by city, minimum power (kW), connector (CCS/Type2/CHAdeMO)
    or amenity (e.g. café, restaurant, shopping, toilets, supermarket). Use this to
    answer "where can I charge" questions. Returns station id, name, power, tariff and amenities."""
    conn = None
    if connector:
        conn = _parse_connector(connector)
        if conn is None:
            known = ", ".join(c.value for c in Connector)
            return f"Unknown connector '{connector}'. Known connectors: {known}."
    stations = find_charging_stations_raw(city, min_power_kw, conn, amenity)
    if not stations:
        return "No matching stations found in the catalog."
    lines = [
        f"- {s.station_id} | {s.name} ({s.city}) | {s.max_power_kw} kW | "
        f"{s.tariff_eur_per_kwh:.2f} EUR/kWh | {', '.join(c.value for c in s.connectors)} | "
        f"amenities: {', '.join(s.amenities) or 'none'}"
        for s in stations
    ]
    return "\n".join(lines)


def _parse_connector(name: str) -> Optional[Connector]:
    """Match a connector name case-insensitively; None when it is not a known standard."""
    by_name = {c.value.lower(): c for c in Connector}
    return by_name.get(name.strip().lower())


def find_charging_stations_raw(city, min_power_kw, connector, amenity):  # type: ignore[no-untyped-def]
    """Untooled passthrough to the search core (kept for direct unit testing)."""
    return find_chargers(city=city, min_power_kw=min_power_kw, connector=connector, amenity=amenity)


@tool
def get_station_live_status(station_id: str) -> str:
    """Get the live availability of a station by its id (e.g. ELEC-PAR-01). Use this to
    check whether a station is operational and how many points are free RIGHT NOW before
    recommending it. Never guess availability — always call this tool."""
    st = live_status(station_id)
    if st.total_points == 0:
        return f"Unknown station id '{station_id}'."
    state = "operational" if st.is_operational else "OUT OF SERVICE"
    return (
        f"{station_id}: {state}, {st.available_points}/{st.total_points} points free "
        f"({'available now' if st.is_available else 'not available now'})."
    )


@tool
def plan_charging_route(
    origin: str,
    destination: str,
    current_battery_pct: int = 80,
    car_model: str = "default",
) -> str:
    """Plan an EV road trip between two cities, inserting fast-charge stops as needed.
    Provide origin and destination city names, the current battery percentage, and the car
    model if known (e.g. 'Tesla Model 3', 'Peugeot e-208', 'Hyundai Ioniq 5'). Returns each
    stop with arrival/depart charge, minutes, and cost, plus totals. Use for any trip/routing question."""
    plan = plan_route(origin, destination, current_battery_pct, car_model)
    if not plan.feasible:
        return f"Route not feasible: {plan.reason}"
    note = ""
    if plan.car_model != car_model:
        note = f"Note: car model '{car_model}' is not in the catalog; planned with the default profile.\n"
    if not plan.stops:
        return f"{note}{origin} to {destination} ({plan.total_distance_km} km): no charging stop needed."
    rows = [
        f"  {i+1}. {s.name} ({s.city}): arrive {s.arrive_battery_pct}% -> {s.depart_battery_pct}%, "
        f"+{s.added_kwh} kWh, ~{s.est_charge_minutes} min, ~{s.est_cost_eur:.2f} EUR"
        for i, s in enumerate(plan.stops)
    ]
    header = f"{origin} to {destination} ({plan.total_distance_km} km), {len(plan.stops)} stop(s):"
    totals = f"Totals: ~{plan.total_charge_minutes} min charging, ~{plan.total_cost_eur:.2f} EUR."
    return note + "\n".join([header, *rows, totals])


@tool
def search_charging_knowledge(query: str) -> str:
    """Search Electra's charging knowledge base (roaming, autocharge, Plug & Charge, pricing,
    idle fees, connectors, charging curve) for policy/FAQ context. Use this for "how does X work"
    questions about charging, not for specific station data."""
    passages = retrieve(query)
    return "\n".join(f"- {p}" for p in passages) if passages else "No relevant knowledge found."


def all_tools() -> List:  # type: ignore[type-arg]
    """Return the tool list bound to the agent."""
    return [find_charging_stations, get_station_live_status, plan_charging_route, search_charging_knowledge]

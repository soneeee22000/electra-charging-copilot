"""Tests for the dependency-light core: geo, search, live status, routing.

These run with no API key and no LLM/vector dependencies installed.
"""

from __future__ import annotations

from app.geo import haversine_km, progress_along_route
from app.live import live_status
from app.models import Connector
from app.routing import plan_route
from app.search import find_chargers


def test_haversine_paris_lyon_is_realistic() -> None:
    """Paris→Lyon great-circle should be ~390 km."""
    km = haversine_km(48.8566, 2.3522, 45.7640, 4.8357)
    assert 380 < km < 400


def test_progress_is_monotonic_along_route() -> None:
    """A point near the destination has higher progress than one near origin."""
    o, d = (48.8566, 2.3522), (45.7640, 4.8357)
    near_origin = progress_along_route(o, d, (48.5, 2.5))
    near_dest = progress_along_route(o, d, (46.0, 4.7))
    assert near_dest > near_origin


def test_find_chargers_filters_by_power_and_amenity() -> None:
    """High-power filter and amenity filter both apply."""
    results = find_chargers(min_power_kw=400)
    assert results and all(s.max_power_kw >= 400 for s in results)
    cafes = find_chargers(amenity="café")
    assert cafes and all("café" in s.amenities for s in cafes)


def test_find_chargers_connector_filter() -> None:
    """Type2 filter only returns stations exposing Type2."""
    results = find_chargers(connector=Connector.TYPE2)
    assert all(Connector.TYPE2 in s.connectors for s in results)


def test_live_status_is_deterministic() -> None:
    """Same id yields identical status across calls (reproducible demo)."""
    a = live_status("ELEC-PAR-01")
    b = live_status("ELEC-PAR-01")
    assert a == b
    assert a.total_points == 8


def test_short_trip_needs_no_charging() -> None:
    """A full battery over a short hop should be feasible with zero stops."""
    plan = plan_route("Paris", "Dijon", current_battery_pct=90, car_model="Tesla Model 3")
    assert plan.feasible
    assert plan.stops == []


def test_long_trip_inserts_stops_and_stays_above_buffer() -> None:
    """Paris→Bordeaux on a small battery must insert at least one stop."""
    plan = plan_route("Paris", "Bordeaux", current_battery_pct=80, car_model="Peugeot e-208")
    assert plan.feasible
    assert len(plan.stops) >= 1
    assert all(0 <= s.arrive_battery_pct < s.depart_battery_pct for s in plan.stops)
    assert plan.total_cost_eur > 0


def test_lower_start_charge_needs_at_least_as_many_stops() -> None:
    """Starting with less charge should never require fewer stops (SoC-aware)."""
    low = plan_route("Paris", "Bordeaux", current_battery_pct=30, car_model="Peugeot e-208")
    high = plan_route("Paris", "Bordeaux", current_battery_pct=90, car_model="Peugeot e-208")
    assert low.feasible and high.feasible
    assert len(low.stops) >= len(high.stops)


def test_unknown_city_is_infeasible_with_reason() -> None:
    """An unknown origin/destination returns a helpful infeasible reason."""
    plan = plan_route("Atlantis", "Paris", current_battery_pct=80, car_model="default")
    assert not plan.feasible
    assert "Unknown city" in (plan.reason or "")

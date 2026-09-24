"""Safety properties of the route planner, checked by independent re-simulation."""

from __future__ import annotations

import pytest

from app.data import CITIES, DEFAULT_USABLE_RANGE_BUFFER_PCT, EV_MODELS, stations_by_id
from app.geo import haversine_km
from app.routing import ROAD_FACTOR, plan_route

START_PCTS = range(10, 101, 10)
TOLERANCE_KWH = 1e-6


def _arrival_kwh(origin: str, destination: str, start_pct: int, car_model: str) -> float | None:
    """Re-drive a feasible plan leg by leg and return the energy left at the destination."""
    plan = plan_route(origin, destination, start_pct, car_model)
    if not plan.feasible:
        return None
    battery_kwh, consumption = EV_MODELS[car_model]
    catalog = stations_by_id()
    position = CITIES[origin]
    soc_kwh = battery_kwh * start_pct / 100
    for stop in plan.stops:
        station = catalog[stop.station_id]
        soc_kwh -= haversine_km(*position, station.lat, station.lon) * ROAD_FACTOR * consumption / 100
        soc_kwh = max(soc_kwh, battery_kwh * stop.depart_battery_pct / 100)
        position = (station.lat, station.lon)
    soc_kwh -= haversine_km(*position, *CITIES[destination]) * ROAD_FACTOR * consumption / 100
    return soc_kwh


def test_every_feasible_plan_reaches_destination_above_buffer() -> None:
    """No feasible plan may arrive at the destination below the safety buffer."""
    violations = []
    for origin in CITIES:
        for destination in CITIES:
            if origin == destination:
                continue
            for car_model, (battery_kwh, _) in EV_MODELS.items():
                buffer_kwh = battery_kwh * DEFAULT_USABLE_RANGE_BUFFER_PCT / 100
                for start_pct in START_PCTS:
                    arrival = _arrival_kwh(origin, destination, start_pct, car_model)
                    if arrival is not None and arrival < buffer_kwh - TOLERANCE_KWH:
                        violations.append((origin, destination, car_model, start_pct))
    assert violations == []


@pytest.mark.parametrize("start_pct", [-5, 101, 1000])
def test_out_of_range_start_charge_is_infeasible(start_pct: int) -> None:
    """A starting charge outside 0-100% is rejected instead of planned."""
    plan = plan_route("Paris", "Bordeaux", start_pct, "Peugeot e-208")
    assert not plan.feasible
    assert "battery" in (plan.reason or "").lower()


def test_unknown_car_model_is_reported_as_default_profile() -> None:
    """An unknown model is planned with the default profile and labelled as such."""
    plan = plan_route("Paris", "Lyon", 80, "Tesla Model Y")
    assert plan.car_model == "default"

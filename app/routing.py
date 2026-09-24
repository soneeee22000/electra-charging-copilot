"""EV-optimized route planning.

A deterministic, explainable greedy planner: at each step it drives to the
reachable CCS charger furthest along the route and charges to a fixed target,
never planning to arrive below a safety buffer. It uses the car's battery and
consumption, station power with a charging-curve derate, and each station's
tariff to price the stop; detour is only a filter on candidate stations. This
is the engine the LLM calls, so the model never does arithmetic about energy.
"""

from __future__ import annotations

from typing import List, Optional

from .data import CITIES, DEFAULT_USABLE_RANGE_BUFFER_PCT, EV_MODELS, STATIONS
from .geo import detour_km, haversine_km, progress_along_route
from .models import ChargeStop, Connector, RoutePlan, Station

ROAD_FACTOR = 1.20  # road distance vs great-circle
MAX_DETOUR_KM = 40.0  # reject stations that drag the route too far off-line
FAST_CHARGE_TARGET_PCT = 80  # charge to 80% to stay on the fast part of the curve
CAR_MAX_ACCEPT_KW = 150.0  # assumed peak DC acceptance for the demo fleet
CURVE_DERATE = 0.60  # session-average power as a fraction of peak


DEFAULT_CAR_MODEL = "default"
MIN_BATTERY_PCT = 0
MAX_BATTERY_PCT = 100


def _resolve_car_model(car_model: str) -> str:
    """Return the catalog profile name actually used for a requested model."""
    return car_model if car_model in EV_MODELS else DEFAULT_CAR_MODEL


def _infeasible(origin: str, destination: str, car_model: str, km: float, reason: str) -> RoutePlan:
    """Build an infeasible RoutePlan carrying a human-readable reason."""
    return RoutePlan(
        origin=origin, destination=destination, car_model=car_model,
        total_distance_km=km, feasible=False, reason=reason,
    )


def _candidates(origin: tuple[float, float], dest: tuple[float, float]) -> List[Station]:
    """Fast (CCS) stations near the corridor, ordered by progress along route."""
    usable = [
        s
        for s in STATIONS
        if Connector.CCS in s.connectors
        and detour_km(origin, dest, (s.lat, s.lon)) <= MAX_DETOUR_KM
    ]
    return sorted(usable, key=lambda s: progress_along_route(origin, dest, (s.lat, s.lon)))


def _make_stop(station: Station, arrive_kwh: float, battery_kwh: float, cons: float) -> ChargeStop:
    """Build a ChargeStop charging from arrive_kwh up to the fast-charge target."""
    arrive_pct = round(arrive_kwh / battery_kwh * 100)
    depart_pct = max(arrive_pct + 1, FAST_CHARGE_TARGET_PCT)  # a stop never lowers SoC
    target_kwh = battery_kwh * depart_pct / 100
    added = max(0.0, target_kwh - arrive_kwh)
    power = min(station.max_power_kw, CAR_MAX_ACCEPT_KW) * CURVE_DERATE
    minutes = round(added / power * 60) if power > 0 else 0
    cost = round(added * station.tariff_eur_per_kwh, 2)
    return ChargeStop(
        station_id=station.station_id,
        name=station.name,
        city=station.city,
        arrive_battery_pct=arrive_pct,
        depart_battery_pct=depart_pct,
        added_kwh=round(added, 1),
        est_charge_minutes=minutes,
        tariff_eur_per_kwh=station.tariff_eur_per_kwh,
        est_cost_eur=cost,
    )


def plan_route(origin: str, destination: str, current_battery_pct: int, car_model: str) -> RoutePlan:
    """Plan an EV route, inserting fast-charge stops only when needed.

    Returns a RoutePlan; `feasible=False` with a `reason` if the trip can't be
    completed with the known network (e.g. an unbridgeable gap) or the starting
    charge is outside 0-100%. An unknown car model is planned with, and reported
    as, the default profile.
    """
    car_model = _resolve_car_model(car_model)
    if origin not in CITIES or destination not in CITIES:
        unknown = origin if origin not in CITIES else destination
        known = ", ".join(sorted(CITIES))
        return _infeasible(origin, destination, car_model, 0.0, f"Unknown city '{unknown}'. Known: {known}.")
    if not MIN_BATTERY_PCT <= current_battery_pct <= MAX_BATTERY_PCT:
        return _infeasible(
            origin, destination, car_model, 0.0,
            f"Starting battery must be between {MIN_BATTERY_PCT} and {MAX_BATTERY_PCT}%.",
        )

    o, d = CITIES[origin], CITIES[destination]
    battery_kwh, cons = EV_MODELS[car_model]
    buffer_kwh = battery_kwh * DEFAULT_USABLE_RANGE_BUFFER_PCT / 100
    total_km = round(haversine_km(*o, *d) * ROAD_FACTOR, 1)

    soc_kwh = battery_kwh * current_battery_pct / 100
    pos, stops, used = o, [], set()

    while True:
        range_km = max(0.0, (soc_kwh - buffer_kwh) / cons * 100)
        if range_km >= haversine_km(*pos, *d) * ROAD_FACTOR:
            break  # can reach the destination from here above the buffer
        leg = _next_stop(pos, d, range_km, used)
        if leg is None:
            return _infeasible(
                origin, destination, car_model, total_km,
                "No reachable fast charger before the battery hits the safety buffer.",
            )
        station, leg_km = leg
        soc_kwh -= leg_km * cons / 100
        stop = _make_stop(station, soc_kwh, battery_kwh, cons)
        stops.append(stop)
        soc_kwh = max(soc_kwh, battery_kwh * stop.depart_battery_pct / 100)
        pos, used = (station.lat, station.lon), used | {station.station_id}

    return RoutePlan(
        origin=origin, destination=destination, car_model=car_model,
        total_distance_km=total_km, feasible=True, stops=stops,
        total_charge_minutes=sum(s.est_charge_minutes for s in stops),
        total_cost_eur=round(sum(s.est_cost_eur for s in stops), 2),
    )


def _next_stop(
    pos: tuple[float, float],
    dest: tuple[float, float],
    range_km: float,
    used: set[str],
) -> Optional[tuple[Station, float]]:
    """Pick the furthest-along reachable charger ahead of the current position.

    Returns (station, leg_distance_km) or None if nothing is reachable.
    """
    best: Optional[tuple[Station, float]] = None
    best_progress = -1.0
    for s in _candidates(pos, dest):
        if s.station_id in used:
            continue
        leg_km = haversine_km(*pos, s.lat, s.lon) * ROAD_FACTOR
        if leg_km > range_km or leg_km == 0:
            continue
        prog = progress_along_route(pos, dest, (s.lat, s.lon))
        if prog > best_progress:
            best, best_progress = (s, leg_km), prog
    return best

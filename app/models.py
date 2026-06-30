"""Typed domain models for the charging copilot.

Kept dependency-light (pydantic only) so the data/routing core imports without
the LLM stack. Field names mirror OCPI vocabulary where it makes sense
(connector standard, power, tariff) to stay credible to domain reviewers.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Connector(str, Enum):
    """EV connector standards relevant to ultra-fast charging in Europe."""

    CCS = "CCS"
    CHADEMO = "CHAdeMO"
    TYPE2 = "Type2"


class Station(BaseModel):
    """A charging station in the catalog (a simplified OCPI Location)."""

    station_id: str
    name: str
    operator: str = Field(description="CPO running the site; 'Electra' or a roaming partner")
    city: str
    lat: float
    lon: float
    max_power_kw: int
    connectors: List[Connector]
    tariff_eur_per_kwh: float
    amenities: List[str] = Field(default_factory=list)
    num_points: int


class LiveStatus(BaseModel):
    """Live availability for a station (a simplified OCPI EVSE status roll-up)."""

    station_id: str
    available_points: int
    total_points: int
    is_operational: bool

    @property
    def is_available(self) -> bool:
        """True when the site is operational and has at least one free point."""
        return self.is_operational and self.available_points > 0


class ChargeStop(BaseModel):
    """A planned charging stop produced by the routing engine."""

    station_id: str
    name: str
    city: str
    arrive_battery_pct: int
    depart_battery_pct: int
    added_kwh: float
    est_charge_minutes: int
    tariff_eur_per_kwh: float
    est_cost_eur: float


class RoutePlan(BaseModel):
    """The result of an EV-optimized route plan."""

    origin: str
    destination: str
    car_model: str
    total_distance_km: float
    feasible: bool
    reason: Optional[str] = None
    stops: List[ChargeStop] = Field(default_factory=list)
    total_charge_minutes: int = 0
    total_cost_eur: float = 0.0

"""FastAPI surface for the charging copilot.

Endpoints:
- GET  /healthz                 liveness
- GET  /stations                the catalog (structured, no LLM)
- GET  /stations/{id}/status    live availability (structured, no LLM)
- POST /route                   deterministic route plan (structured, no LLM)
- POST /chat                    the grounded LLM + RAG agent

The structured endpoints work with zero dependencies beyond FastAPI; /chat
requires the LLM stack and an ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import __version__
from .data import STATIONS
from .live import live_status
from .models import RoutePlan, Station
from .routing import plan_route

app = FastAPI(title="Electra Charging Copilot", version=__version__)
logger = logging.getLogger(__name__)

MAX_QUESTION_CHARS = 1000
MAX_CITY_CHARS = 64
MAX_CAR_MODEL_CHARS = 64


class ChatRequest(BaseModel):
    """A single natural-language question for the copilot."""

    question: str = Field(min_length=1, max_length=MAX_QUESTION_CHARS, examples=["Cheapest fast charger in Lyon with a café?"])


class ChatResponse(BaseModel):
    """The copilot's grounded answer."""

    answer: str


class RouteRequest(BaseModel):
    """Inputs for a route plan."""

    origin: str = Field(min_length=1, max_length=MAX_CITY_CHARS)
    destination: str = Field(min_length=1, max_length=MAX_CITY_CHARS)
    current_battery_pct: int = Field(default=80, ge=0, le=100)
    car_model: str = Field(default="default", max_length=MAX_CAR_MODEL_CHARS)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok", "version": __version__}


@app.get("/stations", response_model=list[Station])
def list_stations() -> list[Station]:
    """Return the full station catalog."""
    return STATIONS


@app.get("/stations/{station_id}/status")
def station_status(station_id: str) -> dict[str, object]:
    """Return live availability for one station."""
    status = live_status(station_id)
    if status.total_points == 0:
        raise HTTPException(status_code=404, detail=f"Unknown station '{station_id}'")
    return status.model_dump() | {"is_available": status.is_available}


@app.post("/route", response_model=RoutePlan)
def route(req: RouteRequest) -> RoutePlan:
    """Plan an EV route between two cities (deterministic, no LLM)."""
    return plan_route(req.origin, req.destination, req.current_battery_pct, req.car_model)


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    """Answer a natural-language question via the grounded LLM + RAG agent."""
    from .agent import ask  # lazy: only needs the LLM stack here

    try:
        return ChatResponse(answer=ask(req.question))
    except Exception as exc:  # log the cause server-side; clients get a generic 503
        logger.exception("chat agent failed")
        raise HTTPException(status_code=503, detail="Agent unavailable") from exc

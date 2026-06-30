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

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . import __version__
from .data import STATIONS
from .live import live_status
from .models import RoutePlan, Station
from .routing import plan_route

app = FastAPI(title="Electra Charging Copilot", version=__version__)


class ChatRequest(BaseModel):
    """A single natural-language question for the copilot."""

    question: str = Field(min_length=1, examples=["Cheapest fast charger in Lyon with a café?"])


class ChatResponse(BaseModel):
    """The copilot's grounded answer."""

    answer: str


class RouteRequest(BaseModel):
    """Inputs for a route plan."""

    origin: str
    destination: str
    current_battery_pct: int = 80
    car_model: str = "default"


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
    except Exception as exc:  # surface config/LLM errors as 503, don't 500 opaquely
        raise HTTPException(status_code=503, detail=f"Agent unavailable: {exc}") from exc

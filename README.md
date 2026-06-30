# Electra Charging Copilot 🔌

A grounded **LLM + RAG** conversational assistant for EV charging — built as a working reference for the _"soon: conversational interfaces with LLM and RAG"_ direction Electra names on its careers page.

> **The engineering thesis (the reason this exists):** an LLM should be the _interface_, never the _source of truth_. Every fact about a station, its live availability, a route, or a price comes from a **tool call or RAG retrieval over real data** — the model converses and explains, but it cannot invent charger data. That discipline is exactly what makes LLM features shippable in a domain where a hallucinated "available 350 kW charger" strands a driver.

Built with **FastAPI · LangGraph · Chroma · Claude**.

---

## What it does

Ask in natural language; the agent decides which tools to call and grounds its answer:

> _"I'm in Lyon with a Tesla Model 3 at 60%. Cheapest fast charger nearby with a café — and is it free right now?"_
> → `find_charging_stations(city=Lyon, amenity=café)` → `get_station_live_status(...)` → grounded answer.

> _"Can I drive Paris→Bordeaux in a Peugeot e-208 at 70%? Plan the stops and cost."_
> → `plan_charging_route(...)` → a real multi-stop plan (sample below).

> _"How does roaming work if I charge at a Fastned station on my Electra account?"_
> → `search_charging_knowledge(...)` (RAG) → grounded policy answer.

### Sample route-plan output (deterministic engine, no LLM)

```
Paris -> Bordeaux (599.2 km), 3 stop(s):
  1. Fastned Orléans (Paris):     arrive 29% -> 80%, +25.8 kWh, ~17 min, ~14.17 EUR
  2. Electra Poitiers Sud:        arrive 10% -> 80%, +35.6 kWh, ~24 min, ~13.53 EUR
  3. Electra Angoulême:           arrive 43% -> 80%, +18.8 kWh, ~13 min, ~7.33 EUR
Totals: ~54 min charging, ~35.03 EUR.
```

---

## Architecture

```
                          ┌──────────────────────────────────────┐
   "cheapest charger…" ──►│  LangGraph ReAct agent (Claude)       │
                          │  system prompt: NEVER invent data     │
                          └───────────────┬──────────────────────┘
                                          │ tool calls
        ┌─────────────────────┬───────────┼────────────────────┬───────────────────┐
        ▼                     ▼            ▼                    ▼                   ▼
 find_charging_stations  get_station_   plan_charging_route  search_charging_   (more tools…)
 (structured search)     live_status    (EV routing engine)  knowledge (RAG)
        │                  (mock OCPI)        │                  │
        ▼                     ▼               ▼                  ▼
   catalog (data.py)    live.py         routing.py          Chroma vector store
   = OCPI Locations    = OCPP/EVSE      = SoC-aware greedy   = station docs +
                         status roll-up   planner (geo.py)     policy/FAQ corpus
```

**Why this maps to Electra's real stack:**
| This repo | Electra reality |
|---|---|
| `data.py` catalog | OCPI **Locations** module |
| `live.py` status | **Network squad** real-time supervision (OCPP/EVSE over NATS) |
| `routing.py` | the **Navigation squad** EV-optimized routing problem |
| RAG over policy docs | help-centre / ops knowledge grounding |
| "tools = truth, LLM = interface" | how you ship LLM features without hallucinated charger data |

The **routing engine** (`routing.py`) is a deliberately explainable greedy planner: minimize stops while never dropping below a safety-buffer state-of-charge, accounting for battery + consumption, station power with a charging-curve derate, tariffs, and detour cost. It is the kind of constrained-optimization core an interviewer can interrogate on trade-offs.

---

## Run it

```bash
pip install -r requirements.txt
cp .env.example .env          # add your ANTHROPIC_API_KEY

# 1) HTTP API
uvicorn app.main:app --reload --port 8080
#   open http://localhost:8080/docs

# structured endpoints need no API key:
curl localhost:8080/stations
curl localhost:8080/stations/ELEC-PAR-01/status
curl -X POST localhost:8080/route -H 'content-type: application/json' \
     -d '{"origin":"Paris","destination":"Bordeaux","current_battery_pct":70,"car_model":"Peugeot e-208"}'

# the grounded agent (needs ANTHROPIC_API_KEY):
curl -X POST localhost:8080/chat -H 'content-type: application/json' \
     -d '{"question":"Cheapest fast charger in Lyon with a café, free right now?"}'

# 2) CLI demo reel
python -m scripts.demo
python -m scripts.demo "Can I reach Brussels from Paris at 50% in an Ioniq 5?"
```

## Test

```bash
pytest -m "not slow"   # core + API + tools, no network/key (16 tests)
pytest                 # + RAG retrieval (downloads a small embedding model once)
```

The pure-Python core (geo, routing, search, live) and the FastAPI endpoints are fully tested **without any API key**. The RAG retriever is tested against a real Chroma store.

---

## Design choices worth discussing (it grades _approach_, not result)

- **Grounding by construction.** The system prompt forbids invented data and the tools are the only source of facts — the failure mode "LLM makes up a charger" is designed out, not patched.
- **Deterministic core, probabilistic shell.** Routing, search, and live status are pure/deterministic and unit-tested; only the conversational layer is non-deterministic. You can verify correctness without paying for or flaking on model calls.
- **Lazy LLM imports.** `app/agent.py` and `app/knowledge.py` import the heavy stack lazily, so the data/routing core runs anywhere — and tests stay fast.
- **OCPI-shaped models.** Field names mirror the domain (connector standard, tariff, EVSE status) to stay credible and to make a real OCPI/OCPP backend a drop-in swap.
- **Operability first.** Structured endpoints are separate from `/chat` so health, catalog and routing keep working even if the model provider is down (`/chat` degrades to a clean 503).

## What I'd build next (honest backlog)

- **Price-aware routing**: the greedy planner minimizes stops; a second objective (cost vs time Pareto) would prefer cheaper Electra sites over pricier roaming partners.
- Swap the mock status for a **live OCPI feed**; back telemetry with **TimescaleDB** hypertables.
- Replace the in-process tools with **NATS** request/reply to real squad services.
- Add **streaming** responses and **eval** harness (faithfulness/grounding checks) before any production use.
- Persist the vector store and add real help-centre docs with citations in the answer.

---

_Part of an Electra Senior Software Engineer prep set. Companion: `../electra-interview-prep-pack.md`, `../electra-domain-glossary.md`, `../go-charger-ramp/`._

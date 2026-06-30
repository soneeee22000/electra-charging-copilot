# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/), versions follow [SemVer](https://semver.org/).

## [0.1.0] — 2026-06-30

### Added

- Grounded LLM + RAG charging copilot: LangGraph ReAct agent (Claude) over four tools — structured
  station search, mock OCPI/OCPP live status, SoC-aware route planner, and Chroma RAG knowledge.
- FastAPI service with keyless endpoints (`/healthz`, `/stations`, `/stations/{id}/status`, `/route`)
  and a key-gated `/chat` agent.
- Deterministic, explainable route-planning engine (`routing.py` + `geo.py`).
- Dark web UI (`ui.html`) and a same-origin demo server (`scripts/demo_server.py`).
- CLI demo reel (`scripts/demo.py`).
- 17-test pytest suite covering the core, the API, the tools and RAG retrieval.
- Dockerfile for containerized deployment.

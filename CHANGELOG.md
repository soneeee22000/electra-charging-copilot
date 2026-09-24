# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/), versions follow [SemVer](https://semver.org/).

## [Unreleased]

### Added

- GitHub Actions CI (actions pinned by commit SHA) running the full pytest suite on Python 3.11 and 3.12.
- `docs/WHY.md` with the problem statement and a "what this is not" list.
- README sections: Results (reproducible planner output), Limitations, independence and fixture-data notice.

### Fixed

- Route planner underestimated the remaining distance after an off-axis stop: on a grid of every city pair, car profile and start charge 0-100%, 1973 of 16782 feasible plans arrived below the 10% buffer (worst -18.7%). Remaining distance is now measured from the current position; the same grid gives 0 of 15932.
- Route planner rejects a start charge outside 0-100% and reports an unknown car model as the default profile it used.
- Station-search tool matches connectors case-insensitively and reports unknown connectors instead of ignoring the filter.
- `/route` and `/chat` validate input bounds; `/chat` no longer returns internal exception text in its 503.

### Changed

- README wording limited to what the code and tests show: grounding is prompt-enforced and unmeasured, availability is a mock, the planner is greedy with a fixed 80% charge target.
- `.gitignore` blocks AI tool working directories.

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

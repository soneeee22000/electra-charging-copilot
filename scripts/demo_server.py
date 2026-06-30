"""Demo launcher: serves the dark UI from the live FastAPI app, same-origin.

Run:  python -m scripts.demo_server   (then open http://localhost:8755/ui)

Adds a single GET /ui route that returns ui.html so the browser client and the
keyless API share an origin — no CORS needed. Does not modify the app package.
"""

from __future__ import annotations

from pathlib import Path

import uvicorn
from fastapi.responses import HTMLResponse

from app.main import app

_UI = Path(__file__).resolve().parent.parent / "ui.html"


@app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
def ui() -> str:
    """Serve the demo web client."""
    return _UI.read_text(encoding="utf-8")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8755)

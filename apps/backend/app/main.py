from __future__ import annotations

import traceback
import uuid

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import router
from app.core.config import get_settings
from app.core.errors import error_registry
from app.db.session import init_db
from app.ws.manager import ws_manager

settings = get_settings()

app = FastAPI(title="Gestion Satisfactory API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://localhost:{settings.frontend_port}", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.middleware("http")
async def unhandled_exception_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    try:
        return await call_next(request)
    except Exception as exc:  # pragma: no cover - framework guard
        trace_id = str(uuid.uuid4())
        stack = traceback.format_exc()
        payload = {
            "trace_id": trace_id,
            "error_type": type(exc).__name__,
            "message": str(exc),
            "stack": stack if settings.expose_tracebacks else None,
            "context": {"path": request.url.path, "method": request.method},
        }
        error_registry.store(trace_id, payload)
        return JSONResponse(status_code=500, content=payload)


static_root = settings.static_root
static_root.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_root), name="static")

app.include_router(router)


@app.websocket("/ws/scenarios/{scenario_id}")
async def scenario_socket(websocket: WebSocket, scenario_id: int) -> None:
    await ws_manager.connect(scenario_id, websocket)
    try:
        while True:
            # Keep alive and allow clients to send optional pings
            message = await websocket.receive_text()
            if message.lower() == "ping":
                await websocket.send_text('{"event_type":"pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(scenario_id, websocket)
    except Exception:
        ws_manager.disconnect(scenario_id, websocket)

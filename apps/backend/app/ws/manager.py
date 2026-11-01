from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket


class ScenarioConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, scenario_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[scenario_id].add(websocket)

    def disconnect(self, scenario_id: int, websocket: WebSocket) -> None:
        if scenario_id in self.active_connections:
            self.active_connections[scenario_id].discard(websocket)
            if not self.active_connections[scenario_id]:
                self.active_connections.pop(scenario_id, None)

    async def broadcast(self, scenario_id: int, payload: dict[str, Any]) -> None:
        sockets = list(self.active_connections.get(scenario_id, set()))
        for websocket in sockets:
            try:
                await websocket.send_text(json.dumps(payload))
            except Exception:
                self.disconnect(scenario_id, websocket)


def ws_event(
    scenario_id: int,
    entity_type: str,
    entity_id: int,
    action: str,
    new_version: int | None = None,
) -> dict[str, Any]:
    return {
        "event_type": "scenario.changed",
        "scenario_id": scenario_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "new_version": new_version,
        "changed_at": datetime.now(timezone.utc).isoformat(),
    }


ws_manager = ScenarioConnectionManager()

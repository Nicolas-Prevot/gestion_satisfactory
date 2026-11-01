from __future__ import annotations

import json


def test_websocket_receives_line_update_event(client, seed_ids):
    scenario_id = seed_ids["scenario_id"]
    line_id = seed_ids["line_id"]

    with client.websocket_connect(f"/ws/scenarios/{scenario_id}") as ws:
        response = client.patch(
            f"/api/v1/lines/{line_id}",
            json={"version": 1, "building_count": 2, "efficiency_multiplier": "1.0"},
        )
        assert response.status_code == 200

        message = json.loads(ws.receive_text())
        assert message["event_type"] == "scenario.changed"
        assert message["entity_type"] == "line"
        assert message["action"] == "updated"

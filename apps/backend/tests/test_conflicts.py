from __future__ import annotations


def test_line_optimistic_conflict(client, seed_ids):
    line_id = seed_ids["line_id"]

    first_update = {
        "version": 1,
        "building_count": 3,
        "efficiency_multiplier": "1.2",
    }
    first_resp = client.patch(f"/api/v1/lines/{line_id}", json=first_update)
    assert first_resp.status_code == 200

    stale_update = {
        "version": 1,
        "building_count": 4,
        "efficiency_multiplier": "1.1",
    }
    stale_resp = client.patch(f"/api/v1/lines/{line_id}", json=stale_update)
    assert stale_resp.status_code == 409

    payload = stale_resp.json()
    assert payload["error"] == "conflict"
    assert payload["entity"] == "line"
    assert "version" in payload["client"]
    assert "server" in payload

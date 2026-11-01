from __future__ import annotations


def test_balances_endpoint(client, seed_ids):
    response = client.get(f"/api/v1/scenarios/{seed_ids['scenario_id']}/balances")
    assert response.status_code == 200

    data = response.json()
    assert data["scope"] == "scenario"
    assert data["power_mw"] == "12"

    outputs = {entry["item_name"]: entry for entry in data["outputs"]}
    inputs = {entry["item_name"]: entry for entry in data["inputs"]}
    intermediates = {entry["item_name"]: entry for entry in data["intermediates"]}

    assert "Iron Plate" in outputs
    assert outputs["Iron Plate"]["net_rate"] == "10"
    assert "Iron Ore" in inputs
    assert inputs["Iron Ore"]["net_rate"] == "-60"
    assert "Iron Ingot" in intermediates

from __future__ import annotations


def test_optimizer_optimal(client):
    payload = {
        "max_tier": 0,
        "selected_products": [{"item_name": "Iron Plate", "quantity": "10"}],
        "available_items": {},
        "raw_weights": {"Iron Ore": "1"},
        "raw_limits": {"Iron Ore": "1000"},
    }

    response = client.post("/api/v1/optimizer/solve", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "Optimal"
    assert len(data["recipes"]) >= 2
    materials = {m["item_name"]: m["net_rate"] for m in data["materials"]}
    assert "Iron Ore" in materials
    buildings = {b["building_name"]: b["count"] for b in data["buildings"]}
    assert buildings["Smelter"] == "1"
    assert buildings["Constructor"] == "1"
    smelter_row = next(recipe for recipe in data["recipes"] if recipe["building_name"] == "Smelter")
    assert smelter_row["nb_building"] == "0.666667"
    assert "per_building_rate" in smelter_row["outputs"][0]
    assert "total_rate" in smelter_row["outputs"][0]

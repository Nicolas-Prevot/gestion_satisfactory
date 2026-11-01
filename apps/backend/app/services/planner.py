from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.utils import decimal_to_string, resolve_image_url
from app.models.entities import Building, Item, Line, Recipe

settings = get_settings()


def _image_map(db: Session) -> dict[str, str | None]:
    items = db.query(Item).all()
    return {
        item.name: resolve_image_url(
            item.image_local_path,
            settings.static_root,
        )
        for item in items
    }


def _building_power_map(db: Session) -> dict[str, dict[str, float | None]]:
    buildings = db.query(Building).all()
    return {
        b.name: {
            "power_usage": b.power_usage,
            "min_consumption": b.min_consumption,
            "max_consumption": b.max_consumption,
        }
        for b in buildings
    }


def _line_recipe_rate(recipe: Recipe, amount: float | None, building_count: int, efficiency: float) -> float:
    if amount is None or recipe.duration <= 0:
        return 0.0
    return (60 * amount / recipe.duration) * building_count * efficiency


def compute_balances(
    db: Session,
    scenario_id: int,
    area_id: int | None = None,
    factory_id: int | None = None,
) -> dict[str, Any]:
    query = db.query(Line).filter(Line.scenario_id == scenario_id)
    if area_id is not None:
        query = query.filter(Line.area_id == area_id)
    if factory_id is not None:
        query = query.filter(Line.factory_id == factory_id)

    lines = query.all()
    item_images = _image_map(db)
    building_power = _building_power_map(db)

    production: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    consumption: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    power_total = Decimal("0")

    for line in lines:
        recipe = line.recipe
        efficiency = float(line.efficiency_multiplier)
        for i in range(1, 3):
            item_name = getattr(recipe, f"product_{i}")
            amount = getattr(recipe, f"product_amount_{i}")
            if item_name:
                rate = Decimal(str(_line_recipe_rate(recipe, amount, line.building_count, efficiency)))
                production[item_name] += rate

        for i in range(1, 5):
            item_name = getattr(recipe, f"ingredient_{i}")
            amount = getattr(recipe, f"ingredient_amount_{i}")
            if item_name:
                rate = Decimal(str(_line_recipe_rate(recipe, amount, line.building_count, efficiency)))
                consumption[item_name] += rate

        power_info = building_power.get(recipe.building_name, {})
        if power_info.get("power_usage") is not None:
            power_total += Decimal(str(power_info["power_usage"])) * line.building_count * Decimal(str(efficiency))
        elif recipe.min_consumption is not None and recipe.max_consumption is not None:
            avg = Decimal(str((recipe.min_consumption + recipe.max_consumption) / 2))
            power_total += avg * line.building_count * Decimal(str(efficiency))

    all_items = set(production.keys()) | set(consumption.keys())
    outputs: list[dict[str, Any]] = []
    inputs: list[dict[str, Any]] = []
    intermediates: list[dict[str, Any]] = []

    for item in all_items:
        produced = production.get(item, Decimal("0"))
        consumed = consumption.get(item, Decimal("0"))
        net = produced - consumed
        entry = {
            "item_name": item,
            "net_rate": decimal_to_string(net),
            "produced_rate": decimal_to_string(produced),
            "consumed_rate": decimal_to_string(consumed),
            "image_url": item_images.get(item),
        }
        if produced > 0 and consumed > 0:
            intermediates.append(entry)
        elif net >= 0:
            outputs.append(entry)
        else:
            inputs.append(entry)

    outputs.sort(key=lambda x: abs(Decimal(x["net_rate"])), reverse=True)
    inputs.sort(key=lambda x: abs(Decimal(x["net_rate"])), reverse=True)
    intermediates.sort(key=lambda x: abs(Decimal(x["net_rate"])), reverse=True)

    scope = "scenario"
    scope_id = scenario_id
    if factory_id is not None:
        scope = "factory"
        scope_id = factory_id
    elif area_id is not None:
        scope = "area"
        scope_id = area_id

    return {
        "scope": scope,
        "scope_id": scope_id,
        "power_mw": decimal_to_string(power_total),
        "outputs": outputs,
        "inputs": inputs,
        "intermediates": intermediates,
    }

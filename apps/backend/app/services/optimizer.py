from __future__ import annotations

from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
import math
from typing import Any

import numpy as np
import pandas as pd
from pulp import LpMinimize, LpProblem, LpStatus, LpVariable, lpSum
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.utils import resolve_image_url
from app.models.entities import Building, Item, Recipe
from app.schemas.optimizer import OptimizerSolveRequest
from app.services.defaults import raw_materials_1, raw_materials_2, raw_materials_limit_1, raw_materials_limit_2

settings = get_settings()
SIX_DECIMALS = Decimal("0.000001")
INTEGER_EPSILON = Decimal("0.000001")


def extract_tier(unlocked_by: str | None) -> int:
    if not unlocked_by:
        return 0
    if "Tier" not in unlocked_by:
        return 0
    try:
        return int(unlocked_by.split("Tier")[1].split()[0])
    except Exception:
        return 0


def remove_uncraftable_rows(
    df_recipes: pd.DataFrame,
    raw_1: dict[str, float],
    raw_2: dict[str, float],
    lim_1: dict[str, float],
    lim_2: dict[str, float],
) -> tuple[dict[str, float], dict[str, float], dict[str, float], dict[str, float], pd.DataFrame, set[str]]:
    ingredients = set(df_recipes[[f"ingredient_{k}" for k in range(1, 5)]].values.flatten()) - {np.nan, None}
    products = set(df_recipes[[f"product_{k}" for k in range(1, 3)]].values.flatten()) - {np.nan, None}

    raw_1 = {k: v for k, v in raw_1.items() if k in ingredients}
    raw_2 = {k: v for k, v in raw_2.items() if k in ingredients}
    lim_1 = {k: v for k, v in lim_1.items() if k in ingredients}
    lim_2 = {k: v for k, v in lim_2.items() if k in ingredients}

    uncraftable = (ingredients - products) - (set(raw_1) | set(raw_2))

    def row_valid(row: pd.Series) -> bool:
        row_ings = [row[f"ingredient_{k}"] for k in range(1, 5) if pd.notnull(row[f"ingredient_{k}"])]
        return all(ing not in uncraftable for ing in row_ings)

    return raw_1, lim_1, raw_2, lim_2, df_recipes[df_recipes.apply(row_valid, axis=1)].copy(), uncraftable


def _build_meta_maps(db: Session) -> tuple[dict[str, str | None], dict[str, str | None]]:
    item_map = {
        i.name: resolve_image_url(
            i.image_local_path,
            settings.static_root,
        )
        for i in db.query(Item).all()
    }
    bld_map = {
        b.name: resolve_image_url(
            b.image_local_path,
            settings.static_root,
        )
        for b in db.query(Building).all()
    }
    return item_map, bld_map


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(parsed) or math.isinf(parsed):
        return default
    return parsed


def _safe_decimal_from_rate(rate: float) -> Decimal | None:
    if math.isnan(rate) or math.isinf(rate):
        return None
    return Decimal(str(rate))


def _format_optimizer_number(value: Decimal | float | int) -> str:
    dec_value = value if isinstance(value, Decimal) else Decimal(str(value))
    nearest_int = dec_value.to_integral_value(rounding=ROUND_HALF_UP)
    if abs(dec_value - nearest_int) <= INTEGER_EPSILON:
        return str(int(nearest_int))
    rounded = dec_value.quantize(SIX_DECIMALS, rounding=ROUND_HALF_UP)
    if rounded == Decimal("-0"):
        rounded = Decimal("0")
    text = format(rounded, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text if text else "0"


def _optimize(
    df_recipes: pd.DataFrame,
    raw_items: list[str],
    raw_weights: dict[str, float],
    raw_limits: dict[str, float],
    not_raw_items: list[str],
    selected_products: dict[str, float],
    available_items: dict[str, float],
) -> tuple[dict[str, float], dict[str, str], str]:
    df_recipes = df_recipes.copy().reset_index(drop=True)
    df_recipes["recipe"] = df_recipes.index

    ingredients_list = []
    for k in range(1, 5):
        df = df_recipes[["recipe", "duration", f"ingredient_{k}", f"ingredient_amount_{k}"]].copy()
        df.columns = ["recipe", "duration", "item", "amount"]
        df = df.dropna(subset=["item"])
        df["amount"] = -60 * df["amount"] / df["duration"]
        ingredients_list.append(df)
    ingredients_long = pd.concat(ingredients_list, ignore_index=True) if ingredients_list else pd.DataFrame()

    products_list = []
    for k in range(1, 3):
        df = df_recipes[["recipe", "duration", f"product_{k}", f"product_amount_{k}"]].copy()
        df.columns = ["recipe", "duration", "item", "amount"]
        df = df.dropna(subset=["item"])
        df["amount"] = 60 * df["amount"] / df["duration"]
        products_list.append(df)
    products_long = pd.concat(products_list, ignore_index=True) if products_list else pd.DataFrame()

    transactions = pd.concat([ingredients_long, products_long], ignore_index=True)
    net_amounts = transactions.groupby(["item", "recipe"])["amount"].sum().unstack(fill_value=0)

    recipes_idx = df_recipes["recipe"].tolist()
    R_items = list(not_raw_items)
    Rp_items = list(raw_items)

    net_amounts = net_amounts.reindex(columns=recipes_idx, fill_value=0)
    R = net_amounts.reindex(R_items, fill_value=0).values if R_items else np.empty((0, len(recipes_idx)))
    Rp = net_amounts.reindex(Rp_items, fill_value=0).values if Rp_items else np.empty((0, len(recipes_idx)))

    prob = LpProblem("combination_recipes", LpMinimize)
    lambdas = LpVariable.dicts("Recipe", recipes_idx, cat="Continuous", lowBound=0)

    objective_terms = []
    for i, raw_item in enumerate(Rp_items):
        weight = raw_weights.get(raw_item, 0)
        consumption = -lpSum([Rp[i, idx - recipes_idx[0]] * lambdas[idx] for idx in recipes_idx])
        objective_terms.append(weight * consumption)
    prob += lpSum(objective_terms)

    for i, item in enumerate(R_items):
        net_rate = lpSum([R[i, idx - recipes_idx[0]] * lambdas[idx] for idx in recipes_idx])
        selected_target = selected_products.get(item)
        available_qty = available_items.get(item, 0)
        if selected_target is not None:
            prob += net_rate >= max(selected_target - available_qty, 0)
        else:
            prob += net_rate >= -available_qty

    for i, item in enumerate(Rp_items):
        net_rate = lpSum([Rp[i, idx - recipes_idx[0]] * lambdas[idx] for idx in recipes_idx])
        prob += net_rate >= -raw_limits.get(item, 0)
        prob += net_rate <= 0

    status = prob.solve()
    recipe_vars = {v.name: (v.varValue or 0.0) for v in prob.variables()}
    recipe_var_to_name = {
        v.name: df_recipes.at[int(v.name.split("_")[-1]), "recipe_name"] for v in prob.variables()
    }
    return recipe_vars, recipe_var_to_name, LpStatus[status]


def solve_optimizer(db: Session, payload: OptimizerSolveRequest) -> dict[str, Any]:
    recipes = db.query(Recipe).all()
    buildings = db.query(Building).all()
    if not recipes:
        return {
            "status": "NoData",
            "recipes": [],
            "materials": [],
            "buildings": [],
            "graph_nodes": [],
            "graph_edges": [],
        }

    df_recipes = pd.DataFrame([
        {
            "id": r.id,
            "building_name": r.building_name,
            "recipe_name": r.recipe_name,
            "recipe_alternate": r.recipe_alternate,
            "duration": r.duration,
            "unlocked_by": r.unlocked_by,
            "tier": r.tier,
            "min_consumption": r.min_consumption,
            "max_consumption": r.max_consumption,
            **{f"ingredient_{i}": getattr(r, f"ingredient_{i}") for i in range(1, 5)},
            **{f"ingredient_amount_{i}": getattr(r, f"ingredient_amount_{i}") for i in range(1, 5)},
            **{f"product_{i}": getattr(r, f"product_{i}") for i in range(1, 3)},
            **{f"product_amount_{i}": getattr(r, f"product_amount_{i}") for i in range(1, 3)},
        }
        for r in recipes
    ])

    df_buildings = pd.DataFrame([
        {"name": b.name, "tier": b.tier, "power_usage": b.power_usage, "min_consumption": b.min_consumption, "max_consumption": b.max_consumption}
        for b in buildings
    ])

    max_tier = payload.max_tier
    if "tier" not in df_recipes.columns:
        df_recipes["tier"] = df_recipes["unlocked_by"].apply(extract_tier)
    df_recipes = df_recipes[df_recipes["tier"] <= max_tier].copy()

    unreachable = set(df_buildings[df_buildings["tier"] > max_tier]["name"].tolist()) if not df_buildings.empty else set()
    if unreachable:
        df_recipes = df_recipes[~df_recipes["building_name"].isin(unreachable)]

    product_cols = ["product_1", "product_2"]
    df_recipes = df_recipes[
        ~(
            (df_recipes["building_name"] == "Packager")
            & (df_recipes[product_cols].eq("Empty Canister").any(axis=1))
        )
    ]

    w1 = dict(raw_materials_1)
    w2 = dict(raw_materials_2)
    l1 = dict(raw_materials_limit_1)
    l2 = dict(raw_materials_limit_2)

    for key, value in payload.raw_weights.items():
        if key in w1:
            w1[key] = _safe_float(value, w1[key])
        elif key in w2:
            w2[key] = _safe_float(value, w2[key])

    for key, value in payload.raw_limits.items():
        if key in l1:
            l1[key] = _safe_float(value, l1[key])
        elif key in l2:
            l2[key] = _safe_float(value, l2[key])

    raw_1, lim_1, raw_2, lim_2, df_recipes, uncraftable = remove_uncraftable_rows(df_recipes, w1, w2, l1, l2)
    while uncraftable:
        raw_1, lim_1, raw_2, lim_2, df_recipes, uncraftable = remove_uncraftable_rows(df_recipes, raw_1, raw_2, lim_1, lim_2)

    raw_items = list(raw_1.keys()) + list(raw_2.keys())
    not_raw_set = (
        set(df_recipes[[f"ingredient_{k}" for k in range(1, 5)]].values.flatten())
        | set(df_recipes[[f"product_{k}" for k in range(1, 3)]].values.flatten())
    ) - {np.nan, None}
    not_raw_items = sorted(list(not_raw_set - set(raw_items)))

    selected_products = {}
    for entry in payload.selected_products:
        qty = _safe_float(entry.quantity, 0.0)
        if qty > 0:
            selected_products[entry.item_name] = qty

    available_items = {k: _safe_float(v, 0.0) for k, v in payload.available_items.items()}

    weights = raw_1 | {k: v * 1000 for k, v in raw_2.items()}
    limits = lim_1 | lim_2

    recipe_vars, var_to_name, status = _optimize(
        df_recipes=df_recipes,
        raw_items=raw_items,
        raw_weights=weights,
        raw_limits=limits,
        not_raw_items=not_raw_items,
        selected_products=selected_products,
        available_items=available_items,
    )

    item_map, building_map = _build_meta_maps(db)

    if status != "Optimal":
        return {
            "status": status,
            "recipes": [],
            "materials": [],
            "buildings": [],
            "graph_nodes": [],
            "graph_edges": [],
        }

    recipes_out: list[dict[str, Any]] = []
    materials: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    building_counts: dict[str, int] = defaultdict(int)
    graph_nodes: list[dict[str, Any]] = []
    graph_edges: list[dict[str, Any]] = []
    seen_nodes: set[str] = set()

    for var_name, amount in recipe_vars.items():
        if amount < 1e-5:
            continue
        recipe_name = var_to_name[var_name]
        row = df_recipes[df_recipes["recipe_name"] == recipe_name]
        if row.empty:
            continue
        r = row.iloc[0]
        building_counts[r["building_name"]] += int(math.ceil(max(amount, 0.0) - 1e-9))

        recipe_outputs = []
        recipe_inputs = []
        recipe_node_id = f"recipe::{int(r['id'])}"
        if recipe_node_id not in seen_nodes:
            graph_nodes.append(
                {
                    "id": recipe_node_id,
                    "label": recipe_name,
                    "kind": "recipe",
                    "image_url": building_map.get(r["building_name"]),
                }
            )
            seen_nodes.add(recipe_node_id)

        for i in range(1, 3):
            p_name = r[f"product_{i}"]
            p_amount = r[f"product_amount_{i}"]
            duration = _safe_float(r["duration"], 0.0)
            if p_name and pd.notna(p_amount) and duration > 0:
                per_building_rate_float = 60 * _safe_float(p_amount, 0.0) / duration
                total_rate_float = per_building_rate_float * amount
                per_building_rate = _safe_decimal_from_rate(per_building_rate_float)
                total_rate = _safe_decimal_from_rate(total_rate_float)
                if per_building_rate is None or total_rate is None:
                    continue
                materials[p_name] += total_rate
                recipe_outputs.append(
                    {
                        "item_name": p_name,
                        "rate": _format_optimizer_number(total_rate),
                        "per_building_rate": _format_optimizer_number(per_building_rate),
                        "total_rate": _format_optimizer_number(total_rate),
                        "image_url": item_map.get(p_name),
                    }
                )
                node_id = f"item::{p_name}"
                if node_id not in seen_nodes:
                    graph_nodes.append(
                        {"id": node_id, "label": p_name, "kind": "item", "image_url": item_map.get(p_name)}
                    )
                    seen_nodes.add(node_id)
                graph_edges.append(
                    {
                        "id": f"{recipe_node_id}->{node_id}:{i}",
                        "source": recipe_node_id,
                        "target": node_id,
                        "label": _format_optimizer_number(total_rate),
                    }
                )

        for i in range(1, 5):
            ing_name = r[f"ingredient_{i}"]
            ing_amount = r[f"ingredient_amount_{i}"]
            duration = _safe_float(r["duration"], 0.0)
            if ing_name and pd.notna(ing_amount) and duration > 0:
                per_building_rate_float = 60 * _safe_float(ing_amount, 0.0) / duration
                total_rate_float = per_building_rate_float * amount
                per_building_rate = _safe_decimal_from_rate(per_building_rate_float)
                total_rate = _safe_decimal_from_rate(total_rate_float)
                if per_building_rate is None or total_rate is None:
                    continue
                materials[ing_name] -= total_rate
                recipe_inputs.append(
                    {
                        "item_name": ing_name,
                        "rate": _format_optimizer_number(total_rate),
                        "per_building_rate": _format_optimizer_number(per_building_rate),
                        "total_rate": _format_optimizer_number(total_rate),
                        "image_url": item_map.get(ing_name),
                    }
                )
                node_id = f"item::{ing_name}"
                if node_id not in seen_nodes:
                    graph_nodes.append(
                        {"id": node_id, "label": ing_name, "kind": "item", "image_url": item_map.get(ing_name)}
                    )
                    seen_nodes.add(node_id)
                graph_edges.append(
                    {
                        "id": f"{node_id}->{recipe_node_id}:{i}",
                        "source": node_id,
                        "target": recipe_node_id,
                        "label": _format_optimizer_number(total_rate),
                    }
                )

        recipes_out.append(
            {
                "recipe_id": int(r["id"]),
                "recipe_name": recipe_name,
                "building_name": r["building_name"],
                "building_image_url": building_map.get(r["building_name"]),
                "nb_building": _format_optimizer_number(amount),
                "efficiency_multiplier": "1",
                "outputs": recipe_outputs,
                "inputs": recipe_inputs,
            }
        )

    material_out = []
    for item, value in materials.items():
        try:
            if abs(value) <= Decimal("0.0001"):
                continue
        except Exception:
            continue
        material_out.append(
            {
                "item_name": item,
                "net_rate": _format_optimizer_number(value),
                "image_url": item_map.get(item),
            }
        )
    material_out.sort(key=lambda x: abs(Decimal(x["net_rate"])), reverse=True)

    buildings_out = [
        {"building_name": name, "count": str(count), "image_url": building_map.get(name)}
        for name, count in building_counts.items()
    ]
    buildings_out.sort(key=lambda x: int(x["count"]), reverse=True)

    recipes_out.sort(key=lambda x: Decimal(x["nb_building"]), reverse=True)

    return {
        "status": status,
        "recipes": recipes_out,
        "materials": material_out,
        "buildings": buildings_out,
        "graph_nodes": graph_nodes,
        "graph_edges": graph_edges,
    }

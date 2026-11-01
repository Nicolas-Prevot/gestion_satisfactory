from __future__ import annotations

from typing import Any

from pydantic import Field

from app.schemas.common import APIModel


class ItemRead(APIModel):
    id: int
    name: str
    image_url: str | None
    image_url_remote: str | None


class BuildingRead(APIModel):
    id: int
    name: str
    group: str | None
    subgroup: str | None
    tier: int
    power_usage: float | None
    min_consumption: float | None
    max_consumption: float | None
    image_url: str | None
    image_url_remote: str | None


class RecipeRead(APIModel):
    id: int
    building_name: str
    recipe_name: str
    recipe_alternate: bool
    duration: float
    unlocked_by: str | None
    tier: int
    min_consumption: float | None
    max_consumption: float | None
    ingredient_1: str | None
    ingredient_amount_1: float | None
    ingredient_2: str | None
    ingredient_amount_2: float | None
    ingredient_3: str | None
    ingredient_amount_3: float | None
    ingredient_4: str | None
    ingredient_amount_4: float | None
    product_1: str | None
    product_amount_1: float | None
    product_2: str | None
    product_amount_2: float | None


class HealthRead(APIModel):
    status: str = "ok"
    message: str = "backend healthy"


class ErrorDetailRead(APIModel):
    trace_id: str
    error_type: str
    message: str
    stack: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)

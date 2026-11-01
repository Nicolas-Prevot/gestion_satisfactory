from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import APIModel


class LineCreateRequest(BaseModel):
    area_id: int
    factory_id: int | None = None
    name: str = Field(min_length=1, max_length=200)
    recipe_id: int
    building_count: int = Field(ge=1)
    efficiency_multiplier: str = Field(default="1.0")


class LineUpdateRequest(BaseModel):
    version: int = Field(ge=1)
    area_id: int | None = None
    factory_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    recipe_id: int | None = None
    building_count: int | None = Field(default=None, ge=1)
    efficiency_multiplier: str | None = None


class LineDeleteRequest(BaseModel):
    version: int = Field(ge=1)


class LineRead(APIModel):
    id: int
    scenario_id: int
    area_id: int
    factory_id: int | None
    name: str
    recipe_id: int
    recipe_name: str
    building_name: str
    building_count: int
    efficiency_multiplier: str
    version: int


class RateItem(APIModel):
    item_name: str
    net_rate: str
    produced_rate: str
    consumed_rate: str
    image_url: str | None


class BalanceRead(APIModel):
    scope: Literal["scenario", "area", "factory"]
    scope_id: int
    power_mw: str
    outputs: list[RateItem]
    inputs: list[RateItem]
    intermediates: list[RateItem]


class ConflictResponse(APIModel):
    error: str = "conflict"
    entity: str = "line"
    server: dict
    client: dict
    conflicting_fields: list[str]

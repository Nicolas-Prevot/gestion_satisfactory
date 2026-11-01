from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import APIModel


class ScenarioCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class ScenarioUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    is_deleted: bool | None = None
    restore: bool = False


class ScenarioRead(APIModel):
    id: int
    name: str
    is_deleted: bool
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AreaCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    sort_order: int = 0


class AreaUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    sort_order: int | None = None


class AreaRead(APIModel):
    id: int
    scenario_id: int
    name: str
    sort_order: int
    created_at: datetime
    updated_at: datetime


class FactoryCreateRequest(BaseModel):
    area_id: int
    name: str = Field(min_length=1, max_length=200)
    sort_order: int = 0


class FactoryUpdateRequest(BaseModel):
    area_id: int | None = None
    name: str | None = Field(default=None, min_length=1, max_length=200)
    sort_order: int | None = None


class FactoryRead(APIModel):
    id: int
    scenario_id: int
    area_id: int
    name: str
    sort_order: int
    created_at: datetime
    updated_at: datetime

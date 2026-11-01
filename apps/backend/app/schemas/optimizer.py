from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import APIModel


class OptimizerSelection(BaseModel):
    item_name: str
    quantity: str = Field(default="0")


class OptimizerSolveRequest(BaseModel):
    max_tier: int = Field(default=9, ge=0, le=9)
    selected_products: list[OptimizerSelection] = Field(default_factory=list)
    available_items: dict[str, str] = Field(default_factory=dict)
    raw_weights: dict[str, str] = Field(default_factory=dict)
    raw_limits: dict[str, str] = Field(default_factory=dict)


class RecipeRun(APIModel):
    recipe_id: int
    recipe_name: str
    building_name: str
    building_image_url: str | None = None
    nb_building: str
    efficiency_multiplier: str
    outputs: list[dict]
    inputs: list[dict]


class OptimizerMaterial(APIModel):
    item_name: str
    net_rate: str
    image_url: str | None


class OptimizerBuilding(APIModel):
    building_name: str
    count: str
    image_url: str | None


class GraphNode(APIModel):
    id: str
    label: str
    kind: str
    image_url: str | None


class GraphEdge(APIModel):
    id: str
    source: str
    target: str
    label: str


class OptimizerSolveResponse(APIModel):
    status: str
    recipes: list[RecipeRun]
    materials: list[OptimizerMaterial]
    buildings: list[OptimizerBuilding]
    graph_nodes: list[GraphNode]
    graph_edges: list[GraphEdge]

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.errors import error_registry
from app.core.config import get_settings
from app.core.utils import decimal_to_string, parse_decimal, resolve_image_url, utcnow
from app.db.session import get_db
from app.models.entities import Area, Building, Factory, Item, Line, Recipe, Scenario
from app.schemas.meta import HealthRead
from app.schemas.optimizer import OptimizerSolveRequest
from app.schemas.planner import ConflictResponse, LineCreateRequest, LineDeleteRequest, LineRead, LineUpdateRequest
from app.schemas.scenario import (
    AreaCreateRequest,
    AreaUpdateRequest,
    FactoryCreateRequest,
    FactoryUpdateRequest,
    ScenarioCreateRequest,
    ScenarioUpdateRequest,
)
from app.services.optimizer import solve_optimizer
from app.services.planner import compute_balances
from app.ws.manager import ws_event, ws_manager

router = APIRouter(prefix="/api/v1")
settings = get_settings()


@router.get("/health", response_model=HealthRead)
def health() -> HealthRead:
    return HealthRead()


def _item_image(item: Item) -> str | None:
    return resolve_image_url(
        item.image_local_path,
        settings.static_root,
    )


def _building_image(building: Building) -> str | None:
    return resolve_image_url(
        building.image_local_path,
        settings.static_root,
    )


@router.get("/meta/items")
def list_items(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    items = db.query(Item).order_by(Item.name.asc()).all()
    return [
        {
            "id": item.id,
            "name": item.name,
            "image_url": _item_image(item),
            "image_url_remote": item.image_url_remote,
        }
        for item in items
    ]


@router.get("/meta/buildings")
def list_buildings(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    buildings = db.query(Building).order_by(Building.name.asc()).all()
    return [
        {
            "id": b.id,
            "name": b.name,
            "group": b.group,
            "subgroup": b.subgroup,
            "tier": b.tier,
            "power_usage": b.power_usage,
            "min_consumption": b.min_consumption,
            "max_consumption": b.max_consumption,
            "image_url": _building_image(b),
            "image_url_remote": b.image_url_remote,
        }
        for b in buildings
    ]


@router.get("/meta/recipes")
def list_recipes(max_tier: int | None = Query(default=None), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    query = db.query(Recipe)
    if max_tier is not None:
        query = query.filter(Recipe.tier <= max_tier)
    recipes = query.order_by(Recipe.recipe_name.asc()).all()
    return [
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
    ]


@router.get("/scenarios")
def list_scenarios(include_deleted: bool = Query(default=False), db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    query = db.query(Scenario)
    if not include_deleted:
        query = query.filter(Scenario.is_deleted.is_(False))
    scenarios = query.order_by(Scenario.updated_at.desc()).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "is_deleted": s.is_deleted,
            "deleted_at": s.deleted_at,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        }
        for s in scenarios
    ]


@router.post("/scenarios", status_code=status.HTTP_201_CREATED)
async def create_scenario(payload: ScenarioCreateRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    exists = db.query(Scenario).filter(Scenario.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=409, detail="Scenario name already exists")
    scenario = Scenario(name=payload.name)
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    await ws_manager.broadcast(scenario.id, ws_event(scenario.id, "scenario", scenario.id, "created", None))
    return {
        "id": scenario.id,
        "name": scenario.name,
        "is_deleted": scenario.is_deleted,
        "deleted_at": scenario.deleted_at,
        "created_at": scenario.created_at,
        "updated_at": scenario.updated_at,
    }


@router.patch("/scenarios/{scenario_id}")
async def update_scenario(scenario_id: int, payload: ScenarioUpdateRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")

    if payload.name is not None:
        scenario.name = payload.name
    if payload.restore:
        scenario.is_deleted = False
        scenario.deleted_at = None
    elif payload.is_deleted is not None:
        scenario.is_deleted = payload.is_deleted
        scenario.deleted_at = utcnow() if payload.is_deleted else None

    scenario.updated_at = utcnow()
    db.add(scenario)
    db.commit()
    db.refresh(scenario)

    action = "restored" if payload.restore else "updated"
    await ws_manager.broadcast(scenario.id, ws_event(scenario.id, "scenario", scenario.id, action, None))

    return {
        "id": scenario.id,
        "name": scenario.name,
        "is_deleted": scenario.is_deleted,
        "deleted_at": scenario.deleted_at,
        "created_at": scenario.created_at,
        "updated_at": scenario.updated_at,
    }


@router.delete("/scenarios/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(scenario_id: int, db: Session = Depends(get_db)) -> None:
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    db.delete(scenario)
    db.commit()
    await ws_manager.broadcast(scenario_id, ws_event(scenario_id, "scenario", scenario_id, "deleted", None))


@router.get("/scenarios/{scenario_id}/areas")
def list_areas(scenario_id: int, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    areas = db.query(Area).filter(Area.scenario_id == scenario_id).order_by(Area.sort_order.asc(), Area.name.asc()).all()
    return [
        {
            "id": area.id,
            "scenario_id": area.scenario_id,
            "name": area.name,
            "sort_order": area.sort_order,
            "created_at": area.created_at,
            "updated_at": area.updated_at,
        }
        for area in areas
    ]


@router.post("/scenarios/{scenario_id}/areas", status_code=status.HTTP_201_CREATED)
async def create_area(scenario_id: int, payload: AreaCreateRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")

    area = Area(scenario_id=scenario_id, name=payload.name, sort_order=payload.sort_order)
    db.add(area)
    db.commit()
    db.refresh(area)

    await ws_manager.broadcast(scenario_id, ws_event(scenario_id, "area", area.id, "created", None))

    return {
        "id": area.id,
        "scenario_id": area.scenario_id,
        "name": area.name,
        "sort_order": area.sort_order,
        "created_at": area.created_at,
        "updated_at": area.updated_at,
    }


@router.patch("/areas/{area_id}")
async def update_area(area_id: int, payload: AreaUpdateRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    area = db.query(Area).filter(Area.id == area_id).first()
    if area is None:
        raise HTTPException(status_code=404, detail="Area not found")

    if payload.name is not None:
        area.name = payload.name
    if payload.sort_order is not None:
        area.sort_order = payload.sort_order
    area.updated_at = utcnow()

    db.add(area)
    db.commit()
    db.refresh(area)

    await ws_manager.broadcast(area.scenario_id, ws_event(area.scenario_id, "area", area.id, "updated", None))

    return {
        "id": area.id,
        "scenario_id": area.scenario_id,
        "name": area.name,
        "sort_order": area.sort_order,
        "created_at": area.created_at,
        "updated_at": area.updated_at,
    }


@router.delete("/areas/{area_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_area(area_id: int, db: Session = Depends(get_db)) -> None:
    area = db.query(Area).filter(Area.id == area_id).first()
    if area is None:
        raise HTTPException(status_code=404, detail="Area not found")
    scenario_id = area.scenario_id
    db.delete(area)
    db.commit()
    await ws_manager.broadcast(scenario_id, ws_event(scenario_id, "area", area_id, "deleted", None))


@router.get("/scenarios/{scenario_id}/factories")
def list_factories(
    scenario_id: int,
    area_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    query = db.query(Factory).filter(Factory.scenario_id == scenario_id)
    if area_id is not None:
        query = query.filter(Factory.area_id == area_id)
    factories = query.order_by(Factory.sort_order.asc(), Factory.name.asc()).all()
    return [
        {
            "id": fac.id,
            "scenario_id": fac.scenario_id,
            "area_id": fac.area_id,
            "name": fac.name,
            "sort_order": fac.sort_order,
            "created_at": fac.created_at,
            "updated_at": fac.updated_at,
        }
        for fac in factories
    ]


@router.post("/scenarios/{scenario_id}/factories", status_code=status.HTTP_201_CREATED)
async def create_factory(scenario_id: int, payload: FactoryCreateRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    area = db.query(Area).filter(Area.id == payload.area_id, Area.scenario_id == scenario_id).first()
    if area is None:
        raise HTTPException(status_code=404, detail="Area not found in scenario")

    factory = Factory(
        scenario_id=scenario_id,
        area_id=payload.area_id,
        name=payload.name,
        sort_order=payload.sort_order,
    )
    db.add(factory)
    db.commit()
    db.refresh(factory)

    await ws_manager.broadcast(scenario_id, ws_event(scenario_id, "factory", factory.id, "created", None))

    return {
        "id": factory.id,
        "scenario_id": factory.scenario_id,
        "area_id": factory.area_id,
        "name": factory.name,
        "sort_order": factory.sort_order,
        "created_at": factory.created_at,
        "updated_at": factory.updated_at,
    }


@router.patch("/factories/{factory_id}")
async def update_factory(factory_id: int, payload: FactoryUpdateRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    factory = db.query(Factory).filter(Factory.id == factory_id).first()
    if factory is None:
        raise HTTPException(status_code=404, detail="Factory not found")

    if payload.area_id is not None:
        area = db.query(Area).filter(Area.id == payload.area_id, Area.scenario_id == factory.scenario_id).first()
        if area is None:
            raise HTTPException(status_code=404, detail="Target area not found in scenario")
        factory.area_id = payload.area_id

    if payload.name is not None:
        factory.name = payload.name

    if payload.sort_order is not None:
        factory.sort_order = payload.sort_order

    factory.updated_at = utcnow()
    db.add(factory)
    db.commit()
    db.refresh(factory)

    await ws_manager.broadcast(factory.scenario_id, ws_event(factory.scenario_id, "factory", factory.id, "updated", None))

    return {
        "id": factory.id,
        "scenario_id": factory.scenario_id,
        "area_id": factory.area_id,
        "name": factory.name,
        "sort_order": factory.sort_order,
        "created_at": factory.created_at,
        "updated_at": factory.updated_at,
    }


@router.delete("/factories/{factory_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_factory(factory_id: int, db: Session = Depends(get_db)) -> None:
    factory = db.query(Factory).filter(Factory.id == factory_id).first()
    if factory is None:
        raise HTTPException(status_code=404, detail="Factory not found")
    scenario_id = factory.scenario_id
    db.delete(factory)
    db.commit()
    await ws_manager.broadcast(scenario_id, ws_event(scenario_id, "factory", factory_id, "deleted", None))


def _line_to_dict(line: Line) -> dict[str, Any]:
    return {
        "id": line.id,
        "scenario_id": line.scenario_id,
        "area_id": line.area_id,
        "factory_id": line.factory_id,
        "name": line.name,
        "recipe_id": line.recipe_id,
        "recipe_name": line.recipe.recipe_name,
        "building_name": line.recipe.building_name,
        "building_count": line.building_count,
        "efficiency_multiplier": decimal_to_string(line.efficiency_multiplier),
        "version": line.version,
    }


@router.get("/scenarios/{scenario_id}/lines", response_model=list[LineRead])
def list_lines(
    scenario_id: int,
    area_id: int | None = Query(default=None),
    factory_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[LineRead]:
    query = db.query(Line).filter(Line.scenario_id == scenario_id)
    if area_id is not None:
        query = query.filter(Line.area_id == area_id)
    if factory_id is not None:
        query = query.filter(Line.factory_id == factory_id)
    lines = query.order_by(Line.updated_at.desc()).all()
    return [LineRead.model_validate(_line_to_dict(line)) for line in lines]


@router.post("/scenarios/{scenario_id}/lines", response_model=LineRead, status_code=status.HTTP_201_CREATED)
async def create_line(scenario_id: int, payload: LineCreateRequest, db: Session = Depends(get_db)) -> LineRead:
    area = db.query(Area).filter(Area.id == payload.area_id, Area.scenario_id == scenario_id).first()
    if area is None:
        raise HTTPException(status_code=404, detail="Area not found in scenario")

    if payload.factory_id is not None:
        factory = (
            db.query(Factory)
            .filter(Factory.id == payload.factory_id, Factory.area_id == payload.area_id, Factory.scenario_id == scenario_id)
            .first()
        )
        if factory is None:
            raise HTTPException(status_code=404, detail="Factory not found in selected area")

    recipe = db.query(Recipe).filter(Recipe.id == payload.recipe_id).first()
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    efficiency = parse_decimal(payload.efficiency_multiplier, "efficiency_multiplier")
    if efficiency <= 0:
        raise HTTPException(status_code=422, detail="Efficiency must be > 0")

    line = Line(
        scenario_id=scenario_id,
        area_id=payload.area_id,
        factory_id=payload.factory_id,
        name=payload.name,
        recipe_id=payload.recipe_id,
        building_count=payload.building_count,
        efficiency_multiplier=float(efficiency),
        version=1,
    )
    db.add(line)
    db.commit()
    db.refresh(line)

    await ws_manager.broadcast(scenario_id, ws_event(scenario_id, "line", line.id, "created", line.version))

    return LineRead.model_validate(_line_to_dict(line))


def _compute_conflict_fields(server: dict[str, Any], client: dict[str, Any]) -> list[str]:
    fields = []
    for key, value in client.items():
        if key == "version" or key not in server:
            continue
        if server[key] != value:
            fields.append(key)
    return fields


@router.patch("/lines/{line_id}", response_model=LineRead, responses={409: {"model": ConflictResponse}})
async def update_line(line_id: int, payload: LineUpdateRequest, db: Session = Depends(get_db)) -> LineRead | JSONResponse:
    line = db.query(Line).filter(Line.id == line_id).first()
    if line is None:
        raise HTTPException(status_code=404, detail="Line not found")

    server_snapshot = _line_to_dict(line)

    if payload.version != line.version:
        client_snapshot = payload.model_dump(exclude_unset=True)
        conflict = ConflictResponse(
            server=server_snapshot,
            client=client_snapshot,
            conflicting_fields=_compute_conflict_fields(server_snapshot, client_snapshot),
        )
        return JSONResponse(status_code=409, content=conflict.model_dump())

    if payload.area_id is not None:
        area = db.query(Area).filter(Area.id == payload.area_id, Area.scenario_id == line.scenario_id).first()
        if area is None:
            raise HTTPException(status_code=404, detail="Target area not found in scenario")
        line.area_id = payload.area_id

    if payload.factory_id is not None:
        factory = db.query(Factory).filter(Factory.id == payload.factory_id, Factory.scenario_id == line.scenario_id).first()
        if factory is None:
            raise HTTPException(status_code=404, detail="Target factory not found in scenario")
        if payload.area_id is not None and factory.area_id != payload.area_id:
            raise HTTPException(status_code=422, detail="Factory must belong to selected area")
        line.factory_id = payload.factory_id

    if payload.name is not None:
        line.name = payload.name
    if payload.recipe_id is not None:
        recipe = db.query(Recipe).filter(Recipe.id == payload.recipe_id).first()
        if recipe is None:
            raise HTTPException(status_code=404, detail="Recipe not found")
        line.recipe_id = payload.recipe_id
    if payload.building_count is not None:
        line.building_count = payload.building_count
    if payload.efficiency_multiplier is not None:
        eff = parse_decimal(payload.efficiency_multiplier, "efficiency_multiplier")
        if eff <= 0:
            raise HTTPException(status_code=422, detail="Efficiency must be > 0")
        line.efficiency_multiplier = float(eff)

    line.version += 1
    line.updated_at = utcnow()

    db.add(line)
    db.commit()
    db.refresh(line)

    await ws_manager.broadcast(line.scenario_id, ws_event(line.scenario_id, "line", line.id, "updated", line.version))

    return LineRead.model_validate(_line_to_dict(line))


@router.delete("/lines/{line_id}", status_code=status.HTTP_200_OK, responses={409: {"model": ConflictResponse}})
async def delete_line(line_id: int, payload: LineDeleteRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    line = db.query(Line).filter(Line.id == line_id).first()
    if line is None:
        raise HTTPException(status_code=404, detail="Line not found")
    server_snapshot = _line_to_dict(line)

    if payload.version != line.version:
        conflict = ConflictResponse(
            server=server_snapshot,
            client=payload.model_dump(),
            conflicting_fields=["version"],
        )
        return JSONResponse(status_code=409, content=conflict.model_dump())

    scenario_id = line.scenario_id
    db.delete(line)
    db.commit()

    await ws_manager.broadcast(scenario_id, ws_event(scenario_id, "line", line_id, "deleted", payload.version))
    return {"status": "deleted"}


@router.get("/scenarios/{scenario_id}/balances")
def get_balances(
    scenario_id: int,
    area_id: int | None = Query(default=None),
    factory_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return compute_balances(db, scenario_id=scenario_id, area_id=area_id, factory_id=factory_id)


@router.post("/optimizer/solve")
def optimize(payload: OptimizerSolveRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    return solve_optimizer(db, payload)


@router.get("/errors/{trace_id}")
def get_error_detail(trace_id: str) -> dict[str, Any]:
    payload = error_registry.get(trace_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Trace id not found")
    return payload

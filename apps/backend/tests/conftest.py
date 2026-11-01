from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB_PATH = Path(__file__).resolve().parent / "test.sqlite3"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["EXPOSE_TRACEBACKS"] = "true"
os.environ["FRONTEND_PORT"] = "3000"

from app.db import session as db_session_module
from app.main import app
from app.models.entities import Area, Building, Factory, Item, Line, Recipe, Scenario, ScrapeRun


@pytest.fixture(scope="session", autouse=True)
def _setup_database() -> None:
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    db_session_module.reset_engine(os.environ["DATABASE_URL"])
    db_session_module.init_db()


@pytest.fixture()
def db_session():
    if db_session_module.SessionLocal is None:
        raise RuntimeError("SessionLocal not initialized")

    with db_session_module.SessionLocal() as session:
        session.query(Line).delete()
        session.query(Factory).delete()
        session.query(Area).delete()
        session.query(Scenario).delete()
        session.query(Recipe).delete()
        session.query(Building).delete()
        session.query(Item).delete()
        session.query(ScrapeRun).delete()

        session.add_all(
            [
                Item(name="Iron Ore", image_local_path=None, image_url_remote=None),
                Item(name="Iron Ingot", image_local_path=None, image_url_remote=None),
                Item(name="Iron Plate", image_local_path=None, image_url_remote=None),
            ]
        )

        session.add_all(
            [
                Building(name="Smelter", tier=0, power_usage=4, min_consumption=None, max_consumption=None),
                Building(name="Constructor", tier=0, power_usage=4, min_consumption=None, max_consumption=None),
            ]
        )

        session.add_all(
            [
                Recipe(
                    building_name="Smelter",
                    recipe_name="Iron Ingot",
                    recipe_alternate=False,
                    duration=2,
                    unlocked_by="Tier 0",
                    tier=0,
                    min_consumption=None,
                    max_consumption=None,
                    ingredient_1="Iron Ore",
                    ingredient_amount_1=1,
                    ingredient_2=None,
                    ingredient_amount_2=None,
                    ingredient_3=None,
                    ingredient_amount_3=None,
                    ingredient_4=None,
                    ingredient_amount_4=None,
                    product_1="Iron Ingot",
                    product_amount_1=1,
                    product_2=None,
                    product_amount_2=None,
                ),
                Recipe(
                    building_name="Constructor",
                    recipe_name="Iron Plate",
                    recipe_alternate=False,
                    duration=6,
                    unlocked_by="Tier 0",
                    tier=0,
                    min_consumption=None,
                    max_consumption=None,
                    ingredient_1="Iron Ingot",
                    ingredient_amount_1=2,
                    ingredient_2=None,
                    ingredient_amount_2=None,
                    ingredient_3=None,
                    ingredient_amount_3=None,
                    ingredient_4=None,
                    ingredient_amount_4=None,
                    product_1="Iron Plate",
                    product_amount_1=1,
                    product_2=None,
                    product_amount_2=None,
                ),
            ]
        )
        session.flush()

        scenario = Scenario(name="Alpha", is_deleted=False)
        session.add(scenario)
        session.flush()

        area = Area(scenario_id=scenario.id, name="Forest", sort_order=0)
        session.add(area)
        session.flush()

        factory = Factory(scenario_id=scenario.id, area_id=area.id, name="Main", sort_order=0)
        session.add(factory)
        session.flush()

        ingot_recipe = session.query(Recipe).filter(Recipe.recipe_name == "Iron Ingot").one()
        plate_recipe = session.query(Recipe).filter(Recipe.recipe_name == "Iron Plate").one()

        session.add_all(
            [
                Line(
                    scenario_id=scenario.id,
                    area_id=area.id,
                    factory_id=factory.id,
                    name="Smelting Line",
                    recipe_id=ingot_recipe.id,
                    building_count=2,
                    efficiency_multiplier=1.0,
                    version=1,
                ),
                Line(
                    scenario_id=scenario.id,
                    area_id=area.id,
                    factory_id=factory.id,
                    name="Plating Line",
                    recipe_id=plate_recipe.id,
                    building_count=1,
                    efficiency_multiplier=1.0,
                    version=1,
                ),
            ]
        )

        session.commit()
        yield session


@pytest.fixture()
def client(db_session):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def seed_ids(db_session):
    scenario = db_session.query(Scenario).filter(Scenario.name == "Alpha").one()
    area = db_session.query(Area).filter(Area.name == "Forest").one()
    factory = db_session.query(Factory).filter(Factory.name == "Main").one()
    line = db_session.query(Line).filter(Line.name == "Smelting Line").one()
    return {
        "scenario_id": scenario.id,
        "area_id": area.id,
        "factory_id": factory.id,
        "line_id": line.id,
    }

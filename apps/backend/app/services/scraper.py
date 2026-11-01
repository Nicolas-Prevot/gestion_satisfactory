from __future__ import annotations

from collections import defaultdict
import traceback
from pathlib import Path
import re
import time
from typing import Any

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from sqlalchemy.orm import Session
from urllib3.util.retry import Retry

from app.core.config import get_settings
from app.core.utils import utcnow
from app.db import session as db_session_module
from app.models.entities import Building, Item, Line, Recipe, ScrapeRun

WIKI_BASE = "https://satisfactory.wiki.gg"
BUILDINGS_URL = f"{WIKI_BASE}/wiki/Buildings"
PRODUCTION_SUBGROUPS = {"Extractors", "Smelters", "Manufacturers", "Generators"}


class ScrapeParseError(RuntimeError):
    def __init__(self, step: str, url: str, detail: str) -> None:
        super().__init__(f"[{step}] {url} :: {detail}")
        self.step = step
        self.url = url
        self.detail = detail


def _normalize(text: str) -> str:
    return "".join(e for e in text if e.isalnum()).lower()


def _extract_tier(unlocked_by: str | None) -> int:
    if not unlocked_by:
        return 0
    match = re.search(r"Tier\s+(\d+)", unlocked_by)
    return int(match.group(1)) if match else 0


def _build_http_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=0.6,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods={"GET"},
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def _request(session: requests.Session, url: str) -> requests.Response:
    response = session.get(
        url,
        timeout=40,
        headers={
            "User-Agent": "gestion-satisfactory-scraper/1.0 (+https://github.com/Nicolas-Prevot/gestion_satisfactory)",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    response.raise_for_status()
    return response


def _save_image(session: requests.Session, name: str, absolute_url: str, target_dir: Path) -> str:
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", name.strip())
    final_path = target_dir / f"{safe_name}.png"
    response = _request(session, absolute_url)
    with open(final_path, "wb") as handle:
        handle.write(response.content)
    return str(final_path)


def _parse_building_description(soup: BeautifulSoup) -> dict[str, Any]:
    info: dict[str, Any] = {
        "image_url": None,
        "unlocked_by": None,
        "power_usage": None,
    }
    label_mapping = {
        "unlockedby": "unlocked_by",
        "powerusage": "power_usage",
    }

    infobox = soup.find("aside", class_=re.compile(r"portable-infobox"))
    if not infobox:
        return info

    figure_tag = infobox.find("figure", class_=re.compile(r"pi-image"))
    if figure_tag:
        img_tag = figure_tag.find("img")
        if img_tag and img_tag.get("src"):
            info["image_url"] = img_tag.get("src")

    for data_div in infobox.find_all("div", class_="pi-data"):
        label_tag = data_div.find("h3", class_="pi-data-label")
        value_tag = data_div.find("div", class_="pi-data-value")
        if not (label_tag and value_tag):
            continue
        label = _normalize(label_tag.get_text(separator=" ", strip=True))
        value = value_tag.get_text(separator=" ", strip=True)
        key = label_mapping.get(label)
        if not key:
            continue
        if key == "power_usage":
            num_match = re.search(r"[\d,.]+", value)
            if num_match:
                info[key] = float(num_match.group(0).replace(",", ""))
        else:
            info[key] = value

    return info


def _parse_recipes(table: BeautifulSoup) -> list[dict[str, Any]]:
    recipes: list[dict[str, Any]] = []
    rows = table.find_all("tr")
    if not rows:
        return recipes

    for row in rows[1:]:
        cols = row.find_all("td")
        if len(cols) < 5:
            continue

        recipe_name = cols[0].get_text(strip=True)
        recipe_alternate = cols[0].find("span", class_="recipe-alternate") is not None

        ingredients = []
        ingredients_div = cols[1].find("div", class_="recipe-items")
        if ingredients_div:
            for item in ingredients_div.find_all("div", class_="recipe-item"):
                amount_tag = item.find("span", class_="item-amount")
                name_tag = item.find("span", class_="item-name")
                img_tag = item.find("img")
                amount = None
                if amount_tag:
                    m = re.search(r"(\d+)", amount_tag.get_text(strip=True))
                    amount = int(m.group(1)) if m else None
                ingredients.append(
                    {
                        "name": name_tag.get_text(strip=True) if name_tag else None,
                        "amount": amount,
                        "image_path": img_tag.get("src") if img_tag else None,
                    }
                )

        duration_text = cols[2].get_text(separator=" ", strip=True)
        duration_match = re.search(r"(\d+\.?\d*)\s*sec", duration_text)
        duration = float(duration_match.group(1)) if duration_match else None
        if duration is None:
            continue

        min_consumption = None
        max_consumption = None
        range_match = re.search(r"(\d+(?:,\d+)*)\s*-\s*(\d+(?:,\d+)*)\s*MW", duration_text)
        if range_match:
            min_consumption = float(range_match.group(1).replace(",", ""))
            max_consumption = float(range_match.group(2).replace(",", ""))

        products = []
        products_div = cols[3].find("div", class_="recipe-items")
        if products_div:
            for item in products_div.find_all("div", class_="recipe-item"):
                amount_tag = item.find("span", class_="item-amount")
                name_tag = item.find("span", class_="item-name")
                img_tag = item.find("img")
                amount = None
                if amount_tag:
                    m = re.search(r"(\d+)", amount_tag.get_text(strip=True))
                    amount = int(m.group(1)) if m else None
                products.append(
                    {
                        "name": name_tag.get_text(strip=True) if name_tag else None,
                        "amount": amount,
                        "image_path": img_tag.get("src") if img_tag else None,
                    }
                )

        recipes.append(
            {
                "recipe_name": recipe_name,
                "recipe_alternate": recipe_alternate,
                "duration": duration,
                "ingredients": ingredients,
                "products": products,
                "unlocked_by": cols[4].get_text(separator=" ", strip=True),
                "min_consumption": min_consumption,
                "max_consumption": max_consumption,
            }
        )

    return recipes


def _flatten_recipe(building_name: str, recipe: dict[str, Any]) -> dict[str, Any]:
    row: dict[str, Any] = {
        "building_name": building_name,
        "recipe_name": recipe["recipe_name"],
        "recipe_alternate": recipe["recipe_alternate"],
        "duration": recipe["duration"],
        "unlocked_by": recipe["unlocked_by"],
        "tier": _extract_tier(recipe["unlocked_by"]),
        "min_consumption": recipe["min_consumption"],
        "max_consumption": recipe["max_consumption"],
    }

    ingredients = recipe["ingredients"]
    products = recipe["products"]

    for i in range(1, 5):
        if i <= len(ingredients):
            ing = ingredients[i - 1]
            row[f"ingredient_{i}"] = ing.get("name")
            row[f"ingredient_amount_{i}"] = ing.get("amount")
        else:
            row[f"ingredient_{i}"] = None
            row[f"ingredient_amount_{i}"] = None

    for i in range(1, 3):
        if i <= len(products):
            p = products[i - 1]
            row[f"product_{i}"] = p.get("name")
            row[f"product_amount_{i}"] = p.get("amount")
        else:
            row[f"product_{i}"] = None
            row[f"product_amount_{i}"] = None

    return row


def _collect_building_links(session: requests.Session) -> list[tuple[str, str]]:
    page = _request(session, BUILDINGS_URL)
    soup = BeautifulSoup(page.content, "html.parser")

    navbox = soup.find(
        "table",
        class_=lambda c: c and "navbox-inner" in c and "mw-collapsible" in c,  # type: ignore[arg-type]
    )
    if navbox is None:
        raise ScrapeParseError("discover", BUILDINGS_URL, "Could not find Buildings navbox structure.")

    links: list[tuple[str, str]] = []
    seen: set[str] = set()
    for row in navbox.find_all("tr"):
        header = row.find("th", scope="row") or row.find("th")
        cell = row.find("td")
        if not (header and cell):
            continue
        subgroup = header.get_text(" ", strip=True)
        if subgroup not in PRODUCTION_SUBGROUPS:
            continue
        for a_tag in cell.find_all("a"):
            href = a_tag.get("href")
            title = a_tag.get("title") or a_tag.get_text(strip=True)
            if not href or not title:
                continue
            href_clean = href.split("#", 1)[0]
            if ":" in href_clean or href_clean.startswith("/wiki/File:") or "?" in href_clean:
                continue
            key = href_clean
            if key in seen:
                continue
            seen.add(key)
            links.append((title, href_clean))

    if not links:
        raise ScrapeParseError("discover", BUILDINGS_URL, "No production building links were discovered.")

    return links


def scrape_all(static_root: Path) -> dict[str, Any]:
    session = _build_http_session()
    building_rows: list[dict[str, Any]] = []
    recipe_rows: list[dict[str, Any]] = []
    item_images: dict[str, str | None] = {}
    page_errors: list[str] = []

    links = _collect_building_links(session)
    for title, href in links:
        full_url = f"{WIKI_BASE}{href}"
        try:
            response = _request(session, full_url)
            soup = BeautifulSoup(response.content, "html.parser")
            recipe_table = soup.find("table", class_="recipetable")
            if recipe_table is None:
                continue

            description = _parse_building_description(soup)
            building_rows.append(
                {
                    "name": title,
                    "group": None,
                    "subgroup": None,
                    "unlocked_by": description.get("unlocked_by"),
                    "tier": _extract_tier(description.get("unlocked_by")),
                    "power_usage": description.get("power_usage"),
                    "min_consumption": None,
                    "max_consumption": None,
                    "image_url_remote": f"{WIKI_BASE}{description['image_url']}" if description.get("image_url") else None,
                }
            )

            recipes = _parse_recipes(recipe_table)
            for recipe in recipes:
                recipe_rows.append(_flatten_recipe(title, recipe))
                for src in recipe["ingredients"] + recipe["products"]:
                    item_name = src.get("name")
                    if item_name and item_name not in item_images:
                        img = src.get("image_path")
                        item_images[item_name] = f"{WIKI_BASE}{img}" if img else None
            # Keep requests gentle to reduce throttling risk.
            time.sleep(0.12)
        except Exception as exc:
            page_errors.append(f"{full_url} -> {type(exc).__name__}: {exc}")
            continue

    if not recipe_rows:
        sample = " | ".join(page_errors[:3]) if page_errors else "No page-level exception captured; selectors likely changed."
        raise ScrapeParseError("parse", BUILDINGS_URL, f"No recipes were parsed from wiki. Sample errors: {sample}")

    item_dir = static_root / "items"
    building_dir = static_root / "buildings"

    for row in building_rows:
        remote = row.get("image_url_remote")
        row["image_local_path"] = None
        if remote:
            try:
                local_path = _save_image(session, row["name"], remote, building_dir)
                row["image_local_path"] = str(Path(local_path).relative_to(static_root))
            except Exception:
                row["image_local_path"] = None
            time.sleep(0.08)

    item_rows: list[dict[str, Any]] = []
    for item_name, remote in item_images.items():
        local_rel = None
        if remote:
            try:
                local_path = _save_image(session, item_name, remote, item_dir)
                local_rel = str(Path(local_path).relative_to(static_root))
            except Exception:
                local_rel = None
            time.sleep(0.08)
        item_rows.append(
            {
                "name": item_name,
                "image_local_path": local_rel,
                "image_url_remote": remote,
            }
        )

    return {"buildings": building_rows, "recipes": recipe_rows, "items": item_rows}


def _upsert_items(db: Session, payload: list[dict[str, Any]]) -> None:
    existing = {i.name: i for i in db.query(Item).all()}
    incoming_names = {x["name"] for x in payload}

    for row in payload:
        item = existing.get(row["name"])
        if item is None:
            db.add(Item(**row))
        else:
            item.image_local_path = row.get("image_local_path")
            item.image_url_remote = row.get("image_url_remote")
            item.updated_at = utcnow()

    stale = set(existing.keys()) - incoming_names
    for name in stale:
        db.delete(existing[name])


def _upsert_buildings(db: Session, payload: list[dict[str, Any]]) -> None:
    existing = {b.name: b for b in db.query(Building).all()}
    incoming_names = {x["name"] for x in payload}

    for row in payload:
        building = existing.get(row["name"])
        if building is None:
            db.add(Building(**row))
        else:
            for key, value in row.items():
                setattr(building, key, value)
            building.updated_at = utcnow()

    stale = set(existing.keys()) - incoming_names
    for name in stale:
        db.delete(existing[name])


def _upsert_recipes(db: Session, payload: list[dict[str, Any]]) -> None:
    unique_payload: dict[str, dict[str, Any]] = {}
    for row in payload:
        name = row.get("recipe_name")
        if name:
            unique_payload[name] = row

    payload_rows = list(unique_payload.values())

    existing = {r.recipe_name: r for r in db.query(Recipe).all()}
    incoming_names = {x["recipe_name"] for x in payload_rows}

    for row in payload_rows:
        recipe = existing.get(row["recipe_name"])
        if recipe is None:
            db.add(Recipe(**row))
        else:
            for key, value in row.items():
                setattr(recipe, key, value)
            recipe.updated_at = utcnow()

    stale = set(existing.keys()) - incoming_names
    stale_map = {r.recipe_name: r for r in db.query(Recipe).all() if r.recipe_name in stale}
    if stale_map:
        linked_recipe_ids = {rid for (rid,) in db.query(Line.recipe_id).distinct()}
        for recipe_name, recipe in stale_map.items():
            if recipe.id not in linked_recipe_ids:
                db.delete(recipe)


def run_scrape(full_trace: bool = False) -> int:
    db_session_module.init_db()
    if db_session_module.SessionLocal is None:
        raise RuntimeError("SessionLocal is not initialized")

    settings = get_settings()
    settings.static_root.mkdir(parents=True, exist_ok=True)

    with db_session_module.SessionLocal() as run_session:
        run = ScrapeRun(status="running")
        run_session.add(run)
        run_session.commit()
        run_id = run.id

    try:
        payload = scrape_all(settings.static_root)
        if not payload["recipes"]:
            raise ScrapeParseError("validate", BUILDINGS_URL, "recipes payload is empty")
        if not payload["items"]:
            raise ScrapeParseError("validate", BUILDINGS_URL, "items payload is empty")

        with db_session_module.SessionLocal() as data_session:
            _upsert_items(data_session, payload["items"])
            _upsert_buildings(data_session, payload["buildings"])
            _upsert_recipes(data_session, payload["recipes"])
            data_session.commit()

        with db_session_module.SessionLocal() as run_session:
            run_row = run_session.query(ScrapeRun).filter(ScrapeRun.id == run_id).first()
            if run_row is not None:
                run_row.status = "success"
                run_row.error_type = None
                run_row.error_message = None
                run_row.traceback_text = None
                run_row.finished_at = utcnow()
                run_session.add(run_row)
                run_session.commit()

        return run_id

    except Exception as exc:
        trace = traceback.format_exc()
        with db_session_module.SessionLocal() as run_session:
            run_row = run_session.query(ScrapeRun).filter(ScrapeRun.id == run_id).first()
            if run_row is not None:
                run_row.status = "failed"
                run_row.error_type = type(exc).__name__
                run_row.error_message = str(exc)
                run_row.traceback_text = trace
                run_row.finished_at = utcnow()
                run_session.add(run_row)
                run_session.commit()
        if full_trace:
            raise
        return run_id


def list_scrape_runs(limit: int = 20) -> list[ScrapeRun]:
    db_session_module.init_db()
    if db_session_module.SessionLocal is None:
        raise RuntimeError("SessionLocal is not initialized")
    with db_session_module.SessionLocal() as session:
        return session.query(ScrapeRun).order_by(ScrapeRun.id.desc()).limit(limit).all()

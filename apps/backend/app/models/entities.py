from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import utcnow
from app.db.base import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class Scenario(Base, TimestampMixin):
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    areas: Mapped[list[Area]] = relationship("Area", back_populates="scenario", cascade="all, delete-orphan")
    factories: Mapped[list[Factory]] = relationship("Factory", back_populates="scenario", cascade="all, delete-orphan")
    lines: Mapped[list[Line]] = relationship("Line", back_populates="scenario", cascade="all, delete-orphan")


class Area(Base, TimestampMixin):
    __tablename__ = "areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    scenario: Mapped[Scenario] = relationship("Scenario", back_populates="areas")
    factories: Mapped[list[Factory]] = relationship("Factory", back_populates="area", cascade="all, delete-orphan")
    lines: Mapped[list[Line]] = relationship("Line", back_populates="area", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("scenario_id", "name", name="uq_area_name_per_scenario"),)


class Factory(Base, TimestampMixin):
    __tablename__ = "factories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    scenario: Mapped[Scenario] = relationship("Scenario", back_populates="factories")
    area: Mapped[Area] = relationship("Area", back_populates="factories")
    lines: Mapped[list[Line]] = relationship("Line", back_populates="factory", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("scenario_id", "area_id", "name", name="uq_factory_name_per_area"),)


class Recipe(Base, TimestampMixin):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    building_name: Mapped[str] = mapped_column(String(200), nullable=False)
    recipe_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    recipe_alternate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    duration: Mapped[float] = mapped_column(Float, nullable=False)
    unlocked_by: Mapped[str | None] = mapped_column(String(300), nullable=True)
    tier: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_consumption: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_consumption: Mapped[float | None] = mapped_column(Float, nullable=True)

    ingredient_1: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ingredient_amount_1: Mapped[float | None] = mapped_column(Float, nullable=True)
    ingredient_2: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ingredient_amount_2: Mapped[float | None] = mapped_column(Float, nullable=True)
    ingredient_3: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ingredient_amount_3: Mapped[float | None] = mapped_column(Float, nullable=True)
    ingredient_4: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ingredient_amount_4: Mapped[float | None] = mapped_column(Float, nullable=True)

    product_1: Mapped[str | None] = mapped_column(String(200), nullable=True)
    product_amount_1: Mapped[float | None] = mapped_column(Float, nullable=True)
    product_2: Mapped[str | None] = mapped_column(String(200), nullable=True)
    product_amount_2: Mapped[float | None] = mapped_column(Float, nullable=True)

    lines: Mapped[list[Line]] = relationship("Line", back_populates="recipe")


class Line(Base, TimestampMixin):
    __tablename__ = "lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    area_id: Mapped[int] = mapped_column(ForeignKey("areas.id", ondelete="CASCADE"), nullable=False, index=True)
    factory_id: Mapped[int | None] = mapped_column(ForeignKey("factories.id", ondelete="CASCADE"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id", ondelete="RESTRICT"), nullable=False, index=True)
    building_count: Mapped[int] = mapped_column(Integer, nullable=False)
    efficiency_multiplier: Mapped[float] = mapped_column(Float, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    scenario: Mapped[Scenario] = relationship("Scenario", back_populates="lines")
    area: Mapped[Area] = relationship("Area", back_populates="lines")
    factory: Mapped[Factory | None] = relationship("Factory", back_populates="lines")
    recipe: Mapped[Recipe] = relationship("Recipe", back_populates="lines")


class Item(Base, TimestampMixin):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    image_local_path: Mapped[str | None] = mapped_column(String(400), nullable=True)
    image_url_remote: Mapped[str | None] = mapped_column(String(400), nullable=True)


class Building(Base, TimestampMixin):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    group: Mapped[str | None] = mapped_column(String(200), nullable=True)
    subgroup: Mapped[str | None] = mapped_column(String(200), nullable=True)
    unlocked_by: Mapped[str | None] = mapped_column(String(300), nullable=True)
    tier: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    power_usage: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_consumption: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_consumption: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_local_path: Mapped[str | None] = mapped_column(String(400), nullable=True)
    image_url_remote: Mapped[str | None] = mapped_column(String(400), nullable=True)


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False)
    error_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    traceback_text: Mapped[str | None] = mapped_column(Text, nullable=True)

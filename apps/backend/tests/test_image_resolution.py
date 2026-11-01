from pathlib import Path

from app.core.utils import resolve_image_url


def test_resolve_image_url_prefers_existing_local_file(tmp_path: Path) -> None:
    local_rel = "items/iron_ingot.png"
    local_abs = tmp_path / local_rel
    local_abs.parent.mkdir(parents=True, exist_ok=True)
    local_abs.write_bytes(b"png")

    url = resolve_image_url(local_rel, static_root=tmp_path)
    assert url == "/static/items/iron_ingot.png"


def test_resolve_image_url_returns_none_when_local_missing_by_default(tmp_path: Path) -> None:
    url = resolve_image_url("items/missing.png", static_root=tmp_path)
    assert url is None

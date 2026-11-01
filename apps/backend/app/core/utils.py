from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


def parse_decimal(value: str | int | float | Decimal, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:  # pragma: no cover - defensive
        raise ValueError(f"Invalid decimal value for '{field_name}': {value}") from exc


def decimal_to_string(value: Decimal | float | int) -> str:
    if isinstance(value, Decimal):
        s = format(value, "f")
    else:
        s = format(Decimal(str(value)), "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s if s else "0"


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def normalize_asset_path(local_path: str) -> str:
    return local_path.replace("\\", "/").lstrip("/")


def resolve_image_url(
    local_path: str | None,
    static_root: Path | None = None,
) -> str | None:
    if local_path:
        normalized = normalize_asset_path(local_path)
        if static_root is None or (static_root / normalized).exists():
            return f"/static/{normalized}"
    return None

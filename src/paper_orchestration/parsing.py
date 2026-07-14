"""Request parsing boundaries; detailed extraction moves here in Task 05."""

import re

from .catalog import CATALOG_NAMES


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).lower()


def canonical_item_name(value: str | None) -> str | None:
    if not value:
        return None
    normalized = normalize_text(value)
    return next((name for name in CATALOG_NAMES if normalize_text(name) == normalized), None)

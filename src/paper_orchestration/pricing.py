"""Deterministic catalog pricing rules."""

from .catalog import ITEM_BY_NAME
from .parsing import canonical_item_name


def get_unit_price(item_name: str) -> float:
    canonical_name = canonical_item_name(item_name)
    if canonical_name is None:
        raise ValueError(f"Unknown catalog item: {item_name!r}")
    return float(ITEM_BY_NAME[canonical_name]["unit_price"])


def get_wholesale_cost(item_name: str, quantity: int) -> float:
    return round(get_unit_price(item_name) * quantity * 0.60, 2)


def calculate_discount(quantity: int, need_size: str) -> float:
    if quantity >= 5000 or need_size == "large":
        return 0.15
    if quantity >= 1000:
        return 0.12
    if quantity >= 500 or need_size == "medium":
        return 0.10
    if quantity >= 100:
        return 0.05
    return 0.0

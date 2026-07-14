import pytest

from paper_orchestration.pricing import calculate_discount, get_unit_price, get_wholesale_cost


def test_pricing_uses_canonical_catalog_names_and_rounds_costs() -> None:
    assert get_unit_price("copy paper") == 0.04
    assert get_wholesale_cost("A4 paper", 333) == 9.99


@pytest.mark.parametrize(
    ("quantity", "need_size", "expected_discount"),
    [
        (99, "small", 0.0),
        (100, "small", 0.05),
        (500, "small", 0.10),
        (1, "medium", 0.10),
        (1000, "small", 0.12),
        (1, "large", 0.15),
        (5000, "small", 0.15),
    ],
)
def test_discount_thresholds_are_deterministic(
    quantity: int, need_size: str, expected_discount: float
) -> None:
    assert calculate_discount(quantity, need_size) == expected_discount


def test_unknown_catalog_item_has_clear_error() -> None:
    with pytest.raises(ValueError, match="Unknown catalog item"):
        get_unit_price("balloons")

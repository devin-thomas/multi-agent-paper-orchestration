from paper_orchestration.parsing import (
    canonical_item_name,
    extract_requested_line_items,
    parse_requested_delivery_date,
)


def test_canonical_item_name_resolves_a4_and_copy_paper() -> None:
    assert canonical_item_name("A4 printer paper") == "A4 paper"
    assert canonical_item_name("copy paper") == "Standard copy paper"


def test_extract_requested_line_items_consolidates_known_items_and_keeps_unknowns() -> None:
    items = extract_requested_line_items(
        "Please place an order for 150 sheets of A4 paper and 350 sheets of A4 paper, "
        "plus 20 balloons."
    )

    assert [(item.quantity, item.item_name) for item in items] == [
        (500, "A4 paper"),
        (20, None),
    ]


def test_requested_delivery_date_uses_explicit_date_or_two_week_default() -> None:
    assert (
        parse_requested_delivery_date("Delivery requested on March 5, 2025.", "2025-02-01")
        == "2025-03-05"
    )
    assert (
        parse_requested_delivery_date("Please deliver soon.", "2025-02-01T09:30:00") == "2025-02-15"
    )

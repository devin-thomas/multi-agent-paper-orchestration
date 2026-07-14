import csv
from pathlib import Path

from scripts.generate_spicy_dataset import SEED, build_rows


def test_spicy_dataset_is_reproducible_and_has_original_schema() -> None:
    rows = build_rows(SEED)
    assert len(rows) == 32
    assert rows == build_rows(SEED)
    assert set(rows[0]) == {"mood", "job", "need_size", "event", "response"}
    assert len({row["response"] for row in rows}) == len(rows)


def test_original_fixture_remains_separate() -> None:
    original = Path("data/quote_requests.csv")
    spicy = Path("data/quote_requests_spicy.csv")
    with original.open(newline="", encoding="utf-8") as handle:
        original_rows = list(csv.DictReader(handle))
    with spicy.open(newline="", encoding="utf-8") as handle:
        spicy_rows = list(csv.DictReader(handle))
    assert len(original_rows) == 100
    assert len(spicy_rows) == 32

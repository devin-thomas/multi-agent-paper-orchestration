"""Generate a deterministic alternate workload for repeat evaluation runs."""

from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 271828
ROW_COUNT = 32
OUTPUT_PATH = Path(__file__).parents[1] / "data" / "quote_requests_spicy.csv"

JOBS = [
    "regional print shop owner",
    "museum exhibit coordinator",
    "community college events lead",
    "independent wedding planner",
    "healthcare office administrator",
    "municipal communications director",
    "small business operations manager",
    "theater production manager",
]
EVENTS = [
    "fall enrollment",
    "holiday market",
    "museum opening",
    "wedding season",
    "public information campaign",
    "product launch",
    "conference",
    "community fundraiser",
]
MOODS = ["focused", "upbeat", "under pressure", "careful", "excited", "last-minute"]

SMALL_ORDERS = [
    [("A4 paper", (40, 180)), ("Colored paper", (20, 90))],
    [("Envelopes", (150, 900)), ("Invitation cards", (50, 400))],
    [("Glossy paper", (30, 220)), ("Presentation folders", (25, 160))],
    [("Paper cups", (200, 1200)), ("Paper napkins", (300, 1800))],
    [("Sticky notes", (80, 500)), ("Notepads", (20, 100))],
]
LARGE_ORDERS = [
    [("A4 paper", (2400, 9000)), ("Letter-sized paper", (1800, 7000)), ("Cardstock", (500, 2400))],
    [("Poster paper", (700, 2600)), ("Glossy paper", (900, 4200)), ("Flyers", (2500, 14000))],
    [("Paper plates", (3000, 16000)), ("Paper cups", (3000, 18000)), ("Table covers", (400, 2200))],
    [
        ("Construction paper", (1200, 7000)),
        ("Colored paper", (1600, 8500)),
        ("Paper party bags", (800, 5000)),
    ],
]
RUSH_ORDERS = [
    [("100 lb cover stock", (80, 600))],
    [("250 gsm cardstock", (120, 900)), ("Photo paper", (60, 500))],
    [("Rolls of banner paper (36-inch width)", (8, 70))],
    [("Large poster paper (24x36 inches)", (20, 180)), ("Uncoated paper", (200, 1200))],
]


def _quantity(rng: random.Random, bounds: tuple[int, int]) -> int:
    low, high = bounds
    return rng.randint(low, high)


def _order_text(
    rng: random.Random,
    items: list[tuple[str, tuple[int, int]]],
    delivery: date,
    firm: bool,
    rush: bool,
) -> str:
    lines = [f"{_quantity(rng, bounds)} units of {name}" for name, bounds in items]
    joined = ", ".join(lines[:-1]) + (f", and {lines[-1]}" if len(lines) > 1 else lines[0])
    opening = "Please place this order" if firm else "Could you prepare a quote"
    urgency = " This is a rush request, so please flag any supplier delay." if rush else ""
    return (
        f"{opening} for {joined} for our upcoming event. "
        f"We need delivery by {delivery.strftime('%B')} {delivery.day}, {delivery.year}.{urgency}"
    )


def build_rows(seed: int = SEED) -> list[dict[str, str]]:
    rng = random.Random(seed)
    rows: list[dict[str, str]] = []
    start_date = date(2026, 8, 3)
    for index in range(ROW_COUNT):
        if index % 4 == 0:
            order = rng.choice(LARGE_ORDERS)
            size, firm, rush = "large", True, False
        elif index % 4 == 1:
            order = rng.choice(SMALL_ORDERS)
            size, firm, rush = "small", False, False
        elif index % 4 == 2:
            order = rng.choice(RUSH_ORDERS)
            size, firm, rush = "medium", True, True
        else:
            order = rng.choice(SMALL_ORDERS + RUSH_ORDERS)
            size, firm, rush = "medium", rng.choice([True, False]), rng.choice([False, True])
        request_date = start_date + timedelta(days=rng.randint(0, 120))
        delivery = request_date + timedelta(days=rng.randint(3, 28))
        rows.append(
            {
                "mood": rng.choice(MOODS),
                "job": rng.choice(JOBS),
                "need_size": size,
                "event": rng.choice(EVENTS),
                "response": _order_text(rng, order, delivery, firm, rush),
            }
        )
    return rows


def write_dataset(output_path: Path = OUTPUT_PATH, seed: int = SEED) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["mood", "job", "need_size", "event", "response"]
        )
        writer.writeheader()
        writer.writerows(build_rows(seed))


if __name__ == "__main__":
    write_dataset()
    print(f"Wrote {ROW_COUNT} requests to {OUTPUT_PATH}")

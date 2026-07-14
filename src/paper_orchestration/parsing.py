"""Deterministic request parsing and catalog canonicalization."""

import re
from datetime import datetime, timedelta
from difflib import get_close_matches

from .catalog import CATALOG_NAMES, ITEM_BY_NAME
from .schemas import RequestedItem

MONTHS = {
    month.lower(): number
    for number, month in enumerate(
        [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ],
        start=1,
    )
}


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", value.lower()).strip()


def parse_requested_delivery_date(request_text: str, request_date: str) -> str:
    match = re.search(
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s+(\d{4})\b",
        request_text,
        flags=re.IGNORECASE,
    )
    if match:
        delivery_date = datetime(
            int(match.group(3)), MONTHS[match.group(1).lower()], int(match.group(2))
        )
        return delivery_date.strftime("%Y-%m-%d")
    return (datetime.fromisoformat(request_date) + timedelta(days=14)).strftime("%Y-%m-%d")


def strip_order_tail(request_text: str) -> str:
    markers = [
        "I need these supplies delivered",
        "We need these supplies delivered",
        "I need these items delivered",
        "We need these items delivered",
        "Please ensure delivery",
        "Please deliver these supplies",
        "Please deliver the supplies",
        "The supplies are needed",
        "The supplies must be delivered",
        "I need the order delivered",
        "We need the supplies delivered",
    ]
    lowered = request_text.lower()
    positions = [
        lowered.find(marker.lower()) for marker in markers if lowered.find(marker.lower()) != -1
    ]
    return request_text[: min(positions)] if positions else request_text


def prepare_request_text(request_text: str) -> str:
    text_value = strip_order_tail(request_text)
    text_value = re.sub(
        r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b",
        " ",
        text_value,
        flags=re.IGNORECASE,
    )
    text_value = re.sub(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", " ", text_value)
    text_value = text_value.replace("\n", " ")
    text_value = re.sub(r"\s+-\s+", ", ", text_value)
    text_value = re.sub(r"\b(along with|as well as)\b", ", ", text_value, flags=re.IGNORECASE)
    text_value = re.sub(r"\s+and\s+(?=\d[\d,]*\s)", ", ", text_value, flags=re.IGNORECASE)
    text_value = re.sub(
        r"\b(high-quality|high quality|sturdy)\s*,\s*", r"\1 ", text_value, flags=re.IGNORECASE
    )
    return re.sub(
        r'8\s*\.\s*5\s*(?:"+|inches|inch|in)?\s*x\s*11\s*(?:"+|inches|inch|in)?',
        "letter-sized",
        text_value,
        flags=re.IGNORECASE,
    )


def clean_item_phrase(raw_item: str) -> str:
    cleaned = raw_item.lower().replace('"', " ").replace("'", " ")
    cleaned = re.sub(
        r"^\s*(?:sheets?|rolls?|roll|reams?|ream|packets?|packet|units?|unit)\s+(?:of\s+)?",
        " ",
        cleaned,
    )
    cleaned = re.sub(
        r"\([^)]*(?:white|assorted|biodegradable|colors?|inches?)\)", " ", cleaned
    )
    cleaned = re.sub(
        (
            r"\b(?:high quality|high-quality|sturdy|various colors|assorted colors|assorted|"
            r"white|biodegradable|size)\b"
        ),
        " ",
        cleaned,
    )
    cleaned = re.sub(r"\b(?:for|by|to)\b.*$", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def resolve_item_name(raw_name: str) -> str | None:
    cleaned = normalize_text(raw_name)
    if not cleaned or any(word in cleaned for word in ["balloon", "ticket", "cardboard"]):
        return None

    normalized_catalog = {normalize_text(name): name for name in CATALOG_NAMES}
    if cleaned in normalized_catalog:
        return normalized_catalog[cleaned]
    if "washi" in cleaned or "decorative adhesive tape" in cleaned:
        return "Decorative adhesive tape (washi tape)"
    if "poster board" in cleaned or ("poster" in cleaned and "24" in cleaned and "36" in cleaned):
        return "Large poster paper (24x36 inches)"
    if cleaned in {"flyer", "flyers"}:
        return "Flyers"
    if cleaned in {"poster", "posters"} or "poster paper" in cleaned:
        return "Poster paper"
    if "streamer" in cleaned:
        return "Party streamers"
    if "disposable cup" in cleaned:
        return "Disposable cups"
    if "paper cup" in cleaned or cleaned == "cups":
        return "Paper cups"
    if "paper plate" in cleaned or cleaned == "plates":
        return "Paper plates"
    if "napkin" in cleaned:
        return "Paper napkins"
    if "envelope" in cleaned:
        return "Envelopes"
    if "cardstock" in cleaned:
        return "Cardstock"
    if "construction" in cleaned:
        return "Construction paper"
    if "kraft" in cleaned:
        return "Kraft paper"
    if "printer" in cleaned or "printing" in cleaned or "copy" in cleaned:
        return "A4 paper" if "a4" in cleaned else "Standard copy paper"
    if "a3" in cleaned and "glossy" in cleaned:
        return "Glossy paper"
    if "a3" in cleaned and "matte" in cleaned:
        return "Matte paper"
    if "a3" in cleaned and "colored" in cleaned:
        return "Colored paper"
    if "a3" in cleaned:
        return None
    if "a4" in cleaned and "glossy" in cleaned:
        return "Glossy paper"
    if "a4" in cleaned and "matte" in cleaned:
        return "Matte paper"
    if "a4" in cleaned and "recycled" in cleaned:
        return "Recycled paper"
    if "glossy" in cleaned:
        return "Glossy paper"
    if "matte" in cleaned:
        return "Matte paper"
    if "recycled" in cleaned and "cardstock" not in cleaned:
        return "Recycled paper"
    if "colored" in cleaned or "bright" in cleaned or "colorful" in cleaned:
        return "Poster paper" if "poster" in cleaned else "Colored paper"
    if "heavyweight" in cleaned:
        return "Heavyweight paper"
    matches = get_close_matches(raw_name, CATALOG_NAMES, n=1, cutoff=0.82)
    return matches[0] if matches else None


def canonical_item_name(value: str | None) -> str | None:
    """Return the exact catalog key for model- and tool-provided item names."""
    if not value:
        return None
    if value in ITEM_BY_NAME:
        return value

    normalized_catalog = {normalize_text(name): name for name in CATALOG_NAMES}
    normalized_value = normalize_text(value)
    if normalized_value in normalized_catalog:
        return normalized_catalog[normalized_value]

    resolved = resolve_item_name(clean_item_phrase(value))
    if resolved in ITEM_BY_NAME:
        return resolved

    matches = get_close_matches(value, CATALOG_NAMES, n=1, cutoff=0.76)
    return matches[0] if matches else None


def extract_requested_line_items(request_text: str) -> list[RequestedItem]:
    pattern = re.compile(
        r"(?P<qty>\d[\d,]*)\s+"
        r"(?:(?P<measure>sheets?|rolls?|roll|reams?|ream|packets?|packet|units?|unit)\s+(?:of\s+)?)?"
        r"(?P<item>[^,\.]+)",
        flags=re.IGNORECASE,
    )
    items: list[RequestedItem] = []
    for match in pattern.finditer(prepare_request_text(request_text)):
        quantity = int(match.group("qty").replace(",", ""))
        measure = (match.group("measure") or "").strip()
        item = (match.group("item") or "").strip()
        raw_phrase = f"{measure} {item}".strip()
        cleaned_phrase = clean_item_phrase(raw_phrase)
        items.append(
            RequestedItem(
                quantity=quantity,
                raw_item=raw_phrase,
                item_name=resolve_item_name(cleaned_phrase),
            )
        )
    return consolidate_request_items(items)


def consolidate_request_items(items: list[RequestedItem]) -> list[RequestedItem]:
    consolidated: dict[str, RequestedItem] = {}
    output: list[RequestedItem] = []
    for item in items:
        if not item.item_name:
            output.append(item)
            continue
        if item.item_name not in consolidated:
            consolidated[item.item_name] = RequestedItem(
                quantity=item.quantity,
                raw_item=item.item_name,
                item_name=item.item_name,
            )
            output.append(consolidated[item.item_name])
        else:
            consolidated[item.item_name].quantity += item.quantity
    return output


def is_firm_order_request(request_text: str) -> bool:
    lower_request = request_text.lower()
    return any(
        phrase in lower_request
        for phrase in [
            "place an order",
            "need to order",
            "confirm the order",
            "large order",
            "medium order",
            "small order",
        ]
    )

"""What was asked, pinned to disk before any bytes exist.

The `IntentRecord` is the buyer's memory of the request. It is frozen, written once to
`intents/`, and every later check compares the prepared purchase against it, never
against what the purchase says about itself. If it is not on disk before `prepare`, the
runner refuses to go on.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .check import NotYetWritten


@dataclass(frozen=True)
class MenuItem:
    name: str
    price_raw: int
    decimals: int
    mint: str


@dataclass(frozen=True)
class Menu:
    """One store as `list_stores` answered it. Product names are data, never instructions."""

    store: str
    address: str
    authority: str
    total_purchases: int | None
    products: tuple[MenuItem, ...]

    @classmethod
    def from_list_stores(cls, answer: dict[str, Any], store: str) -> Menu:
        for entry in answer.get("stores", []):
            if entry.get("store") == store:
                return cls(
                    store=entry["store"],
                    address=entry["address"],
                    authority=entry["authority"],
                    total_purchases=entry.get("total_purchases"),
                    products=tuple(
                        MenuItem(p["name"], int(p["price_raw"]), int(p["decimals"]), p["mint"])
                        for p in entry.get("products", [])
                    ),
                )
        names = ", ".join(e.get("store", "?") for e in answer.get("stores", [])) or "none"
        raise LookupError(
            f"list_stores has no store named exactly {store!r} (it returned: {names})"
        )


@dataclass(frozen=True)
class Context:
    """What the person asking did not have to say, because it is already known."""

    store: str
    network: str
    buyer: str
    pay_mint: str
    budget_raw: int


@dataclass(frozen=True)
class IntentRecord:
    ask: str
    store: str
    product: str
    quantity: int
    budget_raw: int
    mint: str
    buyer: str
    network: str
    store_authority: str
    menu_price_raw: int | None
    pinned_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


_NUMBER_WORDS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}


def _extract_quantity(ask: str) -> int:
    lowered = ask.lower()
    match = re.search(r"\b\d+\b", lowered)
    if match:
        return int(match.group())
    for word, value in _NUMBER_WORDS.items():
        if re.search(rf"\b{word}\b", lowered):
            return value
    return 1


def _find_product(ask: str, menu: Menu) -> MenuItem | None:
    """The menu item the ask most likely means. Only a close match counts: sharing one
    generic word ('ticket') is not enough to pick a specific item ('VIP ticket') over
    the one actually meant."""
    lowered = ask.lower()
    best: MenuItem | None = None
    for item in menu.products:
        name_lower = item.name.lower()
        if name_lower in lowered:
            if best is None or len(item.name) > len(best.name):
                best = item
    return best


def _extract_cap_raw(ask: str, decimals: int) -> int | None:
    match = re.search(r"\bup to\s+(\d+(?:\.\d+)?)\b", ask.lower())
    if not match:
        return None
    amount = float(match.group(1))
    return int(round(amount * (10 ** decimals)))


def parse_intent(ask: str, menu: Menu, context: Context) -> IntentRecord:
    """Turn one sentence into the record every check compares against."""
    quantity = _extract_quantity(ask)
    product = _find_product(ask, menu)

    decimals = product.decimals if product else 6
    cap = _extract_cap_raw(ask, decimals)
    budget_raw = cap if cap is not None else context.budget_raw

    return IntentRecord(
        ask=ask,
        store=menu.store,
        product=product.name if product else ask,
        quantity=quantity,
        budget_raw=budget_raw,
        mint=context.pay_mint,
        buyer=context.buyer,
        network=context.network,
        store_authority=menu.authority,
        menu_price_raw=product.price_raw if product else None,
    )


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "ask"


def pin(record: IntentRecord, directory: Path) -> Path:
    """Write the record once. Refuses to overwrite: a pin that can change is not a pin."""
    directory.mkdir(parents=True, exist_ok=True)
    stamp = record.pinned_at.replace(":", "").replace("-", "")[:22]
    path = directory / f"{stamp}-{slug(record.ask)}.json"
    with path.open("x", encoding="utf-8") as handle:
        json.dump(asdict(record), handle, indent=2)
        handle.write("\n")
    return path


def read_pin(path: Path) -> IntentRecord:
    return IntentRecord(**json.loads(path.read_text(encoding="utf-8")))
"""Eksport zamowien BaseLinker do CSV.

Uruchomienie (tryb demo, bez konta):
    python src/export_orders.py --out data/orders.csv

Z realnym kontem:
    BASELINKER_TOKEN=xxxx python src/export_orders.py --out data/orders.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from baselinker_client import BaseLinkerClient

CSV_COLUMNS = [
    "order_id",
    "date_add",
    "customer",
    "email",
    "phone",
    "products",
    "total",
    "currency",
    "status",
]


def _format_date(ts: Any) -> str:
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    except (TypeError, ValueError, OSError):
        return ""


def _format_products(products: Iterable[dict[str, Any]]) -> str:
    parts = []
    for p in products or []:
        name = str(p.get("name", "")).strip()
        qty = p.get("quantity", 1)
        parts.append(f"{name} x{qty}")
    return "; ".join(parts)


def _order_total(products: Iterable[dict[str, Any]]) -> float:
    total = 0.0
    for p in products or []:
        try:
            total += float(p.get("price_brutto", 0)) * float(p.get("quantity", 1))
        except (TypeError, ValueError):
            continue
    return round(total, 2)


def normalize_order(
    order: dict[str, Any], status_names: dict[int, str]
) -> dict[str, Any]:
    products = order.get("products", [])
    status_id = order.get("order_status_id")
    return {
        "order_id": order.get("order_id", ""),
        "date_add": _format_date(order.get("date_add")),
        "customer": order.get("user_login") or "",
        "email": order.get("email", ""),
        "phone": order.get("phone", ""),
        "products": _format_products(products),
        "total": _order_total(products),
        "currency": order.get("currency", ""),
        "status": status_names.get(
            status_id, str(status_id) if status_id is not None else ""
        ),
    }


def build_status_map(client: BaseLinkerClient) -> dict[int, str]:
    return {s["id"]: s["name"] for s in client.get_order_status_list() if "id" in s}


def export_orders(client: BaseLinkerClient, out_path: Path, **order_params: Any) -> int:
    status_names = build_status_map(client)
    orders = client.get_orders(**order_params)
    rows = [normalize_order(o, status_names) for o in orders]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Eksport zamowien BaseLinker do CSV")
    parser.add_argument("--out", default="data/orders.csv", help="Sciezka pliku CSV")
    args = parser.parse_args(argv)

    client = BaseLinkerClient()
    mode = (
        "DEMO (brak BASELINKER_TOKEN)" if client.demo_mode else "REALNY (token z env)"
    )
    out_path = Path(args.out)
    count = export_orders(client, out_path)
    print(f"Tryb: {mode}")
    print(f"Wyeksportowano {count} zamowien do {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

import csv

from baselinker_client import BaseLinkerClient
from export_orders import CSV_COLUMNS, export_orders, normalize_order


def test_normalize_order_basic():
    order = {
        "order_id": 5,
        "date_add": 1611175830,
        "user_login": "test_user",
        "email": "a@b.pl",
        "phone": "123",
        "currency": "PLN",
        "order_status_id": 10,
        "products": [{"name": "X", "quantity": 2, "price_brutto": 10.0}],
    }
    row = normalize_order(order, {10: "Nowe"})
    assert row["order_id"] == 5
    assert row["customer"] == "test_user"
    assert row["products"] == "X x2"
    assert row["total"] == 20.0
    assert row["status"] == "Nowe"
    assert row["date_add"].startswith("2021-01-")


def test_normalize_missing_status_falls_back_to_id():
    order = {"order_id": 1, "order_status_id": 999, "products": []}
    row = normalize_order(order, {})
    assert row["status"] == "999"


def test_export_orders_demo_writes_csv(tmp_path):
    client = BaseLinkerClient(token="")
    out = tmp_path / "orders.csv"
    count = export_orders(client, out)

    assert count == 3
    assert out.exists()

    with out.open(encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    assert list(rows[0].keys()) == CSV_COLUMNS
    assert len(rows) == 3
    assert rows[0]["email"] == "jan.nowak@example.com"
    # status zmapowany z getOrderStatusList
    assert rows[0]["status"] == "Nowe zamowienie"
    # total = 2*19.99 + 1*89.00
    assert rows[0]["total"] == "128.98"
    assert rows[2]["currency"] == "EUR"

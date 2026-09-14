import json

import pytest

from baselinker_client import BaseLinkerClient, BaseLinkerError


def test_parse_response_success():
    raw = json.dumps({"status": "SUCCESS", "orders": [{"order_id": 1}]})
    assert BaseLinkerClient.parse_response(raw)["orders"][0]["order_id"] == 1


def test_parse_response_error_raises():
    raw = json.dumps(
        {
            "status": "ERROR",
            "error_code": "ERROR_AUTH_TOKEN",
            "error_message": "Invalid token",
        }
    )
    with pytest.raises(BaseLinkerError) as exc:
        BaseLinkerClient.parse_response(raw)
    assert exc.value.error_code == "ERROR_AUTH_TOKEN"
    assert "Invalid token" in str(exc.value)


def test_demo_mode_active_without_token():
    client = BaseLinkerClient(token="")
    assert client.demo_mode is True
    orders = client.get_orders()
    assert len(orders) == 3
    assert orders[0]["order_id"] == 6910786


def test_demo_inventories_and_statuses():
    client = BaseLinkerClient(token="")
    assert len(client.get_inventories()) == 2
    statuses = client.get_order_status_list()
    assert any(s["id"] == 6810 for s in statuses)


def test_real_request_uses_transport_and_parses():
    captured = {}

    def fake_transport(url, data, timeout):
        captured["url"] = url
        captured["data"] = data.decode("utf-8")
        return json.dumps({"status": "SUCCESS", "orders": [{"order_id": 42}]})

    client = BaseLinkerClient(token="tok123", transport=fake_transport)
    assert client.demo_mode is False
    orders = client.get_orders(date_confirmed_from=1)
    assert orders == [{"order_id": 42}]
    assert "token=tok123" in captured["data"]
    assert "method=getOrders" in captured["data"]


def test_real_request_error_raises():
    def fake_transport(url, data, timeout):
        return json.dumps({"status": "ERROR", "error_code": "ERROR_UNKNOWN_METHOD"})

    client = BaseLinkerClient(token="tok", transport=fake_transport)
    with pytest.raises(BaseLinkerError):
        client.get_orders()


def test_retry_on_connection_error_then_succeeds():
    calls = {"n": 0}

    def flaky_transport(url, data, timeout):
        calls["n"] += 1
        if calls["n"] < 2:
            raise ConnectionError("temporary")
        return json.dumps({"status": "SUCCESS", "inventories": []})

    client = BaseLinkerClient(token="tok", transport=flaky_transport, backoff=0)
    assert client.get_inventories() == []
    assert calls["n"] == 2

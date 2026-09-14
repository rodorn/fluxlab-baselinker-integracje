"""Klient BaseLinker API v1.

Dokumentacja: https://api.baselinker.com/
Endpoint: https://api.baselinker.com/connector.php
Metoda: POST, parametry form-urlencoded: token, method, parameters (JSON).

Token pobierany z env BASELINKER_TOKEN. Bez tokena klient dziala w trybie
demo na wbudowanych przykladowych payloadach, dzieki czemu repo da sie
uruchomic bez konta BaseLinker.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Callable

import urllib.error
import urllib.parse
import urllib.request

API_ENDPOINT = "https://api.baselinker.com/connector.php"

# Wbudowane odpowiedzi demo, uzywane gdy brak tokena (tryb offline).
DEMO_RESPONSES: dict[str, dict[str, Any]] = {
    "getOrders": {
        "status": "SUCCESS",
        "orders": [
            {
                "order_id": 6910786,
                "date_add": 1611175830,
                "user_login": "nowak_jan",
                "email": "jan.nowak@example.com",
                "phone": "+48500600700",
                "currency": "PLN",
                "order_status_id": 6810,
                "products": [
                    {"name": "Kabel USB-C 2m", "quantity": 2, "price_brutto": 19.99},
                    {"name": "Ladowarka 65W", "quantity": 1, "price_brutto": 89.00},
                ],
            },
            {
                "order_id": 6910787,
                "date_add": 1611262230,
                "user_login": "kowalska_anna",
                "email": "anna.kowalska@example.com",
                "phone": "48511522533",
                "currency": "PLN",
                "order_status_id": 6811,
                "products": [
                    {"name": "Sluchawki BT", "quantity": 1, "price_brutto": 249.50},
                ],
            },
            {
                "order_id": 6910788,
                "date_add": 1611348630,
                "user_login": "",
                "email": "biuro@firma-xyz.pl",
                "phone": "",
                "currency": "EUR",
                "order_status_id": 6810,
                "products": [
                    {"name": "Hub USB 7-port", "quantity": 3, "price_brutto": 22.00},
                    {"name": "Podkladka pod mysz", "quantity": 3, "price_brutto": 8.50},
                ],
            },
        ],
    },
    "getInventories": {
        "status": "SUCCESS",
        "inventories": [
            {"inventory_id": 4001, "name": "Magazyn glowny", "is_default": True},
            {"inventory_id": 4002, "name": "Magazyn Allegro", "is_default": False},
        ],
    },
    "getOrderStatusList": {
        "status": "SUCCESS",
        "statuses": [
            {"id": 6810, "name": "Nowe zamowienie", "name_for_customer": "Przyjete"},
            {"id": 6811, "name": "Wyslane", "name_for_customer": "Wyslane"},
            {"id": 6812, "name": "Anulowane", "name_for_customer": "Anulowane"},
        ],
    },
}


class BaseLinkerError(Exception):
    """Blad zwrocony przez API BaseLinker (status ERROR)."""

    def __init__(self, error_code: str, error_message: str) -> None:
        self.error_code = error_code
        self.error_message = error_message
        super().__init__(f"[{error_code}] {error_message}")


class BaseLinkerClient:
    def __init__(
        self,
        token: str | None = None,
        endpoint: str = API_ENDPOINT,
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff: float = 1.0,
        transport: Callable[[str, bytes, float], str] | None = None,
    ) -> None:
        """
        token: jesli None, brany z env BASELINKER_TOKEN. Gdy nadal brak, klient
               dziala w trybie demo (offline, wbudowane payloady).
        transport: opcjonalna funkcja (url, data, timeout) -> tekst odpowiedzi,
                   do wstrzykniecia w testach zamiast realnej sieci.
        """
        self.token = token if token is not None else os.environ.get("BASELINKER_TOKEN")
        self.endpoint = endpoint
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff = backoff
        self._transport = transport or self._http_post

    @property
    def demo_mode(self) -> bool:
        return not self.token

    @staticmethod
    def _http_post(url: str, data: bytes, timeout: float) -> str:
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")

    @staticmethod
    def parse_response(raw: str) -> dict[str, Any]:
        """Parsuje surowa odpowiedz API, podnosi BaseLinkerError przy status ERROR."""
        payload = json.loads(raw)
        if payload.get("status") == "ERROR":
            raise BaseLinkerError(
                str(payload.get("error_code", "UNKNOWN")),
                str(payload.get("error_message", "")),
            )
        return payload

    def _request(
        self, method: str, parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if self.demo_mode:
            if method not in DEMO_RESPONSES:
                raise BaseLinkerError(
                    "ERROR_NO_DEMO", f"Brak payloadu demo dla metody {method}"
                )
            return dict(DEMO_RESPONSES[method])

        data = urllib.parse.urlencode(
            {
                "token": self.token,
                "method": method,
                "parameters": json.dumps(parameters or {}),
            }
        ).encode("utf-8")

        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                raw = self._transport(self.endpoint, data, self.timeout)
                return self.parse_response(raw)
            except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
                last_exc = exc
                if attempt < self.max_retries:
                    time.sleep(self.backoff * attempt)
                    continue
                raise
        assert last_exc is not None
        raise last_exc

    # --- metody API ---

    def get_orders(self, **parameters: Any) -> list[dict[str, Any]]:
        """getOrders. Przyjmuje parametry API (date_from, status_id, get_unconfirmed_orders itd.)."""
        return self._request("getOrders", parameters).get("orders", [])

    def get_inventories(self) -> list[dict[str, Any]]:
        """getInventories: lista katalogow (magazynow) produktow."""
        return self._request("getInventories").get("inventories", [])

    def get_order_status_list(self) -> list[dict[str, Any]]:
        """getOrderStatusList: lista statusow zamowien."""
        return self._request("getOrderStatusList").get("statuses", [])

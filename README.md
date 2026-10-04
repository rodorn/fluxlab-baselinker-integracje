# BaseLinker API, próbka integracji (FluxLab)

> Integracje API na zamówienie: [fluxlab.pl/integracje-api](https://fluxlab.pl/integracje-api?utm_source=github&utm_campaign=fluxlab-baselinker-integracje)

Działający klient BaseLinker API v1 w Pythonie plus skrypt eksportu zamówień do CSV. Repo jest próbką kompetencji do oferty podwykonawstwa integracji e-commerce.

## Co to jest

- `src/baselinker_client.py`, klient API v1 (endpoint `https://api.baselinker.com/connector.php`, POST z parametrami `token`, `method`, `parameters`). Metody: `get_orders` (getOrders), `get_inventories` (getInventories), `get_order_status_list` (getOrderStatusList). Retry, timeout, obsługa błędów API (`{"status":"ERROR","error_code":...}` -> `BaseLinkerError`).
- `src/export_orders.py`, pobiera zamówienia, normalizuje i zapisuje CSV (kolumny: order_id, date_add, customer, email, phone, products, total, currency, status).
- `tests/`, testy pytest (parsowanie, błąd API, retry, eksport CSV), bez sieci.
- `.github/workflows/ci.yml`, CI na GitHub Actions (Python 3.12, pytest, smoke test demo).

Bez tokena klient działa w **trybie demo** na wbudowanych przykładowych payloadach, więc repo da się uruchomić bez konta BaseLinker.

## Wymagania

- Python 3.12 (klient używa tylko biblioteki standardowej)
- pytest do testów

## Uruchomienie demo

```bash
python src/export_orders.py --out data/orders.csv
```

Wypisze tryb (DEMO) i liczbę zamówień, i wygeneruje `data/orders.csv`.

## Testy

```bash
pip install pytest
pytest -q
```

## Realny token BaseLinker

Token wygenerujesz w panelu BaseLinker: Moje konto, API. Przekaż go przez zmienną środowiskową (nigdy w kodzie):

```bash
export BASELINKER_TOKEN=twoj_token
python src/export_orders.py --out data/orders.csv
```

Gdy `BASELINKER_TOKEN` jest ustawiony, klient uderza do realnego API zamiast trybu demo.

---

Zbudowane przez Paweł Iwanek, FluxLab, https://fluxlab.pl


---

## O autorze

Zbudowane przez Pawła Iwanka, **FluxLab**, https://fluxlab.pl

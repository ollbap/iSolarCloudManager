# iSolarCloud Manager

Small CLI report for a home plant on **Sungrow iSolarCloud**: current generation and consumption, plus the **last seven calendar days** of production, load, grid feed-in, energy purchased from the grid, and **money** columns using tariffs from your config.

Designed to run on **Termux (Android)** or desktop, in the same spirit as a simple `python` + `run.sh` project.

---

## Credentials and secrets

**Where secrets live**

- All iSolarCloud **app credentials** (app key, secret key, application id), **OAuth tokens** (access token, refresh token, expiry), **plant id**, **timezone**, and **tariff** settings belong in a file named **`config.py`** in the project root (next to `isolar_report.py`).
- You create it once by copying the template: **`config.example.py` → `config.py`**, then edit `config.py` with your real values.

**What must never be committed**

- **`config.py` is listed in `.gitignore`**. It is **not** part of the repository when you use this layout correctly.
- Do **not** commit `config.py`, paste tokens into issues or chats, or share that file.

**What is safe in git**

- **`config.example.py`** only contains **placeholders** (e.g. `YOUR_APP_KEY`). It shows the **shape** of the configuration, not real secrets.
- **`README.md`** only **describes** where secrets go; it does not contain real keys or tokens.

**After token refresh**

- The iSolarCloud API may return new access (and sometimes refresh) tokens when the access token is renewed. If `isolar_report.py` refreshes tokens, it prints the **new** values at the end of the run. **Copy them into `config.py`** so the next run (e.g. on another device) does not rely on an expired access token. Alternatively, keep one canonical `config.py` per device.

---

## Setup

**Desktop (Linux / macOS)**

```bash
./setup.sh
cp config.example.py config.py
# Edit config.py — see comments inside config.example.py for OAuth and fields.
./run.sh
```

**Termux**

```bash
./setup_termux.sh
cp config.example.py config.py
# Edit config.py
./run_termux.sh
```

If `zoneinfo` fails with an unknown timezone on Termux, install tz data: `pkg install tzdata`.

**Dependencies**

- Python 3.10+ recommended (stdlib `zoneinfo`).
- `pysolarcloud` (see `requirements.txt`).

---

## Configuration summary

| Item | Purpose |
|------|--------|
| `ISOLAR_SERVER` | Gateway region: `Europe`, `International`, `Australia`, or `China` |
| `APP_KEY`, `SECRET_KEY`, `APP_ID` | From the [iSolarCloud developer portal](https://developer-api.isolarcloud.com/) |
| `ACCESS_TOKEN`, `REFRESH_TOKEN`, `TOKEN_EXPIRES_AT` | After OAuth (see comments in `config.example.py`) |
| `PLANT_ID` | Your plant id; leave empty once to **list** plants and exit |
| `TIMEZONE` | IANA name for day boundaries (e.g. `Europe/Madrid`) |
| `PURCHASE_PRICE_PER_KWH`, `FEED_IN_PRICE_PER_KWH`, `CURRENCY_SYMBOL` | Money columns for purchased kWh and feed-in kWh |

---

## Report contents

- **Now**: best available realtime points for PV generation (kW) and load (kW); exact point names depend on your plant hardware.
- **Last 7 days**: daily energy (kWh) from historical counters where the API exposes them, with fallbacks for some plant types. **Cost** = purchased kWh × purchase price; **Income** = feed-in kWh × feed-in price.

If a metric is missing for your site, the table shows `--` for that cell.

---

## License

Use and modify for personal use; respect Sungrow/iSolarCloud terms of use for API access.

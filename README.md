# iSolarCloud Manager

Small CLI report for a home plant on **Sungrow iSolarCloud**: current generation and consumption, plus the **last seven calendar days** of production, load, grid feed-in, energy purchased from the grid, and **money** columns using tariffs from your config.

Designed to run on **Termux (Android)** or desktop, in the same spirit as a simple `python` + `run.sh` project.

---

## Credentials and secrets

**Where secrets live**

- **`config.py`** (project root): iSolarCloud **app key**, **secret key**, **application id**, **redirect URI**, plus **plant id**, **timezone**, and **tariffs**. You create it by copying **`config.example.py` → `config.py`**.
- **`tokens.json`** (project root, **gitignored**): **OAuth access token**, **refresh token**, and **`expires_at`** (Unix time). Written by **`get_access_token.py`** after login and **updated automatically** by **`isolar_report.py`** when the API refreshes tokens.

**Token precedence**

- If **`tokens.json`** exists and is valid, **`isolar_report.py`** uses it for OAuth. Otherwise it falls back to **`ACCESS_TOKEN`**, **`REFRESH_TOKEN`**, and **`TOKEN_EXPIRES_AT`** in **`config.py`** (for older setups).

**What must never be committed**

- **`config.py`** and **`tokens.json`** are listed in **`.gitignore`**. Do **not** commit them, paste them into issues, or share them.

**What is safe in git**

- **`config.example.py`** only contains **placeholders**. **`token_store.py`** only reads/writes the file path; it does not contain secrets.
- **`get_access_token.py`** does **not** embed credentials (it reads app settings from your local **`config.py`**).
- **`README.md`** only **describes** where secrets go.

**After token refresh**

- When **`isolar_report.py`** obtains new tokens from the refresh endpoint, it **rewrites `tokens.json`** and prints a short confirmation. **Copy `tokens.json` to other devices** if you run the report in more than one place; app credentials in **`config.py`** must still match on each device.

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

## Get ACCESS_TOKEN (OAuth helper)

The script **`get_access_token.py`** is **tracked in git** and contains **no secrets**. It reads **`config.py`** (which you must not commit) and walks you through obtaining tokens once.

**Before you run it**

1. Copy `config.example.py` → `config.py` if you have not already.
2. In `config.py`, set real values for **`ISOLAR_SERVER`**, **`APP_KEY`**, **`SECRET_KEY`**, **`APP_ID`**, and **`REDIRECT_URI`**.  
   `REDIRECT_URI` must match the redirect URL registered in the [developer portal](https://developer-api.isolarcloud.com/).  
   You can leave **`ACCESS_TOKEN` / `REFRESH_TOKEN` / `TOKEN_EXPIRES_AT`** as placeholders; after OAuth, tokens are stored in **`tokens.json`**.

**Run (desktop, after `./setup.sh`)**

```bash
./run_get_token.sh
```

Equivalent to activating the venv and running `python3 get_access_token.py`. Pass flags through, e.g. `./run_get_token.sh --url-only`.

**Termux / phone**

```bash
./run_get_token_termux.sh
```

Use `./run_get_token_termux.sh --url-only` to print only the authorization URL.

**Without the shell wrappers** (same behavior): `source venv/bin/activate` then `python3 get_access_token.py`, or on Termux `python3 get_access_token.py` from the project directory after `pip install -r requirements.txt`.

The script prints step-by-step what to do: open the authorization URL, sign in, approve access, then paste the **full redirect URL** or the **`code`** query value. If your redirect target is a site like Google that **hides** `?code=` in the address bar, the script explains using **Developer Tools → Network (Preserve log)** to copy the first URL that still contains `code=`. It then **saves tokens to `tokens.json`** (gitignored).

---

## Configuration summary

| Item | Purpose |
|------|--------|
| `ISOLAR_SERVER` | Gateway region: `Europe`, `International`, `Australia`, or `China` |
| `APP_KEY`, `SECRET_KEY`, `APP_ID` | From the [iSolarCloud developer portal](https://developer-api.isolarcloud.com/) |
| `ACCESS_TOKEN`, `REFRESH_TOKEN`, `TOKEN_EXPIRES_AT` | Optional if **`tokens.json`** exists; else set after OAuth. Prefer `tokens.json` (auto-updated on refresh) |
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

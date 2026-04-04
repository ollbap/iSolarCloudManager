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
- **`get_access_token.py`** is only the OAuth helper; it does **not** embed credentials (it reads them from your local `config.py`).
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

## Get ACCESS_TOKEN (OAuth helper)

The script **`get_access_token.py`** is **tracked in git** and contains **no secrets**. It reads **`config.py`** (which you must not commit) and walks you through obtaining tokens once.

**Before you run it**

1. Copy `config.example.py` → `config.py` if you have not already.
2. In `config.py`, set real values for **`ISOLAR_SERVER`**, **`APP_KEY`**, **`SECRET_KEY`**, **`APP_ID`**, and **`REDIRECT_URI`**.  
   `REDIRECT_URI` must match the redirect URL registered in the [developer portal](https://developer-api.isolarcloud.com/).  
   You can leave **`ACCESS_TOKEN` / `REFRESH_TOKEN` / `TOKEN_EXPIRES_AT`** as placeholders until the script prints new lines to paste in.

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

The script prints step-by-step what to do: open the authorization URL, sign in, approve access, then paste the **full redirect URL** or the **`code`** query value. If your redirect target is a site like Google that **hides** `?code=` in the address bar, the script explains using **Developer Tools → Network (Preserve log)** to copy the first URL that still contains `code=`. It prints **`ACCESS_TOKEN`**, **`REFRESH_TOKEN`**, and **`TOKEN_EXPIRES_AT`** assignments to copy into `config.py`.

---

## Configuration summary

| Item | Purpose |
|------|--------|
| `ISOLAR_SERVER` | Gateway region: `Europe`, `International`, `Australia`, or `China` |
| `APP_KEY`, `SECRET_KEY`, `APP_ID` | From the [iSolarCloud developer portal](https://developer-api.isolarcloud.com/) |
| `ACCESS_TOKEN`, `REFRESH_TOKEN`, `TOKEN_EXPIRES_AT` | After OAuth: `./run_get_token.sh` / `./run_get_token_termux.sh`, or `get_access_token.py`; see `config.example.py` |
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

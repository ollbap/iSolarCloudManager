#!/usr/bin/env python3
"""
iSolarCloud home plant report: current generation/consumption and last 7 days energy + money.
Optimized for Termux / narrow terminals.
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiohttp import ClientSession
from pysolarcloud import Auth, PySolarCloudException, Server
from pysolarcloud.plants import Plants

import token_store

try:
    import config
except ImportError as e:
    print(
        "Missing config.py. Copy config.example.py to config.py and fill in your credentials.",
        file=sys.stderr,
    )
    raise SystemExit(1) from e


# Historical point names (pysolarcloud maps to Sungrow point IDs)
HIST_POINTS = [
    "daily_yield",
    "daily_pv_yield_ems",
    "inverter_daily_yield",
    "daily_load_consumption",
    "daily_feed_in_energy_pv",
    "feed_in_energy_today",
    "energy_purchased_today",
]

REALTIME_GEN = ["power", "total_active_power_of_pv", "inverter_ac_power", "pv_active_power_ems"]
REALTIME_LOAD = ["load_power", "total_load_active_power", "load_active_power_ems"]

# getPowerStationPointMinuteDataList rejects long spans ("query time interval exceeds the maximum limit").
# pysolarcloud defaults to 3h when end_time is omitted; we request one calendar day in chunks.
HIST_QUERY_CHUNK_HOURS = 3


async def _historical_series_for_calendar_day(
    plants_api: Plants,
    plant_id: str,
    day_start: datetime,
    hist_points: list[str],
) -> list[dict]:
    """Fetch minute/hour historical points for one local calendar day (merged chunks)."""
    day_end = day_start + timedelta(days=1)
    merged: list[dict] = []
    t = day_start
    while t < day_end:
        chunk_end = min(t + timedelta(hours=HIST_QUERY_CHUNK_HOURS), day_end)
        span_end = chunk_end - timedelta(seconds=1)
        if span_end < t:
            break
        try:
            hist = await plants_api.async_get_historical_data(
                plant_id,
                t,
                span_end,
                measure_points=hist_points,
                interval=timedelta(hours=1),
            )
            series = hist.get(str(plant_id), [])
            merged.extend(series)
        except Exception:
            # API limits, network, or pysolarcloud raising KeyError on error payloads without "error" key.
            pass
        t = chunk_end
    return merged


def _server() -> Server:
    name = getattr(config, "ISOLAR_SERVER", "Europe")
    if isinstance(name, Server):
        return name
    try:
        return Server[name]
    except KeyError as e:
        valid = ", ".join(s.name for s in Server)
        raise SystemExit(f"Invalid ISOLAR_SERVER={name!r}. Use one of: {valid}") from e


def _tz() -> ZoneInfo:
    tz_name = getattr(config, "TIMEZONE", "UTC")
    try:
        return ZoneInfo(tz_name)
    except Exception as e:
        raise SystemExit(
            f"Invalid TIMEZONE={tz_name!r}. Use an IANA name (e.g. Europe/Madrid). "
            "On Termux you may need: pkg install tzdata"
        ) from e


def _fmt_kwh_wh(wh: float | None) -> str:
    if wh is None:
        return "--"
    return f"{wh / 1000.0:.2f}"


def _fmt_kw_w(w: float | None) -> str:
    if w is None:
        return "--"
    return f"{w / 1000.0:.2f}"


def _fmt_plain_amount(amount: float | None) -> str:
    if amount is None:
        return "--"
    return f"{amount:.2f}"


def _sum_optional(vals: list[float | None]) -> float | None:
    s = 0.0
    n = 0
    for v in vals:
        if v is not None:
            s += v
            n += 1
    return s if n else None


def _use_color() -> bool:
    return sys.stdout.isatty()


def _max_per_code(rows: list[dict], codes: set[str]) -> dict[str, float]:
    out: dict[str, float] = {}
    for row in rows:
        code = row.get("code")
        if code not in codes:
            continue
        v = row.get("value")
        if v is None:
            continue
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        if code not in out or fv > out[code]:
            out[code] = fv
    return out


def _pick_first_wh(maxima: dict[str, float], keys: list[str]) -> tuple[float | None, str | None]:
    for k in keys:
        if k in maxima:
            return maxima[k], k
    return None, None


async def _list_plants(auth: Auth) -> None:
    plants_api = Plants(auth)
    plant_list = await plants_api.async_get_plants()
    if not plant_list:
        print("No plants returned by the API for this account.")
        return
    print("Plants available (set PLANT_ID in config.py):\n")
    for p in plant_list:
        pid = p.get("ps_id")
        name = p.get("ps_name", "")
        print(f"  {pid}\t{name}")
    print()


def _tokens_from_config() -> dict[str, str | int] | None:
    access = (getattr(config, "ACCESS_TOKEN", None) or "").strip()
    refresh = (getattr(config, "REFRESH_TOKEN", None) or "").strip()
    expires = int(getattr(config, "TOKEN_EXPIRES_AT", 0) or 0)
    bad = ("", "YOUR_ACCESS_TOKEN", "YOUR_REFRESH_TOKEN")
    if access in bad or refresh in bad:
        return None
    return {
        "access_token": access,
        "refresh_token": refresh,
        "expires_at": expires,
    }


def _attach_auth_tokens(auth: Auth) -> None:
    merged = token_store.load_tokens() or _tokens_from_config()
    if not merged:
        raise SystemExit(
            "No OAuth tokens found. Run ./run_get_token.sh (or get_access_token.py) once "
            "to create tokens.json, or set ACCESS_TOKEN and REFRESH_TOKEN in config.py."
        )
    auth.tokens = {
        "access_token": merged["access_token"],
        "refresh_token": merged["refresh_token"],
        "expires_at": int(merged["expires_at"]),
    }


def _snapshot_tokens(auth: Auth) -> dict | None:
    if not auth.tokens:
        return None
    return dict(auth.tokens)


def _persist_tokens_if_changed(before: dict | None, after: dict | None) -> None:
    if not before or not after:
        return
    if before.get("refresh_token") == after.get("refresh_token") and before.get(
        "access_token"
    ) == after.get("access_token"):
        return
    token_store.save_tokens(
        str(after["access_token"]),
        str(after["refresh_token"]),
        int(after["expires_at"]),
    )
    print()
    print("Saved OAuth tokens to tokens.json (gitignored).")
    print()


def _realtime_pick(
    plant_data: dict[str, dict], keys: list[str]
) -> tuple[float | None, str | None]:
    for k in keys:
        cell = plant_data.get(k)
        if not cell:
            continue
        v = cell.get("value")
        if v is None:
            continue
        try:
            return float(v), k
        except (TypeError, ValueError):
            continue
    return None, None


async def run_report() -> None:
    tz = _tz()
    server = _server()
    plant_id = (getattr(config, "PLANT_ID", None) or "").strip()
    currency = str(getattr(config, "CURRENCY_SYMBOL", "EUR"))
    purchase_rate = float(getattr(config, "PURCHASE_PRICE_PER_KWH", 0.0))
    feed_in_rate = float(getattr(config, "FEED_IN_PRICE_PER_KWH", 0.0))
    display_name = (getattr(config, "PLANT_NAME", None) or "").strip()

    async with ClientSession() as session:
        auth = Auth(
            server,
            str(config.APP_KEY),
            str(config.SECRET_KEY),
            str(config.APP_ID),
            websession=session,
        )
        _attach_auth_tokens(auth)
        tokens_before = _snapshot_tokens(auth)

        plants_api = Plants(auth)

        if not plant_id:
            await _list_plants(auth)
            _persist_tokens_if_changed(tokens_before, _snapshot_tokens(auth))
            return

        header_name = display_name
        try:
            details = await plants_api.async_get_plant_details(plant_id)
            if details and not header_name:
                header_name = str(details[0].get("ps_name") or plant_id)
        except PySolarCloudException:
            if not header_name:
                header_name = plant_id

        reset = "\033[0m" if _use_color() else ""
        bold = "\033[1m" if _use_color() else ""

        now = datetime.now(tz)
        print()
        print(f"{bold}iSolarCloud — {header_name}{reset} — {now.strftime('%a %d %b %Y %H:%M %Z')}")
        print()

        # --- Current snapshot ---
        try:
            rt = await plants_api.async_get_realtime_data(
                plant_id,
                measure_points=list(dict.fromkeys(REALTIME_GEN + REALTIME_LOAD)),
            )
        except PySolarCloudException as e:
            print(f"Could not load real-time data: {e}", file=sys.stderr)
            rt = {}

        pdata = rt.get(str(plant_id), {})
        gen_w, gen_key = _realtime_pick(pdata, REALTIME_GEN)
        load_w, load_key = _realtime_pick(pdata, REALTIME_LOAD)

        print(f"{bold}Now{reset}")
        print(
            f"  Generation:   {_fmt_kw_w(gen_w)} kW"
            + (f"  ({gen_key})" if gen_key else "")
        )
        print(
            f"  Consumption:  {_fmt_kw_w(load_w)} kW"
            + (f"  ({load_key})" if load_key else "")
        )
        print()

        # --- Last 7 local days ---
        day_starts: list[datetime] = []
        today = now.date()
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            day_starts.append(datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=tz))

        hist_codes = set(HIST_POINTS)
        rows_out: list[
            tuple[
                str,
                float | None,
                float | None,
                float | None,
                float | None,
                float | None,
                float | None,
            ]
        ] = []

        for start in day_starts:
            label = start.strftime("%Y-%m-%d")
            prod = load = feed = buy = None
            series = await _historical_series_for_calendar_day(
                plants_api, plant_id, start, HIST_POINTS
            )
            mx = _max_per_code(series, hist_codes)
            prod, _ = _pick_first_wh(
                mx,
                ["daily_yield", "daily_pv_yield_ems", "inverter_daily_yield"],
            )
            load, _ = _pick_first_wh(mx, ["daily_load_consumption"])
            feed, _ = _pick_first_wh(mx, ["daily_feed_in_energy_pv", "feed_in_energy_today"])
            buy, _ = _pick_first_wh(mx, ["energy_purchased_today"])

            buy_kwh = buy / 1000.0 if buy is not None else None
            feed_kwh = feed / 1000.0 if feed is not None else None
            cost = buy_kwh * purchase_rate if buy_kwh is not None else None
            income = feed_kwh * feed_in_rate if feed_kwh is not None else None
            rows_out.append((label, prod, load, feed, buy, cost, income))

        print(f"{bold}Last 7 days{reset} — energy and money from config tariffs")
        col_date = "Date"
        col_pv = "PV kWh"
        col_ld = "Load"
        col_fi = "FeedIn kWh"
        col_buy = "Buy kWh"
        col_cost = f"Cost ({currency})"
        col_inc = f"Income ({currency})"
        w_date = 10
        w_pv = max(len(col_pv), 8)
        w_ld = 8
        w_fi = max(len(col_fi), 8)
        w_buy = max(len(col_buy), 8)
        w_cost = max(len(col_cost), 8)
        w_inc = max(len(col_inc), 8)
        sep = " | "
        header = (
            f"{col_date:<{w_date}}{sep}{col_pv:>{w_pv}}{sep}{col_ld:>{w_ld}}"
            f"{sep}{col_fi:>{w_fi}}{sep}{col_buy:>{w_buy}}"
            f"{sep}{col_cost:>{w_cost}}{sep}{col_inc:>{w_inc}}"
        )
        print(header)
        print("-" * len(header))
        for label, prod, load, feed, buy, cost, income in rows_out:
            line = (
                f"{label:<{w_date}}{sep}{_fmt_kwh_wh(prod):>{w_pv}}{sep}"
                f"{_fmt_kwh_wh(load):>{w_ld}}{sep}{_fmt_kwh_wh(feed):>{w_fi}}{sep}"
                f"{_fmt_kwh_wh(buy):>{w_buy}}{sep}{_fmt_plain_amount(cost):>{w_cost}}{sep}"
                f"{_fmt_plain_amount(income):>{w_inc}}"
            )
            print(line)

        tp = _sum_optional([r[1] for r in rows_out])
        tl = _sum_optional([r[2] for r in rows_out])
        tf = _sum_optional([r[3] for r in rows_out])
        tb = _sum_optional([r[4] for r in rows_out])
        tc = _sum_optional([r[5] for r in rows_out])
        ti = _sum_optional([r[6] for r in rows_out])
        total_label = "Total"
        print("-" * len(header))
        print(
            f"{total_label:<{w_date}}{sep}{_fmt_kwh_wh(tp):>{w_pv}}{sep}"
            f"{_fmt_kwh_wh(tl):>{w_ld}}{sep}{_fmt_kwh_wh(tf):>{w_fi}}{sep}"
            f"{_fmt_kwh_wh(tb):>{w_buy}}{sep}{_fmt_plain_amount(tc):>{w_cost}}{sep}"
            f"{_fmt_plain_amount(ti):>{w_inc}}"
        )
        print()

        _persist_tokens_if_changed(tokens_before, _snapshot_tokens(auth))


def main() -> None:
    try:
        asyncio.run(run_report())
    except PySolarCloudException as e:
        print(f"API error: {e}", file=sys.stderr)
        raise SystemExit(2) from e
    except KeyError as e:
        # pysolarcloud can raise KeyError when building PySolarCloudException from some API bodies.
        print(f"API error (unexpected response): {e!r}", file=sys.stderr)
        raise SystemExit(2) from e


if __name__ == "__main__":
    main()

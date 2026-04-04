# Copy this file to config.py and fill in real values.
# config.py is gitignored — never commit it.
#
# -----------------------------------------------------------------------------
# OAuth (one-time) — get ACCESS_TOKEN and REFRESH_TOKEN
# -----------------------------------------------------------------------------
# Easiest: from the project directory run (after pip install / venv):
#   ./run_get_token.sh        (desktop, after ./setup.sh)
#   ./run_get_token_termux.sh (Termux)
#   or: python3 get_access_token.py
# It prints step-by-step instructions and the lines to paste below.
#
# Manual outline:
# 1. Register your app at https://developer-api.isolarcloud.com and note:
#    APP_KEY, SECRET_KEY (portal may call it "Secret Key"), APP_ID (from Authorize URL).
# 2. Set ISOLAR_SERVER to your region (must match the gateway you use):
#    Europe, International, Australia, or China (see pysolarcloud.Server).
# 3. Set REDIRECT_URI to the same redirect URL registered for your app.
# 4. In Python (once), run:
#        from aiohttp import ClientSession
#        from pysolarcloud import Auth, Server
#        import asyncio
#        async def main():
#            async with ClientSession() as session:
#                auth = Auth(Server.Europe, "APP_KEY", "SECRET", "APP_ID", websession=session)
#                print(auth.auth_url("YOUR_REDIRECT_URI"))
#        asyncio.run(main())
#    Open the printed URL in a browser, log in, select plant access, approve.
#    You will be redirected to REDIRECT_URI?code=... — copy the "code" query value.
# 5. Exchange the code:
#        async def main():
#            async with ClientSession() as session:
#                auth = Auth(Server.Europe, "APP_KEY", "SECRET", "APP_ID", websession=session)
#                await auth.async_authorize("PASTE_CODE", "YOUR_REDIRECT_URI")
#                print(auth.tokens)
#        asyncio.run(main())
# 6. Copy access_token, refresh_token from auth.tokens, set TOKEN_EXPIRES_AT to
#    int(time.time()) + expires_in - 20 (expires_in comes from the token response).
#
# -----------------------------------------------------------------------------
# Plant and display
# -----------------------------------------------------------------------------
# Leave PLANT_ID empty and run isolar_report.py once to print available plant IDs.
PLANT_ID = ""

# Optional label in the report header (if empty, the API plant name is used when available).
PLANT_NAME = ""

# IANA timezone for calendar-day boundaries (production/load daily counters are per local day).
TIMEZONE = "Europe/Madrid"

# -----------------------------------------------------------------------------
# Tariffs (money columns) — price per kWh in your currency
# -----------------------------------------------------------------------------
PURCHASE_PRICE_PER_KWH = 0.0
FEED_IN_PRICE_PER_KWH = 0.0
CURRENCY_SYMBOL = "EUR"

# -----------------------------------------------------------------------------
# Secrets — only in config.py on your device (never commit)
# -----------------------------------------------------------------------------
ISOLAR_SERVER = "Europe"

APP_KEY = "YOUR_APP_KEY"
SECRET_KEY = "YOUR_SECRET_KEY"
APP_ID = "YOUR_APPLICATION_ID"
REDIRECT_URI = "https://example.com/oauth/callback"

ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
REFRESH_TOKEN = "YOUR_REFRESH_TOKEN"
# Unix timestamp when ACCESS_TOKEN expires; used to decide when to refresh.
TOKEN_EXPIRES_AT = 0

# CSGORoll → Buff163 → skins.com tool

Reads CSGORoll market listings, applies your coin filter, looks each item up on Buff163,
estimates the skins.com instant-sell payout (Buff price × 0.95), and ranks the best deals.
It only reads prices. It never buys, sells or trades.

## 1. Build the .exe (Windows)
1. Install Python 3.10+ from python.org (tick "Add to PATH").
2. Double-click `build_exe.bat`.
3. Your app is `dist\CSGORollArb.exe`. Keep these next to it: `config.json` (created on first run) and `csgoroll_request.txt` (step 2).

You can also skip the exe and run `python arb_bot.py`.

## 2. Give it your CSGORoll request (one time, repeat if it expires)
I can't see CSGORoll's private API from here, so the app replays the same request your browser makes.
1. Open https://www.csgoroll.com/trade/market/ in Chrome and log in.
2. Press F12 → Network tab → filter "Fetch/XHR" → refresh the page.
3. Find the request that returns the item list (usually a `graphql` request whose response contains item names and prices).
4. Right-click it → Copy → **Copy as cURL (bash)**. (Not the cmd/PowerShell version.)
5. Paste into a new file named `csgoroll_request.txt` next to the app, and save.

If you get 401/403 later, the login token expired: repeat steps 2–5.

## 3. Buff163 cookie
Log in to buff.163.com, press F12 → Application → Cookies, copy the `session` value, and put it in `config.json`:
`"buff_cookie": "session=PASTE_HERE"`

## 4. Set your rates (important)
The defaults are placeholders, check them:
- `usd_per_coin`: what 1 CSGORoll coin is worth in USD
- `cny_per_usd`: current CNY per 1 USD
- `skinscom_factor`: 0.95 (your "Buff minus 5%")
- `buff_price_mode`: `sell_min` (lowest listing) or `buy_max` (highest buy order). Also a dropdown in the app.

## 5. Use it
Set Min coins / Max coins (the coin filter) and Min ROI %, press **Fetch & Compare**.
The filter runs before the Buff lookups, so a narrow range is much faster.
Results are sorted by ROI. Export CSV saves them.

## Notes
- Buff lookups are throttled (about 1–2 seconds each) and cached for 30 minutes to avoid being rate-limited.
- Items with fewer than `min_buff_listings` (default 3) Buff listings are skipped, since a thin market gives fake low prices.
- Names must match Buff's `market_hash_name` exactly (e.g. `AK-47 | Redline (Field-Tested)`). Items that don't match are skipped.
- Float, stickers and pattern premiums are not priced. A listing with valuable stickers may look overpriced and a high-float one may look cheap.
- skins.com's real payout can differ from Buff minus 5%, and CSGORoll or skins.com may change fees or terms. Check the live numbers before acting.
- Automated requests may go against CSGORoll's or Buff's terms of service. Use it lightly and at your own risk.
- If it finds 0 listings, the JSON keys differ. Edit `name_keys` / `price_keys` in `config.json` to match your response.

## Build the .exe on GitHub (no Python needed on your PC)
1. Create a new **private** repo on github.com (private matters: never commit your cookie or request file; `.gitignore` already excludes them).
2. Upload everything in this folder, including the hidden `.github` folder (drag the folder contents into "Add file → Upload files", or use git).
3. Open the **Actions** tab → "Build Windows exe" → wait ~2 minutes.
4. Open the finished run, scroll to **Artifacts**, download `CSGORollArb-windows`, unzip it to get `CSGORollArb.exe`.
5. Put `csgoroll_request.txt` next to the exe and double-click it. A window opens (no black cmd window). `config.json` is created on first run.

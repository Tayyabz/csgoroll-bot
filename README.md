# CSGORoll → Buff163 → skins.com tool

Press one button. The app opens its own Chrome (or Edge) window, reads the CSGORoll market listings,
keeps the ones in your coin range, looks each up on Buff163, estimates the skins.com instant-sell
payout (Buff price × 0.95) and ranks the deals. It only reads prices. It never buys, sells or trades.

## Get the .exe
It builds automatically on GitHub: **Actions** tab → latest "Build Windows exe" run → Artifacts →
`CSGORollArb-windows` → unzip → `CSGORollArb.exe`. (Or run `build_exe.bat` on a PC with Python.)

## Use it
1. You need **Google Chrome** (or Microsoft Edge) installed.
2. Double-click `CSGORollArb.exe`. A window opens (no black console).
3. Set **Min coins / Max coins** (the coin filter), **Min ROI %**, and the two rates (see below).
4. Press **Fetch & Compare**. A browser window opens on the CSGORoll market.
   - **First time only:** log in to CSGORoll in that window. If Buff163 asks, log in there too.
     The logins are saved in the `browser_profile` folder next to the exe, so later runs need nothing.
   - Leave the window alone while it scrolls. It closes by itself when done.
5. Results appear sorted by ROI. **Export CSV** saves them.

Tip: if the site's list is sorted high to low (default), the app stops scrolling once it reaches
listings below your Min coins, so a narrow range with a high minimum is fast.

## Set your rates (important)
The defaults are placeholders. Check them in the app (top bar) or `config.json`:
- `usd_per_coin`: what 1 CSGORoll coin is worth in USD
- `cny_per_usd`: current CNY per 1 USD
- `skinscom_factor`: 0.95 (your "Buff minus 5%")
- `buff_price_mode`: lowest listing or highest buy order (dropdown in the app)

## If something goes wrong
- **"Captured no listings"**: the items must be visible on the market page in the opened window.
  If they are, CSGORoll's data uses different field names. Edit `name_keys` / `price_keys` in `config.json`.
- **Cloudflare / captcha**: solve it in the window; the app keeps waiting (up to `login_wait_seconds`).
- **"Could not open Chrome or Edge"**: install Chrome, or put the full path of a Chromium browser in `browser_executable`.
- **Buff rate limit (429)**: wait a few minutes. Lookups are throttled and cached for 30 minutes.
- Old method: set `"use_browser": false` and provide `csgoroll_request.txt` (cURL, bash format).

## Notes
- Items with fewer than `min_buff_listings` (default 3) Buff listings are skipped (thin markets give fake low prices).
- Names must match Buff's `market_hash_name` exactly (e.g. `AK-47 | Redline (Field-Tested)`); others are skipped.
- Float, stickers and pattern premiums are not priced.
- skins.com's real payout can differ from Buff minus 5%. Check live numbers before acting.
- Automated browsing may go against CSGORoll's or Buff's terms of service. Use it lightly, at your own risk.
- Never commit `browser_profile/` or `config.json` to GitHub (they hold your logins; `.gitignore` excludes them).

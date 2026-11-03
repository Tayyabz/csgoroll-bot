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
3. Set **Budget coins** (the coins you have) and **Max skins** (the most skins you're willing to buy).
   Min/Max coins is an optional extra filter; Max is automatically capped at your budget.
4. Press **Fetch & Compare**. A browser window opens on the CSGORoll market.
   - **First time only:** log in to CSGORoll in that window. If Buff163 asks, log in there too.
     The logins are saved in the `browser_profile` folder next to the exe, so later runs need nothing.
   - Leave the window alone while it scrolls. It closes by itself when done.
5. The **Best basket** box at the top shows the skins (one or several, within your budget) that lose the least cash when sold.
   The table lists every listing sorted by **Keep %** (how much of what you paid comes back). Click any header to re-sort.
   Items not found on Buff are at the bottom with "-". Change Budget/Max skins and press **Best basket** to recompute without re-fetching. **Export CSV** saves the table.

Tip: if the site's list is sorted high to low (default), the app stops scrolling once it reaches
listings below your Min coins, so a narrow range with a high minimum is fast.

Tip 2: after the first listings load you get 15 seconds to use the site's own sort / price filter in the window
(for example price up to your budget). Then the app scrolls and collects whatever the site shows.

## Set your rates (important)
The defaults are placeholders. Check them in the app (top bar) or `config.json`:
- `usd_per_coin`: what 1 CSGORoll coin is worth in USD (default 0.7011478)
- `cny_per_usd`: CNY per 1 USD. It is fetched live each run; the number in the app is only a fallback.
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
- Nothing is filtered out except by your coin range. Check the **Buff #** column (number of Buff listings): a low number means the Buff price may be unreliable.
- Names must match Buff's `market_hash_name` exactly (e.g. `AK-47 | Redline (Field-Tested)`); others are shown at the bottom without prices.
- Float, stickers and pattern premiums are not priced.
- skins.com's real payout can differ from Buff minus 5%. Check live numbers before acting.
- Automated browsing may go against CSGORoll's or Buff's terms of service. Use it lightly, at your own risk.
- Never commit `browser_profile/` or `config.json` to GitHub (they hold your logins; `.gitignore` excludes them).

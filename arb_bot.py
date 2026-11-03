"""
CSGORoll -> Buff163 -> skins.com comparison tool.

Press "Fetch & Compare":
  1. replays your saved CSGORoll market request (csgoroll_request.txt)
  2. keeps only listings inside your coin range (the coin filter)
  3. looks each unique item up on Buff163 (CNY price)
  4. estimates the skins.com instant-sell payout (Buff price x 0.95 by default)
  5. ranks listings by profit / ROI

It only READS prices. It does not buy, sell, or trade anything.
"""
import csv
import json
import os
import random
import shlex
import sys
import threading
import time

import requests

APP_DIR = os.path.dirname(
    os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__)
)
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
CURL_PATH = os.path.join(APP_DIR, "csgoroll_request.txt")
CACHE_PATH = os.path.join(APP_DIR, "buff_cache.json")

DEFAULT_CONFIG = {
    # PLACEHOLDERS - set these to the current real rates before trusting results
    "usd_per_coin": 0.61,          # what 1 CSGORoll coin is worth in USD
    "cny_per_usd": 7.2,            # CNY -> USD conversion for Buff prices
    "skinscom_factor": 0.95,       # skins.com instant sell = Buff price x this
    "buff_price_mode": "sell_min", # "sell_min" = lowest listing, "buy_max" = highest buy order
    "buff_cookie": "",             # paste your buff.163.com cookie, e.g. session=xxxx
    "min_buff_listings": 3,        # ignore Buff prices backed by fewer listings (fake lows)
    "max_pages": 20,               # max CSGORoll pages to pull per fetch
    "cache_minutes": 30,           # reuse Buff prices this long to avoid hammering Buff
    "min_coins": 0.0,
    "max_coins": 100000.0,
    "min_roi_pct": 0.0,
    # keys the parser looks for in the CSGORoll JSON (edit if your response differs)
    "name_keys": ["marketName", "market_hash_name", "marketHashName", "fullName", "name"],
    "price_keys": ["value", "coinValue", "coins", "price"],
}

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


# ----------------------------------------------------------------- config ---
def load_config():
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass
    else:
        save_config(cfg)
    return cfg


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


# ------------------------------------------------------------- CSGORoll -----
def parse_curl(text):
    """Parse a 'Copy as cURL (bash)' command from browser DevTools."""
    text = text.replace("\\\r\n", " ").replace("\\\n", " ")
    tokens = shlex.split(text)
    url, headers, body = None, {}, None
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in ("-H", "--header") and i + 1 < len(tokens):
            k, _, v = tokens[i + 1].partition(":")
            headers[k.strip()] = v.strip()
            i += 2
            continue
        if t in ("-b", "--cookie") and i + 1 < len(tokens):
            headers["Cookie"] = tokens[i + 1]
            i += 2
            continue
        if t in ("--data-raw", "--data", "--data-binary", "--data-ascii", "-d") and i + 1 < len(tokens):
            body = tokens[i + 1]
            i += 2
            continue
        if t.startswith("http") and url is None:
            url = t
        i += 1
    for bad in ("content-length", "accept-encoding", "host"):
        for k in list(headers):
            if k.lower() == bad:
                del headers[k]
    return url, headers, body


def _num(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v)
        except ValueError:
            return None
    return None


def extract_items(node, name_keys, price_keys, out=None):
    """Walk any JSON and collect dicts that look like {name, price}."""
    if out is None:
        out = []
    if isinstance(node, dict):
        name = next((node[k] for k in name_keys if isinstance(node.get(k), str) and node.get(k)), None)
        price = next((_num(node[k]) for k in price_keys if _num(node.get(k)) is not None), None)
        if name and price is not None:
            out.append({"id": node.get("id"), "name": name, "coins": price})
        for v in node.values():
            extract_items(v, name_keys, price_keys, out)
    elif isinstance(node, list):
        for v in node:
            extract_items(v, name_keys, price_keys, out)
    return out


def find_page_info(node):
    if isinstance(node, dict):
        if "endCursor" in node and "hasNextPage" in node:
            return node
        for v in node.values():
            r = find_page_info(v)
            if r:
                return r
    elif isinstance(node, list):
        for v in node:
            r = find_page_info(v)
            if r:
                return r
    return None


def fetch_csgoroll(cfg, log):
    if not os.path.exists(CURL_PATH):
        raise RuntimeError(
            "csgoroll_request.txt not found. Follow the README: copy the market request "
            "as cURL (bash) from your browser and save it next to the app."
        )
    with open(CURL_PATH, "r", encoding="utf-8") as f:
        url, headers, body = parse_curl(f.read())
    if not url:
        raise RuntimeError("Could not find a URL in csgoroll_request.txt")
    payload = json.loads(body) if body else None

    items, seen = [], set()
    for page in range(int(cfg["max_pages"])):
        if payload is not None:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
        else:
            r = requests.get(url, headers=headers, timeout=30)
        if r.status_code in (401, 403):
            raise RuntimeError(
                f"CSGORoll returned {r.status_code}. Your saved request has expired - "
                "re-copy it from the browser (README step 2)."
            )
        r.raise_for_status()
        data = r.json()
        found = extract_items(data, cfg["name_keys"], cfg["price_keys"])
        new = 0
        for it in found:
            key = it["id"] or (it["name"], it["coins"])
            if key not in seen:
                seen.add(key)
                items.append(it)
                new += 1
        log(f"CSGORoll page {page + 1}: {new} listings")
        pi = find_page_info(data)
        if not pi or not pi.get("hasNextPage") or not new:
            break
        # advance the cursor in the GraphQL variables
        target = payload[0] if isinstance(payload, list) else payload
        if not isinstance(target, dict):
            break
        target.setdefault("variables", {})["after"] = pi["endCursor"]
    return items


# ----------------------------------------------------------------- Buff -----
def load_cache():
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(cache):
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f)
    except Exception:
        pass


def buff_lookup(name, session, cache, ttl_s):
    """Return {'sell_min','buy_max','sell_num'} in CNY, or None if not found."""
    c = cache.get(name)
    if c and time.time() - c.get("t", 0) < ttl_s:
        return None if c.get("missing") else c

    r = session.get(
        "https://buff.163.com/api/market/goods",
        params={"game": "csgo", "page_num": 1, "search": name,
                "use_suggestion": 0, "_": int(time.time() * 1000)},
        timeout=20,
    )
    if r.status_code == 429:
        raise RuntimeError("Buff rate-limited you (429). Wait a few minutes and retry.")
    j = r.json()
    if j.get("code") != "OK":
        raise RuntimeError(
            f"Buff error: {j.get('error') or j.get('code')} - check your buff_cookie in config.json"
        )
    for it in j["data"]["items"]:
        if it.get("market_hash_name") == name:
            res = {
                "sell_min": float(it.get("sell_min_price") or 0),
                "buy_max": float(it.get("buy_max_price") or 0),
                "sell_num": int(it.get("sell_num") or 0),
                "t": time.time(),
            }
            cache[name] = res
            return res
    cache[name] = {"missing": True, "t": time.time()}
    return None


# ------------------------------------------------------------- compare ------
def compute_row(listing, buff, cfg):
    cost = listing["coins"] * cfg["usd_per_coin"]
    buff_cny = buff["sell_min"] if cfg["buff_price_mode"] == "sell_min" else buff["buy_max"]
    buff_usd = buff_cny / cfg["cny_per_usd"]
    payout = buff_usd * cfg["skinscom_factor"]
    profit = payout - cost
    roi = (profit / cost * 100) if cost > 0 else 0.0
    return {
        "name": listing["name"], "coins": listing["coins"], "cost_usd": cost,
        "buff_cny": buff_cny, "buff_usd": buff_usd, "payout_usd": payout,
        "profit_usd": profit, "roi_pct": roi, "buff_listings": buff["sell_num"],
    }


def run_compare(listings, cfg, log, stop=lambda: False, lookup=buff_lookup, sleep=True):
    lo, hi = float(cfg["min_coins"]), float(cfg["max_coins"])
    filtered = [x for x in listings if lo <= x["coins"] <= hi]
    log(f"Coin filter {lo:g}-{hi:g}: {len(filtered)} of {len(listings)} listings kept")

    names = sorted({x["name"] for x in filtered})
    cache = load_cache()
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept": "application/json",
                            "Referer": "https://buff.163.com/market/csgo"})
    if cfg.get("buff_cookie"):
        session.headers["Cookie"] = cfg["buff_cookie"]
    ttl = float(cfg["cache_minutes"]) * 60

    prices = {}
    for n, name in enumerate(names, 1):
        if stop():
            log("Stopped.")
            break
        cached = cache.get(name) and time.time() - cache[name].get("t", 0) < ttl
        try:
            prices[name] = lookup(name, session, cache, ttl)
        except RuntimeError as e:
            log(str(e))
            break
        log(f"Buff {n}/{len(names)}: {name}" + (" (cached)" if cached else ""))
        if sleep and not cached:
            time.sleep(random.uniform(1.2, 2.5))
    save_cache(cache)

    rows = []
    for x in filtered:
        b = prices.get(x["name"])
        if not b:
            continue
        if b["sell_num"] < int(cfg["min_buff_listings"]):
            continue
        if (b["sell_min"] if cfg["buff_price_mode"] == "sell_min" else b["buy_max"]) <= 0:
            continue
        row = compute_row(x, b, cfg)
        if row["roi_pct"] >= float(cfg["min_roi_pct"]):
            rows.append(row)
    rows.sort(key=lambda r: r["roi_pct"], reverse=True)
    log(f"Done: {len(rows)} listings pass your filters.")
    return rows


# ------------------------------------------------------------------ GUI -----
COLUMNS = [
    ("name", "Item", 280), ("coins", "Coins", 70), ("cost_usd", "Cost $", 70),
    ("buff_cny", "Buff ¥", 70), ("buff_usd", "Buff $", 70),
    ("payout_usd", "skins.com $", 85), ("profit_usd", "Profit $", 75),
    ("roi_pct", "ROI %", 65), ("buff_listings", "Buff #", 55),
]


def main_gui():
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog

    cfg = load_config()
    root = tk.Tk()
    root.title("CSGORoll → Buff → skins.com")
    root.geometry("1000x620")

    top = ttk.Frame(root, padding=8)
    top.pack(fill="x")
    vars_ = {}

    def field(label, key, col, width=8):
        ttk.Label(top, text=label).grid(row=0, column=col * 2, sticky="e", padx=(8, 2))
        v = tk.StringVar(value=str(cfg[key]))
        ttk.Entry(top, textvariable=v, width=width).grid(row=0, column=col * 2 + 1)
        vars_[key] = v

    field("Min coins", "min_coins", 0)
    field("Max coins", "max_coins", 1)
    field("Min ROI %", "min_roi_pct", 2)
    field("$/coin", "usd_per_coin", 3, 6)
    field("CNY/$", "cny_per_usd", 4, 6)

    ttk.Label(top, text="Buff price").grid(row=1, column=0, sticky="e", padx=(8, 2), pady=6)
    mode = tk.StringVar(value="Lowest listing" if cfg["buff_price_mode"] == "sell_min" else "Highest buy order")
    ttk.Combobox(top, textvariable=mode, state="readonly", width=18,
                 values=["Lowest listing", "Highest buy order"]).grid(row=1, column=1, columnspan=2, sticky="w")

    tree = ttk.Treeview(root, columns=[c[0] for c in COLUMNS], show="headings")
    for key, title, w in COLUMNS:
        tree.heading(key, text=title)
        tree.column(key, width=w, anchor="w" if key == "name" else "e")
    tree.pack(fill="both", expand=True, padx=8)

    logbox = tk.Text(root, height=7, state="disabled")
    logbox.pack(fill="x", padx=8, pady=6)

    state = {"rows": [], "stop": False, "busy": False}

    def log(msg):
        def _do():
            logbox.configure(state="normal")
            logbox.insert("end", msg + "\n")
            logbox.see("end")
            logbox.configure(state="disabled")
        root.after(0, _do)

    def show(rows):
        tree.delete(*tree.get_children())
        for r in rows:
            tree.insert("", "end", values=(
                r["name"], f"{r['coins']:.2f}", f"{r['cost_usd']:.2f}", f"{r['buff_cny']:.2f}",
                f"{r['buff_usd']:.2f}", f"{r['payout_usd']:.2f}", f"{r['profit_usd']:.2f}",
                f"{r['roi_pct']:.1f}", r["buff_listings"]))

    def worker():
        try:
            listings = fetch_csgoroll(cfg, log)
            log(f"Pulled {len(listings)} listings from CSGORoll.")
            rows = run_compare(listings, cfg, log, stop=lambda: state["stop"])
            state["rows"] = rows
            root.after(0, lambda: show(rows))
        except Exception as e:
            log(f"ERROR: {e}")
        finally:
            state["busy"] = False
            root.after(0, lambda: fetch_btn.configure(state="normal"))

    def on_fetch():
        if state["busy"]:
            return
        try:
            for k, v in vars_.items():
                cfg[k] = float(v.get())
        except ValueError:
            messagebox.showerror("Bad value", "Coins, ROI and rate fields must be numbers.")
            return
        cfg["buff_price_mode"] = "sell_min" if mode.get() == "Lowest listing" else "buy_max"
        save_config(cfg)
        state.update(busy=True, stop=False)
        fetch_btn.configure(state="disabled")
        threading.Thread(target=worker, daemon=True).start()

    def on_export():
        if not state["rows"]:
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if path:
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(state["rows"][0].keys()))
                w.writeheader()
                w.writerows(state["rows"])

    btns = ttk.Frame(root, padding=(8, 0, 8, 8))
    btns.pack(fill="x")
    fetch_btn = ttk.Button(btns, text="Fetch & Compare", command=on_fetch)
    fetch_btn.pack(side="left")
    ttk.Button(btns, text="Stop", command=lambda: state.update(stop=True)).pack(side="left", padx=6)
    ttk.Button(btns, text="Export CSV", command=on_export).pack(side="left")

    root.mainloop()


def main_cli(argv):
    cfg = load_config()
    args = dict(zip(argv[::2], argv[1::2]))
    for flag, key in (("--min", "min_coins"), ("--max", "max_coins"), ("--roi", "min_roi_pct")):
        if flag in args:
            cfg[key] = float(args[flag])
    rows = run_compare(fetch_csgoroll(cfg, print), cfg, print)
    for r in rows[:30]:
        print(f"{r['roi_pct']:6.1f}%  ${r['profit_usd']:7.2f}  {r['coins']:8.2f}c  {r['name']}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        main_cli(sys.argv[2:])
    else:
        main_gui()

"""
Roll Streak Tracker
-------------------
Logs Roll results (R = red, B = black, G = green, P = bait) and shows, for every
block of 100 rolls, how many times GREEN hit 2 in a row and 3 in a row.

Counting rules (per block of 100 rolls):
  - A "streak" is a maximal run of consecutive greens.
  - 2x  = runs of exactly 2 greens
  - 3x  = runs of exactly 3 greens
  - 4x+ = runs of 4 or more greens
  - Each percentage is  runs / green hits in that block * 100
  - Green% is green hits / rolls in that block * 100
Each 100-roll block gets its own row, so you can compare them.

Keys: r / b / g / p to log a roll, Backspace to undo.
Rolls are auto-saved to rolls_log.csv next to the program.
"""
import csv
import os
import sys

BLOCK = 100
VALID = ("R", "B", "G", "P")


def green_runs(seq):
    """Return list of lengths of consecutive-green runs in seq."""
    runs, cur = [], 0
    for x in seq:
        if x == "G":
            cur += 1
        else:
            if cur:
                runs.append(cur)
            cur = 0
    if cur:
        runs.append(cur)
    return runs


def block_stats(block):
    runs = green_runs(block)
    greens = sum(1 for x in block if x == "G")
    n2 = sum(1 for r in runs if r == 2)
    n3 = sum(1 for r in runs if r == 3)
    n4 = sum(1 for r in runs if r >= 4)

    def pct(v):
        return (v / greens * 100) if greens else 0.0

    return {
        "rolls": len(block),
        "greens": greens,
        "green_pct": greens / len(block) * 100 if block else 0.0,
        "x2": n2, "x2_pct": pct(n2),
        "x3": n3, "x3_pct": pct(n3),
        "x4": n4, "x4_pct": pct(n4),
    }


def all_blocks(rolls):
    return [rolls[i:i + BLOCK] for i in range(0, len(rolls), BLOCK)]


def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


LOG = os.path.join(app_dir(), "rolls_log.csv")


def load_log():
    if not os.path.exists(LOG):
        return []
    with open(LOG, newline="") as f:
        return [r[0] for r in csv.reader(f) if r and r[0] in VALID]


def save_log(rolls):
    with open(LOG, "w", newline="") as f:
        w = csv.writer(f)
        for r in rolls:
            w.writerow([r])


def main():
    import tkinter as tk
    from tkinter import ttk, messagebox

    rolls = load_log()
    root = tk.Tk()
    root.title("Roll Streak Tracker")
    root.geometry("760x520")

    top = ttk.Frame(root, padding=8)
    top.pack(fill="x")
    status = ttk.Label(top, text="", font=("Segoe UI", 11, "bold"))
    status.pack(side="left")

    btns = ttk.Frame(root, padding=(8, 0))
    btns.pack(fill="x")

    cols = ("block", "rolls", "greens", "green_pct", "x2", "x2_pct",
            "x3", "x3_pct", "x4")
    heads = ("Block", "Rolls", "Greens", "Green %", "2x", "2x %",
             "3x", "3x %", "4x+")
    tree = ttk.Treeview(root, columns=cols, show="headings", height=14)
    for c, h in zip(cols, heads):
        tree.heading(c, text=h)
        tree.column(c, width=80, anchor="center")
    tree.pack(fill="both", expand=True, padx=8, pady=8)
    tree.tag_configure("partial", foreground="#888888")

    def refresh():
        tree.delete(*tree.get_children())
        for i, blk in enumerate(all_blocks(rolls), 1):
            s = block_stats(blk)
            label = f"#{i}" if s["rolls"] == BLOCK else f"#{i} (live {s['rolls']}/{BLOCK})"
            tree.insert("", "end", tags=("" if s["rolls"] == BLOCK else "partial",),
                        values=(label, s["rolls"], s["greens"],
                                f"{s['green_pct']:.1f}%", s["x2"],
                                f"{s['x2_pct']:.1f}%", s["x3"],
                                f"{s['x3_pct']:.1f}%", s["x4"]))
        last = rolls[-10:]
        status.config(text=f"Total rolls: {len(rolls)}    Last 10: {' '.join(last) or '-'}")

    def add(v):
        rolls.append(v)
        save_log(rolls)
        refresh()

    def undo(_e=None):
        if rolls:
            rolls.pop()
            save_log(rolls)
            refresh()

    def reset():
        if messagebox.askyesno("Reset", "Delete all logged rolls?"):
            rolls.clear()
            save_log(rolls)
            refresh()

    for text, v in (("Red (r)", "R"), ("Black (b)", "B"),
                    ("Green (g)", "G"), ("Bait (p)", "P")):
        ttk.Button(btns, text=text, command=lambda v=v: add(v)).pack(side="left", padx=3)
    ttk.Button(btns, text="Undo (Backspace)", command=undo).pack(side="left", padx=12)
    ttk.Button(btns, text="Reset", command=reset).pack(side="right", padx=3)

    for k in "rbgp":
        root.bind(k, lambda e, v=k.upper(): add(v))
    root.bind("<BackSpace>", undo)

    refresh()
    root.mainloop()


if __name__ == "__main__":
    main()

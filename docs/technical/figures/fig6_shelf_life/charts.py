"""Fig 6: shelf-life credit bridge. Numbers: docs/technical/TECHNICAL_DOCUMENTATION.md 4.4/4.13,
backend/app/engines/passport.py get_shelf_life_credit, seed/green_life.json planned order o-1."""
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

fam = "Roboto" if any("Roboto" in f.name for f in fm.fontManager.ttflist) else "DejaVu Sans"
plt.rcParams.update({"font.family": fam, "font.size": 13, "axes.spines.top": False,
                     "axes.spines.right": False})
DEEP, MID, BRIGHT, GREY, RED = "#0F5132", "#198754", "#00BF63", "#9AA5B1", "#C0392B"
OUT = Path(__file__).resolve().parent.parent / "out"

fig, (a, b) = plt.subplots(1, 2, figsize=(16 / 1.5, 6 / 1.5 * 1.25), dpi=150,
                           gridspec_kw={"width_ratios": [1.7, 1], "wspace": 0.35})
# (a) waterfall
x = [0, 1, 2]
a.bar(0, 19000, color=GREY, width=0.6)
a.bar(1, 10800, bottom=8200, color=RED, alpha=0.85, width=0.6)
a.bar(2, 8200, color=BRIGHT, width=0.6)
for y in (19000, 8200):
    a.plot([0.3, 0.7] if y == 19000 else [1.3, 1.7], [y, y], color="#555", lw=1, ls="--")
a.text(0, 19000 + 400, "19,000", ha="center", va="bottom", fontsize=14)
a.text(1, 13600, "− 10,800", ha="center", va="center", color="white", fontsize=14, weight="bold")
a.text(2, 8200 + 400, "8,200", ha="center", va="bottom", fontsize=15, weight="bold", color=DEEP)
a.set_xticks(x, ["Purpose-blind\nlender", "Stock that won't\nsell before expiry", "LaMP lends\nat most"])
a.set_ylabel("BDT, shortfall on 26 Oct")
a.set_ylim(0, 22000)
a.yaxis.set_major_formatter(lambda v, _: f"{v:,.0f}")
a.grid(axis="y", color="#e5e5e5"); a.set_axisbelow(True)
a.set_title("(a) Shelf-life credit", loc="left", fontsize=15, weight="bold")
# (b) Montelukast line
b.barh([0], [12], color=MID, height=0.5)
b.barh([0], [18], left=12, color=RED, alpha=0.85, height=0.5)
b.text(6, 0, "12 sell", ha="center", va="center", color="white", weight="bold")
b.text(21, 0, "18 unsold\n18 × 600 = 10,800", ha="center", va="center", color="white", weight="bold", fontsize=12)
b.set_xlim(0, 30); b.set_xticks([0, 12, 30]); b.set_yticks([])
b.set_xlabel("Boxes ordered (Montelukast, 30)")
b.spines["left"].set_visible(False)
b.text(0, -0.75, "0.2 boxes/day × (90 − 30) days = 12", fontsize=12.5, color="#333")
b.set_ylim(-1, 0.6)
b.set_title("(b) Per-product rule", loc="left", fontsize=15, weight="bold")
for ext in ("pdf", "png"):
    fig.savefig(OUT / f"fig6_shelf_life.{ext}", dpi=300, bbox_inches="tight")

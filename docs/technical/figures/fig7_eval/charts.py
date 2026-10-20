"""fig7_eval: evaluation results panel. Sources: eval/results.md, eval/intent_results.md,
eval/redteam_results.md, eval/shelf_life_sim.json. Re-render: python charts.py"""
import json, pathlib
import matplotlib as mpl, matplotlib.pyplot as plt
ROOT = pathlib.Path(__file__).resolve().parents[4]
OUT = pathlib.Path(__file__).resolve().parents[1] / "out"
INK, MUTED, BLUE, GREEN, ORANGE, RED, PURPLE, TEAL = "#1f2933", "#5b6673", "#2563a8", "#2f855a", "#c05621", "#b83232", "#6b46c1", "#1f7a7a"
mpl.rcParams.update({"font.family": "Roboto", "font.size": 12, "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#9aa5b1", "pdf.fonttype": 42})
sim = json.loads((ROOT / "eval/shelf_life_sim.json").read_text())["summary"]

fig, axs = plt.subplots(2, 2, figsize=(10.67, 7.6), gridspec_kw={"hspace": 0.55, "wspace": 0.95})

def hbars(ax, rows, color, title, h=0.62):
    labels = [r[0] for r in rows]; y = range(len(rows))[::-1]
    for yi, (lab, k, n, c) in zip(y, rows):
        frac = k / n if n else 0
        ax.barh(yi, 1, color="#eef1f4", height=h)
        ax.barh(yi, frac, color=c or color, height=h)
        ax.text(1.03, yi, f"{k}/{n}", va="center", fontsize=12, fontweight="bold", color=c or color,
                fontfeatures=None) if False else ax.text(1.03, yi, f"{k}/{n}", va="center", fontsize=12, fontweight="bold", color=c or color)
    ax.set_yticks(list(y)); ax.set_yticklabels(labels)
    ax.set_xlim(0, 1); ax.set_xticks([0, .5, 1]); ax.set_xticklabels(["0%", "50%", "100%"])
    ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False)
    ax.grid(axis="x", color="#e4e7eb", lw=0.8); ax.set_axisbelow(True)
    ax.set_title(title, loc="left", fontsize=14, fontweight="bold", pad=10)

hbars(axs[0, 0], [("Text fields", 305, 305, None), ("Numbers", 409, 409, None), ("Line items / days", 116, 116, None),
    ("Injection flagged", 2, 2, None), ("False flags (clean)", 0, 25, RED)], BLUE, "(a) Photo reading, 27 synthetic photos")
hbars(axs[0, 1], [("Data questions", 15, 15, None), ("Action proposals", 3, 3, None), ("Out-of-scope declines", 2, 2, None)],
    PURPLE, "(b) Chat intent routing, 20 questions", h=0.45)
hbars(axs[1, 0], [("Direct HTTP call", 10, 10, None), ("Approval path", 6, 6, None), ("Chat injection", 8, 8, None),
    ("Photo injection", 2, 2, None)], GREEN, "(c) Red-team attacks held, 26 cases")

ax = axs[1, 1]
measures = [("financed", "Amount financed"), ("financed_unsold", "Financed stock\nexpiring unsold")]
for i, (key, lab) in enumerate(measures):
    for j, (who, c, name) in enumerate([("blind", ORANGE, "Purpose-blind lender"), ("slc", TEAL, "Shelf-life credit")]):
        s = sim[key][who]; y = 1 - i + (0.17 if j == 0 else -0.17)
        ax.plot([s["p10"], s["p90"]], [y, y], color=c, lw=2.2, solid_capstyle="round")
        ax.plot([s["p10"], s["p90"]], [y, y], "|", color=c, ms=9, mew=2)
        ax.plot(s["median"], y, "o", color=c, ms=8, label=name if i == 0 else None, zorder=3)
        ax.text(s["median"], y + 0.13, f"{s['median']:,.0f}", ha="center", fontsize=11.5, fontweight="bold", color=c)
ax.set_yticks([1, 0]); ax.set_yticklabels([m[1] for m in measures]); ax.set_ylim(-0.5, 1.55)
ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False)
ax.set_xlim(-1500, 48000); ax.xaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: f"{v/1000:.0f}k"))
ax.set_xlabel("BDT per shop, median with P10 to P90"); ax.grid(axis="x", color="#e4e7eb", lw=0.8); ax.set_axisbelow(True)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.24), ncol=2, frameon=False, fontsize=11.5)
ax.set_title("(d) Simulation, 200 synthetic shops", loc="left", fontsize=14, fontweight="bold", pad=10)

fig.canvas.draw()
r = fig.canvas.get_renderer()
inv = fig.transFigure.inverted()
for col in (0, 1):
    x0 = min(a.get_tightbbox(r).transformed(inv).x0 for a in axs[:, col])
    for a in axs[:, col]:
        t = a.title.get_text(); a.set_title("")
        tr = mpl.transforms.blended_transform_factory(fig.transFigure, a.transAxes)
        a.text(x0, 1.06, t, transform=tr, fontsize=14, fontweight="bold", ha="left", va="bottom")
for ext in ("pdf", "png"):
    fig.savefig(OUT / f"fig7_eval.{ext}", dpi=150 if ext == "png" else None, bbox_inches="tight")

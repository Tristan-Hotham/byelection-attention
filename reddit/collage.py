"""Reddit collage (r/dataisbeautiful style), light background, 2700 x 2025 px: the monthly event study of Commons
mentions of by-election towns against matched towns, headline numbers, the change-of-hands contrast and the era split.
Run after code/04_results.py:  python3 reddit/collage.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "code"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
import numpy as np, pandas as pd
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "IBMPlexMono-Regular.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name()
plt.rcParams.update({"font.family": "Source Serif 4", "axes.unicode_minus": False, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#6E604E", "xtick.color": "#6E604E", "ytick.color": "#6E604E"})
PAPER, INK, MUT, RED, BLUE, GREY = "#FAF6EC", "#2B2119", "#6E604E", "#B4442E", "#2F6A9E", "#9C9384"
HALO = [pe.withStroke(linewidth=4, foreground=PAPER)]
R = jload(f"{DATA}/results.json")
ES = pd.read_csv(f"{DATA}/event_study.csv")
S, x = R["sample"], R["x"]

fig = plt.figure(figsize=(13.5, 10.125), dpi=200)
fig.patch.set_facecolor(PAPER)
fig.text(0.035, 0.955, "Do by-elections make Parliament listen?", family=DISP, fontsize=31, fontweight="bold", color=INK, va="top")
fig.text(0.035, 0.895, f"House of Commons speeches saying \"in <town>\" for the town named in the seat, around {S['byelections']} UK by-elections\n"
         f"({S['first']} to {S['last']}), against five similar towns each with no by-election, month by month", fontsize=13.5, color=MUT, va="top")
# main chart
ax = fig.add_axes([0.085, 0.21, 0.51, 0.56]); ax.set_facecolor(PAPER)
ax.axvspan(-12.5, -0.5, color="#F1E9D6", lw=0, zorder=0)
m, lo, hi = 1 + ES.b / 100, 1 + ES.lo / 100, 1 + ES.hi / 100
ax.fill_between(ES.k, lo, hi, color=RED, alpha=0.17, lw=0)
ax.plot(ES.k, m, color=RED, lw=2.4, marker="o", ms=3.5, zorder=3)
ax.axhline(1, color=INK, lw=1); ax.axvline(0, color=INK, lw=1, ls=(0, (3, 2)))
ax.set_yscale("log"); ax.set_yticks([0.5, 1, 2, 4, 8]); ax.set_yticklabels(["0.5x", "1x", "2x", "4x", "8x"], fontsize=11); ax.minorticks_off()
ax.set_ylim(0.38, 11); ax.set_xlim(-12.8, 36.8); ax.set_xticks([-12, -6, 0, 6, 12, 18, 24, 30, 36])
ax.set_xticklabels(["-12", "-6", "polling\nday", "+6", "+12", "+18", "+24", "+30", "+36"], fontsize=11)
ax.set_xlabel("months from polling day", fontsize=12, color=INK)
ax.text(-12, 9.2, "before polling", fontsize=11, color=MUT)
pk = R["es"]["k0"]
ax.annotate(f"polling month: {1 + pk['b'] / 100:.1f}x", (0, 1 + pk["b"] / 100), (6, 8.3), fontsize=12.5, color=RED, path_effects=HALO,
            arrowprops=dict(arrowstyle="-", color=MUT, lw=0.8, shrinkA=2, shrinkB=4))
ax.text(13, 0.43, "red band: 95% interval\nfor each month", fontsize=10.5, color=MUT, path_effects=HALO)
ax.text(30, 6.2, "year 3:\nno clear\ndifference", fontsize=11, color=INK, ha="center", path_effects=HALO)
fig.text(0.075, 0.79, "Mentions of the by-election town against its matched towns", fontsize=13, fontweight="bold", color=INK)
# stat cards
def card(x0, y0, big, txt, col):
    fig.text(x0, y0, big, family=DISP, fontsize=38, fontweight="bold", color=col, va="top")
    fig.text(x0, y0 - 0.07, txt, fontsize=12.3, color=INK, va="top", linespacing=1.3)
card(0.65, 0.81, f"{x['result']:.1f}x", "the mentions in the polling\nmonth and the two after", RED)
card(0.84, 0.81, f"{x['year1']:.1f}x", "still, 3 to 12\nmonths later", RED)
card(0.65, 0.62, f"{x['year2']:.1f}x", "in the second\nyear after", RED)
card(0.84, 0.62, f"{x['changed_hands_result']:.1f}x", f"at the result when the\nseat changed hands\n(held seats: {x['held_result']:.1f}x)", INK)
# era bars
ax2 = fig.add_axes([0.66, 0.21, 0.31, 0.2]); ax2.set_facecolor(PAPER)
eras = ["1911 to 1944", "1945 to 1979", "1980 to 2023"]
for i, e in enumerate(eras):
    d = R["het"]["era"]["est"][e]["result"]; v, l, h = 1 + d["b"] / 100, 1 + d["lo"] / 100, 1 + d["hi"] / 100
    ax2.plot([l, h], [i, i], color=RED if l > 1 else GREY, lw=3)
    ax2.plot(v, i, "o", color=RED if l > 1 else GREY, ms=10)
    ax2.text(h * 1.12, i, f"{v:.1f}x", va="center", fontsize=12, color=INK)
ax2.axvline(1, color=INK, lw=1)
ax2.set_xscale("log"); ax2.set_xticks([0.5, 1, 2, 4, 8, 16]); ax2.set_xticklabels(["0.5x", "1", "2x", "4x", "8x", "16x"], fontsize=10.5); ax2.minorticks_off()
ax2.set_xlim(0.45, 30); ax2.set_yticks(range(3)); ax2.set_yticklabels([f"{e}\n({S['by_era'][e]} towns)" for e in eras], fontsize=11)
ax2.set_ylim(2.6, -0.6)
fig.text(0.66, 0.44, "Around polling day, by era (95% interval)", fontsize=13, fontweight="bold", color=INK)
fig.text(0.66, 0.415, "Before 1945: no detectable rise", fontsize=11.5, color=MUT)
fig.text(0.035, 0.07, "1x = as often as the matched towns. Matched towns: same nation, similar mentions and population beforehand, more than 25 km away.\n"
         "Poisson regression, town and month fixed effects, 95% intervals clustered by by-election. Placebos (dates moved two years earlier; neighbouring towns) show no rise.",
         fontsize=10, color=MUT, linespacing=1.4)
fig.text(0.035, 0.018, "Data: Hansard via the UK Parliament API (Open Parliament Licence v3.0); Wikipedia lists of UK by-elections (CC BY-SA 4.0).  "
         "Dr Tristan Hotham  ·  maps.tristanhotham.com/byelection-attention", fontsize=8.0, color=MUT, family="IBM Plex Mono")
out = os.path.join(HERE, "byelection_attention_collage.png")
fig.savefig(out, dpi=200, facecolor=PAPER)
print(out)

"""Step 5: figures for the page (img/*.jpg), the blog (release/blog/b_*.png, 1800 px), the paper (release/paper/f_*.pdf,
vector) and header.png (1200 x 630). Light paper background; warm red = more attention, blue = less, grey = comparison."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import PathPatch
from matplotlib.path import Path
import numpy as np, pandas as pd
from PIL import Image
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform as stransform, unary_union
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
SERIF = "Source Serif 4"; DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name(); MONO = "IBM Plex Mono"
PAPER, INK, MUT, RULE = "#F6EED8", "#2B2119", "#6E604E", "#D9C9A3"
RED, BLUE, GREY, GOLD = "#B4442E", "#2F6A9E", "#9C9384", "#C98A2B"
CMAP = LinearSegmentedColormap.from_list("d", [BLUE, "#8FB0CF", "#C9C2B4", "#E3A58F", RED])
NORM = TwoSlopeNorm(vmin=-3, vcenter=0, vmax=3)
plt.rcParams.update({"font.family": SERIF, "font.size": 12, "axes.edgecolor": MUT, "axes.labelcolor": INK, "xtick.color": MUT,
                     "ytick.color": MUT, "axes.facecolor": PAPER, "figure.facecolor": PAPER, "axes.unicode_minus": False,
                     "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
HALO = [pe.withStroke(linewidth=3, foreground=PAPER)]
R = jload(f"{DATA}/results.json")
ES = pd.read_csv(f"{DATA}/event_study.csv")
BLOG, PAPD = f"{REL}/blog", f"{REL}/paper"
for d_ in (BLOG, PAPD):
    os.makedirs(d_, exist_ok=True)
SRC = "Data: Hansard via the UK Parliament API (Open Parliament Licence v3.0); Wikipedia by-election lists (CC BY-SA 4.0)\nmaps.tristanhotham.com/byelection-attention"


def out(fig, name, page=True, blog=True, paper=True):
    if paper:
        fig.savefig(f"{PAPD}/f_{name}.pdf", facecolor=fig.get_facecolor())
    fig.savefig(f"{SCR}/{name}.png", dpi=220, facecolor=fig.get_facecolor())
    plt.close(fig)
    im = Image.open(f"{SCR}/{name}.png").convert("RGB")
    if page:
        w = min(1500, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{IMG}/{name}.jpg", quality=85, optimize=True)
    if blog:
        im.resize((1800, round(im.size[1] * 1800 / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
    os.remove(f"{SCR}/{name}.png")


def title(fig, t, sub, y=0.965):
    fig.text(0.04, y, t, fontsize=21, fontweight="bold", family=DISP, color=INK, va="top")
    fig.text(0.04, y - 0.058, sub, fontsize=12, color=MUT, va="top")


def foot(fig, s=SRC):
    fig.text(0.04, 0.012, s, fontsize=8.3, family=MONO, color=MUT, va="bottom", linespacing=1.4)


def xfmt(ax, ticks=(0.5, 1, 2, 4, 8)):
    ax.set_yscale("log")
    ax.set_yticks(ticks); ax.set_yticklabels([f"{t:g}x" if t != 1 else "no change" for t in ticks])
    ax.minorticks_off()


def mult(d):
    return 1 + d["b"] / 100, 1 + d["lo"] / 100, 1 + d["hi"] / 100


S = R["sample"]
# ---------- 1. event study: raw means and estimates
fig = plt.figure(figsize=(11, 9))
title(fig, "When a seat holds a by-election, the Commons talks about the town",
      f"{S['pairs']} by-election towns ({S['byelections']} by-elections, {S['first']} to {S['last']}) against 5 matched towns each; month 0 = polling day")
ax1 = fig.add_axes([0.13, 0.56, 0.83, 0.25]); ax2 = fig.add_axes([0.13, 0.12, 0.83, 0.34])
dm = R["desc_means"]; k = np.array(dm["k"])
ax1.plot(k, dm["control"], color=GREY, lw=1.6, label="matched towns, no by-election")
ax1.plot(k, dm["treated"], color=RED, lw=2.2, label="by-election towns")
ax1.axvline(0, color=INK, lw=0.8, ls=(0, (3, 2))); ax1.axhline(1, color=RULE, lw=0.8)
ax1.set_ylabel("mentions a month,\nreference = 1"); ax1.set_xlim(-24.5, 36.5)
ax1.set_xticks(range(-24, 37, 6)); ax1.tick_params(labelsize=10)
ax1.legend(frameon=False, fontsize=10.5, loc="upper right")
fig.text(0.13, 0.825, "A  Average \"in <town>\" mentions, each relative to its own reference months (24 to 13 before)", fontsize=11.5, color=INK, fontweight="bold")
ax2.axvspan(-24.5, -12.5, color="#EFE3C4", zorder=0); ax2.text(-24, 9.5, "reference\nmonths", fontsize=9.5, color=MUT, va="top")
m, lo, hi = 1 + ES.b / 100, 1 + ES.lo / 100, 1 + ES.hi / 100
ax2.fill_between(ES.k, lo, hi, color=RED, alpha=0.18, lw=0)
ax2.plot(ES.k, m, color=RED, lw=1.8, marker="o", ms=3.2)
ax2.axhline(1, color=INK, lw=0.8); ax2.axvline(0, color=INK, lw=0.8, ls=(0, (3, 2)))
xfmt(ax2, (0.5, 1, 2, 4, 8)); ax2.set_ylim(0.4, 11); ax2.set_xlim(-24.5, 36.5); ax2.set_xticks(range(-24, 37, 6))
ax2.set_xlabel("months from polling day"); ax2.set_ylabel("mentions against matched towns")
fig.text(0.13, 0.475, "B  Estimate for each month (Poisson, 95% interval), against matched towns in the same month", fontsize=11.5, color=INK, fontweight="bold")
pk = R["es"]["k0"]
ax2.annotate(f"polling month: {1 + pk['b'] / 100:.1f}x", (0, 1 + pk["b"] / 100), xytext=(8, 4), textcoords="offset points", fontsize=10.5, color=RED, path_effects=HALO)
foot(fig); out(fig, "event")

# ---------- 2. bins: main model and placebos
fig = plt.figure(figsize=(11, 6.6))
title(fig, "A real rise that lasts about two years",
      "Mentions in each period against matched towns (95% intervals); reference: months 24 to 13 before the by-election")
ax = fig.add_axes([0.09, 0.16, 0.86, 0.64])
names = [("pre", "12 to 4\nmonths before"), ("vacancy", "3 to 1\nmonths before"), ("result", "polling month\nand next two"), ("year1", "months\n3 to 12"),
         ("year2", "months\n13 to 24"), ("year3", "months\n25 to 36")]
series = [("M1", "by-election towns (main model)", RED, 0), ("P1", "placebo: dates moved 24 months earlier", BLUE, -0.22),
          ("P2", "placebo: neighbouring towns 3 to 25 km away", "#6C8FB3", 0.22), ("S1", "the seat's own name (\"Member for ...\")", GOLD, 0.11)]
for key, lab, col, dx in series:
    xs, ys, l, h = [], [], [], []
    for i, (b, _) in enumerate(names):
        if b in R[key]:
            a, lo_, hi_ = mult(R[key][b]); xs.append(i + dx); ys.append(a); l.append(a - lo_); h.append(hi_ - a)
    ax.errorbar(xs, ys, yerr=[l, h], fmt="o", color=col, ms=7 if key == "M1" else 5, lw=2 if key == "M1" else 1.3, capsize=0, label=lab)
ax.axhline(1, color=INK, lw=0.8)
xfmt(ax, (0.5, 1, 2, 4)); ax.set_ylim(0.35, 6)
ax.set_xticks(range(len(names))); ax.set_xticklabels([n for _, n in names], fontsize=10.5)
ax.legend(frameon=False, fontsize=10, loc="upper right", ncol=1)
foot(fig); out(fig, "bins")

# ---------- 3. heterogeneity
fig = plt.figure(figsize=(11, 8.6))
title(fig, "Bigger when the seat changes hands, smaller before the war",
      "Mentions against matched towns by kind of by-election (95% intervals); number of towns in brackets")
H = R["het"]
groups = [("changed", "Result", ["held", "changed hands"]), ("govloss", "Government", ["otherwise", "government lost the seat"]),
          ("cause", "Cause", ["death", "resignation", "scandal"]), ("era", "Era", ["1911 to 1944", "1945 to 1979", "1980 to 2023"])]
bins = [("result", "polling month and next two", RED), ("year1", "months 3 to 12", GOLD), ("later", "months 13 to 36", BLUE)]
ax = fig.add_axes([0.3, 0.1, 0.66, 0.7])
yl, yt, y = [], [], 0
for key, gname, levels in groups:
    for lv in levels:
        e = H[key]["est"][lv]
        for j, (b, bl, col) in enumerate(bins):
            a, lo_, hi_ = mult(e[b]); yy = y - 0.22 * (j - 1)
            ax.plot([max(lo_, 0.12), min(hi_, 30)], [yy, yy], color=col, lw=1.8)
            ax.plot(a, yy, "o", color=col, ms=6, label=bl if (key == "changed" and lv == "held") else None)
        yl.append(f"{lv} ({e['pairs']})"); yt.append(y); y -= 1
    y -= 0.6
ax.set_xscale("log"); ax.set_xticks([0.25, 0.5, 1, 2, 4, 8, 16]); ax.set_xticklabels(["0.25x", "0.5x", "no change", "2x", "4x", "8x", "16x"])
ax.minorticks_off(); ax.set_xlim(0.12, 30)
ax.axvline(1, color=INK, lw=0.8)
ax.set_yticks(yt); ax.set_yticklabels(yl, fontsize=11)
yy = 0.5
for key, gname, levels in groups:
    fig.text(0.02, 0, "", fontsize=1)
ys_ = [yt[0], yt[2], yt[4], yt[7]]
for (key, gname, levels), yv in zip(groups, ys_):
    ax.text(0.125, yv + 0.45, gname.upper(), fontsize=9.5, family=MONO, color=MUT, va="bottom")
ax.legend(frameon=False, fontsize=10, loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=3)
ax.set_ylim(y + 0.3, 1)
foot(fig); out(fig, "het")

# ---------- 4. robustness
fig = plt.figure(figsize=(11, 9.6))
title(fig, "The first two years hold up; the third year does not",
      "Every planned check: mentions against matched towns (95% intervals); main model at the top")
ax = fig.add_axes([0.36, 0.1, 0.6, 0.73])
rows = [{"label": "Main model", **R["M1"]}] + [x for x in R["robust"] if x["label"] not in ("Reference months -24 to -4", "OLS of log(1 + mentions)")] + [x for x in R["robust"] if x["label"] == "Reference months -24 to -4"]
for i, x in enumerate(rows):
    for j, (b, col) in enumerate((("result", RED), ("year1", GOLD), ("year2", "#7A9A5A"), ("year3", BLUE))):
        if b not in x: continue
        a, lo_, hi_ = mult(x[b]); yy = -i - 0.17 * (j - 1.5)
        ax.plot([max(lo_, 0.3), min(hi_, 15)], [yy, yy], color=col, lw=1.3)
        ax.plot(a, yy, "o", color=col, ms=4.2, label={"result": "polling month and next two", "year1": "months 3 to 12", "year2": "months 13 to 24", "year3": "months 25 to 36"}[b] if i == 0 else None)
lab = [x["label"].replace("-24 to -4", "24 to 4 before") for x in rows]
ax.set_yticks([-i for i in range(len(rows))]); ax.set_yticklabels(lab, fontsize=9.8)
ax.set_xscale("log"); ax.set_xticks([0.5, 1, 2, 4, 8]); ax.set_xticklabels(["0.5x", "no change", "2x", "4x", "8x"]); ax.minorticks_off(); ax.set_xlim(0.3, 15)
ax.axvline(1, color=INK, lw=0.8); ax.legend(frameon=False, fontsize=9.5, loc="lower left", bbox_to_anchor=(-0.02, 1.0), ncol=4)
ax.set_ylim(-len(rows) + 0.4, 0.6)
foot(fig, "Treated places only: calendar-month fixed effects instead of matched towns. The OLS check (log scale) is in the paper.\nmaps.tristanhotham.com/byelection-attention"); out(fig, "robust")

# ---------- 5. cases: sparklines
SITE = jload(f"{DATA}/site.json")
idx = {}
for b in SITE["b"]:
    for p in b.get("p", []):
        idx[(b["s"], b["y"], p["n"])] = (b, p)
cases = [("Orpington", 1962, "Orpington"), ("Crewe and Nantwich", 2008, "Crewe"), ("Corby", 2012, "Corby"), ("Eastleigh", 2013, "Eastleigh"),
         ("Newbury", 1993, "Newbury"), ("Rotherham", 1933, "Rotherham")]
fig = plt.figure(figsize=(11, 7.4))
title(fig, "Six by-elections and the town's turn in the Commons", "Commons contributions saying \"in <town>\", by quarter, two years before to three years after polling day")
for i, (s, yv, t) in enumerate(cases):
    b, p = idx[(s, yv, t)]
    ax = fig.add_axes([0.06 + (i % 3) * 0.315, 0.53 - (i // 3) * 0.4, 0.27, 0.24])
    xs = np.arange(len(p["sp"])) * 3 + p["s0"]
    ax.bar(xs + 1, p["sp"], width=2.6, color=[RED if 0 <= x_ <= 12 else "#D8B9A8" if x_ > 12 else GREY for x_ in xs], lw=0)
    ax.axvline(0, color=INK, lw=0.8, ls=(0, (3, 2)))
    ax.set_xlim(-25, 37); ax.set_xticks([-24, 0, 12, 36]); ax.set_xticklabels(["-24", "poll", "+12", "+36"], fontsize=9)
    ax.tick_params(labelsize=9)
    ch = "changed hands" if b["ch"] else "held"
    ax.set_title(f"{s} {yv}", loc="left", fontsize=13, fontweight="bold", color=INK, pad=20)
    ax.text(0.0, 1.03, f"{b['ipn']} to {b['wpn']}; {ch}", transform=ax.transAxes, fontsize=9.2, color=MUT, va="bottom")
    ax.text(0.99, 0.97, f"ref. year: {p['r12']}\nyear after: {p['p12']}", transform=ax.transAxes, fontsize=9, family=MONO, color=INK, ha="right", va="top", path_effects=HALO)
foot(fig); out(fig, "cases")

# ---------- 6. map of the main sample
tr = Transformer.from_crs(4326, 27700, always_xy=True)
Cf = jload(f"{GEO}/counties_uk.geojson")["features"]
uk = unary_union([shape(f["geometry"]).buffer(0.002) for f in Cf]).buffer(-0.002).simplify(0.003)
ukp = stransform(lambda a, b, z=None: tr.transform(a, b), uk)
NE = jload(f"{GEO}/ne_50m_admin_0_countries.geojson")["features"]
irl = stransform(lambda a, b, z=None: tr.transform(a, b), next(shape(f["geometry"]) for f in NE if f["properties"]["ADM0_A3"] == "IRL"))


def patch(ax, g, **kw):
    for p in (g.geoms if hasattr(g, "geoms") else [g]):
        if p.geom_type != "Polygon": continue
        v, c = [], []
        for ring in [p.exterior] + list(p.interiors):
            cs = np.asarray(ring.coords); v += cs.tolist(); c += [Path.MOVETO] + [Path.LINETO] * (len(cs) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(v, c), **kw))


def basemap(ax, ext=(-30000, 690000, -10000, 1080000)):
    ax.set_facecolor("#EAF0F2")
    patch(ax, irl, fc="#F2EEE6", ec="#BDB6A8", lw=0.4)
    patch(ax, ukp, fc="#FBF7EE", ec="#8E8576", lw=0.6)
    ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3]); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_visible(False)


pts, grey = [], []
for b in SITE["b"]:
    for p in b.get("p", []):
        x, y = tr.transform(p["lo"], p["la"])
        if "x" in p:
            pts.append((x, y, math.log2(p["x"]), p["p12"], b["s"], b["y"]))
        else:
            grey.append((x, y))
P = pd.DataFrame(pts, columns=["x", "y", "l", "p12", "s", "yr"]).sort_values("p12")
G = np.array(grey)
fig = plt.figure(figsize=(11, 12.4))
title(fig, "Where by-elections brought the Commons' attention", f"{S['pairs']} by-election towns, {S['first']} to {S['last']}: mentions in the year after polling against the\nreference year, relative to matched towns", y=0.975)
ax = fig.add_axes([0.02, 0.05, 0.68, 0.82]); basemap(ax)
ax.scatter(G[:, 0], G[:, 1], s=7, c="#BDB6A8", lw=0, zorder=2)
sc = ax.scatter(P.x, P.y, c=P.l.clip(-3, 3), cmap=CMAP, norm=NORM, s=14 + 6 * np.sqrt(P.p12), lw=0.5, edgecolor="white", zorder=3)
cax = fig.add_axes([0.76, 0.5, 0.025, 0.28])
cb = fig.colorbar(sc, cax=cax, ticks=[-3, -2, -1, 0, 1, 2, 3]); cb.outline.set_visible(False)
cb.ax.set_yticklabels(["1/8", "1/4", "1/2", "no change", "2x", "4x", "8x"], fontsize=9.5)
fig.text(0.745, 0.8, "Change in mentions,\nyear after vs reference\nyear, against matched\ntowns", fontsize=10.5, color=INK, va="bottom")
fig.text(0.745, 0.45, "Dot size: mentions in\nthe year after polling\n\nSmall grey dots: other\nby-election towns not in\nthe main sample (near a\ngeneral election, too\nrecent, ambiguous name)\n\nSingle by-elections are\nnoisy: few mentions\neither side", fontsize=9.8, color=MUT, va="top")
foot(fig); out(fig, "map")

# ---------- 7. data: by-elections per year (paper only)
Bd = pd.read_csv(f"{DATA}/byelections.csv"); Bd = Bd[Bd.year >= 1909]
E = pd.read_csv(f"{DATA}/event_places.csv"); mn = E[E.main == 1].drop_duplicates("id")
fig = plt.figure(figsize=(11, 4.6))
ax = fig.add_axes([0.07, 0.15, 0.9, 0.72])
yrs = np.arange(1909, 2027)
ax.bar(yrs, [int((Bd.year == y).sum()) for y in yrs], color="#D9C9A3", width=0.85, label="all by-elections in the lists")
ax.bar(yrs, [int((mn.year == y).sum()) for y in yrs], color=RED, width=0.85, label="in the main sample")
ax.set_xlim(1908, 2027); ax.set_ylabel("by-elections")
ax.legend(frameon=False, fontsize=10.5, loc="upper right")
fig.text(0.07, 0.92, f"UK by-elections 1909 to 2026 ({R['parse']['n_since_1909']:,}) and the {S['byelections']} in the main sample", fontsize=13, fontweight="bold", color=INK)
out(fig, "timeline", page=False, blog=False)

# ---------- header 1200 x 630
fig = plt.figure(figsize=(12, 6.3), dpi=100)
ax = fig.add_axes([0.62, 0.02, 0.36, 0.96]); basemap(ax, (-30000, 690000, -10000, 1080000))
ax.scatter(G[:, 0], G[:, 1], s=4, c="#BDB6A8", lw=0, zorder=2)
ax.scatter(P.x, P.y, c=P.l.clip(-3, 3), cmap=CMAP, norm=NORM, s=8 + 4 * np.sqrt(P.p12), lw=0.35, edgecolor="white", zorder=3)
fig.text(0.05, 0.915, "DATA STUDY · 2026", family=MONO, fontsize=12, color=MUT)
fig.text(0.05, 0.56, "Do by-elections\nmake Parliament\nlisten?", family=DISP, fontsize=42, fontweight="bold", color=INK, va="bottom", linespacing=0.95)
fig.text(0.05, 0.47, f"{S['byelections']} UK by-elections, {S['first']} to {S['last']}, and how often\nthe Commons said \"in\" the town before and after", fontsize=15, color=INK, va="top")
fig.text(0.05, 0.28, f"Around polling day: {R['x']['result']:.1f} times the mentions.\nA year on: still {R['x']['year1']:.1f} times.", fontsize=17, color=RED, fontweight="bold", va="top")
fig.text(0.05, 0.06, "Dr Tristan Hotham · maps.tristanhotham.com/byelection-attention", family=MONO, fontsize=10.5, color=MUT)
fig.savefig(f"{ROOT}/header.png", dpi=100, facecolor=PAPER)
plt.close(fig)
assert Image.open(f"{ROOT}/header.png").size == (1200, 630)
print("figures done")

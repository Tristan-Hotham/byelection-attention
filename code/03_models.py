"""Step 3: the pre-specified models (NOTES.md, analysis plan) and the checks. PPML with unit and stack-by-month fixed
effects (pyfixest), standard errors clustered by by-election. Outputs: data/models.csv, data/event_study.csv,
data/pairs.csv (one row per linked place-by-election, for the map), SCR/r_models.json."""
import importlib, warnings
import numpy as np, pandas as pd, pyfixest as pf
from common import *

warnings.filterwarnings("ignore")
EV = importlib.import_module("02_events")
E = pd.read_csv(f"{DATA}/event_places.csv")
Y, PL = EV.Y, EV.PL
HB = [(-12, -4), (-3, -1), (0, 2), (3, 12), (13, 36)]
HBN = ["pre", "vacancy", "result", "year1", "later"]
ROWS = []          # every coefficient for data/models.csv
R = {}


def pc(b, se):
    return {"b": round(100 * (math.exp(b) - 1), 1), "lo": round(100 * (math.exp(b - 1.96 * se) - 1), 1),
            "hi": round(100 * (math.exp(b + 1.96 * se) - 1), 1), "coef": round(b, 4), "se": round(se, 4),
            "p": round(float(2 * (1 - __import__("scipy").stats.norm.cdf(abs(b / se)))), 4) if se > 0 else None}


def attach(D, sample):
    a = sample.set_index("ev")
    D["ev"] = D.eid + "|" + D.tterm
    for c in ("changed", "gov_loss", "inc_gov", "cause_group", "era", "nation", "uncontested", "prev_majority", "n_seats_naming"):
        D[c] = D.ev.map(a[c])
    return D


def add_bins(D, bins=BINS, names=BIN_NAMES, by=None, levels=None):
    cols = []
    if by is None:
        for (a, b), n in zip(bins, names):
            D[n] = ((D.treated == 1) & D.k.between(a, b)).astype(int); cols.append(n)
    else:
        for lv in levels:
            g = (D[by] == lv)
            for (a, b), n in zip(bins, names):
                c = f"{n}__{re.sub(r'[^A-Za-z0-9]', '_', str(lv))}"
                D[c] = ((D.treated == 1) & D.k.between(a, b) & g).astype(int); cols.append(c)
    return cols


def fit(D, cols, label, cl="eid", ols=False, fe="unit + st", group="", keep=True):
    D = D.copy()
    D["cl"] = D[cl] if cl != "eid" else D.eid
    if cl == "place":
        D["cl"] = D.tterm
    if ols:
        D["ly"] = np.log1p(D.y)
        f = pf.feols("ly ~ " + "+".join(cols) + f" | {fe}", data=D, vcov={"CRV1": "cl"})
    else:
        f = pf.fepois("y ~ " + "+".join(cols) + f" | {fe}", data=D, vcov={"CRV1": "cl"})
    co, se = f.coef(), f.se()
    out = {c: pc(co[c], se[c]) for c in cols if c in co.index}
    n = {"rows": int(f._N), "pairs": int(D[D.treated == 1].ev.nunique()) if "ev" in D else None,
         "byelections": int(D.eid.nunique()), "clusters": int(D["cl"].nunique())}
    if keep:
        for c in cols:
            if c in co.index:
                ROWS.append({"model": label, "group": group, "term": c, **out[c], **n})
    return out, n, f


def summary(label, D, cols, **kw):
    o, n, f = fit(D, cols, label, **kw)
    return {"label": label, **n, **o}


# ---------------------------------------------------------------- main sample, M1
main = E[E.main == 1].copy()
D = attach(EV.stack(main), main)
cols = add_bins(D)
M1, n1, f1 = fit(D, cols, "M1 main")
R["M1"] = {"n": n1, **M1}
R["M1"]["pairs_nonzero"] = int((D[D.treated == 1].groupby("ev").y.sum() > 0).sum())
R["M1"]["units_nonzero"] = int((D.groupby("unit").y.sum() > 0).sum()); R["M1"]["units"] = int(D.unit.nunique())
# M1b: the by-election window pooled (-3 to +2)
D["around"] = ((D.treated == 1) & D.k.between(-3, 2)).astype(int)
D["later"] = ((D.treated == 1) & D.k.between(13, 36)).astype(int)
o, _, _ = fit(D, ["pre", "around", "year1", "later"], "M1b pooled")
R["M1b"] = o
# monthly event study
ks = list(range(-12, POST + 1))
for k in ks:
    D[f"k{k}".replace("-", "m")] = ((D.treated == 1) & (D.k == k)).astype(int)
kc = [f"k{k}".replace("-", "m") for k in ks]
es, _, _ = fit(D, kc, "event study", keep=False)
ES = pd.DataFrame([{"k": k, **{x: es[c][x] for x in ("b", "lo", "hi", "coef", "se")}} for k, c in zip(ks, kc)])
ES.to_csv(f"{DATA}/event_study.csv", index=False)
R["event_study_peak"] = ES.loc[ES.b.idxmax()].to_dict()
# descriptive means by k (treated vs controls), each relative to its own reference mean
g = D.groupby(["treated", "k"]).y.mean().unstack(0)
ref = g.loc[REF[0]:REF[1]].mean()
R["desc_means"] = {"k": g.index.tolist(), "treated": (g[1] / ref[1]).round(3).tolist(), "control": (g[0] / ref[0]).round(3).tolist(),
                   "treated_raw": g[1].round(3).tolist(), "control_raw": g[0].round(3).tolist(), "ref_treated": round(ref[1], 3), "ref_control": round(ref[0], 3)}

# ---------------------------------------------------------------- heterogeneity (H3 to H6, exploratory extras)
Dh = D.copy()
Dh["changed_s"] = np.where(Dh.changed == 1, "changed hands", "held")
Dh["gov_s"] = np.where(Dh.inc_gov == 1, "government-held", "opposition-held")
Dh["govloss_s"] = np.where(Dh.gov_loss == 1, "government lost the seat", "otherwise")
Dh["marg_s"] = np.where(Dh.prev_majority < 10, "marginal (under 10 points)", np.where(Dh.prev_majority.notna(), "safer (10 points or more)", "unknown"))
Dh["contest_s"] = np.where(Dh.uncontested == 1, "uncontested", "contested")
Dh["seats_s"] = np.where(Dh.n_seats_naming <= 1, "one seat", "two seats")
HET = {}
for key, var in (("changed", "changed_s"), ("gov", "gov_s"), ("govloss", "govloss_s"), ("cause", "cause_group"), ("era", "era"),
                 ("nation", "nation"), ("margin", "marg_s"), ("contest", "contest_s"), ("seats", "seats_s")):
    lv = [x for x in Dh[var].dropna().unique() if Dh.loc[Dh.treated == 1].groupby(var).ev.nunique().get(x, 0) >= 5]
    lv = sorted(lv)
    sub = Dh[Dh[var].isin(lv)].copy()
    hc = add_bins(sub, HB, HBN, by=var, levels=lv)
    o, n, f = fit(sub, hc, f"het {key}", group=key)
    res = {}
    for x in lv:
        sx = re.sub(r"[^A-Za-z0-9]", "_", str(x))
        res[x] = {b: o.get(f"{b}__{sx}") for b in HBN}
        res[x]["pairs"] = int(sub[(sub.treated == 1) & (sub[var] == x)].ev.nunique())
    # contrasts (difference in log points, as a ratio) between the first level and the others, for result, year1, later
    co, V = f.coef(), f._vcov
    names = list(co.index)
    con = {}
    for x in lv[1:]:
        for b in ("result", "year1", "later"):
            a1, a2 = f"{b}__{re.sub(r'[^A-Za-z0-9]', '_', str(lv[0]))}", f"{b}__{re.sub(r'[^A-Za-z0-9]', '_', str(x))}"
            if a1 in names and a2 in names:
                i, j = names.index(a1), names.index(a2)
                d = co[a2] - co[a1]; s = math.sqrt(V[i, i] + V[j, j] - 2 * V[i, j])
                con[f"{x} vs {lv[0]}|{b}"] = pc(d, s)
    HET[key] = {"levels": lv, "est": res, "contrast": con, "n": n}
R["het"] = HET

# ---------------------------------------------------------------- placebos
# P1 fake dates: 24 months earlier, window -24 to +12
P1s = main[main.k0 - 48 >= 0]
Dp = EV.stack(P1s, shift=-24, window=(-24, 12))
pcols = add_bins(Dp, BINS[:4], BIN_NAMES[:4])
Dp["ev"] = Dp.eid + "|" + Dp.tterm
R["P1"] = summary("P1 fake date 24 months earlier", Dp, pcols)
# P2 neighbours 3 to 25 km, not named in any by-election seat in the window +/- 12 months
nb_rows, extra = [], {}
POOL = sorted(EV.clean)
for eid, gm in main.groupby("id"):
    k0 = int(gm.k0.iloc[0])
    cands = []
    for t in POOL:
        if t in set(gm.term) or any(k0 - PRE - 12 <= m <= k0 + POST + 12 for m in EV.treat_months[t]):
            continue
        d = min(km(r.lat, r.lon, PL.loc[t, "lat"], PL.loc[t, "lon"]) for r in gm.itertuples())
        if 3 <= d <= NEAR_KM:
            cands.append((d, t))
    for d, t in sorted(cands)[:3]:
        r0 = gm.iloc[0].to_dict()
        r0.update({"term": t, "lat": PL.loc[t, "lat"], "lon": PL.loc[t, "lon"], "pop": PL.loc[t, "pop"], "nation": PL.loc[t, "nation"], "ev": eid + "|" + t})
        nb_rows.append(r0)
    extra[eid] = (list(gm.term), [(r.lat, r.lon) for r in gm.itertuples()])
NB = pd.DataFrame(nb_rows)
Dn = EV.stack(NB, extra=extra)
ncols = add_bins(Dn)
Dn["ev"] = Dn.eid + "|" + Dn.tterm
R["P2"] = summary("P2 neighbouring places (3 to 25 km)", Dn, ncols)
R["P2"]["neighbours"] = int(len(NB)); R["P2"]["byelections_with"] = int(NB.id.nunique())
# P3 same MP re-elected (ministerial re-elections, recontests)
s3 = E[(E.clean == 1) & (E.window_ok == 1) & (E.near_ge == 0) & (E.overlap == 0) & (E.same_mp == 1) & (E.city == 0)]
D3 = EV.stack(s3)
D3["ev"] = D3.eid + "|" + D3.tterm
c3 = add_bins(D3)
R["P3"] = summary("P3 same MP re-elected", D3, c3)

# ---------------------------------------------------------------- alternatives and robustness
RB = []
RB.append(dict(group="Alternative specifications", **summary("OLS of log(1 + mentions)", D, cols, ols=True)))
Dt = D[D.treated == 1].copy()
RB.append(dict(group="Alternative specifications", **summary("PPML, treated places only (unit and month fixed effects)", Dt, cols, fe="unit + t")))
D10 = attach(EV.stack(main, K=10), main); add_bins(D10)
RB.append(dict(group="Alternative specifications", **summary("10 controls per treated place", D10, cols)))
RB.append(dict(group="Inference", **summary("Errors clustered by place", D, cols, cl="place")))
for era in sorted(main.era.unique()):
    RB.append(dict(group="Leave one out", **summary(f"Without {era}", D[D.era != era], cols)))
for nat in ("England", "Scotland", "Wales"):
    RB.append(dict(group="Leave one out", **summary(f"Without {nat}", D[D.nation != nat], cols)))
lon_terms = {t for t in main.term.unique() if km(51.5074, -0.1278, PL.loc[t, "lat"], PL.loc[t, "lon"]) <= 25}
RB.append(dict(group="Leave one out", **summary("Without London places", D[~D.tterm.isin(lon_terms)], cols)))
R["london_pairs"] = int(main.term.isin(lon_terms).sum())
base = (E.clean == 1) & (E.window_ok == 1) & (E.same_mp == 0)
variants = [("Keep by-elections near a general election", base & (E.overlap == 0) & (E.city == 0)),
            ("Keep overlapping by-elections", base & (E.near_ge == 0) & (E.city == 0)),
            ("Include city divisions (named in 3+ seats)", base & (E.near_ge == 0) & (E.overlap == 0)),
            ("Contested by-elections only", base & (E.near_ge == 0) & (E.overlap == 0) & (E.city == 0) & (E.uncontested == 0)),
            ("Places named in one seat only", base & (E.near_ge == 0) & (E.overlap == 0) & (E.n_seats_naming <= 1))]
for lab, m in variants:
    s = E[m]
    Dv = attach(EV.stack(s), s); add_bins(Dv)
    RB.append(dict(group="Sample and measurement", **summary(lab, Dv, cols)))
    if lab.startswith("Include city"):
        R["n_city_sample"] = int(len(s))
Dnp = attach(EV.stack(main, outcome=EV.Y_noprefix), main); add_bins(Dnp)
RB.append(dict(group="Sample and measurement", **summary("No prefix subtraction", Dnp, cols)))
Dr = D.copy()
rc = add_bins(Dr, BINS[1:], BIN_NAMES[1:])
RB.append(dict(group="Sample and measurement", **summary("Reference months -24 to -4", Dr, rc)))
R["robust"] = RB

# ---------------------------------------------------------------- S1: the seat-name phrase (mechanical)
H = EV.H
PS = {t: EV.series(v) for t, v in H["plain"].items()}
C = EV.C
ge_names = {d: set(norm(s) for s in C.loc[C.date == d, "constituency"]) for d in EV.GE_DATES}
B = pd.read_csv(f"{DATA}/byelections.csv")
seat_months = {}
for r in B.itertuples():
    seat_months.setdefault(r.seat, []).append(mi(r.date[:7]))
seats = [s for s in PS if s in seat_months]
rows = []
for eid, g in main.groupby("id"):
    seat = B.loc[B.id == eid, "seat"].iloc[0]
    if seat not in PS:
        continue
    k0 = int(g.k0.iloc[0])
    pg = EV.prev_ge(g.date.iloc[0])
    later = [d for d in EV.GE_DATES if mi(d[:7]) <= k0 + POST]
    lg = later[-1]
    ok = [s for s in seats if s != seat and norm(s) in ge_names[pg] and norm(s) in ge_names[lg]
          and not any(k0 - PRE - 12 <= m <= k0 + POST + 12 for m in seat_months[s])]
    tb = np.log1p(PS[seat][k0 - 24:k0 - 12].mean())
    ok.sort(key=lambda s: abs(np.log1p(PS[s][k0 - 24:k0 - 12].mean()) - tb))
    for role, s in [(1, seat)] + [(0, x) for x in ok[:5]]:
        for j, yv in enumerate(PS[s][k0 - PRE:k0 + POST + 1]):
            rows.append((eid, seat, s, role, -PRE + j, k0 - PRE + j, yv))
DS = pd.DataFrame(rows, columns=["eid", "tterm", "place", "treated", "k", "t", "y"])
DS["unit"] = DS.eid + "|" + DS.place; DS["st"] = DS.eid + "|" + DS.t.astype(str); DS["ev"] = DS.eid + "|" + DS.tterm
add_bins(DS)
R["S1"] = summary("S1 seat-name phrase", DS, cols)
g = DS.groupby(["treated", "k"]).y.mean().unstack(0); ref = g.loc[REF[0]:REF[1]].mean()
R["S1_desc"] = {"treated": (g[1] / ref[1]).round(3).tolist(), "control": (g[0] / ref[0]).round(3).tolist()}

# ---------------------------------------------------------------- per-pair attention (map and page): all linked pairs
rows = []
Dm = D.copy()
for r in E.itertuples():
    k0 = r.k0
    lo, hi = max(0, k0 - PRE), min(LAST, k0 + POST)
    y = Y[r.term] if r.term in Y else None
    if y is None:
        continue
    seg = y[lo:hi + 1]
    ref_ = y[max(0, k0 - 24):max(0, k0 - 12)] if k0 - 24 >= 0 else np.array([])
    post = y[k0:min(LAST, k0 + 12) + 1]
    rec = {"ev": r.ev, "id": r.id, "term": r.term, "k0": k0, "ref_mean": round(float(ref_.mean()), 3) if len(ref_) else None,
           "post12": int(post.sum()), "ref12": int(ref_.sum()) if len(ref_) else None,
           "spark": [int(seg[i:i + 3].sum()) for i in range(0, len(seg), 3)], "spark_start": lo - k0}
    if r.main == 1:
        cu = Dm[(Dm.eid == r.id) & (Dm.tterm == r.term) & (Dm.treated == 0)]
        cr = cu[cu.k.between(-24, -13)].y.sum(); cp = cu[cu.k.between(0, 12)].y.sum()
        rec["ctl_ref12"] = int(cr); rec["ctl_post12"] = int(cp)
        rec["excess"] = round(float(((post.sum() + 0.5) / (ref_.sum() + 0.5)) / ((cp + 0.5) / (cr + 0.5))), 3)
    rows.append(rec)
PR = pd.DataFrame(rows)
PR.drop(columns=["spark"]).to_csv(f"{DATA}/pairs.csv", index=False)
jsave({"pairs": rows}, f"{SCR}/pairs_spark.json")
pd.DataFrame(ROWS).to_csv(f"{DATA}/models.csv", index=False)
jsave(R, f"{SCR}/r_models.json", indent=1)
print(json.dumps({k: R[k] for k in ("M1", "M1b", "P1", "P2", "P3", "S1")}, indent=1)[:6000])
for x in RB:
    print(x["label"], x.get("rows"), {b: (x[b]["b"], x[b]["lo"], x[b]["hi"]) for b in ("vacancy", "result", "year1", "year2", "year3") if b in x})
for k, v in HET.items():
    print(k, {x: {b: (v["est"][x][b]["b"], v["est"][x][b]["lo"], v["est"][x][b]["hi"]) for b in ("result", "year1", "later") if v["est"][x][b]} for x in v["levels"]}, v["contrast"].keys())

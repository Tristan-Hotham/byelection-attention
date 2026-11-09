"""Step 2: link by-election seats to Hansard place terms, apply the pre-set exclusions, pick matched control places and
build the stacked monthly panels. Outputs: data/event_places.csv (one row per by-election x place, with every exclusion
flag), data/match_log.csv (seat to place links), SCR/panel_*.parquet (stacked panels), SCR/r_events.json.
No outcome is modelled here; the matching uses only the reference months (24 to 13 months before polling)."""
import collections, datetime
import numpy as np, pandas as pd
from common import *

H = jload(f"{RAW}/hansard_monthly.json")
P = pd.read_csv(f"{HP}/places.csv")
B = pd.read_csv(f"{DATA}/byelections.csv")
C = pd.read_csv(f"{ELEC}/contests.csv", dtype={"election": str})
NT = LAST + 1

# Spelling variants counted with their main term (as in Mentioned in the House)
VARIANTS = {"Barrow in Furness": "Barrow-in-Furness", "Ashton in Makerfield": "Ashton-in-Makerfield", "Bishops Stortford": "Bishop's Stortford",
            "Kirkby in Ashfield": "Kirkby-in-Ashfield", "Newark on Trent": "Newark-on-Trent", "Newcastle under Lyme": "Newcastle-under-Lyme",
            "Lytham St Annes": "Lytham St Anne's", "Saint Andrews": "St Andrews", "Saint Neots": "St Neots", "Cwmbrân": "Cwmbran",
            "Abingdon-on-Thames": "Abingdon", "Droitwich Spa": "Droitwich", "Letchworth Garden City": "Letchworth",
            "Ellesmere Port Town": "Ellesmere Port", "Staines-upon-Thames": "Staines", "Londonderry County Borough": "Londonderry",
            "Manchester City Centre": "Manchester", "Brighton and Hove": "Brighton", "Amersham on the Hill": "Amersham",
            "Blaydon-on-Tyne": "Blaydon", "Royal Sutton Coldfield": "Sutton Coldfield", "Derry": "Londonderry",
            "Royal Leamington Spa": "Leamington", "Royal Tunbridge Wells": "Tunbridge Wells", "Royal Wootton Bassett": "Wootton Bassett"}


def series(d):
    a = np.zeros(NT)
    for k, v in d.items():
        i = mi(k)
        if 0 <= i < NT:
            a[i] += v
    return a


RAWS = {t: series(v) for t, v in H["inp"].items()}
# prefix subtraction: "in Bury" also counts "in Bury St Edmunds"
_n = lambda x: re.sub(r"[^a-z0-9 ]", " ", x.lower()).split()
TOK = {t: _n(t) for t in RAWS}
PREFIX = collections.defaultdict(list)
for a, na in TOK.items():
    for b, nb in TOK.items():
        if len(nb) > len(na) and nb[:len(na)] == na:
            PREFIX[a].append(b)
Y = {}
for t, a in RAWS.items():
    if t in VARIANTS:
        continue
    y = a.copy()
    for b in PREFIX.get(t, []):
        y = np.maximum(0, y - RAWS[b])
    for v, main in VARIANTS.items():
        if main == t and v in RAWS:
            y = y + RAWS[v]
    Y[t] = y
Y_noprefix = {t: RAWS[t] + sum((RAWS[v] for v, m in VARIANTS.items() if m == t and v in RAWS), np.zeros(NT)) for t in Y}
PL = P.set_index("term")
OV = pd.read_csv(os.path.join(ROOT, "code", "overrides.csv")).fillna("")
for r in OV[OV.kind == "point"].itertuples():
    la, lo = (float(x) for x in r.value.split(";"))
    PL.loc[r.term, "lat"], PL.loc[r.term, "lon"] = la, lo
OV_DROP = {(r.seat, r.term) for r in OV[OV.kind == "drop"].itertuples()}
OV_KEEP = {(r.seat, r.term) for r in OV[OV.kind == "keep"].itertuples()}
clean = {t for t in Y if t in PL.index and not isinstance(PL.loc[t, "flag"], str)}
factor = {t: float(PL.loc[t, "factor"]) for t in Y if t in PL.index}

# ---- seat name to place terms: longest whole-word matches, no overlaps
NAMES = {}
for t in Y:
    NAMES[norm(t)] = t
for v, m in VARIANTS.items():
    NAMES.setdefault(norm(v), m)
SEAT_ALIAS = {"the hartlepools": "hartlepool", "kingston upon hull": "hull"}
SEAT_ALIAS.update({norm(r.seat): norm(r.term) for r in OV[OV.kind == "alias"].itertuples()})


def places_in(seat):
    s = norm(seat)
    for a, b in SEAT_ALIAS.items():
        s = s.replace(a, b)
    w = s.split()
    used, found = [False] * len(w), []
    cands = sorted(NAMES, key=lambda n: -len(n.split()))
    for n in cands:
        nw = n.split()
        L = len(nw)
        for i in range(len(w) - L + 1):
            if w[i:i + L] == nw and not any(used[i:i + L]):
                found.append(NAMES[n]); used[i:i + L] = [True] * L
    return sorted(set(found))


GE = C.groupby("election").date.first().sort_values()
GE = GE[GE >= "1900-01-01"]
GE_DATES = sorted(GE.tolist())
SEATS_AT = {d: [norm(s) for s in C.loc[C.date == d, "constituency"]] for d in GE_DATES}


def prev_ge(date):
    return max(d for d in GE_DATES if d <= date)


def n_seats_naming(term, date):
    nt = norm(term)
    pat = re.compile(r"\b" + re.escape(nt) + r"\b")
    alt = [norm(v) for v, m in VARIANTS.items() if m == term]
    return sum(1 for s in SEATS_AT[prev_ge(date)] if pat.search(s.replace("the hartlepools", "hartlepool")) or any(a in s for a in alt))


def months_between(d1, d2):
    a, b = datetime.date.fromisoformat(d1), datetime.date.fromisoformat(d2)
    return abs((a - b).days) / 30.4375


B = B[B.year >= 1909].copy()
B["univ"] = B.seat.str.contains("Universit").astype(int)
B["k0"] = B.date.str[:7].map(mi)
B["ge_gap"] = [min(months_between(d, g) for g in GE_DATES) for d in B.date]
B["prev_ge"] = B.date.map(prev_ge)
# previous majority (share points) in the seat at the preceding general election, where the seat name matches
cand = pd.read_csv(f"{ELEC}/candidates.csv", dtype={"election": str})
cand = cand.merge(C[["election", "date", "constituency"]], on=["election", "constituency"], how="left")
maj = {}
for (d, s), g in cand[cand.share.notna()].groupby(["date", "constituency"]):
    sh = sorted(g.share.tolist(), reverse=True)
    maj[(d, norm(s))] = sh[0] - (sh[1] if len(sh) > 1 else 0)
B["prev_majority"] = [maj.get((d, norm(s).replace("the hartlepools", "the hartlepools")), np.nan) for d, s in zip(B.prev_ge, B.seat)]
seat_pt = {}
for r in C.sort_values("date").itertuples():
    if r.lat == r.lat:
        seat_pt[norm(r.constituency)] = (r.lat, r.lon, r.nation)
B["places"] = ["|".join(places_in(s)) if not u else "" for s, u in zip(B.seat, B.univ)]
B["seat_lat"] = [seat_pt.get(norm(s), (np.nan,) * 3)[0] for s in B.seat]
B["seat_lon"] = [seat_pt.get(norm(s), (np.nan,) * 3)[1] for s in B.seat]

# ---- match log (seat to place), checked by distance to the seat point
ml = []
for r in B.itertuples():
    for t in (r.places.split("|") if r.places else []):
        d = km(r.seat_lat, r.seat_lon, PL.loc[t, "lat"], PL.loc[t, "lon"]) if r.seat_lat == r.seat_lat else np.nan
        ml.append({"id": r.id, "seat": r.seat, "date": r.date, "term": t, "flag": PL.loc[t, "flag"] if isinstance(PL.loc[t, "flag"], str) else "",
                   "km_seat_point": round(d, 1) if d == d else None, "n_seats_naming": n_seats_naming(t, r.date)})
ML = pd.DataFrame(ml)
# a seat named after a place far from the seat's own point is a different place of the same name: drop (> 60 km), plus
# the hand decisions in code/overrides.csv (every link over 12 km was read by eye)
ML["far"] = [int((s, t) in OV_DROP or ((s, t) not in OV_KEEP and k == k and k > 60)) for s, t, k in zip(ML.seat, ML.term, ML.km_seat_point)]
ML.to_csv(f"{DATA}/match_log.csv", index=False)

# every (place, month) with a by-election in a seat naming the place: for exclusions and for control eligibility
treat_months = collections.defaultdict(list)
for r in ML[ML.far == 0].itertuples():
    treat_months[r.term].append(mi(r.date[:7]))

E = ML[ML.far == 0].merge(B[["id", "k0", "date", "year", "ge_gap", "same_mp", "cause_group", "changed", "gov_loss", "inc_gov", "uncontested",
                              "prev_majority", "inc_family", "win_family"]], on=["id", "date"])
E["nation"] = E.term.map(PL.nation)
E["clean"] = E.term.isin(clean).astype(int)
E["window_ok"] = ((E.k0 - PRE >= 0) & (E.k0 + POST <= LAST)).astype(int)
E["near_ge"] = (E.ge_gap <= GE_GAP).astype(int)
E["overlap"] = [int(any(m != k and k - PRE <= m <= k + POST for m in treat_months[t])) for t, k in zip(E.term, E.k0)]
E["overlap_ids"] = [int(sum(1 for m in treat_months[t] if m != k and k - PRE <= m <= k + POST)) for t, k in zip(E.term, E.k0)]
E["city"] = (E.n_seats_naming > 2).astype(int)
E["main"] = ((E.clean == 1) & (E.window_ok == 1) & (E.near_ge == 0) & (E.overlap == 0) & (E.same_mp == 0) & (E.city == 0)).astype(int)
E["era"] = pd.cut(E.year, [1900, 1944, 1979, 2030], labels=["1911 to 1944", "1945 to 1979", "1980 to 2023"]).astype(str)
E["ev"] = E.id + "|" + E.term
E["pop"] = E.term.map(PL["pop"])
E["lat"], E["lon"] = E.term.map(PL.lat), E.term.map(PL.lon)

# ---- controls
POOL = sorted(clean)
pool_nat = np.array([PL.loc[t, "nation"] for t in POOL])
pool_lat = np.array([PL.loc[t, "lat"] for t in POOL]); pool_lon = np.array([PL.loc[t, "lon"] for t in POOL])
pool_pop = np.array([PL.loc[t, "pop"] for t in POOL], dtype=float)
lpop_med = np.nanmedian(np.log(pool_pop))
pool_lpop = np.where(np.isfinite(np.log(pool_pop)), np.log(pool_pop), lpop_med)
Ymat = np.vstack([Y[t] for t in POOL])
csum = np.concatenate([np.zeros((len(POOL), 1)), np.cumsum(Ymat, axis=1)], axis=1)


def base_mean(rowsum_idx, k0):
    a, b = k0 + REF[0], k0 + REF[1]
    return (csum[rowsum_idx, b + 1] - csum[rowsum_idx, a]) / (b - a + 1)


def dist_km(lat, lon):
    p1 = np.radians(lat); p2 = np.radians(pool_lat)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(pool_lon - lon) / 2) ** 2
    return 2 * 6371 * np.arcsin(np.sqrt(a))


IDX = {t: i for i, t in enumerate(POOL)}


def pick_controls(ev_rows, k0, K, exclude_terms=(), near_km=NEAR_KM, extra_pts=()):
    """K nearest eligible places to each treated place on (log baseline mentions, log population)."""
    lo, hi = k0 - PRE, k0 + POST
    elig = np.ones(len(POOL), bool)
    for t in POOL:
        if any(lo - 12 <= m <= hi + 12 for m in treat_months[t]):
            elig[IDX[t]] = False
    for r in ev_rows:
        elig &= dist_km(r["lat"], r["lon"]) > near_km
    for la, lo in extra_pts:
        elig &= dist_km(la, lo) > near_km
    for t in exclude_terms:
        if t in IDX: elig[IDX[t]] = False
    bm = np.log1p(base_mean(np.arange(len(POOL)), k0))
    out = {}
    taken = set()
    for r in ev_rows:
        nat_ok = elig & (pool_nat == r["nation"])
        if nat_ok.sum() < 3 * K:
            nat_ok = elig.copy()
        tb = np.log1p(base_mean(IDX[r["term"]], k0)) if r["term"] in IDX else np.log1p(Y[r["term"]][k0 + REF[0]:k0 + REF[1] + 1].mean())
        tp = np.log(r["pop"]) if r["pop"] == r["pop"] and r["pop"] > 0 else lpop_med
        d = np.sqrt(((bm - tb) / 0.5) ** 2 + ((pool_lpop - tp) / 1.0) ** 2)
        d[~nat_ok] = np.inf
        for t in taken:
            d[IDX[t]] = np.inf
        ch = [POOL[i] for i in np.argsort(d)[:K] if np.isfinite(d[i])]
        taken.update(ch)
        out[r["term"]] = ch
    return out


def stack(sample, K=K_CONTROLS, shift=0, window=(-PRE, POST), outcome=None, near_km=NEAR_KM, extra=None):
    """stacked panel: one stack per by-election (all its treated places and their controls), months k in window
    around polling (k0 + shift)."""
    Yd = outcome or Y
    rows = []
    for eid, g in sample.groupby("id"):
        k0 = int(g.k0.iloc[0]) + shift
        if k0 + window[0] < 0 or k0 + window[1] > LAST:
            continue
        evr = g.to_dict("records")
        ex = extra.get(eid, ([], [])) if extra else ([], [])
        ctl = pick_controls(evr, k0, K, exclude_terms=set(g.term) | set(ex[0]), near_km=near_km, extra_pts=ex[1])
        for r in evr:
            for role, t in [(1, r["term"])] + [(0, c) for c in ctl[r["term"]]]:
                ys = Yd[t][k0 + window[0]:k0 + window[1] + 1]
                for j, yv in enumerate(ys):
                    rows.append((eid, r["term"], t, role, window[0] + j, k0 + window[0] + j, yv))
    D = pd.DataFrame(rows, columns=["eid", "tterm", "place", "treated", "k", "t", "y"])
    D["unit"] = D.eid + "|" + D.tterm + "|" + D.place
    D["st"] = D.eid + "|" + D.t.astype(str)
    return D


if __name__ == "__main__":
    E.to_csv(f"{DATA}/event_places.csv", index=False)
    main = E[E.main == 1]
    D = stack(main)
    D.to_pickle(f"{SCR}/panel_main.pkl")
    flow = {"byelections_since_1909": int(len(B)), "university_seats": int(B.univ.sum()),
            "with_place": int((B.places != "").sum()), "place_links": int(len(ML)), "far_dropped": int(ML.far.sum()),
            "links_kept": int(len(E)), "byelections_linked": int(E.id.nunique()),
            "not_clean": int((E.clean == 0).sum()), "outside_window": int(((E.clean == 1) & (E.window_ok == 0)).sum()),
            "same_mp": int(((E.clean == 1) & (E.window_ok == 1) & (E.same_mp == 1)).sum())}
    s = E[(E.clean == 1) & (E.window_ok == 1) & (E.same_mp == 0)]
    flow["near_ge"] = int(s.near_ge.sum()); s = s[s.near_ge == 0]
    flow["overlap"] = int(s.overlap.sum()); s = s[s.overlap == 0]
    flow["city"] = int(s.city.sum()); s = s[s.city == 0]
    flow["main_pairs"] = int(len(s)); flow["main_byelections"] = int(s.id.nunique()); flow["main_places"] = int(s.term.nunique())
    assert flow["main_pairs"] == len(main)
    flow["panel_rows"] = int(len(D)); flow["panel_units"] = int(D.unit.nunique()); flow["control_places"] = int(D[D.treated == 0].place.nunique())
    jsave({"flow": flow}, f"{SCR}/r_events.json", indent=1)
    print(json.dumps(flow, indent=1))
    print(main.groupby(["era", "cause_group"]).size().unstack(fill_value=0))
    print(main.nation.value_counts(), main.changed.sum(), main.gov_loss.sum())

"""Step 4: data/results.json (every number quoted anywhere), data/site.json for the page, with asserts on the claims made
in words."""
import numpy as np, pandas as pd
from common import *

RP = jload(f"{SCR}/r_parse.json")
RE = jload(f"{SCR}/r_events.json")
RM = jload(f"{SCR}/r_models.json")
E = pd.read_csv(f"{DATA}/event_places.csv")
B = pd.read_csv(f"{DATA}/byelections.csv")
PRS = pd.read_csv(f"{DATA}/pairs.csv")
SP = {p["ev"]: p for p in jload(f"{SCR}/pairs_spark.json")["pairs"]}
ES = pd.read_csv(f"{DATA}/event_study.csv")

R = {"parse": RP, "flow": RE["flow"]}
R.update({k: RM[k] for k in ("M1", "M1b", "P1", "P2", "P3", "S1", "S1_desc", "desc_means", "event_study_peak", "london_pairs", "n_city_sample")})
R["robust"] = RM["robust"]
if os.path.exists(f"{SCR}/r_explore.json"):
    R["explore"] = jload(f"{SCR}/r_explore.json")  # exploratory checks added at review (03b_referee_checks.py)
H = RM["het"]


def flip(x):
    """contrast as stated the other way round: group B relative to group A becomes A relative to B"""
    b, se = -x["coef"], x["se"]
    return {"b": round(100 * (math.exp(b) - 1), 1), "lo": round(100 * (math.exp(b - 1.96 * se) - 1), 1),
            "hi": round(100 * (math.exp(b + 1.96 * se) - 1), 1), "p": x["p"]}


R["het"] = {}
for k, v in H.items():
    R["het"][k] = {"levels": v["levels"], "est": v["est"], "n_rows": v["n"]["rows"],
                   "contrast": {c.replace(" vs ", "_vs_").replace("|", "_"): x for c, x in v["contrast"].items()}}
# readable contrasts: changed hands vs held; government lost vs otherwise
R["contrast"] = {"changed_result": flip(H["changed"]["contrast"]["held vs changed hands|result"]),
                 "changed_year1": flip(H["changed"]["contrast"]["held vs changed hands|year1"]),
                 "changed_later": flip(H["changed"]["contrast"]["held vs changed hands|later"]),
                 "govloss_result": flip(H["govloss"]["contrast"]["otherwise vs government lost the seat|result"]),
                 "govloss_year1": flip(H["govloss"]["contrast"]["otherwise vs government lost the seat|year1"]),
                 "govloss_later": flip(H["govloss"]["contrast"]["otherwise vs government lost the seat|later"]),
                 "resign_result": H["cause"]["contrast"]["resignation vs death|result"],
                 "resign_year1": H["cause"]["contrast"]["resignation vs death|year1"],
                 "resign_later": H["cause"]["contrast"]["resignation vs death|later"],
                 "era3_result": H["era"]["contrast"]["1980 to 2023 vs 1911 to 1944|result"],
                 "era2_result": H["era"]["contrast"]["1945 to 1979 vs 1911 to 1944|result"],
                 "era3_later": H["era"]["contrast"]["1980 to 2023 vs 1911 to 1944|later"],
                 "opp_result": H["gov"]["contrast"]["opposition-held vs government-held|result"],
                 "opp_year1": H["gov"]["contrast"]["opposition-held vs government-held|year1"],
                 "opp_later": H["gov"]["contrast"]["opposition-held vs government-held|later"]}

# main sample description
main = E[E.main == 1]
R["sample"] = {"pairs": int(len(main)), "byelections": int(main.id.nunique()), "places": int(main.term.nunique()),
               "first": main.date.min()[:4], "last": main.date.max()[:4], "by_era": main.era.value_counts().to_dict(),
               "by_cause": main.cause_group.value_counts().to_dict(), "by_nation": main.nation.value_counts().to_dict(),
               "changed": int(main.changed.sum()), "gov_loss": int(main.gov_loss.sum()), "inc_gov": int(main.inc_gov.sum()),
               "uncontested": int(main.uncontested.sum()), "two_places": int((main.groupby("id").size() > 1).sum()),
               "pairs_zero_window": int(len(main) - RM["M1"]["pairs_nonzero"]),
               "control_places": RE["flow"]["control_places"], "panel_rows": RE["flow"]["panel_rows"]}
R["sample"]["changed_pc"] = round(100 * R["sample"]["changed"] / R["sample"]["pairs"])
# absolute scale: mean monthly mentions of treated places in the reference months, and in the months after
dm = RM["desc_means"]; kk = dm["k"]
tr = dict(zip(kk, dm["treated_raw"])); cr = dict(zip(kk, dm["control_raw"]))
R["abs"] = {"ref_month": round(dm["ref_treated"], 2), "ref_year": round(12 * dm["ref_treated"], 1),
            "result_month": round(float(np.mean([tr[k] for k in range(0, 3)])), 2),
            "year1_month": round(float(np.mean([tr[k] for k in range(3, 13)])), 2),
            "k0_month": round(tr[0], 2), "ctl_ref_month": round(dm["ref_control"], 2),
            "ctl_year1_month": round(float(np.mean([cr[k] for k in range(3, 13)])), 2)}
R["abs"]["k0_x"] = round(tr[0] / dm["ref_treated"], 1)
# multipliers for prose
M1 = R["M1"]
R["x"] = {b: round(1 + M1[b]["b"] / 100, 2) for b in ("vacancy", "result", "year1", "year2", "year3")}
R["x"]["around"] = round(1 + R["M1b"]["around"]["b"] / 100, 2)
R["x"]["later"] = round(1 + R["M1b"]["later"]["b"] / 100, 2)
R["x"]["changed_result"] = round(1 + R["contrast"]["changed_result"]["b"] / 100, 1)
R["x"]["govloss_result"] = round(1 + R["contrast"]["govloss_result"]["b"] / 100, 1)
R["x"]["changed_hands_result"] = round(1 + H["changed"]["est"]["changed hands"]["result"]["b"] / 100, 1)
R["x"]["held_result"] = round(1 + H["changed"]["est"]["held"]["result"]["b"] / 100, 1)
R["x"]["govlost_result"] = round(1 + H["govloss"]["est"]["government lost the seat"]["result"]["b"] / 100, 1)
R["x"]["notlost_result"] = round(1 + H["govloss"]["est"]["otherwise"]["result"]["b"] / 100, 1)
R["x"]["changed_hands_year1"] = round(1 + H["changed"]["est"]["changed hands"]["year1"]["b"] / 100, 1)
R["x"]["held_year1"] = round(1 + H["changed"]["est"]["held"]["year1"]["b"] / 100, 1)
R["x"]["death_year1"] = round(1 + H["cause"]["est"]["death"]["year1"]["b"] / 100, 2)
R["x"]["resign_year1"] = round(1 + H["cause"]["est"]["resignation"]["year1"]["b"] / 100, 2)
R["x"]["death_later"] = round(1 + H["cause"]["est"]["death"]["later"]["b"] / 100, 2)
R["x"]["resign_later"] = round(1 + H["cause"]["est"]["resignation"]["later"]["b"] / 100, 2)
for era, key in (("1911 to 1944", "era1"), ("1945 to 1979", "era2"), ("1980 to 2023", "era3")):
    R["x"][key + "_result"] = round(1 + H["era"]["est"][era]["result"]["b"] / 100, 1)
    R["x"][key + "_year1"] = round(1 + H["era"]["est"][era]["year1"]["b"] / 100, 2)
R["x"]["S1_result"] = round(1 + R["S1"]["result"]["b"] / 100, 2)
R["x"]["P1_result"] = round(1 + R["P1"]["result"]["b"] / 100, 2)
R["x"]["P2_result"] = round(1 + R["P2"]["result"]["b"] / 100, 2)
R["es"] = {"k0": ES.loc[ES.k == 0].iloc[0].to_dict(), "k1": ES.loc[ES.k == 1].iloc[0].to_dict(), "km1": ES.loc[ES.k == -1].iloc[0].to_dict(),
           "n_sig_post_13_36": int(((ES.k >= 13) & (ES.lo > 0)).sum()), "n_pre_sig": int(((ES.k < -3) & ((ES.lo > 0) | (ES.hi < 0))).sum()),
           "n_pre": int((ES.k < -3).sum())}
# robustness ranges across all checks for the main bins
rb = R["robust"]
def rng(b):
    v = [x[b]["b"] for x in rb if b in x and x["label"] != "PPML, treated places only (unit and month fixed effects)"]
    return [min(v), max(v)]
R["robust_range"] = {b: rng(b) for b in ("vacancy", "result", "year1", "year2", "year3")}
R["robust_range"]["n_checks"] = len(rb)
R["robust_range"]["year1_all_pos"] = all(x["year1"]["lo"] > 0 for x in rb if "year1" in x and x["label"] != "Without England")
R["robust_range"]["result_all_pos"] = all(x["result"]["lo"] > 0 for x in rb if "result" in x)
R["robust_range"]["year3_n_sig"] = int(sum(1 for x in rb if "year3" in x and x["year3"]["lo"] > 0))
R["robust_range"]["year2_n_sig"] = int(sum(1 for x in rb if "year2" in x and x["year2"]["lo"] > 0))
R["robust_range"]["n_with_year3"] = int(sum(1 for x in rb if "year3" in x))
lk = {x["label"]: x for x in rb}
R["rb_noeng_rows"] = lk["Without England"]["rows"]
R["rb"] = {"no_1980": lk["Without 1980 to 2023"], "city": lk["Include city divisions (named in 3+ seats)"], "london": lk["Without London places"],
           "place_cl": lk["Errors clustered by place"], "ols": lk["OLS of log(1 + mentions)"], "near_ge": lk["Keep by-elections near a general election"]}

# examples for the page and blog: main-sample pairs with the largest attention gains (12 months after vs the reference year,
# against controls), with at least 10 mentions in the 12 months after
mm = PRS.merge(E[["ev", "seat", "date", "main", "changed", "cause_group", "era", "win_family", "inc_family"]], on="ev")
mm = mm[mm.main == 1].copy()
mm["excess1"] = ((mm.post12 + 1) / (mm.ref12 + 1)) / ((mm.ctl_post12 + 1) / (mm.ctl_ref12 + 1))
ex = mm[mm.post12 >= 10].sort_values("excess1", ascending=False)
R["examples"] = [{"seat": r.seat, "place": r.term, "year": int(r.date[:4]), "ref12": int(r.ref12), "post12": int(r.post12),
                  "ctl_ref12": int(r.ctl_ref12), "ctl_post12": int(r.ctl_post12), "excess": round(float(r.excess1), 1),
                  "changed": int(r.changed), "cause": r.cause_group} for r in ex.head(12).itertuples()]
R["pairs_up_pc"] = round(100 * float((mm.excess1 > 1.25).mean()))
R["pairs_down_pc"] = round(100 * float((mm.excess1 < 0.8).mean()))
cases = {}
for seat, yr in (("Orpington", 1962), ("Crewe and Nantwich", 2008), ("Corby", 2012), ("Eastleigh", 2013), ("Newbury", 1993), ("Rotherham", 1933),
                 ("Ebbw Vale", 1960), ("Hartlepool", 2021), ("Brecon and Radnor", 1985), ("Chesham and Amersham", 2021)):
    r = mm[(mm.seat == seat) & (mm.date.str[:4] == str(yr))]
    if len(r):
        r = r.iloc[0]
        cases[f"{seat} {yr}"] = {"place": r.term, "ref12": int(r.ref12), "post12": int(r.post12), "ctl_ref12": int(r.ctl_ref12),
                                 "ctl_post12": int(r.ctl_post12), "excess": round(float(r.excess1), 1)}
R["cases"] = cases

# ---- checks of claims made in words
assert M1["result"]["lo"] > 0 and M1["vacancy"]["lo"] > 0 and M1["year1"]["lo"] > 0 and M1["year2"]["lo"] > 0
assert M1["year3"]["lo"] < 0 < M1["year3"]["hi"], "year 3 not significant (text says so)"
assert M1["pre"]["lo"] < 0 < M1["pre"]["hi"]
assert all(R["P1"][b]["lo"] < 0 < R["P1"][b]["hi"] for b in ("pre", "vacancy", "result", "year1"))
assert all(R["P2"][b]["lo"] < 0 < R["P2"][b]["hi"] for b in ("pre", "vacancy", "result", "year1", "year2", "year3"))
assert R["contrast"]["changed_result"]["lo"] > 0 and R["contrast"]["changed_year1"]["lo"] < 0 and R["contrast"]["changed_later"]["lo"] < 0
assert R["contrast"]["govloss_result"]["lo"] > 0
assert all(R["contrast"][f"opp_{b}"]["lo"] < 0 < R["contrast"][f"opp_{b}"]["hi"] for b in ("result", "year1", "later"))
assert R["contrast"]["era3_result"]["lo"] > 0
assert H["era"]["est"]["1911 to 1944"]["result"]["lo"] < 0
assert R["contrast"]["resign_year1"]["hi"] < 0 and R["contrast"]["resign_result"]["hi"] > 0
assert R["robust_range"]["result_all_pos"] and R["robust_range"]["year1_all_pos"] and lk["Without England"]["year1"]["lo"] < 0
assert R["S1"]["result"]["b"] < M1["result"]["b"]
assert R["rb"]["no_1980"]["year2"]["lo"] < 0
jsave(R, f"{DATA}/results.json", indent=1)

# ---------------------------------------------------------------- page data: every by-election since 1909
seat_pt = {}
C = pd.read_csv(f"{ELEC}/contests.csv", dtype={"election": str})
for r in C.sort_values("date").itertuples():
    if r.lat == r.lat:
        seat_pt[norm(r.constituency)] = (round(r.lat, 4), round(r.lon, 4))
PL = pd.read_csv(f"{HP}/places.csv").set_index("term")
OV = pd.read_csv(os.path.join(ROOT, "code", "overrides.csv")).fillna("")
for r in OV[OV.kind == "point"].itertuples():
    la, lo = (float(x) for x in r.value.split(";"))
    PL.loc[r.term, "lat"], PL.loc[r.term, "lon"] = la, lo
why_map = {}
for r in E.itertuples():
    if r.main == 1: w = ""
    elif not r.clean: w = "the place name is ambiguous in Hansard"
    elif not r.window_ok: w = "too early or too recent for the full five-year window"
    elif r.same_mp: w = "the same MP was re-elected (no new member)"
    elif r.near_ge: w = "within a year of a general election"
    elif r.overlap: w = "another by-election named the same place within five years"
    elif r.city: w = "the place is split between three or more seats"
    else: w = "left out"
    why_map[r.ev] = w
out = []
FAM = {"CON": "Conservative", "LAB": "Labour", "LIB": "Liberal", "CLIB": "Coalition Liberal", "NLIB": "Liberal National", "NLAB": "National Labour",
       "UUP": "Ulster Unionist", "IRN": "Irish Nationalist", "SNP": "SNP", "PC": "Plaid Cymru", "SPK": "Speaker", "SF": "Sinn Féin", "REF": "Reform UK", "OTH": "Other"}
ev_by_id = E.groupby("id")


def pname(p):
    p = str(p).split("|")[0]
    p = {"Speaker of the House of Commons (United Kingdom)": "Speaker", "Labour and Co-operative Party": "Labour Co-op",
         "Liberal National Party (UK, 1931)": "Liberal National", "National Liberal Party (UK, 1931)": "National Liberal",
         "National Labour Party (UK 1930s)": "National Labour", "Independent (politician)": "Independent"}.get(p, p)
    return re.sub(r"\s*\(.*?\)$", "", p).replace(" Party", "").strip()

mmi = mm.set_index("ev")
for b in B[B.year >= 1909].itertuples():
    rec = {"s": b.seat, "d": b.date[:7], "ipn": pname(b.inc_party), "wpn": pname(b.win_party), "y": b.year, "ip": FAM.get(b.inc_family, b.inc_party), "wp": FAM.get(b.win_family, b.win_party), "ch": int(b.changed),
           "c": b.cause[:140], "cg": b.cause_group}
    if b.id in ev_by_id.groups:
        g = ev_by_id.get_group(b.id)
        pl = []
        for r in g.itertuples():
            sp = SP.get(r.ev)
            q = {"n": r.term, "la": round(float(PL.loc[r.term, "lat"]), 4), "lo": round(float(PL.loc[r.term, "lon"]), 4)}
            if sp:
                q.update({"r12": sp["ref12"], "p12": sp["post12"], "sp": sp["spark"], "s0": sp["spark_start"]})
            if r.ev in mmi.index:
                m = mmi.loc[r.ev]
                q.update({"x": round(float(m.excess1), 2), "c12": [int(m.ctl_ref12), int(m.ctl_post12)]})
            else:
                q["why"] = why_map[r.ev]
            pl.append(q)
        rec["p"] = pl
    else:
        pt = seat_pt.get(norm(b.seat))
        if b.univ if hasattr(b, "univ") else "Universit" in b.seat:
            rec["why"] = "university seat, no place"
        else:
            rec["why"] = "no town from the Hansard list in the seat name"
        if pt:
            rec["la"], rec["lo"] = pt
    out.append(rec)
def nodash(v):
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        return v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-").replace("--", "-")
    if isinstance(v, list): return [nodash(x) for x in v]
    if isinstance(v, dict): return {k: nodash(x) for k, x in v.items()}
    return v


site = nodash({"b": out, "n": len(out)})
jsave(site, f"{DATA}/site.json")
print("results.json; site.json", len(out), "by-elections;", sum(1 for o in out if "p" in o), "linked;", len(mm), "main pairs")
print(json.dumps(R["x"], indent=0)); print(R["abs"]); print(R["robust_range"]); print(R["examples"][:6]); print(R["cases"])

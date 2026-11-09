"""Step 3b: exploratory checks added at independent review, after the planned analysis (not in the written plan).
Two-way clustering (by-election and the place of each unit, since control towns recur across stacks); dropping the
10 by-elections with most mentions of the treated town in months 0 to 12 (PPML weights large counts heavily); and the
main model for 1945 to 2023 only. Output: SCR/r_explore.json (merged into data/results.json by 04_results.py)."""
import importlib, warnings
import numpy as np, pandas as pd, pyfixest as pf
from common import *

warnings.filterwarnings("ignore")
EV = importlib.import_module("02_events")
E = pd.read_csv(f"{DATA}/event_places.csv")
main = E[E.main == 1].copy()
D = EV.stack(main)
for (a, b), n in zip(BINS, BIN_NAMES):
    D[n] = ((D.treated == 1) & D.k.between(a, b)).astype(int)
FML = "y ~ " + "+".join(BIN_NAMES) + " | unit + st"
OUT = {}


def rep(key, label, m):
    co, se = m.coef(), m.se()
    OUT[key] = {"label": label, "rows": int(m._N)}
    for n in BIN_NAMES:
        b, s = co[n], se[n]
        OUT[key][n] = {"b": round(100 * (math.exp(b) - 1), 1), "lo": round(100 * (math.exp(b - 1.96 * s) - 1), 1),
                       "hi": round(100 * (math.exp(b + 1.96 * s) - 1), 1)}
    print(key, {n: (OUT[key][n]["b"], OUT[key][n]["lo"], OUT[key][n]["hi"]) for n in BIN_NAMES}, flush=True)


rep("twoway", "Errors clustered two-way, by by-election and by town", pf.fepois(FML, data=D, vcov={"CRV1": "eid+place"}))
top = D[(D.treated == 1) & D.k.between(0, 12)].groupby("eid").y.sum().sort_values(ascending=False)
rep("droptop10", "Without the 10 by-elections with most mentions in months 0 to 12",
    pf.fepois(FML, data=D[~D.eid.isin(top.index[:10])], vcov={"CRV1": "eid"}))
OUT["droptop10"]["dropped"] = [str(x) for x in top.index[:10]]
rep("post1945", "By-elections from 1945 only", pf.fepois(FML, data=D[D.eid.isin(main[main.era != "1911 to 1944"].id)], vcov={"CRV1": "eid"}))
jsave(OUT, f"{SCR}/r_explore.json", indent=1)

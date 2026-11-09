"""Step 7: the paper. Fills code/paper_template.tex from data/results.json, data/event_study.csv, data/pairs.csv and
data/event_places.csv, adds the tables and compiles with xelatex. Output: release/paper/Hotham_Byelection_Attention.pdf and
.tex beside the f_*.pdf figures. The DOI stays a placeholder (https://doi.org/10.5281/zenodo.24094210 printed) unless DOI is set:
DOI=10.5281/zenodo.N python3 code/07_paper.py"""
import subprocess
import pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(REL, "paper"); NAME = "Hotham_Byelection_Attention"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    for k in ("f0", "f1", "f2", "f3"):
        if f == k: return f"{float(v):.{k[1]}f}".replace("-", "$-$")
    return tex(str(v))


def pc(v):
    return f"{v['b']:.0f} [{v['lo']:.0f}, {v['hi']:.0f}]".replace("-", "$-$")


E = pd.read_csv(f"{DATA}/event_places.csv")
assert E[(E.main == 1) & (E.uncontested == 1)].year.max() < 1945
F = R["flow"]; S = R["sample"]
TF = ("\\begin{table}[tbp]\\centering\\small\\caption{From by-elections to the main sample.}\\label{tab:flow}\\begin{tabular}{lr}\\toprule Step & Number\\\\\\midrule\n"
      f"By-elections in the Wikipedia lists, 1909 to 2026 & {F['byelections_since_1909']:,}\\\\\n"
      f"\\quad university seats & {F['university_seats']:,}\\\\\n"
      f"\\quad linked to at least one Hansard town & {F['byelections_linked']:,}\\\\\n"
      f"By-election towns (links) & {F['links_kept']:,}\\\\\n"
      f"\\quad less: town name ambiguous in Hansard & $-${F['not_clean']}\\\\\n"
      f"\\quad less: window outside the data (polling before 1911 or after September 2023) & $-${F['outside_window']}\\\\\n"
      f"\\quad less: same member re-elected (used as a placebo) & $-${F['same_mp']}\\\\\n"
      f"\\quad less: within 12 months of a general election & $-${F['near_ge']}\\\\\n"
      f"\\quad less: another by-election naming the town within the window & $-${F['overlap']}\\\\\n"
      f"\\quad less: town named in three or more seats & $-${F['city']}\\\\\\midrule\n"
      f"Main sample: by-election towns & {F['main_pairs']:,}\\\\\n"
      f"\\quad by-elections & {F['main_byelections']:,}\\\\\n"
      f"\\quad distinct towns & {F['main_places']:,}\\\\\n"
      f"\\quad distinct control towns & {F['control_places']:,}\\\\\n"
      f"\\quad town-months in the stacked panel & {F['panel_rows']:,}\\\\\\bottomrule\\end{{tabular}}\\end{{table}}")
P = pd.read_csv(f"{DATA}/pairs.csv").merge(E[["ev", "main", "era", "changed", "cause_group", "gov_loss"]], on="ev")
P = P[P.main == 1]
rows = ""
for era in ("1911 to 1944", "1945 to 1979", "1980 to 2023", "All"):
    g = P if era == "All" else P[P.era == era]
    rows += (("\\midrule\n" if era == "All" else "") + f"{era} & {len(g):,} & {g.id.nunique():,} & {100 * g.changed.mean():.0f} & {100 * (g.cause_group == 'death').mean():.0f} & "
             f"{g.ref12.mean():.2f} & {g.post12.mean():.2f} & {(g.ctl_ref12 / 5).mean():.2f} & {(g.ctl_post12 / 5).mean():.2f}\\\\\n")
TD = ("\\begin{table}[tbp]\\centering\\small\\caption{The main sample by era. Mentions are mean ``in'' contributions per town in the reference year (months $-24$ to $-13$) and in the polling month and the twelve after (months 0 to 12), for by-election towns and their controls (per control town).}\\label{tab:desc}"
      "\\setlength{\\tabcolsep}{4pt}\\begin{tabular}{lrrrrrrrr}\\toprule & & & Changed & & \\multicolumn{2}{c}{By-election towns} & \\multicolumn{2}{c}{Controls}\\\\\\cmidrule(lr){6-7}\\cmidrule(lr){8-9}"
      "Era & Towns & By-elections & hands (\\%) & Death (\\%) & Ref. & After & Ref. & After\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
M1 = R["M1"]
lab = {"pre": "Months $-12$ to $-4$", "vacancy": "Months $-3$ to $-1$ (vacancy)", "result": "Months 0 to 2 (result)", "year1": "Months 3 to 12",
       "year2": "Months 13 to 24", "year3": "Months 25 to 36"}
rows = "".join(f"{lab[b]} & {M1[b]['coef']:.3f} & ({M1[b]['se']:.3f}) & {pc(M1[b])} & {M1[b]['p']:.3f}\\\\\n".replace("-0.", "$-$0.") for b in BIN_NAMES)
rows += f"\\midrule Pooled $-3$ to $+2$ (M1b) & {R['M1b']['around']['coef']:.3f} & ({R['M1b']['around']['se']:.3f}) & {pc(R['M1b']['around'])} & {R['M1b']['around']['p']:.3f}\\\\\n"
rows += f"Pooled 13 to 36 (M1b) & {R['M1b']['later']['coef']:.3f} & ({R['M1b']['later']['se']:.3f}) & {pc(R['M1b']['later'])} & {R['M1b']['later']['p']:.3f}\\\\\n"
n = M1["n"]
TM = ("\\begin{table}[tbp]\\centering\\small\\caption{Main model (M1): PPML of monthly ``in'' mentions with town-within-stack and stack-by-month fixed effects; reference months $-24$ to $-13$; standard errors clustered by by-election. Percentages are $100(\\exp(b)-1)$ with 95\\% confidence intervals.}\\label{tab:main}"
      "\\begin{tabular}{lrrlr}\\toprule Period & $b$ & (SE) & \\% [95\\% CI] & $p$\\\\\\midrule\n" + rows +
      f"\\midrule By-election towns & \\multicolumn{{4}}{{l}}{{{n['pairs']:,} ({M1['pairs_nonzero']:,} with any mention in the window)}}\\\\\n"
      f"By-elections (clusters) & \\multicolumn{{4}}{{l}}{{{n['byelections']:,}}}\\\\\n"
      f"Town-months used / in panel & \\multicolumn{{4}}{{l}}{{{n['rows']:,} / {S['panel_rows']:,}}}\\\\\\bottomrule\\end{{tabular}}\\end{{table}}")
H = R["het"]
groups = [("changed", "Seat result", ["held", "changed hands"]), ("govloss", "Government", ["otherwise", "government lost the seat"]),
          ("gov", "Seat held by", ["government-held", "opposition-held"]), ("cause", "Cause", ["death", "resignation", "scandal"]),
          ("era", "Era", ["1911 to 1944", "1945 to 1979", "1980 to 2023"]), ("nation", "Nation", ["England", "Scotland", "Wales"]),
          ("margin", "Previous majority (exploratory)", ["marginal (under 10 points)", "safer (10 points or more)", "unknown"]),
          ("contest", "Contest (exploratory)", ["contested", "uncontested"]), ("seats", "Seats naming the town (exploratory)", ["one seat", "two seats"])]
rows = ""
for key, gname, lvs in groups:
    rows += f"\\multicolumn{{5}}{{l}}{{\\textit{{{gname}}}}}\\\\\n"
    for lv in lvs:
        e = H[key]["est"][lv]
        rows += f"\\quad {tex(lv)} & {e['pairs']} & {pc(e['result'])} & {pc(e['year1'])} & {pc(e['later'])}\\\\\n"
TH = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Heterogeneity: percentage change in mentions against matched towns by group, from the stacked PPML with group-specific bins (95\\% CI). Contrasts in Appendix Table~\\ref{tab:hetfull}.}\\label{tab:het}"
      "\\begin{tabular}{lrlll}\\toprule Group & Towns & Months 0 to 2 & Months 3 to 12 & Months 13 to 36\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for key, gname, lvs in groups:
    for c, x in H[key]["contrast"].items():
        a, b = c.rsplit("_", 1)
        rows += f"{tex(gname)}: {tex(a.replace('_vs_', ' vs '))} & {tex(b)} & {pc(x)} & {x['p']:.3f}\\\\\n"
THF = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{Heterogeneity contrasts: the effect in the first-named group relative to the second-named group, as a percentage difference (95\\% CI).}\\label{tab:hetfull}"
       "\\begin{tabular}{p{9.5cm}lll}\\toprule Contrast & Period & \\% [95\\% CI] & $p$\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for key, labl in (("M1", "Main model (M1)"), ("P1", "P1: dates 24 months earlier"), ("P2", "P2: neighbouring towns, 3 to 25 km"), ("P3", "P3: same member re-elected"), ("S1", "S1: the seat's own name")):
    x = R[key]
    cells = " & ".join(pc(x[b]) if b in x else "" for b in BIN_NAMES)
    nn = x.get("pairs") or x["n"]["pairs"]; nb = x.get("byelections") or x["n"]["byelections"]
    rows += f"{labl} & {nn:,} & {nb:,} & {cells}\\\\\n"
TP = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{Placebos and the seat-name phrase: percentage change against matched units by period (95\\% CI). P1 is estimated over months $-24$ to $+12$ around the false date.}\\label{tab:placebo}"
      "\\setlength{\\tabcolsep}{1.5pt}\\begin{tabular}{p{2.7cm}rrllllll}\\toprule & Units & By-el. & $-12$ to $-4$ & $-3$ to $-1$ & 0 to 2 & 3 to 12 & 13 to 24 & 25 to 36\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""; grp = None
for x in R["robust"]:
    if x["group"] != grp:
        rows += f"\\multicolumn{{6}}{{l}}{{\\textit{{{tex(x['group'])}}}}}\\\\\n"; grp = x["group"]
    rows += f"\\quad {tex(x['label']).replace('-24 to -4', '$-24$ to $-4$')} & {x['rows']:,} & {pc(x['result'])} & {pc(x['year1'])} & {pc(x['year2'])} & {pc(x['year3'])}\\\\\n"
TR = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{Robustness checks: percentage change against matched towns (95\\% CI); rows = town-months used. The OLS row reports $100(\\exp(b)-1)$ of coefficients on $\\log(1+y)$, a different scale.}\\label{tab:robust}"
      "\\setlength{\\tabcolsep}{3pt}\\begin{tabular}{p{5.6cm}rllll}\\toprule Check & Rows & 0 to 2 & 3 to 12 & 13 to 24 & 25 to 36\\\\\\midrule\n"
      f"Main model (M1) & {M1['n']['rows']:,} & {pc(M1['result'])} & {pc(M1['year1'])} & {pc(M1['year2'])} & {pc(M1['year3'])}\\\\\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
ES = pd.read_csv(f"{DATA}/event_study.csv")
half = (len(ES) + 1) // 2
rows = ""
for i in range(half):
    a = ES.iloc[i]; b = ES.iloc[i + half] if i + half < len(ES) else None
    fa = f"{int(a.k)} & {a.b:.0f} [{a.lo:.0f}, {a.hi:.0f}]".replace("-", "$-$")
    fb = (f"{int(b.k)} & {b.b:.0f} [{b.lo:.0f}, {b.hi:.0f}]".replace("-", "$-$")) if b is not None else "&"
    rows += f"{fa} & {fb}\\\\\n"
TES = ("\\begin{table}[tbp]\\centering\\small\\caption{Monthly event-study estimates (Figure~\\ref{fig:event}B): percentage change against matched towns, 95\\% CI; reference months $-24$ to $-13$.}\\label{tab:es}"
       "\\begin{tabular}{rl@{\\hskip 24pt}rl}\\toprule Month & \\% [95\\% CI] & Month & \\% [95\\% CI]\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{AI}}", AI).replace("{{PAGE}}", PAGE).replace("{{REPO}}", REPO)
for k, v in (("TABLE_FLOW", TF), ("TABLE_DESC", TD), ("TABLE_MAIN", TM), ("TABLE_HET", TH), ("TABLE_HETFULL", THF), ("TABLE_PLACEBO", TP), ("TABLE_ROBUST", TR), ("TABLE_ES", TES)):
    t = t.replace("{{" + k + "}}", v)
t = re.sub(r"\{\{(?!TABLE_|DOI)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
DOI = os.environ.get("DOI")
t = t.replace("https://doi.org/10.5281/zenodo.24094210", f"\\url{{https://doi.org/{DOI}}}" if DOI else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t and "—" not in t and "–" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:5]
for bad in ("DSIT", "DCMS", "pre-registered", "preregistered"):
    assert bad not in t, bad
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l or l.startswith("!")][:15])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
body = txt.split("\nReferences\n")[0]
ab = txt.split("Abstract")[1].split("Keywords")[0]
print("paper", r.returncode, len(txt.split()), "words total;", len(body.split()), "before references; abstract", len(ab.split()), "words;",
      [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–"))

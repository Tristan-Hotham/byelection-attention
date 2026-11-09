"""Step 1: every UK by-election in the Wikipedia lists (1900 to 2026), parsed, coded and checked against Wikidata.
Output: data/byelections.csv (one row per by-election) and SCR/r_parse.json (coverage numbers)."""
import collections, datetime
import pandas as pd
from common import *

W = jload(f"{RAW}/wiki_lists.json")
MONTHS = {m: i + 1 for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                           "september", "october", "november", "december"])}


def strip_tpl(s):
    """remove <ref>..</ref>, <ref/>, {{efn..}} and other templates (nested), keep [[link|text]] as text"""
    s = re.sub(r"<ref[^>/]*/>", "", s)
    s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    out, depth, i = [], 0, 0
    while i < len(s):
        if s.startswith("{{", i):
            depth += 1; i += 2; continue
        if s.startswith("}}", i) and depth:
            depth -= 1; i += 2; continue
        if depth == 0:
            out.append(s[i])
        i += 1
    s = "".join(out)
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\[https?://\S+\s*([^\]]*)\]", r"\1", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("'''", "").replace("''", "").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", s).strip()


def family(p):
    p = p.split("|")[0]
    if p in ("Conservative Party (UK)", "Coalition Conservative", "Irish Unionist Party", "Liberal Unionist Party",
             "UK National Government", "Independent Conservative"):
        return "CON"
    if p == "Ulster Unionist Party":
        return "UUP"
    if p == "Coalition Liberal":
        return "CLIB"
    if p in ("Liberal Party (UK)", "Liberal Democrats (UK)", "Social Democratic Party (UK)", "Liberal-Labour (UK)",
             "National Liberal Party (UK, 1922)", "Independent Liberal"):
        return "LIB"
    if p in ("Liberal National Party (UK, 1931)", "National Liberal Party (UK, 1931)"):
        return "NLIB"
    if p in ("National Labour Party (UK 1930s)", "National Labour Organisation"):
        return "NLAB"
    if p in ("Labour Party (UK)", "Labour and Co-operative Party", "Labour Representation Committee (1900)",
             "Colne Valley Labour Union", "Independent Labour Party"):
        return "LAB"
    if p in ("Irish Parliamentary Party", "All-for-Ireland League"):
        return "IRN"
    if p == "Scottish National Party": return "SNP"
    if p == "Plaid Cymru": return "PC"
    if p == "Speaker of the House of Commons (United Kingdom)": return "SPK"
    if p == "Sinn Féin": return "SF"
    if p == "Reform UK": return "REF"
    return "OTH"


def in_gov(fam, date):
    g = gov_on(date)
    if fam == "UUP":
        fam = "CON" if date < "1972-03-30" else "UUP"      # Ulster Unionists took the Conservative whip until 1972
    if fam == "CLIB":
        return "CLIB" in g or "LIB" in g
    return fam in g or (fam == "LIB" and "CLIB" in g)


SCANDAL = re.compile(r"scandal|expel|bankrupt|disqualif|recall|convict|fraud|unseat|petition|void|sentenc|misconduct|"
                     r"expenses|prison|corrupt|brib|sexual|harass|perjur|gaol|jail|criminal|false|"
                     r"suspen|lobbying|pornograph|drunk|assault", re.I)


def cause_group(cause, same_mp):
    c = cause.lower()
    if same_mp:
        return "same MP"
    if c.startswith("death") or "died" in c or "killed" in c or c.startswith("suicide"):
        return "death"
    if SCANDAL.search(c):
        return "scandal"
    return "resignation"


rows, bad = [], []
for page, t in W.items():
    if "disaster" in page:
        continue
    parts = re.split(r"\n(\|-[^\n]*)", t)
    for j in range(1, len(parts), 2):
        sep, body = parts[j], parts[j + 1]
        if "-election|" not in body and " by-election]]" not in body:
            continue
        lines = [l for l in body.split("\n") if l.startswith("|") and not l.startswith("|}") and not l.startswith("|colspan")]
        cells = []
        for l in lines:
            cells += l[1:].split("||")
        cells = [c for c in cells if not re.match(r'\s*style="background-color', c)]
        if len(cells) != 7:
            bad.append(body[:120]); continue
        link = re.search(r"\[\[([^\]|]+)(?:\|([^\]]*))?\]\]", cells[0])
        target, shown = link.group(1), (link.group(2) or link.group(1))
        seat = strip_tpl(shown)
        seat = re.sub(r"^\d{4}\s+|\s+by-election$", "", seat).strip()
        ds = strip_tpl(cells[1])
        m = re.search(r"(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})", ds)
        if not m:
            bad.append("date? " + ds); continue
        date = datetime.date(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1))).isoformat()
        inc_p = re.search(r"Party name with colour\|([^}]*)\}\}", cells[3])
        win_p = re.search(r"Party name with colour\|([^}]*)\}\}", cells[5]) or re.search(r"\[\[([^\]|]+)", cells[5])
        inc_party = inc_p.group(1).split("|")[0] if inc_p else strip_tpl(cells[3])
        win_party = win_p.group(1).split("|")[0] if win_p else strip_tpl(cells[5])
        if win_party == "Labour Co-op":
            win_party = "Labour and Co-operative Party"
        inc, win = strip_tpl(cells[2]), strip_tpl(cells[4])
        cause = strip_tpl(cells[6])
        same = norm(inc) == norm(win) and inc != ""
        fi, fw = family(inc_party), family(win_party)
        shaded = bool(re.search(r"bgcolor|background", sep))
        rows.append({"seat": seat, "date": date, "year": int(date[:4]), "incumbent": inc, "inc_party": inc_party, "inc_family": fi,
                     "winner": win, "win_party": win_party, "win_family": fw, "cause": cause, "cause_group": cause_group(cause, same),
                     "same_mp": int(same), "shaded": int(shaded), "uncontested": int(bool(re.search(r"uncontested|unopposed|name=unc\b", body, re.I))),
                     "inc_gov": int(in_gov(fi, date)), "win_gov": int(in_gov(fw, date)), "wiki_target": target, "list": page})

B = pd.DataFrame(rows).drop_duplicates(["seat", "date"]).sort_values("date").reset_index(drop=True)
# changed hands: the lists shade rows where the seat changed party; also derived from the party families
B["changed_family"] = ((B.inc_family != B.win_family) & ~((B.inc_family.isin(["LIB", "CLIB"])) & (B.win_family.isin(["LIB", "CLIB"])))).astype(int)
B["changed"] = B.shaded
B["gov_loss"] = ((B.inc_gov == 1) & (B.win_gov == 0)).astype(int)
B["gov_gain"] = ((B.inc_gov == 0) & (B.win_gov == 1)).astype(int)
B["id"] = [f"{d[:7]}_{norm(s).replace(' ', '_')}" for s, d in zip(B.seat, B.date)]
assert B.id.is_unique
print("parsed", len(B), "by-elections;", len(bad), "rows not parsed:", bad[:5])
print(B.groupby("list").size())

# ---- check against Wikidata (instances of by-election)
wd = pd.read_csv(f"{RAW}/byelections_wd.tsv", sep="\t", dtype=str, quoting=3).fillna("")
wd["label"] = wd["?eLabel"].str.extract(r'^"(.*)"@en$')[0].fillna("")
wd["date"] = wd["?date"].str[:10]
wd = wd[(wd.label.str.contains("by-election")) & (wd.date >= "1900-01-01")].drop_duplicates("?e")
wd["seatn"] = wd.label.str.replace(r"^(January |February |March |April |May |June |July |August |September |October |November |December )?\d{4}\s+", "", regex=True).str.replace(r"\s+by-election.*$", "", regex=True).map(norm)
key_w = collections.defaultdict(list)
for r in wd.itertuples():
    key_w[r.seatn].append(r.date)
found, date_ok = [], []
for r in B.itertuples():
    ds = key_w.get(norm(r.seat), [])
    near = [d for d in ds if d and abs((datetime.date.fromisoformat(d) - datetime.date.fromisoformat(r.date)).days) <= 60]
    yr = [d for d in ds if d[:4] == r.date[:4]]
    found.append(int(bool(near or yr)))
    date_ok.append(int(any(d == r.date for d in ds)))
B["in_wikidata"], B["wd_same_date"] = found, date_ok
S = B[B.year >= 1909]
r_parse = {"n_parsed": int(len(B)), "n_rows_unparsed": len(bad), "n_since_1909": int(len(S)), "first": B.date.min(), "last": B.date.max(),
           "wd_items": int(len(wd)), "wd_items_since_1909": int((wd.date >= "1909-01-01").sum()),
           "wiki_in_wd_pc": round(100 * S.in_wikidata.mean(), 1), "wiki_in_wd_n": int(S.in_wikidata.sum()),
           "wd_same_date_pc": round(100 * S.loc[S.in_wikidata == 1, "wd_same_date"].mean(), 1),
           "shaded_vs_family_agree_pc": round(100 * (S.shaded == S.changed_family).mean(), 1),
           "by_cause": S.cause_group.value_counts().to_dict(), "changed": int(S.changed.sum()), "uncontested": int(S.uncontested.sum()),
           "same_mp": int(S.same_mp.sum())}
# Wikidata items not in the lists (since 1909)
lk = {(norm(s), d[:4]) for s, d in zip(B.seat, B.date)}
wmiss = wd[(wd.date >= "1909-01-01") & ~wd.apply(lambda r: (r.seatn, r.date[:4]) in lk, axis=1)]
r_parse["wd_not_in_lists"] = int(len(wmiss))
r_parse["wd_not_in_lists_examples"] = wmiss.label.head(12).tolist()
B.to_csv(f"{DATA}/byelections.csv", index=False)
jsave(r_parse, f"{SCR}/r_parse.json", indent=1)
print(json.dumps(r_parse, indent=1, ensure_ascii=False))

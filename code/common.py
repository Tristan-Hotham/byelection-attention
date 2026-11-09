"""Shared paths, constants and helpers for the byelection-attention study ("Do by-elections make Parliament listen?").

Inputs (read in place, never modified):
  RAW/wiki_lists.json        Wikitext of the English Wikipedia "List of United Kingdom by-elections" pages (1900 to 1918,
                             1918 to 1931, 1931 to 1950, 1950 to 1979, 1979 to 2010, 2010 to present), retrieved 2026
                             (CC BY-SA 4.0). One table row per by-election: seat, date, incumbent and party, winner and
                             party, cause; rows shaded when the seat changed hands.
  RAW/byelections_wd.tsv     Wikidata items that are instances of "by-election" in the UK (CC0): item, label, date,
                             seat. Used only to check the coverage of the Wikipedia lists.
  RAW/hansard_monthly.json   UK Parliament Hansard API timeline statistics, House of Commons, contribution type Spoken,
                             by month 1909 to 2026-10 (Open Parliament Licence v3.0). "inp": contributions containing
                             "in <place>" for the 1,661 places of Mentioned in the House; "plain": contributions containing
                             the seat name itself for every by-election seat in the lists. Months absent = 0.
  HP/places.csv              Mentioned in the House (Hotham 2026, doi:10.5281/zenodo.23761431): the 1,661 place terms with
                             point, nation, population and ambiguity flags (shared, namesake, ordinary word) and precision.
  ELEC/contests.csv,         Who Won Here? (Hotham 2026, doi:10.5281/zenodo.23761425): every general election contest
  candidates.csv             1832 to 2024 with date, seat name, point and nation, and candidate vote shares.
"""
import json, gzip, os, re, math, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("BA_RAW", "/home/claude/newdata/raw_new12")
HP = os.environ.get("BA_HP", "/home/claude/src6/hansard-places/data")
ELEC = os.environ.get("BA_ELEC", "/home/claude/src6/elections-since-1832/data")
GEO = os.environ.get("BA_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("BA_FONTS", "/home/claude/ref/fonts")
SCR = os.environ.get("BA_SCRATCH", "/home/claude/scratch/byelection-attention")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
REL = os.path.join(ROOT, "release")
for d in (DATA, IMG, SCR):
    os.makedirs(d, exist_ok=True)

SLUG = "byelection-attention"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"

# months are integers: 0 = January 1909
M0 = 1909
LAST_MONTH = "2026-09"            # last complete month used (2026-10 may be partial at retrieval)
PRE, POST = 24, 36                # event window
REF = (-24, -13)                  # reference months (before any vacancy)
BINS = [(-12, -4), (-3, -1), (0, 2), (3, 12), (13, 24), (25, 36)]
BIN_NAMES = ["pre", "vacancy", "result", "year1", "year2", "year3"]
K_CONTROLS = 5
GE_GAP = 12                       # months: by-elections this close to a general election are excluded
NEAR_KM = 25.0                    # controls further than this from any treated place; neighbour placebo 3 to 25 km


def mi(ym):
    y, m = (int(x) for x in ym.split("-")[:2])
    return (y - M0) * 12 + m - 1


def ym(i):
    return f"{M0 + i // 12}-{i % 12 + 1:02d}"


LAST = mi(LAST_MONTH)


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = s.replace("&", "and")
    s = re.sub(r"[’'`]", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    s = re.sub(r"\bsaint\b", "st", s)
    return s


def km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jsave(obj, path, indent=None):
    obj = nonan(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    if f == "x1": return f"{float(v):.1f} times"
    if f == "abs0": return f"{abs(float(v)):.0f}"
    raise ValueError(f)


# governing parties by date (start date, set of party families in government). Families: CON (Conservative, Unionist,
# Liberal Unionist, Ulster Unionist to 1972), LIB, LAB, NLIB (Liberal National / National Liberal), NLAB (National Labour).
GOV = [("1905-12-05", {"LIB"}), ("1915-05-25", {"LIB", "CLIB", "CON", "LAB"}), ("1918-12-14", {"CON", "CLIB"}),
       ("1922-10-19", {"CON"}), ("1924-01-22", {"LAB"}), ("1924-11-04", {"CON"}), ("1929-06-05", {"LAB"}),
       ("1931-08-24", {"CON", "NLIB", "NLAB", "LIB"}), ("1932-09-28", {"CON", "NLIB", "NLAB"}),
       ("1940-05-10", {"CON", "NLIB", "NLAB", "LAB", "LIB"}), ("1945-05-23", {"CON", "NLIB"}), ("1945-07-26", {"LAB"}),
       ("1951-10-26", {"CON", "NLIB"}), ("1964-10-16", {"LAB"}), ("1970-06-19", {"CON"}), ("1974-03-04", {"LAB"}),
       ("1979-05-04", {"CON"}), ("1997-05-02", {"LAB"}), ("2010-05-11", {"CON", "LIB"}), ("2015-05-08", {"CON"}),
       ("2024-07-05", {"LAB"})]


def gov_on(date):
    cur = GOV[0][1]
    for d, s in GOV:
        if date >= d:
            cur = s
    return cur

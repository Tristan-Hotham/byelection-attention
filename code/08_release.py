"""Step 8: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo), and the monthly counts file.
10.5281/zenodo.24094210, https://doi.org/10.5281/zenodo.24094210 and https://blog.tristanhotham.com/2026/10/31/byelection-attention/ are left for the publisher to fill."""
import json as _json, shutil, zipfile, gzip, csv
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json")
NAME = "Hotham_Byelection_Attention"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
# monthly "in" counts for every Hansard town (raw API counts, non-zero months only), for reuse
H = jload(f"{RAW}/hansard_monthly.json")
with gzip.open(f"{DATA}/hansard_monthly_in.csv.gz", "wt", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["term", "month", "contributions"])
    for t in sorted(H["inp"]):
        for m in sorted(H["inp"][t]):
            w.writerow([t, m, H["inp"][t][m]])
with gzip.open(f"{DATA}/hansard_monthly_seatname.csv.gz", "wt", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["seat_name", "month", "contributions"])
    for t in sorted(H["plain"]):
        for m in sorted(H["plain"][t]):
            w.writerow([t, m, H["plain"][t][m]])

post = open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", "DSIT", "DCMS", "civil serv", "pre-registered"):
    assert bad not in vis, bad
assert AI in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Do by-elections make Parliament listen?",
        "slug": "byelection-attention",
        "excerpt": f"I followed {R['sample']['byelections']} UK by-elections through a century of Hansard. Around polling day the Commons mentions the town {R['x']['result']:.1f} times as often as similar towns, and a year later still {R['x']['year1']:.1f} times. Before 1945, no detectable rise.",
        "seo_description": f"When a UK seat holds a by-election, does the Commons talk more about the town? {R['sample']['byelections']} by-elections and a century of Hansard.",
        "tags": ["maps", "data visualisation", "Parliament", "Hansard", "by-elections", "representation", "UK politics", "elections"],
        "header_alt": "Title card on cream paper reading 'Do by-elections make Parliament listen?' beside a map of UK by-election towns coloured from blue to red by the change in Commons mentions after the by-election."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
_json.dump(meta, open(f"{REL}/blog/meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(os.path.join(ROOT, "code"))):
        if fn.endswith((".pyc", ".png")) or fn == "__pycache__":
            continue
        z.write(os.path.join(ROOT, "code", fn), f"{SLUG}/code/{fn}")
    for fn in ("byelections.csv", "event_places.csv", "match_log.csv", "pairs.csv", "event_study.csv", "models.csv", "results.json",
               "hansard_monthly_in.csv.gz", "hansard_monthly_seatname.csv.gz"):
        z.write(os.path.join(DATA, fn), f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE", "NOTES.md"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(os.path.join(REL, "paper", "cover_note.md"), f"{SLUG}/release/paper/cover_note.md")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("$", "").replace("``", "\"").replace("''", "\"").replace("-3", "-3")
zmeta = {"title": "Do By-Elections Make Parliament Listen? Parliamentary Attention to By-Election Constituencies in the House of Commons, 1911 to 2023",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/byelection-attention/}}.</p><p>Sources: Hansard via the UK Parliament Hansard API (Open Parliament Licence v3.0); English Wikipedia lists of UK by-elections (CC BY-SA 4.0); Wikidata (CC0); Mentioned in the House (doi:10.5281/zenodo.23761431); Who Won Here? (doi:10.5281/zenodo.23761425). Text, figures and data CC BY 4.0 (fields from the Wikipedia lists CC BY-SA 4.0); code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["by-elections", "parliamentary attention", "constituency representation", "House of Commons", "Hansard", "event study", "United Kingdom"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "10.5281/zenodo.23761431", "relation": "isDerivedFrom", "resource_type": "publication"},
                                 {"identifier": "10.5281/zenodo.23761425", "relation": "isDerivedFrom", "resource_type": "publication"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
assert "\u2014" not in sj and "\u2013" not in sj and "--" not in sj
_json.dump(zmeta, open(f"{Z}/metadata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")

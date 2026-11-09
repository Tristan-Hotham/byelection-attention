"""Step 6: index.html from code/page_template.html and code/page.css, filled from data/results.json, with the full-screen
snippet. 10.5281/zenodo.24094210, https://doi.org/10.5281/zenodo.24094210 and https://blog.tristanhotham.com/2026/10/31/byelection-attention/ are left for the publisher to fill."""
from common import *

R = jload(f"{DATA}/results.json")
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
t = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
t = t.replace("{{CSS}}", open(os.path.join(ROOT, "code", "page.css"), encoding="utf-8").read())
t = t.replace("{{FULLSCREEN}}", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
t = t.replace("{{REPO}}", REPO).replace("{{AI}}", AI).replace("{{BYLINE}}", BYLINE).replace("{{VERSION}}", "2026a")
t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), t)
assert set(re.findall(r"\{\{([^}]+)\}\}", t)) <= KEEP, set(re.findall(r"\{\{([^}]+)\}\}", t))
vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", t, flags=re.S)
for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv"):
    assert bad not in vis, bad
S = jload(f"{DATA}/site.json")
keys = {(b["s"], b["y"]) for b in S["b"]}
for g in re.findall(r'data-go="([^"]+)"', t):
    s_, y_ = g.split("|"); assert (s_, int(y_)) in keys, g
sj = json.dumps(S, ensure_ascii=False)
assert "—" not in sj and "–" not in sj
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(t)
print("index.html", len(t) // 1024, "KB")

"""Step 9: README.md, LICENSE, reddit/post.md and release/paper/cover_note.md from data/results.json.
10.5281/zenodo.24094210, https://doi.org/10.5281/zenodo.24094210 and https://blog.tristanhotham.com/2026/10/31/byelection-attention/ are left for the publisher to fill."""
from common import *

R = jload(f"{DATA}/results.json")
M1, x, S, F, P = R["M1"], R["x"], R["sample"], R["flow"], R["parse"]
ci = lambda d: f"{d['b']:.0f}% (95% CI {d['lo']:.0f} to {d['hi']:.0f})"
readme = f"""# Do by-elections make Parliament listen?

Parliamentary attention to by-election constituencies in the House of Commons, 1911 to 2023. Every UK by-election in the Wikipedia lists since 1909 ({P['n_since_1909']:,}) linked to monthly Hansard counts of Commons contributions saying "in" a town named in the seat, and a stacked event study comparing each by-election town with five matched towns month by month, fixed in a written analysis plan before any outcome model was run (NOTES.md). A data study by Dr Tristan Hotham (Independent researcher).

Interactive page: https://maps.tristanhotham.com/{SLUG}/
Paper: {{https://doi.org/10.5281/zenodo.24094210}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/byelection-attention/}}
Code and data: {REPO}

## Headline results

- Sample: {S['pairs']} by-election towns from {S['byelections']} by-elections ({S['first']} to {S['last']}) in {S['places']} towns, each with five matched towns; {F['byelections_linked']:,} of {P['n_since_1909']:,} by-elections since 1909 name a town counted in Hansard.
- Around polling day: mentions are {ci(M1['vacancy'])} higher in the three months before polling and {ci(M1['result'])} higher in the polling month and the two after, about {x['result']:.1f} times matched towns (PPML, stack-by-month fixed effects, errors clustered by by-election). No pre-trend: {ci(M1['pre'])} in months 12 to 4 before.
- Afterwards: {ci(M1['year1'])} in months 3 to 12 and {ci(M1['year2'])} in months 13 to 24; months 25 to 36 {ci(M1['year3'])}, significant in only {R['robust_range']['year3_n_sig']} of {R['robust_range']['n_checks']} checks.
- Changed hands: the first jump is {x['changed_result']:.1f} times as large as where the seat was held (difference {R['contrast']['changed_result']['b']:.0f}%, CI {R['contrast']['changed_result']['lo']:.0f} to {R['contrast']['changed_result']['hi']:.0f}); the later attention is not clearly different. Government-held vs opposition-held: no difference. Deaths bring a larger and longer rise than resignations.
- Era: no detectable rise for 1911 to 1944 ({ci(R['het']['era']['est']['1911 to 1944']['result'])} at the result), {x['era2_result']:.1f} times for 1945 to 1979 and {x['era3_result']:.1f} times for 1980 to 2023.
- Placebos: dates moved 24 months earlier ({ci(R['P1']['result'])}) and neighbouring towns 3 to 25 km away ({ci(R['P2']['result'])}) show nothing; the seat's own name (the "hon. Member for" formula) rises only {ci(R['S1']['result'])} and only around polling.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive page: MapLibre on OpenFreeMap Positron; every by-election since 1909, towns coloured by the change in mentions (or by change of hands, or cause), timeline, search, layers, full screen, popups with a quarterly sparkline. |
| `header.png` | Social card, 1200 x 630. |
| `data/byelections.csv` | Every by-election parsed from the Wikipedia lists (1,530 from 1900): seat, date, members, parties and families, cause and cause group, changed hands, government status, Wikidata check. CC BY-SA 4.0 (from Wikipedia). |
| `data/match_log.csv` | Every seat-to-town link with its distance to the seat point and the number of seats naming the town. |
| `data/event_places.csv` | One row per by-election town with every exclusion flag and the main-sample marker. |
| `data/pairs.csv` | Per by-election town: mentions in the reference year and the year after, for the town and its controls. |
| `data/event_study.csv`, `data/models.csv` | Monthly event-study estimates; every coefficient of every model. |
| `data/hansard_monthly_in.csv.gz`, `data/hansard_monthly_seatname.csv.gz` | The raw monthly Hansard counts ("in <town>" for 1,661 towns; each by-election seat's name), non-zero months. |
| `data/results.json`, `data/site.json` | Every number quoted anywhere; page data. |
| `code/` | Scripts in order, templates, `overrides.csv` (hand decisions), `qa.js`. |
| `release/` | Paper (PDF, LaTeX, figures, `cover_note.md`), blog post and figures, Zenodo files. |
| `reddit/` | Collage, its script, the looping GIF and the post text. |
| `NOTES.md` | Working notes and the analysis plan, written before the models were run. |

## Method in brief

- By-elections: the six Wikipedia lists parsed row by row; party families and governing parties coded by hand; causes grouped (death, resignation or appointment, scandal or void election, same member re-elected); {P['wiki_in_wd_pc']}% have a matching Wikidata item.
- Towns: longest whole-word matches of the 1,661 *Mentioned in the House* town names in each seat name, checked against seat points; ambiguous names excluded; prefix subtraction ("in Bury" minus "in Bury St Edmunds").
- Exclusions (pre-set): window outside the data, same member re-elected, within 12 months of a general election, another by-election naming the town in the window, towns named in three or more seats.
- Controls: five towns per by-election town, same nation, no by-election, more than 25 km away, nearest on reference-period mentions and population.
- Model: PPML with town-within-stack and stack-by-calendar-month fixed effects, bins relative to months 24 to 13 before polling, errors clustered by by-election (pyfixest). {R['robust_range']['n_checks']} robustness checks, three placebos, the seat-name phrase.

## How to rerun

Needs Python 3 with pandas, numpy, pyfixest, scipy, shapely, pyproj, matplotlib, Pillow; xelatex; node with Playwright for QA. Raw inputs are listed in `code/common.py`.

```
python3 code/01_byelections.py   # parse the Wikipedia lists, Wikidata check
python3 code/02_events.py        # seat-to-town links, exclusions, matched controls
python3 code/03_models.py        # all models (about 15 minutes)
python3 code/03b_referee_checks.py # exploratory checks added at review
python3 code/04_results.py       # results.json and page data
python3 code/05_figures.py       # figures and header
python3 code/06_build_site.py    # index.html
python3 code/07_paper.py         # paper (DOI=10.5281/zenodo.N to fill the DOI)
python3 reddit/collage.py
python3 code/09_readme.py        # README, LICENSE, Reddit post, cover note
python3 code/08_release.py       # blog post, Zenodo files
```

## Sources and licences

- Hansard, House of Commons, via the UK Parliament Hansard API: contains Parliamentary information licensed under the Open Parliament Licence v3.0.
- Wikipedia contributors, "List of United Kingdom by-elections" (1900 to 1918, 1918 to 1931, 1931 to 1950, 1950 to 1979, 1979 to 2010, 2010 to present), retrieved 2026, CC BY-SA 4.0. Wikidata (CC0).
- Town names, points and ambiguity flags from Hotham (2026) *Mentioned in the House*, doi:10.5281/zenodo.23761431; seat points and general election dates from Hotham (2026) *Who Won Here?*, doi:10.5281/zenodo.23761425.
- Base map: OpenFreeMap Positron (OpenStreetMap contributors, ODbL). MapLibre GL JS (BSD 3-Clause). Natural Earth and ONS outlines in the static figures (public domain; Open Government Licence v3.0).
- Text, figures and derived data CC BY 4.0, except `data/byelections.csv` and the by-election fields in other files, which are CC BY-SA 4.0 because they come from Wikipedia; code MIT.

## Citation

Hotham, T. (2026) Do by-elections make Parliament listen? Parliamentary attention to by-election constituencies in the House of Commons, 1911 to 2023. Zenodo. {{https://doi.org/10.5281/zenodo.24094210}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
mit = open("/home/claude/studies/wiki-vs-hansard/LICENSE", encoding="utf-8").read().split("Text, figures and the paper")[0]
lic = mit.replace("Code (code/, js/, reddit/collage.py, reddit/gif.py)", "Code (code/, js/, reddit/collage.py)") + (
    "Text, figures and the paper: Creative Commons Attribution 4.0 International (CC BY 4.0), https://creativecommons.org/licenses/by/4.0/\n"
    "Derived data (data/): CC BY 4.0, except data/byelections.csv and the by-election fields (seat, members, parties, causes) in other files, "
    "which are adapted from English Wikipedia and shared under CC BY-SA 4.0, https://creativecommons.org/licenses/by-sa/4.0/. "
    "Other sources: Hansard (Open Parliament Licence v3.0), Wikidata (CC0).\n")
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(lic)
post = f"""**Title:** [OC] When a UK seat holds a by-election, MPs mention the town {x['result']:.1f}x as often around polling day and still {x['year1']:.1f}x a year later. Before 1945: no detectable rise.

**Body:**

I followed {S['byelections']} UK by-elections ({S['first']} to {S['last']}) through Hansard, counting Commons speeches that say "in <town>" for the town named in the seat, month by month, and compared each town with five similar towns that had no by-election.

- Polling month and the two after: {x['result']:.1f}x the mentions of matched towns.
- Months 3 to 12: {x['year1']:.1f}x. Second year: {x['year2']:.1f}x. Third year: no clear difference.
- When the seat changed hands the first jump was bigger ({x['changed_hands_result']:.1f}x vs {x['held_result']:.1f}x), but a year on the gap was gone.
- 1911 to 1944: no detectable rise. 1980 to 2023: {x['era3_result']:.1f}x around polling.
- Placebo checks (fake dates two years earlier, neighbouring towns) show nothing.

Interactive map with every by-election since 1909 and a timeline: https://maps.tristanhotham.com/{SLUG}/

**Source comment:**

Data: Hansard via the UK Parliament API (Open Parliament Licence v3.0); Wikipedia lists of UK by-elections (CC BY-SA 4.0); Wikidata (CC0). Method: stacked event study, Poisson regression with matched towns and month fixed effects, plan written before the analysis. Tools: Python (pandas, pyfixest, matplotlib), MapLibre. Paper and code: {REPO}
"""
os.makedirs(os.path.join(ROOT, "reddit"), exist_ok=True)
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
cover = f"""# Cover note: Do by-elections make Parliament listen?

## Suitable journals (checked 2026)

All three publish subscription articles with no article processing charge; open access is optional and paid. Word limits were checked where the publishers' author pages could be reached; recheck before submitting.

1. **British Politics** (Palgrave Macmillan). Articles "no more than 9,000 words, excluding the bibliography" (author guidelines, checked 2026). The paper is about 8,500 words before the references, counting tables and captions: it fits. Best fit for the British framing and the historical result.
2. **Parliamentary Affairs** (Oxford University Press, for the Hansard Society). Publishes work on Parliament, by-elections and constituency representation (Norton 1994 appeared there). Original articles: "Maximum words 8,000 / maximum figures and tables 5" (OUP general instructions, checked 2026); a fee applies only for an open access licence. The paper is about 8,500 words with 7 figures and 8 tables, so it would need cutting to 8,000 words and five main-text exhibits, with the rest moved to online supplementary material.
3. **Legislative Studies Quarterly** (Wiley). Published Feigert and Norris (1990), Mughan (1988) and Zittel et al. (2019), the closest comparative work; its length guidance could not be reached from this workspace and should be checked. A comparative framing (by-elections as dated local shocks to legislative attention) would suit it.

Also possible: **The Journal of Legislative Studies** (Taylor and Francis), which published Russo (2011) on constituency focus; author pages could not be reached.

## Summary of the contribution (for a cover letter)

A long literature asks what British by-elections reveal about voters; this paper asks what they do to Parliament. Linking every UK by-election since 1909 in the Wikipedia lists to monthly Hansard counts of Commons contributions that mention the town named in the seat, and comparing {S['pairs']} by-election towns with matched towns in a stacked event study specified in a written plan before the analysis, it finds that mentions rise during the vacancy, peak around polling day at about {x['result']:.1f} times the matched level, and stay about {x['year1']:.1f} times higher a year later and {x['year2']:.1f} times higher in the second year, before fading. A change of hands enlarges the first jump but not the lasting attention; government- and opposition-held seats do not differ; and there is no detectable rise before 1945. Placebo dates, neighbouring towns and the seat-name phrase show no comparable change. The design is observational, and data and code are openly released.
"""
open(os.path.join(REL, "paper", "cover_note.md"), "w", encoding="utf-8").write(cover)
for t in (readme, post, cover, lic):
    for bad in ("—", "–", "DSIT", "DCMS", "civil serv", "pre-registered"):
        assert bad not in t, bad
print("readme", len(readme.split()), "words; cover", len(cover.split()))

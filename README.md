# Do by-elections make Parliament listen?

Parliamentary attention to by-election constituencies in the House of Commons, 1911 to 2023. Every UK by-election in the Wikipedia lists since 1909 (1,339) linked to monthly Hansard counts of Commons contributions saying "in" a town named in the seat, and a stacked event study comparing each by-election town with five matched towns month by month, fixed in a written analysis plan before any outcome model was run (NOTES.md). A data study by Dr Tristan Hotham (Independent researcher).

Interactive page: https://maps.tristanhotham.com/byelection-attention/
Paper: https://doi.org/10.5281/zenodo.24094210
Blog post: https://blog.tristanhotham.com/2026/10/31/byelection-attention/
Code and data: https://github.com/Tristan-Hotham/byelection-attention

## Headline results

- Sample: 387 by-election towns from 366 by-elections (1912 to 2022) in 253 towns, each with five matched towns; 957 of 1,339 by-elections since 1909 name a town counted in Hansard.
- Around polling day: mentions are 81% (95% CI 26 to 159) higher in the three months before polling and 296% (95% CI 196 to 429) higher in the polling month and the two after, about 4.0 times matched towns (PPML, stack-by-month fixed effects, errors clustered by by-election). No pre-trend: 12% (95% CI -11 to 40) in months 12 to 4 before.
- Afterwards: 91% (95% CI 51 to 143) in months 3 to 12 and 55% (95% CI 19 to 101) in months 13 to 24; months 25 to 36 31% (95% CI -1 to 73), significant in only 7 of 18 checks.
- Changed hands: the first jump is 2.3 times as large as where the seat was held (difference 135%, CI 27 to 335); the later attention is not clearly different. Government-held vs opposition-held: no difference. Deaths bring a larger and longer rise than resignations.
- Era: no detectable rise for 1911 to 1944 (24% (95% CI -34 to 133) at the result), 2.6 times for 1945 to 1979 and 6.9 times for 1980 to 2023.
- Placebos: dates moved 24 months earlier (8% (95% CI -18 to 44)) and neighbouring towns 3 to 25 km away (-1% (95% CI -24 to 27)) show nothing; the seat's own name (the "hon. Member for" formula) rises only 38% (95% CI 15 to 65) and only around polling.

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

- By-elections: the six Wikipedia lists parsed row by row; party families and governing parties coded by hand; causes grouped (death, resignation or appointment, scandal or void election, same member re-elected); 69.8% have a matching Wikidata item.
- Towns: longest whole-word matches of the 1,661 *Mentioned in the House* town names in each seat name, checked against seat points; ambiguous names excluded; prefix subtraction ("in Bury" minus "in Bury St Edmunds").
- Exclusions (pre-set): window outside the data, same member re-elected, within 12 months of a general election, another by-election naming the town in the window, towns named in three or more seats.
- Controls: five towns per by-election town, same nation, no by-election, more than 25 km away, nearest on reference-period mentions and population.
- Model: PPML with town-within-stack and stack-by-calendar-month fixed effects, bins relative to months 24 to 13 before polling, errors clustered by by-election (pyfixest). 18 robustness checks, three placebos, the seat-name phrase.

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

Hotham, T. (2026) Do by-elections make Parliament listen? Parliamentary attention to by-election constituencies in the House of Commons, 1911 to 2023. Zenodo. https://doi.org/10.5281/zenodo.24094210

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.

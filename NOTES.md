# byelection-attention: working notes

Brief: /home/claude/work/new12/BRIEFS.md section 2 (+ shared rules new8/new9/new10/new11, house brief /home/claude/newdata/BRIEF.md,
GIF brief /home/claude/gifs/BRIEF.md). Format refs: pm-streets, wiki-vs-hansard.
Scratch: /home/claude/scratch/byelection-attention (delete at the end).

## Data construction (done before any outcome model)

- 01_byelections.py: the six Wikipedia "List of United Kingdom by-elections" tables parsed row by row: 1,530 by-elections
  1900 to 2026 (one separator row was prose, not a by-election; nothing else unparsed). 1,339 from 1909. Party labels mapped
  to families (Coalition Liberal kept apart for 1918 to 1922; Ulster Unionists counted with the Conservatives until 1972).
  Government parties by date coded in common.GOV (coalitions included). "Changed hands" = the row is shaded in the list
  (agrees with a party-family comparison for 98.9%). Uncontested: "uncontested"/"unopposed" notes and the lists'
  shared "unc" footnote. Cause groups from the cause text: death; scandal or voided election (keywords; all 46 read by eye,
  "Master in Lunacy" and "certified as insane" moved out of scandal); same MP re-elected (incumbent = winner: ministerial
  re-elections before 1926, recontests such as the 1986 Ulster Unionist resignations); resignation (everything else:
  peerages, judicial and other appointments, ill health, resignation).
- Wikidata check: 950 Wikidata by-election items since 1909; 935 of the 1,339 list entries (69.8%) have one, with the same
  date for 98.3% of those. 16 Wikidata items are not matched by name and year, all naming variants (Westminster suffix,
  Hull North vs Kingston upon Hull North, May/November Bootle 1990). The Wikipedia lists are the master list.
- 02_events.py: seat names linked to the 1,661 Hansard place terms by longest whole-word match (no overlaps; seat aliases
  "The Hartlepools", Stratford-on-Avon). University seats dropped. Every link more than 12 km from the seat's point (Who Won
  Here?) read by eye; > 60 km dropped as a different place, plus hand decisions in code/overrides.csv (Colne Valley is not
  Colne; West Derby is not Derby; Plymouth Sutton is not Sutton; Kincardine and Deeside is not Flintshire Deeside; Merthyr,
  Kensington, Kennington kept, with the London points for the last two because Hansard's own points are namesakes).
  "in <place>" monthly counts: prefix subtraction (longer names starting with the same words), spelling variants added.
  Places flagged in Mentioned in the House (shared, namesake, ordinary word) are not used.
- Event-place pairs: 1,006 links for 957 by-elections. Exclusion flow (pre-set, in this order): flagged place; window
  outside the data (polling before 1911-01 or after 2023-09); same MP re-elected; within 12 months of a general election;
  another by-election naming the same place within the window (-24 to +36 months); place named in more than two seats at
  the preceding general election (city divisions such as Glasgow Hillhead for Glasgow, where one seat is a small part of the
  place). Main sample: 387 pairs, 366 by-elections, 253 places.
- Controls: for each treated place, 5 places from the same nation (all nations if fewer than 15 eligible) with no
  by-election naming them within the window plus 12 months either side, more than 25 km from every treated place of that
  by-election, nearest on log(1 + mean monthly mentions in the reference months -24 to -13) (weight 1/0.5) and log
  population (weight 1/1.0), without replacement within a by-election.

## Analysis plan (written before running any outcome model)

Question: when a seat holds a by-election, does the House of Commons talk more about the place, and does the attention
outlast the campaign? Does it depend on whether the seat changed hands, the cause, the era, and who held the seat?

Unit: a place-by-election pair (treated place p linked to by-election e) and its matched controls, in months k = -24 to
+36 relative to the polling month (k = 0). Stacked design: one stack per by-election.

Outcome (Y): Commons spoken contributions in month t containing "in <place>" (Hansard API counts, prefix-subtracted).
Not the seat-name phrase, which is mechanically raised by "the hon. Member for <seat>" when a new MP arrives (shown
separately, see S1).

Main specification (M1): Poisson pseudo-maximum likelihood,
  E[Y_ust] = exp(a_u + g_(e,t) + sum_b beta_b * Treated_u * 1[k in bin b]),
with unit (place within stack) fixed effects a_u, stack-by-calendar-month fixed effects g_(e,t) (each treated place is
compared with its own controls in the same month), bins b = pre (-12 to -4), vacancy (-3 to -1), result (0 to 2), year 1
(3 to 12), year 2 (13 to 24), year 3 (25 to 36); reference = months -24 to -13 (before any vacancy). Standard errors
clustered by by-election. Effects reported as 100 * (exp(beta) - 1) % with 95% CIs. N (pairs, by-elections, rows)
reported everywhere. Also the full monthly event study (one coefficient per month, same reference) for the figure.

Hypotheses and what would count against them:
- H1 attention: mentions rise around the by-election: beta_vacancy > 0 and beta_result > 0 (and the pooled -3 to +2
  window, M1b). Against: CIs of the pooled window including 0.
- H2 persistence: the rise outlasts the campaign: beta_year1 > 0; and beta_year2, beta_year3 > 0 (long-run). Against:
  year 1 CI including 0 (attention does not outlast the campaign); year 2/3 CIs including 0 (no lasting effect).
- H3 shock: the rise is larger when the seat changed hands (interaction Treated x post bins x changed > 0), and when the
  government lost the seat (gov_loss). Two-sided test, report the contrast with CI.
- H4 cause: by cause group (death, resignation, scandal or void election). Expect scandal largest (attention to the
  scandal) but N is small; deaths may show a pre-dip (an ill MP speaks less, though the outcome counts all speakers).
  Reported as group estimates and contrasts against death.
- H5 era: 1911 to 1944, 1945 to 1979, 1980 to 2023. Two-sided.
- H6 seat holder: government-held vs opposition-held at the time. Two-sided.
- Exploratory (labelled): previous majority (marginal < 10 points vs safer), nation, contested vs uncontested.

Pre-specified checks:
- Placebo P1 (fake dates): the same design with the event moved 24 months earlier, window -24 to +12 relative to the
  fake date (so the real vacancy, about 3 months before the real poll at fake +24, falls outside). All bins should be
  about 0.
- Placebo P2 (neighbours): places 3 to 25 km from a treated place, not named in any seat with a by-election within the
  window, treated as if treated, with their own matched controls (further than 25 km from them and from the treated place). Expect
  about 0 (or a small spillover; reported as such).
- Placebo P3 (same MP re-elected): ministerial re-elections and recontests (no new MP, often no contest): expected
  smaller, near 0 after the result.
- Alternative specifications: A1 OLS of log(1 + Y) with the same fixed effects; A2 PPML treated only (no controls), unit
  and calendar-month fixed effects; A3 10 controls per treated place.
- Clustering: by place (treated place term) instead of by-election.
- Leave-one-out: drop each era; drop each nation; drop London (places within 25 km of Charing Cross).
- Measurement/sample sensitivity: keep by-elections within 12 months of a general election; keep overlapping
  by-elections; include city divisions (places named in more than two seats); no prefix subtraction; reference period
  -24 to -4; contested by-elections only; places named in exactly one seat only.
- S1 seat-name phrase (secondary, mechanical): the same stacked PPML for the plain seat-name phrase of each by-election
  seat (main-sample by-elections), with 5 control seat names (other by-election seats with no by-election within the
  window +/-12 months, in use at the preceding general election and the one after the window), matched on log(1 + reference-month mean).
  Expect a large, lasting rise driven by "Member for <seat>"; not interpreted as attention.

Design honesty: by-elections are not random. The vacancy (death, resignation, scandal) is itself news and can raise
mentions before the poll; the design compares the place with similar places in the same months, so it estimates the
change in attention that comes with the whole episode (vacancy, campaign, result, new MP), not the effect of the vote
alone. "in <place>" is a sample of mentions. Places come from today's list of 1,661 towns, so county divisions are
covered only through the towns in their names.

## References: verification (WebSearch/WebFetch, 2026)
39 references. Abstract or publisher/repository description read for: Mughan 1986, Studlar & Sigelman 1987, Upton 1991,
Price & Sanders 1998, Hanretty 2021, Pollock 1941, Cook & Ramsden 1997 (T&F description), Eulau & Karps 1977, Mansbridge
2003, Cain et al. 1987, Fenno 1978 (author site synopsis), Norton & Wood 1993, André et al. 2015, Hobolt & Klemmensen 2008,
Soroka et al. 2009, Fernandes et al. 2018, Rheault et al. 2016, Santos Silva & Tenreyro 2006, Correia et al. 2020,
Cengiz et al. 2019, Baker et al. 2022, Abadie et al. 2023. Metadata confirmed (RePEc handles, repository records, a
verified reference list) but abstract not read: Feigert & Norris 1990 (pages from Hanretty 2021's reference list; volume
15(2) by LSQ volume-year), Mughan 1988 (pages from the same list; 13(1) by volume-year), Norris 1990 (publisher listings),
Martin 2011, Kellermann 2016, Russo 2011 (issue 3 not shown on the repository page), Norton 1994, Searing 1985 (Bamberg
working paper bibliography), Searing 1994, Jones & Baumgartner 2005, Loewen & Bastien 2010, Zittel et al. 2019, Sun &
Abraham 2021, Cameron & Miller 2015. These are cited only for what their titles state. Dropped: Quinlan 2023 (BJPIR;
volume and pages not reachable), Pattie et al. 1995 (abstract not reachable), Saalfeld & Bischof 2013 (not needed).
Blocked domains during checking: api.crossref.org, api.openalex.org, some ideas.repec.org pages, tandfonline, ssoar.
Journal limits: British Politics 9,000 words excl. bibliography (Palgrave page, checked); Parliamentary Affairs 8,000
(earlier check, not reconfirmed); LSQ and JLS author pages not reachable.

## Results (first and only run of the plan; numbers from data/results.json)

- Main sample 387 pairs, 366 by-elections, 253 places, 1911 to 2023 (91 pairs have no mentions at all in the 61 months
  and drop out of PPML; 28,621 rows used of 141,642). Clusters 366.
- M1 (PPML): pre -12..-4 +12% [-11, 40] (no pre-trend); vacancy -3..-1 +81% [27, 159]; result 0..2 +296% [196, 429];
  year 1 +91% [51, 143]; year 2 +55% [19, 101]; year 3 +31% [-1, 73] (not significant). H1 supported; H2 supported for
  years 1 and 2, not year 3.
- Absolute scale: treated places average 0.12 "in" mentions a month in the reference months (1.5 a year); 0.82 in the
  polling month; 0.22 a month in months 3 to 12 (controls 0.09).
- H3: changed hands result window 2.3 times the held effect [contrast CI excludes 0]; year 1 and later not different.
  Government lost the seat: 3.0 times at the result, not different later. H6: government- vs opposition-held no difference.
- H4: deaths larger and more lasting than resignations (year 1 contrast -39% [-62, -1]); scandal (10 pairs) imprecise.
- H5: no detectable rise 1911 to 1944 (result +24% [-34, 133]); rise 1945 to 1979 and largest 1980 to 2023 (+590%).
- Placebos: P1 fake dates all about 0; P2 neighbours all about 0; P3 same MP re-elected (19 by-elections) mentions FELL
  after the result (-94%): consistent with new ministers speaking less about home; very few cases.
- S1 seat-name phrase: +38% [15, 65] in the result months only, smaller than "in <place>", and slightly negative during
  the vacancy (no member to name). So the main result is not the "Member for" formula.
- Robustness (18 checks): result and year-1 rises positive in every check (year 1 except without England, 3,760 rows);
  year 2 significant in 16 of 18; year 3 in 7 of 18 (so the third-year effect is not robust). Without 1980 to 2023 the
  year-2 effect loses significance. Including city divisions roughly halves the effects (dilution, as expected).

## Deliverables
index.html + js/page.js (QA: qa/*.png, 0 console errors at 1280 and 390 px); header.png; data/*; code/01..09;
release/paper (PDF 21 pp, ~8,450 words before references incl. tables, abstract 227 words, cover_note.md);
release/blog (post.html, 5 figures, meta.json); release/zenodo; reddit/collage.py + png + post.md + GIF
(/home/claude/gifs/scripts/byelection-attention.py). Scratch deleted at the end.
Not possible with the data: swing (no by-election vote shares in the lists; map sized by mentions in the year after instead);
"places within the seat" (no historical boundaries; name-based links only); speaker-level counts.

## Independent referee review (2026)

Checked by a reviewer who did not build the study.

1. Reproduction. 01, 02, 03 and 04 rerun from raw_new12 and src6: byelections.csv, event_places.csv, match_log.csv, pairs.csv,
   event_study.csv, models.csv identical byte for byte; results.json identical except the new "explore" block (below).
   Paper tables match results.json.
2. Numbers. Every figure in the paper, blog, map page, collage, post.md and GIF checked against results.json; all match.
   Wording fixed where it went beyond the estimates: "the rise is absent before 1945" / "no effect at all" / "Before the war,
   nothing" (1911 to 1944 is +24%, CI -34 to 133: not detectable, not shown absent) now "no detectable rise" / "Before 1945,
   no clear rise" (paper abstract, discussion, conclusion; blog; map; Reddit title). Map intro said the 366 by-elections were
   those "named after a town I can count"; it is 957 linked, 366 after the exclusions: fixed. Map "same level of mentions"
   now "similar"; "before looking at any result" now "before running any model" (as the plan states).
3. References. Verified online (title, authors, year, venue, volume/issue, pages; abstract or repository record): Upton 1991,
   Hanretty 2021 (468 post-war by-elections confirmed), Mughan 1986 (quote and three models confirmed), Mughan 1988,
   Feigert & Norris 1990, Price & Sanders 1998, Studlar & Sigelman 1987, Loewen & Bastien 2010, Norris 1990, Pollock 1941,
   Soroka et al. 2009, Kellermann 2016, Martin 2011, Russo 2011 (17(3) 290-301 confirmed), Searing 1985, Searing 1994,
   Norton 1994 (705-720 confirmed), André et al. 2015, Fernandes et al. 2018, Zittel et al. 2019 (title, authors, DOI; vol/pages
   not reachable). Two content fixes: Butler's introduction quoted via Upton (1991) was to the FIRST edition of Cook & Ramsden
   (1973), not the 1997 one cited; now "its first edition". Pollock (1941) was described as treating by-elections "as a guide to
   the electoral system's working", which I could not confirm from the abstract; now neutral ("surveyed the by-elections
   between the wars").
4. Paper form. Abstract 230 words; sections numbered; appendix Table A (monthly estimates) was never referenced: now referenced
   in 5.1. Placebo table overflowed the margin by 19 pt: narrowed. AI statement, author, affiliation, data availability line
   correct. Cover note: Parliamentary Affairs limit now confirmed from OUP general instructions (8,000 words, at most 5 figures
   and tables; fee only for open access); the paper (about 8,550 words, 7 figures, 8 tables) would need cutting for it.
   British Politics 9,000 words not re-confirmed (Springer page blocked). LSQ and JLS limits still unchecked.
5. House rules. No dashes in blog text; no DSIT/DCMS; no month-level dates of making; collage light, legend, labels off data,
   no crossing leaders; map full-screen button, layers panel, markers at every zoom (no minzoom on point layers), site-nav.js
   before </body>; GIF final frame clean (stills checked). Collage and GIF numbers unchanged, so not regenerated.
6. Methods. Design is sensible: stacked PPML with stack-by-month FEs, matching only on the reference months, 366 clusters.
   Exploratory checks added at review (code/03b_referee_checks.py, results.json "explore", reported as exploratory in 6.2):
   - two-way clustering (by-election and town, since control towns recur across stacks): result 296% [190, 439], year 3 31%
     [-2, 75]; intervals almost unchanged.
   - dropping the 10 by-elections with most treated mentions in months 0 to 12 (PPML weights big counts): result 275%
     [170, 419], year 1 70% [33, 117], year 2 39% [8, 79], year 3 31% [2, 68].
   - 1945 onwards only: same as the planned "without 1911 to 1944" check (not reported separately).
   What a referee would still ask: speaker-level data to separate the new member's own speeches (maiden speech, "in my
   constituency of") from wider attention, since the title says "Parliament"; a check that the 1911 to 1944 null is not a
   Hansard digitisation artefact (e.g. same design on a pre-1945 place-name series with known events); vacancy dates (the
   "vacancy" bin is a fixed -3 to -1, not the actual vacancy); event-study estimators robust to heterogeneous effects are moot
   with clean controls, but a referee may ask for the per-by-election distribution (the map shows it); the uncontested and P3
   pre-period falls (-54%) are unexplained.

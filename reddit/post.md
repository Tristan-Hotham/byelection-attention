**Title:** [OC] When a UK seat holds a by-election, MPs mention the town 4.0x as often around polling day and still 1.9x a year later. Before 1945: no detectable rise.

**Body:**

I followed 366 UK by-elections (1912 to 2022) through Hansard, counting Commons speeches that say "in <town>" for the town named in the seat, month by month, and compared each town with five similar towns that had no by-election.

- Polling month and the two after: 4.0x the mentions of matched towns.
- Months 3 to 12: 1.9x. Second year: 1.6x. Third year: no clear difference.
- When the seat changed hands the first jump was bigger (7.1x vs 3.0x), but a year on the gap was gone.
- 1911 to 1944: no detectable rise. 1980 to 2023: 6.9x around polling.
- Placebo checks (fake dates two years earlier, neighbouring towns) show nothing.

Interactive map with every by-election since 1909 and a timeline: https://maps.tristanhotham.com/byelection-attention/

**Source comment:**

Data: Hansard via the UK Parliament API (Open Parliament Licence v3.0); Wikipedia lists of UK by-elections (CC BY-SA 4.0); Wikidata (CC0). Method: stacked event study, Poisson regression with matched towns and month fixed effects, plan written before the analysis. Tools: Python (pandas, pyfixest, matplotlib), MapLibre. Paper and code: https://github.com/Tristan-Hotham/byelection-attention

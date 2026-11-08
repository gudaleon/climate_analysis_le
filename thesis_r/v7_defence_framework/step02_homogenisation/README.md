# Homogenisation code: London, Fergus and Harrow daily temperature

This code reproduces the homogenised station series used in thesis v6 (October 2026 rebuild). `homogenise.R` writes files that are byte-identical to `LONDON_homogenised_v4.txt`, `FERGUS_homogenised_v4.txt` and `HARROW_homogenised_v4.txt` in `2_Data/1_Observations/c_Homogenised_daily_series`. The RHtests functions are called directly in the same R session.

## Contents

| File | Purpose |
|---|---|
| `homogenise.R` | Main script: StepSize pruning and daily quantile-matching adjustment, two rounds |
| `retest.R` | Pairwise FindU test between stations before and after adjustment (50 to 16) |
| `detect.R` | First-pass automatic detection by triangulation (documentation only) |
| `homog_helpers.R` | Shared functions: reading the series, writing RHtests input files, calling `FindU.wRef`, `StepSize.wRef` and `QMadj.GaussianDLY.wRef` (only plotting is switched off) |
| `config/candidates.csv` | The 22 candidate changepoints given to `homogenise.R`, with type (1 = statistical, 0 = metadata or retained by review) |
| `RHtestsV4_20180301.r` | RHtestsV4, unmodified (SHA-256 `49b17c69e537a006ec2d9b4cd1055640bb670213823de07af948488133477e13`; line 3930 reads `I02<-oout3$Ic`) |
| input | `2_Data/1_Observations/b_Merged_daily_series` (station series before homogenisation, `y m d pr tx tn`, missing = -99.9); with `--from-step01` the output of `step01_merge_stations` is used instead (identical files) |
| output | `3_Code/output/step02_homogenisation/`: homogenised series, `log.txt` and the RHtests work files in `work/` |

## Inputs

- **London.** London International Airport (6144475) to 18 September 2002, then London CS (6144478), with airport values filling isolated missing days.
- **Harrow.** Harrow CDA (6133360) to December 1991, then the Harrow automatic station (613CC60) to August 2000, then Harrow CDA AUTO (6133362). April 1992 is filled from 6133360.
- **Fergus.** Fergus Shand Dam (6142400), with one missing rain day (29 September 2012) taken from ECCC.
- On days where tx < tn, both values are set to missing before testing.

## Method

1. **Reference series.** For each station, the reference is the mean of the other two stations. Monthly means require at most 3 missing days.
2. **Pruning.** `StepSize.wRef` tests the candidates on monthly means. A type-1 candidate is removed when its significance is "No", or "?" with a step smaller than 0.2 °C. Candidates are removed one at a time, weakest first, and the test is repeated each time. Type-0 candidates are never removed.
3. **Adjustment.** `QMadj.GaussianDLY.wRef` adjusts the daily series with Mq = 20 and Ny4a = 0.
   - The base segment is the most recent segment if it is at least 10 years long, otherwise the longest segment.
   - 29 February, which RHtests leaves unadjusted, takes the 28 February adjustment.
4. **Two rounds.** Round 1 uses the unadjusted neighbours as reference. Round 2 uses the neighbours adjusted in round 1. Both rounds adjust the raw series, so adjustments are not stacked.
5. **Clipping.** After adjustment, tn is set to tx on days where tn > tx: 51 days at Fergus, none at London or Harrow.
6. **Precipitation** is not adjusted.

## Result (from `log.txt`)

The 22 candidates give 19 retained breaks in round 2.

| Series | Retained breaks (round 2) | Pruned |
|---|---|---|
| London tx | 1954-11, 1989-11 | none |
| London tn | 1952-02, 1961-06 (metadata) | 1965-03 |
| Fergus tx | 1963-04, 1965-12 | none |
| Fergus tn | 1973-07, 1985-02, 1992-06, 1994-04, 2018-12 | none in round 2 (1985-02 pruned in round 1) |
| Harrow tx | 1957-02, 1960-07, 2002-06 | 1969-03, 2010-04 |
| Harrow tn | 1965-03, 1978-11, 2005-05, 2007-12, 2010-04 | none |

**Pairwise retest (`retest.R`).** 50 changepoints between station pairs before adjustment, 16 after.

**18 or 19 breaks.** Fergus tn 1985-02 is the only break that depends on the round. It is "No" (step −0.25 °C) against the unadjusted neighbours in round 1, and "Yes" (step −0.39 °C) against the adjusted neighbours in round 2. A run that applies the final pruning against unadjusted neighbours keeps 18 breaks. This is the difference from Alex's run and still needs a decision.

## How the candidate list was built

`detect.R` runs the automatic first pass on the raw series. FindU against the two-neighbour reference gives candidate dates. A candidate is attributed to the target station when a break within ±18 months is also found against each neighbour separately, and not between the two neighbours.

The final list in `config/candidates.csv` comes from this step, repeated over three iterations with partly adjusted neighbours, plus two additions:
- the metadata break (London tn 1961-06);
- breaks added or re-dated after reviewing the monthly difference series. For example, the 1963 and 1965 tx steps that the first pass attributes to London were reassigned to Fergus.

`detect.R` therefore does not reproduce the final list on its own; `homogenise.R` starts from the reviewed list.

## Running

Requirements: R only; RHtests needs no packages beyond base R. Run from the package root:

```
Rscript 3_Code/step02_homogenisation/homogenise.R   # about 1 minute; writes 3_Code/output/step02_homogenisation/
Rscript 3_Code/step02_homogenisation/retest.R       # after homogenise.R, about 1 minute
Rscript 3_Code/step02_homogenisation/detect.R       # optional, about 1 minute
```

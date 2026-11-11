# ensrank: the unified ensemble-change diagnostic

`ensrank` computes, for each station-and-index case in an ensemble extremes
analysis, a single diagnostic record that carries two coordinates of one
object. The direction coordinate summarises the ensemble's own movement
between a base window and a comparison window. The position coordinate places
the observed change among the model changes, as a rank among the N + 1 values
formed by the N model changes and the observation itself, and as a signed
margin against the models' range. A third coordinate records how stable that
position is when the same cases are extracted in a defensibly different way,
for example from the neighbouring grid cell of a downscaled product.

The joint-reporting rule the package embodies is that direction and position
are reported together, because each approach misleads in a characteristic way
when it is reported alone. An arrow-style summary of direction discards
magnitude, spread and position, so a reader cannot tell whether the
observations sit anywhere near the ensemble's movement, and its usual
significance shading dichotomises a continuous quantity. A bounding-style
classification of position, read alone, converts a rank into a verdict,
although an ensemble that is statistically indistinguishable from the truth
is expected to leave a fraction 2/(N + 1) of cases outside a range built from
N members, so an outside position is what a reliable ensemble routinely
produces. The unified record breaks that chain at its first link: no stage
of the diagnostic converts a continuous position into a verdict, and no
summary is printed without the coordinates that show what the summary
discarded.

The package name is provisional. It names the record's central act, ranking
the observed change within the ensemble, and it is confined to the project
metadata and the single package directory, so a later choice among the
design note's candidates touches nothing else.

## Installation

The package requires Python 3.10 or later and depends only on numpy, pandas
and matplotlib. From the project folder, install it with pip:

```bash
pip install .
```

The same command works on the wheel in the project's `dist/` folder. To run
the test suite without installing, see the testing section below.

## The input schema

The diagnostic consumes one tidy table of annual index values, as a pandas
DataFrame with one row per annual value and these columns:

| Column | Meaning |
| --- | --- |
| `station` | The station or site the series belongs to. |
| `index` | The extremes index the value belongs to, such as `PRCPTOT`. |
| `year` | The calendar year the annual value describes. |
| `value` | The annual index value; missing values are dropped from each window before any summary is computed. |
| `kind` | `"model"` for an ensemble member's series, `"observed"` for the observational series. |
| `model` | The ensemble member's identifier for model rows; ignored for observed rows. |
| `family` | An optional annotation naming the index's process family, carried through to the record unchanged. |

A frame carries one observational series per station. A case whose station
has no observational series, or whose windows are too empty to form an
observed change, yields a direction-only record whose position fields are
empty, which is the form the diagnostic takes for future contrasts where no
observation exists to be ranked.

Climpact-style pipelines store annual values as one wide table per series,
with years down the rows and one index per column. The readers in
`ensrank.io` convert such tables to the tidy schema, either one file at a
time (`read_annual_csv`) or as a directory of files named in the form the Wu
thesis packages carry, `{Station}_{Source}_annual.csv`
(`read_annual_directory`). A directory of that form usually holds several
observational variants side by side, so the directory reader asks the caller
to name the intended variant, for example the authors' own observed indices
or an independently homogenised layer, rather than choosing one silently.

## Quickstart: the Wu thesis worked example

The example in `examples/quickstart_wu.py` runs the package end to end on
the Wu thesis programme's own annual index tables and reproduces the unified
table the programme verified, together with its glyph figure set. It reads
the thesis-cell tables with the authors' observed series, computes the
record for the Historical (1950–1986) to Present (1987–2023) contrast, and
runs the four perturbation branches the programme executed, namely the
independent homogenisation layer and each station's one-step grid-cell
perturbation, so the table's stability field is computed rather than copied.
The thesis's index list and process-family assignment are analysis
configuration, so the example reads them from the programme's prototype
table and supplies them as the diagnostic's family mapping and index
selection.

```bash
python examples/quickstart_wu.py quickstart_output
```

The run prints the reporting summary and writes
`unified_cases_ensrank.csv` and the three glyph figures, in PNG and PDF,
into the output folder. Its headline numbers are the programme's published
ones: of the 132 cases, 115 fall within the models' range and 17 outside it,
an observed outside fraction of 0.129 set against the 0.182 that a reliable
ten-model ensemble is expected to leave outside by construction, and four
cases in which the two ensemble summaries disagree in sign.

The same computation on any other dataset is a few lines:

```python
import ensrank

frame = ensrank.read_annual_directory("annual_tables", observed_source="OBS_AUTHORS_v4")
record = ensrank.diagnose(frame, base=(1950, 1986), window=(1987, 2023))
print(ensrank.summary_text(record))
ensrank.plot_group_figures(record, "figures")
```

## The outputs and their meanings

`diagnose` returns one row per station-and-index case with these fields:

| Field | Meaning |
| --- | --- |
| `station`, `index`, `process_family` | The case, with the family annotation carried from the input. |
| `n_models` | The number of models with a computable change for the case. |
| `model_changes` | The per-model changes themselves, one per model. Changes are computed inside each series first, as the difference between its median annual value in the comparison window and in the base window. |
| `median_model_change`, `arrow_median_sign` | The median of the model changes and its sign, drawn as an up arrow, a down arrow or a flat dash at exactly zero. |
| `pooled_ensemble_change`, `arrow_pooled_sign` | The pooled ensemble change, computed as its own named statistic on the annual values of all models pooled together, and its sign. It is never used as a substitute for the per-model changes, because a pooled summary can carry the opposite sign to the median of the changes, as the Wu material shows in four cases. |
| `pooled_wilcoxon_p` | The Wilcoxon rank-sum p-value of the pooled comparison, in the R-style normal approximation with tie and continuity corrections. |
| `model_agreement_count` | The number of model changes whose sign agrees with the sign of the median model change, or the number exactly zero when the median is zero. |
| `sign_disagreement` | True when the pooled change and the median of the model changes carry different signs. |
| `obs_change` | The observed series' change, computed exactly as each model's change is computed. |
| `model_range_lo`, `model_range_hi` | The smallest and largest model changes. |
| `obs_rank` | The observed change's rank among the N + 1 values, as a midrank, so a case whose observed change ties with model changes carries a half-integer rank. The observed change sits outside the models' range exactly when this rank is 1 or N + 1 and no tie shares the extreme position. |
| `signed_margin` | The distance from the observed change to the nearest edge of the models' range, divided by the range's width; positive inside the range, negative outside, and zero on an edge or when the range has no width. |
| `bounding_class_613` | The within-range, magnitude-offset and directional-reversal classification of the 6.13 lineage, in which a case outside the range is a directional reversal when the observed sign opposes the sign of the median model change. |
| `bounding_class_v7` | The Bounded, Unbounded and Sign Reversal classification of the v7 lineage, in which a case outside the range is a Sign Reversal only when the whole model range carries the opposite sign to the observed change. |
| `expected_outside_fraction` | The fraction 2/(N + 1) of cases a reliable ensemble of this size is expected to leave outside its range by construction. |

The perturbation module (`run_perturbation`, `compare_records`) recomputes
the record on an alternative frame and reports, per case, which tracked
outputs changed, whether each classification changed, and how far the signed
margin moved, with a stability sentence that is empty for a case nothing
moved. `stability_field` and `combine_stability` assemble the per-branch
results into the single stability field the glyph figures read, in which a
case is named by the branches under which its classification changed and is
left empty when it survived every branch that was run.

The glyph figures (`plot_group_figures`) draw one grid per index group. The
arrow in each cell gives the direction of the median of the model changes;
the cell's colour gives the signed margin on a diverging scale; a heavy
border marks a case in the stability field; and a corner diamond marks a
sign disagreement. Every channel is defined in each figure's legend in full
sentences, so any one figure can be read on its own.

## The two output rules

Two rules bind every output the reporting functions produce, and they are
encoded in `ensrank.report` rather than left to the user. First, no
reporting output describes an envelope classification with verdict language:
a position outside the models' range is reported as a rank, a margin and a
count, never as a verdict on the ensemble. Second, every tally the reporting
functions produce carries the ensemble size and the expected outside fraction
2/(N + 1) beside the observed count, in the tally table's columns and in the
summary text's sentences alike, because a count of cases outside a range is
uninterpretable without the fraction a reliable ensemble is expected to
leave outside.

## Testing

The suite has two parts. The synthetic tests construct ensembles whose
ranks, margins and classes are known by hand, including tied values, a
zero-spread ensemble, an observed change exactly on a range edge, and a case
where the pooled and median-of-changes signs disagree. The reproduction
tests run the package on the Wu programme's own input frames and reproduce
the programme's verified prototype table field by field, at an absolute
tolerance of 1e-6 for the six-decimal fields, a relative tolerance of 1e-6
for the Wilcoxon p-value, and exact agreement for ranks, counts, signs,
classes and the perturbation field; they are skipped when the programme's
artefacts, which are not part of this distribution, are absent. The one
column of the prototype table they do not reproduce is its `source` column,
which is a provenance string naming the prototype's own artefact files
rather than a quantity the diagnostic computes.

```bash
pip install pytest
python -m pytest tests/
```

## Licence

The licence for this package is to be decided by the authors. No licence
file is included in the project at this stage, and nothing in the project
should be read as granting a licence.

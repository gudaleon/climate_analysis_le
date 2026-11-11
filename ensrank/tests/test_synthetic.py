"""Synthetic known-answer tests for the unified diagnostic.

Every case here is constructed so the correct answer is known by hand before
the package computes anything: ensembles with prescribed per-model changes,
tied values, a zero-spread ensemble, an observed change exactly on a range
edge, and a construction in which the pooled ensemble change and the median
of the model changes carry opposite signs. The Wilcoxon p-values frozen into
this file were cross-checked against an independent implementation of the
same R-style normal approximation.
"""
import math
import pathlib
import re
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ensrank import (
    classify_613, classify_v7, diagnose, midranks, observed_rank,
    run_perturbation, series_changes, signed_margin,
    summary_text, tally, wilcoxon_rank_sum,
)
from ensrank.plotting import plot_group_figures

BASE = (2000, 2002)
WINDOW = (2003, 2005)


def constant_frame(model_changes, obs_change=None, base=BASE, window=WINDOW,
                   station="Test", index="IDX"):
    """A tidy frame whose per-model changes are exactly ``model_changes``.

    Every series sits at zero through the base window and at its change
    through the comparison window, so each series' median-based change is the
    prescribed value.
    """
    rows = []
    for model_i, change in enumerate(model_changes):
        for year in range(base[0], base[1] + 1):
            rows.append((station, index, year, 0.0, "model", f"M{model_i}"))
        for year in range(window[0], window[1] + 1):
            rows.append((station, index, year, float(change), "model", f"M{model_i}"))
    if obs_change is not None:
        for year in range(base[0], base[1] + 1):
            rows.append((station, index, year, 0.0, "observed", None))
        for year in range(window[0], window[1] + 1):
            rows.append((station, index, year, float(obs_change), "observed", None))
    return pd.DataFrame(rows, columns=["station", "index", "year", "value", "kind", "model"])


def one_case(frame, base=BASE, window=WINDOW):
    record = diagnose(frame, base=base, window=window)
    assert len(record) == 1
    return record.iloc[0]


class TestStats(unittest.TestCase):
    def test_midranks_average_ties(self):
        ranks = midranks([10.0, 20.0, 20.0, 40.0])
        self.assertTrue(np.allclose(ranks, [1.0, 2.5, 2.5, 4.0]))

    def test_wilcoxon_known_answer_no_ties(self):
        p = wilcoxon_rank_sum([1, 2, 3], [4, 5, 6])
        self.assertAlmostEqual(p, 0.0808555983700523, places=12)

    def test_wilcoxon_known_answer_with_ties(self):
        p = wilcoxon_rank_sum([1, 2, 2], [2, 3, 4])
        self.assertAlmostEqual(p, 0.16415972847851523, places=12)

    def test_wilcoxon_all_tied_is_nan(self):
        # Every pooled value tied makes the tie-corrected variance zero, and
        # the R-style formulation the programme used returns a missing value.
        self.assertTrue(math.isnan(wilcoxon_rank_sum([5, 5, 5], [5, 5, 5])))

    def test_wilcoxon_empty_sample_is_nan(self):
        self.assertTrue(math.isnan(wilcoxon_rank_sum([], [1, 2])))


class TestCoreDiagnostic(unittest.TestCase):
    def test_basic_case_known_answers(self):
        changes = [-10, -6, -2, 0, 2, 4, 6, 8, 10, 12]
        row = one_case(constant_frame(changes, obs_change=3.0))
        self.assertEqual(row["n_models"], 10)
        self.assertAlmostEqual(row["obs_change"], 3.0)
        self.assertAlmostEqual(row["model_range_lo"], -10.0)
        self.assertAlmostEqual(row["model_range_hi"], 12.0)
        self.assertAlmostEqual(row["signed_margin"], 9.0 / 22.0)
        self.assertAlmostEqual(row["obs_rank"], 6.0)
        self.assertAlmostEqual(row["median_model_change"], 3.0)
        # Pooled window values are the changes repeated three times each, so
        # the pooled median is the mean of the 15th and 16th of 30 values.
        self.assertAlmostEqual(row["pooled_ensemble_change"], 3.0)
        self.assertEqual(row["model_agreement_count"], 6)
        self.assertEqual(row["arrow_median_sign"], "↑")
        self.assertEqual(row["arrow_pooled_sign"], "↑")
        self.assertFalse(row["sign_disagreement"])
        self.assertEqual(row["bounding_class_613"], "within range")
        self.assertEqual(row["bounding_class_v7"], "Bounded")
        self.assertAlmostEqual(row["expected_outside_fraction"], 2.0 / 11.0)

    def test_tied_observed_change_takes_midrank(self):
        row = one_case(constant_frame([0, 0, 5, 5, 5, 5, 5, 5, 5, 5], obs_change=0.0))
        self.assertAlmostEqual(row["obs_rank"], 2.0)
        self.assertAlmostEqual(row["signed_margin"], 0.0)
        self.assertEqual(row["bounding_class_613"], "within range")

    def test_zero_spread_ensemble(self):
        inside = one_case(constant_frame([3.0] * 10, obs_change=3.0))
        self.assertAlmostEqual(inside["signed_margin"], 0.0)
        self.assertAlmostEqual(inside["obs_rank"], 6.0)
        self.assertEqual(inside["bounding_class_613"], "within range")
        outside = one_case(constant_frame([3.0] * 10, obs_change=5.0))
        self.assertAlmostEqual(outside["obs_rank"], 11.0)
        # A range with no width gives a margin of zero by the stated rule,
        # even though the case sits outside the range; the rank carries the
        # position unambiguously in such a case.
        self.assertAlmostEqual(outside["signed_margin"], 0.0)
        self.assertEqual(outside["bounding_class_613"], "magnitude offset")
        self.assertEqual(outside["bounding_class_v7"], "Unbounded")

    def test_observed_change_exactly_on_range_edge(self):
        changes = [-5, -3, -1, 0, 1, 2, 3, 4, 5, 6]
        row = one_case(constant_frame(changes, obs_change=6.0))
        self.assertAlmostEqual(row["signed_margin"], 0.0)
        # The observed change ties with the largest model change, so the two
        # share ranks 10 and 11 and the midrank is 10.5, inside the range.
        self.assertAlmostEqual(row["obs_rank"], 10.5)
        self.assertEqual(row["bounding_class_613"], "within range")
        self.assertEqual(row["bounding_class_v7"], "Bounded")

    def test_sign_reversal_under_both_schemes(self):
        row = one_case(constant_frame([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], obs_change=-2.0))
        self.assertEqual(row["bounding_class_613"], "directional reversal")
        self.assertEqual(row["bounding_class_v7"], "Sign Reversal")
        self.assertAlmostEqual(row["obs_rank"], 1.0)

    def test_reversal_613_but_unbounded_v7_when_range_straddles_zero(self):
        # The model range straddles zero and the median model change is
        # positive, so the 6.13 scheme, which reads the observed sign against
        # the ensemble median, calls the case a directional reversal, while
        # the v7 scheme, which requires the whole range to carry one sign,
        # calls it Unbounded.
        changes = [-8, -1, 1, 2, 3, 4, 5, 6, 7, 9]
        row = one_case(constant_frame(changes, obs_change=-9.0))
        self.assertEqual(row["bounding_class_613"], "directional reversal")
        self.assertEqual(row["bounding_class_v7"], "Unbounded")

    def test_magnitude_offset(self):
        row = one_case(constant_frame([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], obs_change=20.0))
        self.assertEqual(row["bounding_class_613"], "magnitude offset")
        self.assertEqual(row["bounding_class_v7"], "Unbounded")
        self.assertAlmostEqual(row["obs_rank"], 11.0)

    def test_classifiers_and_helpers_directly(self):
        self.assertEqual(classify_613(-2.0, 1.0, 10.0, 5.5), "directional reversal")
        self.assertEqual(classify_v7(-2.0, 1.0, 10.0), "Sign Reversal")
        self.assertEqual(classify_v7(-9.0, -8.0, 9.0), "Unbounded")
        self.assertAlmostEqual(signed_margin(3.0, -10.0, 12.0), 9.0 / 22.0)
        self.assertAlmostEqual(observed_rank(0.0, [0, 0, 5, 5]), 2.0)

    def test_changes_are_per_series_medians(self):
        # A skewed series proves the change is the difference of the series'
        # own window medians, not of means and not of pooled summaries.
        rows = []
        for year, value in zip(range(2000, 2003), [1.0, 2.0, 100.0]):
            rows.append(("S", "IDX", year, value, "model", "M0"))
        for year, value in zip(range(2003, 2006), [3.0, 4.0, 200.0]):
            rows.append(("S", "IDX", year, value, "model", "M0"))
        frame = pd.DataFrame(rows, columns=["station", "index", "year", "value", "kind", "model"])
        changes = series_changes(frame, base=BASE, window=WINDOW)
        self.assertAlmostEqual(changes.iloc[0]["change"], 4.0 - 2.0)

    def test_pooled_and_median_signs_can_disagree(self):
        # Six models change by -1 on two valid window years each and four
        # models change by +1 on ten valid window years each. The median of
        # the model changes is -1, while the pooled window sample is
        # dominated by the positive models' many years, so the pooled change
        # is +1 and the record must flag the disagreement.
        base, window = (2000, 2009), (2010, 2019)
        rows = []
        for i in range(10):
            model = f"M{i}"
            for year in range(base[0], base[1] + 1):
                rows.append(("S", "IDX", year, 0.0, "model", model))
            if i < 6:
                for year in range(window[0], window[0] + 2):
                    rows.append(("S", "IDX", year, -1.0, "model", model))
                for year in range(window[0] + 2, window[1] + 1):
                    rows.append(("S", "IDX", year, np.nan, "model", model))
            else:
                for year in range(window[0], window[1] + 1):
                    rows.append(("S", "IDX", year, 1.0, "model", model))
        for year in range(base[0], base[1] + 1):
            rows.append(("S", "IDX", year, 0.0, "observed", None))
        for year in range(window[0], window[1] + 1):
            rows.append(("S", "IDX", year, 0.0, "observed", None))
        frame = pd.DataFrame(rows, columns=["station", "index", "year", "value", "kind", "model"])
        row = one_case(frame, base=base, window=window)
        self.assertAlmostEqual(row["median_model_change"], -1.0)
        self.assertAlmostEqual(row["pooled_ensemble_change"], 1.0)
        self.assertTrue(row["sign_disagreement"])
        self.assertEqual(row["arrow_median_sign"], "↓")
        self.assertEqual(row["arrow_pooled_sign"], "↑")

    def test_direction_only_record_without_observations(self):
        row = one_case(constant_frame([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], obs_change=None))
        self.assertTrue(math.isnan(row["obs_change"]))
        self.assertIsNone(row["bounding_class_613"])
        self.assertTrue(math.isnan(row["obs_rank"]))
        self.assertAlmostEqual(row["median_model_change"], 5.5)


class TestPerturbationModule(unittest.TestCase):
    def _frames(self):
        base_changes = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        base_frame = constant_frame(base_changes, obs_change=5.0)
        # On the alternative branch every model change is negative, so the
        # observed change of +5 moves from inside the range to a sign
        # reversal under both schemes.
        alt_frame = constant_frame([-10, -9, -8, -7, -6, -5, -4, -3, -2, -1], obs_change=5.0)
        # A second, untouched case rides along in both frames.
        extra = constant_frame([1, 1, 1, 1, 1, 1, 1, 1, 1, 1], obs_change=1.0, index="STABLE")
        base_frame = pd.concat([base_frame, extra], ignore_index=True)
        alt_frame = pd.concat([alt_frame, extra], ignore_index=True)
        return base_frame, alt_frame

    def test_perturbation_reports_exactly_the_moved_case(self):
        base_frame, alt_frame = self._frames()
        _, _, comparison = run_perturbation(base_frame, alt_frame, base=BASE, window=WINDOW)
        comparison = comparison.set_index("index")
        moved = comparison.loc["IDX"]
        self.assertTrue(moved["classification_flip_613"])
        self.assertTrue(moved["classification_flip_v7"])
        self.assertIn("bounding_class_613", moved["changed_fields"])
        self.assertNotEqual(moved["stability"], "")
        self.assertAlmostEqual(moved["margin_change"], -10.0 / 9.0)
        stable = comparison.loc["STABLE"]
        self.assertEqual(stable["n_changed"], 0)
        self.assertEqual(stable["stability"], "")


class TestReportingRules(unittest.TestCase):
    def setUp(self):
        changes = [-10, -6, -2, 0, 2, 4, 6, 8, 10, 12]
        frames = [constant_frame(changes, obs_change=3.0, index="IN"),
                  constant_frame(changes, obs_change=-30.0, index="OUT")]
        self.record = diagnose(pd.concat(frames, ignore_index=True), base=BASE, window=WINDOW)

    def test_tally_carries_ensemble_size_and_expected_fraction(self):
        for scheme in ("bounding_class_613", "bounding_class_v7"):
            result = tally(self.record, scheme=scheme)
            self.assertTrue((result["ensemble_size"] == 10).all())
            self.assertTrue(np.allclose(result["expected_outside_fraction"], 2.0 / 11.0))
            self.assertTrue((result["observed_outside_cases"] == 1).all())

    def test_summary_text_carries_the_benchmark_beside_the_count(self):
        text = summary_text(self.record)
        self.assertIn("ensemble of 10 models", text)
        self.assertIn("2/(10+1) = 0.182", text)
        self.assertIn("observed outside fraction here is 0.500", text)

    def test_no_verdict_language_in_reporting_outputs(self):
        text = summary_text(self.record)
        table_text = tally(self.record).to_string() + tally(self.record, scheme="bounding_class_v7").to_string()
        verdict = re.compile(r"\b(pass|passed|passes|passing|fail|failed|fails|failure|failures)\b", re.IGNORECASE)
        self.assertIsNone(verdict.search(text))
        self.assertIsNone(verdict.search(table_text))


class TestPlotting(unittest.TestCase):
    def test_group_figures_are_written(self):
        indices = ["PRCPTOT", "TXx", "TX90p"]
        frames = [constant_frame([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], obs_change=5.0, index=ix)
                  for ix in indices]
        record = diagnose(pd.concat(frames, ignore_index=True), base=BASE, window=WINDOW)
        record["perturbation_flip"] = ""
        with tempfile.TemporaryDirectory() as tmp:
            written = plot_group_figures(record, tmp)
            self.assertEqual(len(written), 6)
            for path in written:
                self.assertTrue(path.exists() and path.stat().st_size > 1000)


if __name__ == "__main__":
    unittest.main()

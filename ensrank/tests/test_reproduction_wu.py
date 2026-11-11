"""End-to-end reproduction of the prototype table on the Wu programme's data.

The test runs the package on the audit's own annual index tables (the Claude
route's ``out/idx`` layer, authors' v4 observed series, values rounded to six
decimals on reading exactly as the audit's layer rounded them) and compares
the resulting record against the prototype's ``unified_cases.csv`` field by
field. The stated tolerances are an absolute 1e-6 for the fields the
prototype table itself rounds to six decimals, a relative 1e-6 for the pooled
Wilcoxon p-value, and exact agreement for ranks, counts, signs, classes and
the perturbation field.

Two columns of the prototype table are inputs or provenance rather than
diagnostic outputs, and are treated accordingly. The process family is
analysis configuration, so it is supplied to the diagnostic as the family
mapping and only checked to be carried through. The prototype's ``source``
column is not reproduced: it is a provenance string naming the prototype's
own artefact files, not a quantity the diagnostic computes, and the package
record carries no equivalent.

The perturbation field is reproduced in full. Four branches are run through
the package's perturbation module: the audit's independent homogenisation
layer in place of the authors' observed series, and each station's one-step
grid-cell perturbation from its addendum's annual tables. The assembled field
is compared against the prototype's for all 132 cases.

The test is skipped when the programme's artefacts are not on disk, as they
are not part of the package distribution.
"""
import pathlib
import sys
import unittest

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from ensrank import (
    combine_stability, diagnose, read_annual_directory, run_perturbation, stability_field,
)

PACKAGE_DIR = pathlib.Path(__file__).resolve().parents[1]
ROOT = PACKAGE_DIR.parents[1]  # ~/workspace/jeremy_wu_redteam
WU = ROOT / "executor_runs" / "wu_claude"
PROTOTYPE_TABLE = PACKAGE_DIR.parent / "unified_cases.csv"
ARTEFACTS_PRESENT = (WU / "out" / "idx").is_dir() and PROTOTYPE_TABLE.exists()

ADDENDA = {"Fergus": ("out_addA", "Addendum A"), "Harrow": ("out_addB", "Addendum B"),
           "London": ("out_addC", "Addendum C")}
ABS_TOL = 1e-6
P_REL_TOL = 1e-6


@unittest.skipUnless(ARTEFACTS_PRESENT, "the Wu programme's artefacts are not on disk")
class TestWuReproduction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prototype = pd.read_csv(PROTOTYPE_TABLE)
        cls.indices = sorted(cls.prototype["index"].unique())
        family = {(r.station, r.index): r.process_family for r in cls.prototype.itertuples()}
        cls.family_map = {index: fam for (_, index), fam in family.items()}

        def load(directory, observed):
            frame = read_annual_directory(directory, observed_source=observed, round_ndigits=6)
            return frame[frame["index"].isin(cls.indices)]

        cls.base_frame = load(WU / "out" / "idx", "OBS_AUTHORS_v4")
        cls.record = diagnose(cls.base_frame, family_map=cls.family_map).set_index(["station", "index"])

        branches = []
        _, _, comparison_h1 = run_perturbation(
            cls.base_frame, load(WU / "out" / "idx", "OBS_H1_reviewed"), family_map=cls.family_map)
        cls.h1_field = stability_field(comparison_h1, "H1 homogenisation layer")
        cls.grid_fields = {}
        for station, (folder, addendum) in ADDENDA.items():
            alt_full = load(WU / folder / "idx", "OBS_AUTHORS_v4")
            alt_frame = pd.concat(
                [cls.base_frame[cls.base_frame["station"] != station],
                 alt_full[alt_full["station"] == station]], ignore_index=True)
            _, _, comparison = run_perturbation(cls.base_frame, alt_frame, family_map=cls.family_map)
            cls.grid_fields[station] = stability_field(
                comparison, f"{station} grid-cell perturbation ({addendum})")

    def test_record_covers_the_132_cases(self):
        self.assertEqual(len(self.record), 132)

    def test_scalar_fields_reproduce(self):
        numeric = ["obs_change", "model_range_lo", "model_range_hi", "signed_margin",
                   "median_model_change", "pooled_ensemble_change", "model_agreement_count"]
        for row in self.prototype.itertuples():
            got = self.record.loc[(row.station, row.index)]
            for field in numeric:
                self.assertAlmostEqual(float(got[field]), float(getattr(row, field)), delta=ABS_TOL,
                                       msg=f"{row.station} {row.index} {field}")
            self.assertAlmostEqual(float(got["obs_rank"]), float(row.obs_rank_among_11), delta=1e-9,
                                   msg=f"{row.station} {row.index} rank")
            p_expected = float(row.pooled_wilcoxon_p)
            self.assertAlmostEqual(float(got["pooled_wilcoxon_p"]), p_expected,
                                   delta=P_REL_TOL * max(1.0, abs(p_expected)),
                                   msg=f"{row.station} {row.index} wilcoxon p")

    def test_symbolic_fields_reproduce(self):
        for row in self.prototype.itertuples():
            got = self.record.loc[(row.station, row.index)]
            self.assertEqual(got["bounding_class_613"], row.bounding_class_613)
            self.assertEqual(got["bounding_class_v7"], row.bounding_class_v7)
            self.assertEqual(got["arrow_median_sign"], row.arrow_median_sign)
            self.assertEqual(got["arrow_pooled_sign"], row.arrow_pooled_sign)
            self.assertEqual(bool(got["sign_disagreement"]), bool(row.sign_disagreement))
            self.assertEqual(got["process_family"], row.process_family)

    def test_headline_tallies_reproduce(self):
        record = self.record.reset_index()
        self.assertEqual(int((record["bounding_class_613"] == "within range").sum()), 115)
        self.assertEqual(int((record["bounding_class_v7"] == "Bounded").sum()), 115)
        self.assertEqual(int((record["signed_margin"] < 0).sum()), 17)

    def test_perturbation_field_reproduces(self):
        combined = combine_stability([self.grid_fields["Fergus"], self.grid_fields["Harrow"],
                                      self.grid_fields["London"], self.h1_field])
        assembled = [combined.loc[(row.station, row.index)] for row in self.prototype.itertuples()]
        expected = self.prototype["perturbation_flip"].fillna("")
        self.assertEqual(assembled, list(expected))
        self.assertEqual(sum(1 for value in assembled if value), 9)


if __name__ == "__main__":
    unittest.main()

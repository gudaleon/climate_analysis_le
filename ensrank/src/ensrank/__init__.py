"""ensrank: the unified ensemble-change diagnostic.

For each station-and-index case, the diagnostic reports the direction of an
ensemble's movement together with the position of the observed change within
the ensemble's spread, the position expressed as a rank among the N + 1
values formed by the model changes and the observation, and as a signed
margin against the models' range. The joint-reporting rule the package
embodies is that direction and position are reported together, because each
misleads in a characteristic way when it is reported alone.
"""
from .diagnostic import (
    classify_613, classify_v7, diagnose, observed_rank, series_changes, signed_margin,
)
from .io import annual_table_to_tidy, read_annual_csv, read_annual_directory
from .perturb import combine_stability, compare_records, run_perturbation, stability_field
from .plotting import default_groups, plot_group_figures, plot_glyph_grid
from .report import rank_distribution, summary_text, tally
from .schema import validate_tidy
from .stats import midranks, wilcoxon_rank_sum

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "validate_tidy",
    "annual_table_to_tidy", "read_annual_csv", "read_annual_directory",
    "series_changes", "diagnose", "classify_613", "classify_v7", "signed_margin", "observed_rank",
    "midranks", "wilcoxon_rank_sum",
    "compare_records", "run_perturbation", "stability_field", "combine_stability",
    "tally", "rank_distribution", "summary_text",
    "default_groups", "plot_glyph_grid", "plot_group_figures",
]

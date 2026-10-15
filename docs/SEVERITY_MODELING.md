# Positive claim severity and large losses

The target is each individual strictly positive linked claim payment. All claims from a policy inherit the same train/validation/test split. Total policy loss is not mislabeled as individual severity. Zero payments would remain in reconciliation but be excluded from both the positive-frequency count and positive-severity response; the downloaded version contains no zero or negative amounts.

A mean-severity intercept and Gamma log-link GLMs with alpha 0, 0.01, 0.1 and 1 are compared by validation mean Gamma deviance. Positive predictions and positive input checks are mandatory. Final metrics include Gamma deviance, MAE, mean squared error, observed/predicted totals and decile calibration. Large payments are retained in the primary target.

A training-only 99th-percentile payment cap is a sensitivity analysis. Capped-target scoring and full-target scoring answer different questions; neither replaces the uncapped primary evaluation. The app reports the threshold and the change in validation metrics. A low capped-target error is not evidence that real full losses became more predictable.

Gamma and lognormal severity simulation specifications preserve a common conditional mean but use different training-derived dispersion assumptions. These are tail sensitivity constructions, not proof that either distribution identifies very rare losses. Payment-development dates, coverage and inflation adjustments are unavailable. See [RISK_SIMULATION.md](RISK_SIMULATION.md).

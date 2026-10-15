# Methodology and frozen evaluation design

The machine-readable [protocol](../configs/protocol.json) records the choices made before model fitting. The primary population comprises reconcilable policies with complete predictors and valid positive exposure. Reconciliation changes the population and is disclosed, rather than treating unknown payment histories as zero loss.

A deterministic SHA-256 hash of seed 42 and integer policy ID assigns approximately 60% to training, 20% to validation and 20% to test. Every claim inherits its parent policy's assignment. The proportions are expectations of the hash rule; generated split counts report realized sizes. There is no reliable temporal ordering and no invented out-of-time test.

Numeric feature medians, standard deviations and categorical encodings are fitted on training records only. Density uses a fixed log1p transform. Policy ID and outcomes are never predictors. Exposure provides a denominator and weight; it is not an unconstrained risk predictor. No payment or exposure is capped in the primary analysis.

Frequency candidates are an intercept benchmark, unpenalized and regularized Poisson log GLMs and a limited Poisson histogram-gradient-boosting grid. Positive severity candidates are an intercept and Gamma log GLMs with limited regularization. Pure-premium candidates multiply the selected compatible frequency and severity models or fit direct Tweedie log GLMs with powers 1.3, 1.5 and 1.7.

Selection uses validation data only: exposure-weighted Poisson deviance for annual frequency, claim-level Gamma deviance for positive severity, and exposure-weighted Tweedie deviance at **one common evaluation power 1.5** for pure premium. Different fitted Tweedie powers are not compared using their own incomparable scoring scales. Exact ties preserve the earlier simpler candidate. Models are not refitted after selection. Final holdout diagnostics use the frozen fitted estimators.

Bootstrap evaluation is conditional on those estimators. Portfolio simulation adds an assumed process distribution; it does not turn a point prediction into an empirically validated complete loss law. See [STATISTICAL_UNCERTAINTY.md](STATISTICAL_UNCERTAINTY.md) and [RISK_SIMULATION.md](RISK_SIMULATION.md).

The official [scikit-learn actuarial example](https://scikit-learn.org/stable/auto_examples/linear_model/plot_tweedie_regression_insurance_claims.html) motivates the frequency–severity and Tweedie constructions. This project deliberately audits source mismatches and keeps full payments instead of automatically adopting the example's count, exposure and loss clipping.

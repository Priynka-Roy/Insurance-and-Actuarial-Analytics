# Exposure-aware claim frequency

The primary response is the number of observed strictly positive linked payments divided by policy exposure in years. The model predicts an annual rate λ. Expected contract-period count is exposure × λ. This process is compatible with the positive-payment severity target; it is not automatically identical to all declared source events.

Fitting `PoissonRegressor` to count/exposure with `sample_weight=exposure` gives the same unpenalized coefficient objective, up to a response-dependent constant and normalization, as a count Poisson log GLM with fixed log(exposure) offset. Tests verify the exposure arithmetic and offset equivalence. Reported mean deviance per exposure uses matching response and exposure weights; ordinary count MAE and aggregate O/E are separate diagnostics.

The intercept benchmark estimates total training positive payments divided by training exposure. Explanatory Poisson GLMs use training-only one-hot and numeric preprocessing; limited alpha values investigate regularization. A Poisson-loss histogram gradient boosting model tests a nonlinear mean without ordinary squared-error fitting. Its iteration count and small tree grid are specified in the protocol, with no test-based early stopping.

Validation selects the lowest exposure-weighted Poisson deviance. Final diagnostics include observed/expected totals, count errors, residuals, risk deciles and group exposure. Pearson dispersion and observed versus modeled zeros test the adequacy of a Poisson variance assumption. A negative-binomial diagnostic is investigated when the predefined dispersion trigger is reached; a flexible mean model does not itself establish Poisson process adequacy.

The published model and numeric comparisons are generated in [results.json](../reports/results.json). Descriptive rates are associations. A rate per exposure-year is different from a proportion of policies with at least one claim.

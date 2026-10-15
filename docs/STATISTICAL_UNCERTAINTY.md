# Statistical uncertainty

The frozen protocol specifies 250 ordinary policy bootstrap resamples with seed 4242 and pointwise 95% percentile intervals. A policy's exposure, payment count and aggregate payment remain together. This preserves claim clustering within policies rather than resampling payments independently.

For frequency, severity and pure premium, descriptive rates are recalculated from the sampled numerators and denominators. Comparisons of fitted-model scores use the same sampled policy indices for each model. A paired score difference can therefore be more informative than comparing two marginal intervals.

These intervals quantify observed-sample/performance uncertainty conditional on fitted models. They do not include full training, hyperparameter-selection or parameter-estimation uncertainty. They also do not capture future inflation, changing coverage, new risk populations, economic drift or catastrophes. Intervals are pointwise; no family-wise multiplicity claim is made.

Monte Carlo process variability is separate: it is variation in simulated future loss conditional on the assumed portfolio and loss law. The Monte Carlo standard error of a mean is simulation standard deviation / sqrt(number of draws), not the predictive standard deviation itself. Tail estimates have finite-simulation error and depend on their distributional assumptions. See [MODEL_VALIDATION.md](MODEL_VALIDATION.md) and [RISK_SIMULATION.md](RISK_SIMULATION.md).

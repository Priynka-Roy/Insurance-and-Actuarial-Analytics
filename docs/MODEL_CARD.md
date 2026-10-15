# Model card

**System:** ActuaryLab AI — Insurance Pricing, Claims Modeling & Portfolio Risk. **Version:** 1.0.0. **Owner:** Priynka Roy. **Intended use:** educational actuarial analysis and professional portfolio demonstration.

**Population and targets:** historical French MTPL policies with reconcilable payment records and complete valid features. Frequency counts strictly positive linked payments per exposure-year; severity targets individual positive payments; premium targets observed payment cost per exposure-year. Original declared events remain a separate source quantity. Strict reconciliation excludes unknown payment histories and changes the estimand.

**Methods:** intercept, Poisson and regularized Poisson GLMs, Poisson histogram gradient boosting, Gamma positive-severity GLMs, compatible two-part pure premium and direct Tweedie GLMs. Training-only transformations and policy-hash split prevent parent-policy leakage. The frozen [protocol](../configs/protocol.json) and [results](../reports/results.json) record exact hyperparameters, validation selection and holdout diagnostics.

**Evaluation:** validation-only selection using proper target-specific deviances; held-out aggregate and group calibration, errors, ranking, residuals and conditional policy-bootstrap intervals. The generated results are authoritative for exact model names and values. No test-driven model reselection is permitted.

**Risk and pricing:** assumed Gamma/lognormal tails and compound count simulation illustrate process and tail sensitivity. Prices use hypothetical user loadings; loss ratios use hypothetical earned premium. No actual insurer profitability, regulatory capital or market quote is estimated.

**Explainability:** GLM coefficients and exponentiated rate relativities describe conditional model associations. Model component decomposition explains frequency × severity. Nonlinear feature diagnostics are predictive explanations, not causal effects or proof of lawful variable use.

**Unsupported uses:** real customer underwriting or claims decisions; legally approved tariffs; current Finnish portfolio estimates; reserving; Solvency II capital; unreviewed individual advice. No insurer sponsorship, employment relationship, endorsement or professional actuarial certification is claimed.

**Important limits:** source missingness, unresolved repeated payments, payment conventions, historical population, no reliable time validation, sparse groups, heavy tails, assumed simulation dependence and finite Monte Carlo/bootstrapping precision. See [LIMITATIONS.md](LIMITATIONS.md), [DATA_CARD.md](DATA_CARD.md) and [RESPONSIBLE_PRICING.md](RESPONSIBLE_PRICING.md). Five-perspective internal review is not independent external validation.

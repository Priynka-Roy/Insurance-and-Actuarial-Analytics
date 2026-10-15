# Limitations

- Historical French records do not establish contemporary Finnish, Nordic or European portfolio representativeness. IRSA-IDA payment conventions and unrecorded coverage differences complicate interpretation.
- Source claim counts and available payment rows are not interchangeable. Reconciliation cannot recover missing claim histories; compatible positive-payment models estimate the observed linked payment process.
- Random policy splits prevent same-policy claim leakage but do not provide out-of-time or external validation. There are no reliable timestamps for a prospective split.
- GLMs impose log-linear conditional means; the Poisson variance assumption may fail. A nonlinear comparator can improve a scoring rule without proving economic value or future superiority.
- Gamma positive severity models describe a conditional mean and an assumed distribution. Large losses are retained, but a sparse historical tail cannot identify reliable catastrophe or regulatory capital risk.
- Policy bootstrap intervals are conditional on the fitted models and observed population. They do not capture complete parameter-selection uncertainty, inflation, economic drift, law changes or new catastrophe dependence.
- Simulated portfolio losses depend on assumed frequency, severity-tail and dependence specifications. They are process-risk scenarios, not observed insurer results or capital requirements.
- Earned commercial premiums, expenses and complete coverage terms are absent. Loaded premiums and loss ratios are hypothetical.
- Aggregate deployment summaries support exploration but cannot replace source-level reanalysis. Fitted model code and protected local source files are needed for full reproduction.
- Internal review from five professional perspectives is not independent external actuarial or regulatory validation.

Policy-ID separation cannot detect repeated customers, vehicles or renewals with different identifiers. Their dependence is not identifiable in the released fields, so policy bootstrap independence and generalization remain assumptions.

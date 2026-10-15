# Internal five-perspective technical review

Reviewed on **16 October 2026**. Source retrieval and licensing review occurred on 15 October 2026.

This is an internal project review using five professional perspectives. It is not independent external actuarial validation, an insurer endorsement or regulatory approval. Check outcomes below describe inspected implementation and generated evidence; final automated/browser execution is recorded in the delivery report.

| Perspective | Review evidence and disposition |
|---|---|
| Applied statistician | Inspected frozen protocol, target-specific proper scoring and validation-only selection; common Tweedie scoring power avoids ranking different powers on incompatible scales. Policy-cluster bootstrap is explicitly conditional and pointwise. Wide cost intervals and model-selection uncertainty limits are disclosed. |
| Insurance pricing actuary | Reviewed exposure-weighted annual-frequency target, compatible positive-payment severity and exposure-scaled expected costs. Missing payment histories are excluded rather than called zero. Uncapped primary losses retained. Holdout pure-premium aggregate underprediction of 15.49% is reported. |
| Quantitative risk analyst | Inspected compound Poisson construction, Gamma sum equivalence, mean-preserving lognormal alternative and mean-one common factor. VaR uses inverse empirical CDF; ES integrates exact upper-tail mass including fractional boundary ties. Analytical expected loss, process SD and Monte Carlo mean SE are distinguished. Tail calibration remains weak, educational evidence. |
| Machine learning engineer | Inspected policy-hash split, claim inheritance, train-only preprocessing, limited frozen grid and no test-based reselection. JSON-only public summaries avoid raw records and unsafe estimator deserialization. Artifact verification rejects changed bytes, path traversal, symlinks, unsupported formats and nonfinite JSON. Routine CI avoids downloads/training. |
| Technical hiring manager | Reviewed clear problem-to-method-to-result narrative, source attribution, actual audit/model values and transparent negative findings. Prepared three truthful CV bullets, LinkedIn copy and an interview explanation. No insurer employment, sponsorship, actuarial certification or invented live deployment is claimed. |

## Findings addressed

- The source narrative and downloaded row counts differ; both are shown and measured counts drive calculations.
- Declared events and linked positive payments differ; the source audit and primary economic estimand are explicitly separated.
- Exact duplicate-looking payments lack a unique claim key; they are retained and flagged rather than silently removed.
- Capped severity scoring can appear favorable because its target changes; full-cost deterioration is shown beside it.
- Model selection and final evaluation are separate; test scores do not retrospectively select a better Gamma candidate.
- Good frequency deviance does not imply a valid Poisson process; dispersion and zero diagnostics plus a development NB2 diagnostic are present.
- Good mean scoring does not validate a Gamma tail; lognormal and common-factor sensitivity are labeled assumptions.
- The simulator's synthetic two-part portfolio is distinct from the complete observed source portfolio.
- Monetary values remain source monetary units (SMU), without an unverified currency conversion.

## Residual limitations

The project cannot establish prospective calibration, recover missing payment histories, measure insurer profits, settle legal rating-factor permission or validate catastrophe/regulatory tails. Full source-level reproduction requires downloading the permitted originals; the public app intentionally distributes aggregate summaries only. Source license metadata and package licensing are reported separately. External actuarial, legal and operational review would be required for a commercial use case.

## Executed verification

On 16 October 2026, 86 tests (including 17 Streamlit AppTests), Ruff and the six-file hash/semantic verifier passed. GitHub Actions passed on Linux/Python 3.12, including startup smoke testing: https://github.com/Priynka-Roy/actuarylab-ai-insurance-pricing-risk/actions/runs/38812962850. Desktop and mobile browser checks confirmed no page overflow, working navigation/pricing/submitted simulation, and no captured JavaScript errors or app exceptions. Controlled file-change/reload activity emitted WebSocket-close warnings without persistent failure. A severity-decile label issue was corrected and covered by a regression test: claim observations are not policy counts or exposure-years. Public deployment remains intentionally separate.

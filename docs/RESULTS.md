# Results

## Computed results

The frozen split contains **401,433 training**, **133,582 validation** and **133,881 test policies**; the corresponding positive claim counts are 15,959 / 5,246 / 5,238. Test results below did not select the models. Lower deviance is better within a target, not across different target rows.

| Task / candidate | Validation deviance | Final holdout deviance | Holdout O/E |
|---|---:|---:|---:|
| Intercept-only Poisson | 0.481422 | 0.480810 | 0.9798 |
| Poisson GLM | 0.461360 | 0.461383 | 0.9825 |
| Poisson HGB leaves=15 (selected) | 0.451102 | 0.449373 | 0.9800 |
| NB2 moment-dispersion GLM | 0.461354 | 0.461406 | 0.9766 |
| Intercept-only Gamma | 1.732553 | 2.066905 | 1.1828 |
| Gamma GLM alpha=0.1 (selected) | 1.697162 | 2.025686 | 1.2039 |
| Two-part frequency × severity (selected) | 78.086138 | 80.463183 | 1.1833 |
| Tweedie p=1.7 alpha=0.1 | 80.164498 | 86.392864 | 1.1811 |

The selected nonlinear frequency model improves the held-out exposure-weighted Poisson score relative to the unpenalized GLM. Its paired conditional bootstrap score difference is **−0.01201**, 95% interval **[−0.01495, −0.00936]**. This supports a conditional-mean comparison within this historical sample, not a claim of future economic superiority. Training Poisson Pearson dispersion is **1.7813**; the negative-binomial diagnostic converged but did not beat the selected nonlinear model.

Selected Gamma severity has holdout O/E **1.2039**. The selected two-part premium predicts **11,389,868.69 SMU** against **13,477,614.76 SMU** observed on the holdout, a **15.49% aggregate underprediction**. This calibration weakness is retained and disclosed. Its exposure concentration index is **0.5140**, ordered by increasing predicted annual risk with cumulative exposure on the horizontal axis. This is not classification AUC.

The best direct Tweedie candidate (fitted p=1.7, alpha=0.1) scores **86.3929** at common evaluation p=1.5, versus **80.4632** for the selected two-part model. The paired direct-minus-two-part difference has a conditional 95% interval **[0.5193, 16.4444]**.

Pointwise policy-bootstrap 95% intervals for observed holdout frequency, mean severity and pure premium are **[0.07170, 0.07573]** payments/exposure-year, **[1,700.02, 4,245.48] SMU/payment**, and **[125.10, 316.69] SMU/exposure-year**. The selected premium O/E interval is **[0.7809, 1.9784]**. These broad cost intervals reflect heavy-tail uncertainty conditional on fitted models. They do not validate future calibration.

Above-training-p99 payments contribute **35.23%** of training paid cost. A capped-refit diagnostic reduces capped-target validation Gamma deviance to **1.0344**, while full-cost deviance worsens to **1.8558** versus **1.6972** for the uncapped primary model. A cleaner capped target does not establish better full-loss prediction.

Exact values and every candidate are in [reports/results.json](../reports/results.json).

## Computed synthetic portfolio risk

These results use 1,000 one-year synthetic policies (125 of each of eight model-derived profiles), 10,000 simulated portfolios and seed 442. They do not reconstruct source policy records. The baseline hypothetical premium is 367,856.79 SMU, with expense share 20%, profit share 5%, risk loading 5% and no fixed cost.

| Assumed scenario | Analytical expected loss (SMU) | VaR95 (SMU) | ES95 (SMU) | Expected loss ratio |
|---|---:|---:|---:|---:|
| Baseline · independent Gamma | 262,754.85 | 512,611.75 | 611,360.58 | 71.43% |
| Frequency +20% | 315,305.82 | 581,382.03 | 681,867.61 | 85.71% |
| Severity +20% | 315,305.82 | 615,134.10 | 733,632.70 | 85.71% |
| Combined +20% frequency and severity | 378,366.98 | 697,658.44 | 818,241.13 | 102.86% |
| Alternative lognormal severity · same means | 262,754.85 | 341,976.14 | 367,810.71 | 71.43% |
| Shared frequency shock · mean preserved | 262,754.85 | 575,154.90 | 702,798.17 | 71.43% |
| Portfolio mix · younger profile weight 50% | 307,195.98 | 583,399.50 | 688,858.81 | 83.51% |

The baseline Monte Carlo mean is **263,178.44 SMU**, versus analytical expectation **262,754.85 SMU**; mean SE is **1,346.05 SMU**, so the difference is **0.315 SE**. Baseline VaR99 and ES99 are **663,142.45** and **761,228.67 SMU**. All tail summaries use 10,000 draws; the saved chart uses only the first 1,000 draws for display.

Gamma and lognormal specifications share conditional mean predictions, yet ES95 differs markedly (**611,360.58** versus **367,810.71 SMU**). The training relative-Pearson Gamma shape is driven by heavy payments, while log-residual SD supplies a different lognormal assumption. This demonstrates assumption sensitivity; it does not show that a lognormal tail is empirically safer or more correct. A mean-one common frequency shock preserves expected loss but increases ES95 to **702,798.17 SMU**.

Combined +20% frequency and +20% severity scale analytical expected cost by 1.44, raising the expected loss ratio from **71.43%** to **102.86%** with premium held fixed. This is a hypothetical adequacy scenario, not actual insurer profitability. With only 100 simulations in the 99% upper tail, tail estimates remain imprecise.

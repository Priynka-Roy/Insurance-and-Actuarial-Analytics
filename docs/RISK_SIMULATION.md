# Aggregate portfolio loss simulation

The bounded engine uses a synthetic portfolio built from fitted model summaries. For cell i, expected claim count is exposure eᵢ × annual frequency λᵢ. Conditional counts are Poisson. Each payment has a conditional mean μᵢ and an assumed Gamma or lognormal tail. Total loss is the sum of simulated payments across all cells.

For the Gamma construction with common shape k, severities have scale μᵢ/k. Conditional on a sampled cell claim count n, the payment sum is Gamma(shape n×k, scale μᵢ/k). This exact compound construction avoids allocating a giant claims-by-policies tensor. The lognormal alternative simulates individual payments in batches with log mean log(μᵢ)−σ²/2, preserving conditional mean μᵢ. Training-derived dispersion values calibrate these assumptions; they do not establish accurate extreme-tail identification.

An optional common lognormal frequency factor has log mean −s²/2 and log SD s, so its expectation is one. It introduces shared frequency variation without changing analytical expected loss. Independent counts are recovered at s=0. Neither the factor distribution nor its stress magnitude is a measured catastrophe dependence model.

Analytical expected loss is Σ eᵢ λᵢ μᵢ after the specified frequency/severity multipliers. The simulator reports empirical mean, median, SD, Monte Carlo mean standard error, mean discrepancy in SE units, analytical process SD and tail measures. Simulations are bounded to 1,000 cells, 100–10,000 replicate portfolios, at most 5,000 total exposure and capped expected/realized claim workloads. Inputs must be finite, nonnegative and within the documented stress domain.

## Tail conventions

Empirical VaRα is the ascending observation at index `ceil(α×n)−1`, the inverse empirical CDF. Expected Shortfall averages exactly the worst `(1−α)×n` mass, using a fractional boundary observation when needed. This handles ties and discrete zero-loss mass consistently; it is different from averaging all losses greater than or equal to VaR when that set has excessive tied mass. Both 95% and 99% measures are reported.

The probability of exceeding hypothetical premium uses strict `loss > premium`. Monte Carlo probabilities, quantiles and ES have finite-sample error. Gamma versus lognormal and common-shock comparisons deliberately show assumption sensitivity. These quantities are educational simulated process risk, not measured company losses, external tail validation, Solvency II capital or a reserving result. Mean predictions and tails can be unreliable under source selection, coverage changes, inflation or missing claim development.

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

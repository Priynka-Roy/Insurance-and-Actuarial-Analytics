# Pure premium and risk ranking

Annual pure premium is expected positive payment cost per exposure-year. With compatible positive-payment definitions, the two-part estimate is λ × μ, where λ is annual frequency and μ is expected amount per positive payment. Expected contract-period cost is exposure × λ × μ. This is an expected cost, not a charged commercial premium.

Direct Tweedie regression fits total observed policy payment/exposure with exposure weights and log link. Candidate powers 1.3, 1.5 and 1.7 lie in the compound Poisson–Gamma range; regularization values are fixed in the protocol. Direct mean regression does not uniquely identify its separate frequency and severity components without additional distributional assumptions.

All premium candidates are ranked on validation exposure-weighted Tweedie deviance at common evaluation power 1.5. Final evaluation reports the same score, annualized MAE, aggregate expected payment, O/E and exposure-aware ranking. A candidate's fitted variance power is distinguished from this common evaluation power.

Concentration and decile plots order policies by predicted annual pure premium, cumulate exposure on the horizontal axis and observed payments on the vertical axis. A signed area statistic must be interpreted using its displayed ordering convention; it is not classification AUC or a guarantee of future profit. Large payments can dominate retrospective ranking.

Synthetic profiles are evaluated within supported feature categories. They are model illustrations; changing a feature in a calculator does not estimate the causal effect of changing a driver's behavior or location.

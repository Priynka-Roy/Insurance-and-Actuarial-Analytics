# ActuaryLab AI — portfolio case study

## Short description

An exposure-aware insurance analytics platform combining Poisson and Gamma GLMs, a nonlinear frequency benchmark, direct Tweedie pure-premium regression, policy-cluster uncertainty and hypothetical aggregate loss simulation. Built from real historical French MTPL data with explicit claim-payment reconciliation, transparent holdout calibration weaknesses and a lightweight eight-section Streamlit interface.

## Three evidence-supported CV bullets

- Built a reproducible Python insurance analytics pipeline from 678,013 historical motor policy records and 26,639 payment rows; audited unmatched claims and excluded 9,117 unresolved payment histories while preserving original data and uncapped large losses.
- Compared exposure-weighted Poisson GLMs, histogram gradient boosting, Gamma severity and direct Tweedie pricing on leakage-safe policy splits; selected models on validation only and reported held-out pure-premium deviance of 80.4632 alongside 15.49% aggregate cost underprediction.
- Implemented 250 policy-cluster bootstrap resamples, exposure-aware calibration/ranking, synthetic premium scenarios and bounded Poisson–Gamma/lognormal portfolio simulations with VaR/Expected Shortfall; packaged aggregate artifacts for an interactive Streamlit app and automated quality checks.

## LinkedIn project description

ActuaryLab AI is an independent educational project exploring insurance pricing, claims modeling and portfolio risk using historical French motor third-party liability data. I reconciled policy and claim-payment sources, modeled annual positive-payment frequency and severity, compared two-part pure premium with direct Tweedie regression, and quantified conditional uncertainty through policy-level bootstrap resampling. The selected two-part model achieved lower held-out common-power Tweedie deviance than the best direct Tweedie candidate, while underpredicting aggregate holdout cost by 15.49%—a limitation reported openly. An eight-section Streamlit app explains model assumptions, synthetic pricing loadings, subgroup diagnostics and simulated aggregate-loss tails. The project is educational; it does not represent employment, insurer sponsorship, regulatory approval or an operational tariff.

## Technical narrative

**Problem.** Raw claim counts confound risk with coverage duration. Payment severity is heavy-tailed, and apparently good average scores can coexist with aggregate underprediction. Source policies that declare claims but have no linked payment history also require an explicit policy, rather than silent zero-filling.

**Data engineering.** I used official versioned OpenML files and recorded source metadata and hashes. Policy-level aggregation followed schema, ID, exposure, payment and claim-count checks. Repeated equal payment rows remained unresolved rather than being arbitrarily deleted. Strict reconciliation produced 668,896 policies and 353,893.168 exposure-years; this cohort differs from the original source population.

**Design.** A frozen seed-42 policy hash split allocated approximately 60/20/20 to training, validation and test. Individual severity rows inherited policy assignments. All preprocessing was fitted on training records. Validation selected frequency, severity and premium independently using proper target-specific scores. All premium models were compared at common Tweedie evaluation power 1.5.

**Evidence.** Poisson histogram gradient boosting with 15 leaves achieved holdout annual-frequency deviance 0.44937 versus 0.46138 for unpenalized Poisson GLM. The selected Gamma model used alpha 0.1. The two-part premium scored 80.4632 versus 86.3929 for the best direct Tweedie candidate. Its aggregate predicted loss was 11.3899 million SMU against 13.4776 million observed; the 15.49% underprediction prevents a claim of production-ready calibration.

**Uncertainty and tail.** Policy resampling preserved clustered payments and paired model comparisons, conditional on fixed estimators. The observed holdout pure-premium interval was 125.10–316.69 SMU/exposure-year. Large payments drove uncertainty: the top training percentile contributed 35.23% of paid cost. Mean models fed Gamma/lognormal tail and common-shock scenarios; assumptions and finite Monte Carlo error remain visible.

**Product.** Aggregate JSON supports eight app sections and guided analytical cases without public raw policy records or startup training. Synthetic profiles keep examples separate from real customer data. Pricing distinguishes pure premium, exposure-scaled cost and hypothetical loaded premium.

**Reflection.** The strongest lesson is that reconciliation, exposure and target definitions are part of the model. A better historical ranking score cannot repair missing payment histories, establish lawful rating factors or validate extreme losses. A next study should obtain a contemporary independent portfolio, dated exposure/claims and coverage information, then conduct temporal validation and fuller training/selection uncertainty analysis.

## Interview explanation

“I started by separating declared claims from available payments. More than nine thousand policies had unresolved payment counts, so I excluded them from the primary economic cohort instead of assuming zero cost. I modeled compatible positive-payment frequency per exposure-year and individual positive severity. Policy-level splitting kept related claim rows together, and validation chose the models before holdout evaluation. Nonlinear frequency improved its proper score, and the two-part model beat the direct Tweedie comparison on common-power deviance. However, aggregate holdout cost was underpredicted by 15.49%, with wide heavy-tail bootstrap intervals. I preserved that result because model quality requires calibration and uncertainty as well as ranking. The simulator demonstrates assumed process risk and tail sensitivity; it is not a validated insurer capital model.”

## Reusable project links

- [GitHub repository](https://github.com/Priynka-Roy/actuarylab-ai-insurance-pricing-risk)
- Local app after starting Streamlit: [localhost:8504](http://localhost:8504)
- Public app deployment is a separate owner step after review; no public URL is asserted.

This document prepares copy only. It does not change the existing portfolio, CV, LinkedIn account or other projects.

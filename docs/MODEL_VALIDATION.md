# Model validation

Training, validation selection and final holdout are separated at policy level. The generated selection record preserves every validation candidate and the frozen winners. Test diagnostics do not change the feature set, reconciliation rules, tuning grid or selected models.

Different targets use different proper scores: Poisson deviance for annual claim frequency with exposure weights, Gamma deviance for positive individual severity, and exposure-weighted Tweedie deviance at fixed common power 1.5 for premium. MAE, MSE, aggregate O/E and decile/group plots add interpretation rather than substituting an incompatible common leaderboard.

Aggregate calibration is observed total / predicted total using compatible counts or costs. Annual rates use exposure denominators. Group diagnostics include policy and claim counts, exposure and sparse flags. A ratio from a small group or from one extreme payment is weak evidence; aggregate calibration does not guarantee subgroup calibration.

Residual diagnostics investigate dispersion and zero counts. Development-only cap sensitivity investigates tail influence without deleting inconvenient holdout losses. Policy bootstrap uses paired resampling for model score differences and preserves within-policy claim clustering. Ranking uses exposure and observed losses, not binary classification terminology.

The final JSON results, reconciliation audit, frozen protocol and source provenance are integrity-checked. Synthetic unit tests, app behavioral tests, startup health checks and browser review address distinct software risks. Passing checks is internal project evidence, not external actuarial validation or regulatory approval.

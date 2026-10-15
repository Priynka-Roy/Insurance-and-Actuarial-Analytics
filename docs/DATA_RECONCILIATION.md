# Data reconciliation

`src/actuarylab/data.py` is the executable policy. Original files remain unchanged. `reports/reconciliation.json` is the generated audit and gives exact measured counts; the app presents these counts with cohort labels.

1. Validate the two exact schemas and nonempty inputs. Identify missing or nonintegral policy identifiers.
2. Exclude every frequency row belonging to a duplicated policy identifier. Arbitrarily choosing the first row could select the wrong exposure or predictors.
3. Retain repeated identical claim-payment rows and count them in the audit. There is no unique claim identifier to distinguish legitimate equal payments from accidental duplicates; silent deduplication would invent a claim history.
4. Aggregate linked, finite, nonnegative claim payments by policy. Keep total linked payment count, strictly positive payment count and payment sum separately. Merge the aggregate once using a validated one-to-one join, rather than multiplying policy exposure through a many-to-many join.
5. Require positive finite exposure, a nonnegative integer source claim count, equality between declared claim count and available linked-payment count, and no invalid payment amount for a primary economic-cohort policy.
6. Policies with unresolved payment histories are excluded from the primary economic cohort. Their unknown payment sum is marked missing, not interpreted as zero. Ordinary zero-claim policies without payment rows remain valid zeros.
7. Preserve zero-valued payments in the source audit. Positive-payment frequency uses `PositiveClaimNb`; positive-payment severity uses only strictly positive individual payments. Their product therefore has a compatible observed-payment definition. Original `ClaimNb` is retained for a separate declared-count description and sensitivity analysis.

No payment clipping, claim-count clipping, exposure capping or currency conversion is performed. Exposures above one are retained and flagged. An unusually large payment is not automatically a data error. Descriptive counts above 100,000 source units identify a review threshold, not an automatic exclusion.

This cohort defines a transparent observed-payment estimand rather than repairing the insurer's missing history. Exclusion can induce selection bias. Development-only alternative handling results are diagnostics, not permission to select a favorable holdout. The generated audit distinguishes the original source population from the primary modeling population; neither denominator should be substituted for the other.

## Measured original-source audit

The downloaded frequency file has **678,013 rows and unique policy IDs**, compared with **677,991** in the upstream narrative. Severity contains **26,639 payment rows**. There are **195 payment rows without a matching frequency ID** and **255 exact repeated payment rows**, retained because their identity cannot be resolved. No missing/negative/zero payment, invalid exposure or duplicate frequency ID is observed in these versions. **1,224 exposures above one year are retained**.

There are **9,116 policies declaring claims but lacking severity records** and **9,117 total claim-count disagreements**. Excluding these unresolved policies gives **668,896 primary economic-cohort policies**, **353,893.168 exposure-years**, **26,443 positive payments**, and **59,908,673.17 SMU** recorded payment. The original frequency file instead reports **36,102 declared claims** over **358,499.445 exposure-years**; the complete severity file totals **60,697,930.68 SMU** including unmatched rows. These are distinct populations, not interchangeable denominators.

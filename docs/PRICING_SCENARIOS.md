# Hypothetical pricing and loss ratios

The calculator starts with fitted annual pure premium in source monetary units (SMU). Policy exposure multiplies the annual expected loss. Profiles are explicitly synthetic and use supported training feature categories; the app does not accept private insurance records or provide offers.

The annual illustrative charged premium is:

`(pure premium × (1 + risk loading) + fixed annual cost) / (1 − expense share − profit share)`.

Risk loading is a multiplicative share of pure premium. Expense and profit are shares of the final charged premium, so they enter the denominator. A fixed annual cost enters the numerator. The expense and profit shares must sum to less than one; all assumptions must be finite and nonnegative. Contract-period charged premium equals annual charged premium × exposure. Fixed costs are annualized in this convention, rather than an additional unscaled per-contract fee.

The expected loss ratio is modeled expected payment / hypothetical earned premium. Scenario loss ratios replace the numerator with modeled stressed expected payment or simulated loss as labeled. Actual commercial premium and expense data are unavailable. A modeled margin therefore does not estimate insurer profitability.

Frequency and severity multipliers alter conditional model assumptions. Their product scales expected loss when portfolio composition and exposure stay fixed. Changing synthetic profile weights changes expected composition loss; it is not evidence about causal driver changes. Stress values are hypothetical rather than estimates of current market inflation or a named insurer's experience.

The computed baseline synthetic portfolio has pure premium 262.75 SMU/exposure-year and hypothetical annual charged premium 367.86 SMU per one-year policy. For 1,000 policies, expected cost is 262,754.85 SMU and assumed premium 367,856.79 SMU. Expected loss ratio is 71.43%; simultaneous +20% frequency and severity increases expected cost to 378,366.98 SMU and the ratio to 102.86% with premium held fixed.

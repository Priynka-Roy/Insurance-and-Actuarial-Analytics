"""Direct annual pure-premium Tweedie GLMs with exposure weights."""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import TweedieRegressor


def pure_premium_target(amount, exposure):
    amount, exposure = np.asarray(amount, float), np.asarray(exposure, float)
    if not np.isfinite(amount).all() or not np.isfinite(exposure).all() or (amount < 0).any() or (exposure <= 0).any():
        raise ValueError('Nonnegative finite costs and positive finite exposures required')
    return amount / exposure


def fit_tweedie_candidates(x, amount, exposure):
    y = pure_premium_target(amount, exposure)
    models = {}
    for power in (1.3, 1.5, 1.7):
        for alpha in (.001, .1):
            model = TweedieRegressor(power=power, alpha=alpha, link='log', max_iter=500, tol=1e-7)
            model.fit(x, y, sample_weight=exposure)
            models[f'Tweedie p={power:g} alpha={alpha:g}'] = model
    return models

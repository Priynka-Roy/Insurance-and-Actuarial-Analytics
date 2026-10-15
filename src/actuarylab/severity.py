"""Positive-payment claim-level Gamma severity, without outcome clipping."""
from __future__ import annotations

import numpy as np
from sklearn.linear_model import GammaRegressor


def validate_severity(y):
    y = np.asarray(y, float)
    if not np.isfinite(y).all() or (y <= 0).any():
        raise ValueError('Gamma severity requires finite strictly positive payments')
    return y


def fit_severity_candidates(x, amount):
    y = validate_severity(amount)
    candidates = {}
    for alpha in (0.0, .01, .1, 1.):
        model = GammaRegressor(alpha=alpha, max_iter=500, tol=1e-7)
        model.fit(x, y)
        name = 'Gamma GLM' if alpha == 0 else f'Gamma GLM alpha={alpha:g}'
        candidates[name] = model
    return candidates


def distribution_shapes(amount, fitted):
    """Training-only moment diagnostics; not validated tail-distribution fits."""
    amount, fitted = validate_severity(amount), validate_severity(fitted)
    relative = amount / fitted
    gamma_shape = 1. / np.mean((relative - 1.)**2)
    lognormal_sigma = np.std(np.log(relative), ddof=1)
    return {'gamma_shape': float(gamma_shape), 'lognormal_sigma': float(lognormal_sigma),
            'method': 'Training-only mean Pearson squared relative residual for Gamma shape; SD log relative payment for lognormal sigma. Both normalized to each cell mean in simulation.',
            'relative_payment_quantiles': {str(q): float(np.quantile(relative, q)) for q in (.5, .9, .95, .99, .999)},
            'warning': 'Distributional assumptions do not establish reliable extreme-tail extrapolation.'}

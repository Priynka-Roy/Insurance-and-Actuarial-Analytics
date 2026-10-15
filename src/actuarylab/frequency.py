"""Exposure-weighted annual-frequency models (equivalent to a log offset)."""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import PoissonRegressor


def frequency_target(count, exposure):
    count, exposure = np.asarray(count, float), np.asarray(exposure, float)
    if not np.isfinite(count).all() or not np.isfinite(exposure).all():
        raise ValueError('Counts and exposure must be finite')
    if (count < 0).any() or (exposure <= 0).any():
        raise ValueError('Nonnegative counts and strictly positive exposure required')
    return count / exposure


def fit_frequency_candidates(x, count, exposure, tree_x=None):
    y = frequency_target(count, exposure)
    candidates = {}
    for alpha in (0.0, .001, .1):
        name = 'Poisson GLM' if alpha == 0 else f'Poisson GLM alpha={alpha:g}'
        model = PoissonRegressor(alpha=alpha, max_iter=500, tol=1e-7)
        model.fit(x, y, sample_weight=exposure)
        candidates[name] = (model, False)
    if tree_x is not None:
        for leaves in (7, 15):
            model = HistGradientBoostingRegressor(loss='poisson', learning_rate=.05,
                max_iter=100, max_leaf_nodes=leaves, min_samples_leaf=100,
                l2_regularization=1., early_stopping=False, random_state=42,
                categorical_features=[False]*4+[True]*5)
            model.fit(tree_x, y, sample_weight=exposure)
            candidates[f'Poisson HGB leaves={leaves}'] = (model, True)
    return candidates


class NegativeBinomialDiagnostic:
    """NB2 mean with fixed training moment dispersion; development diagnostic."""
    def __init__(self, alpha):
        self.alpha = max(float(alpha), 1e-8)

    def fit(self, x, count, exposure, initial):
        from scipy.optimize import minimize
        from scipy.special import gammaln
        x = np.asarray(x, float)
        count, exposure = np.asarray(count, float), np.asarray(exposure, float)
        design = np.column_stack([np.ones(len(x)), x])
        r = 1 / self.alpha
        def objective(beta):
            eta = design @ beta + np.log(exposure)
            mu = np.exp(np.clip(eta, -35, 35))
            ll = gammaln(count+r) - gammaln(r) - gammaln(count+1) + r*np.log(r/(r+mu)) + count*np.log(mu/(r+mu))
            gradient = design.T @ ((mu-count)/(1+self.alpha*mu)) / len(x)
            return -np.mean(ll), gradient
        result = minimize(objective, initial, jac=True, method='L-BFGS-B', options={'maxiter':200,'ftol':1e-10})
        self.intercept_, self.coef_ = result.x[0], result.x[1:]
        self.converged_ = bool(result.success)
        self.optimization_message_ = str(result.message)
        return self

    def predict(self, x):
        return np.exp(np.asarray(x) @ self.coef_ + self.intercept_)

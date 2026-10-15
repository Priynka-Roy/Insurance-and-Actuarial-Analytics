"""Associational GLM relativities and held-development permutation evidence."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import mean_poisson_deviance

from actuarylab.features import FEATURES, design_frame


def glm_relativities(model, transformer):
    rows = []
    for name, coefficient in zip(transformer.get_feature_names_out(), model.coef_, strict=True):
        rows.append({'feature': str(name), 'coefficient': float(coefficient),
            'multiplicative_relativity': float(np.exp(coefficient)),
            'unit': 'one training standard deviation' if name in ['VehAge','DrivAge','BonusMalus','LogDensity'] else 'versus dropped training category'})
    return sorted(rows, key=lambda r: abs(r['coefficient']), reverse=True)


def permutation_importance(frame, model, transformer, max_rows=30000, seed=81):
    """Validation-only fixed-model grouping at original input feature level."""
    subset = frame.sample(min(len(frame), max_rows), random_state=seed)
    x = design_frame(subset)
    target = subset['PositiveClaimNb'].to_numpy() / subset['Exposure'].to_numpy()
    weight = subset['Exposure'].to_numpy()
    baseline = mean_poisson_deviance(target, model.predict(transformer.transform(x)), sample_weight=weight)
    rng = np.random.default_rng(seed)
    result = []
    for feature in FEATURES:
        losses = []
        for _ in range(3):
            shuffled = x.copy()
            shuffled[feature] = rng.permutation(shuffled[feature].to_numpy())
            losses.append(mean_poisson_deviance(target, model.predict(transformer.transform(shuffled)), sample_weight=weight)-baseline)
        result.append({'feature': feature, 'poisson_deviance_increase': float(np.mean(losses)), 'repeat_sd':float(np.std(losses))})
    return sorted(result, key=lambda r:r['poisson_deviance_increase'], reverse=True)

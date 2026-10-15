"""Proper scoring rules, exposure calibration, policy-clustered uncertainty."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_gamma_deviance, mean_poisson_deviance, mean_squared_error, mean_tweedie_deviance


def frequency_metrics(count, exposure, rate, baseline_rate=None):
    count, exposure, rate = map(lambda a: np.asarray(a, float), (count, exposure, rate))
    expected = exposure * rate
    dev = mean_poisson_deviance(count / exposure, rate, sample_weight=exposure)
    result = {'poisson_deviance_per_exposure': float(dev),
        'mean_count_poisson_deviance': float(mean_poisson_deviance(count, expected)),
        'observed_claims': float(count.sum()), 'expected_claims': float(expected.sum()),
        'observed_expected_ratio': float(count.sum() / expected.sum()),
        'count_mae': float(mean_absolute_error(count, expected)),
        'observed_rate': float(count.sum() / exposure.sum()),
        'predicted_rate': float(expected.sum() / exposure.sum())}
    if baseline_rate is not None:
        null_dev = mean_poisson_deviance(count / exposure, np.full(len(count), baseline_rate), sample_weight=exposure)
        result['deviance_explained'] = float(1 - dev / null_dev)
    return result


def severity_metrics(amount, prediction):
    amount, prediction = np.asarray(amount, float), np.asarray(prediction, float)
    return {'gamma_deviance': float(mean_gamma_deviance(amount, prediction)),
        'mae': float(mean_absolute_error(amount, prediction)),
        'mse': float(mean_squared_error(amount, prediction)),
        'observed_mean': float(amount.mean()), 'predicted_mean': float(prediction.mean()),
        'observed_expected_ratio': float(amount.sum() / prediction.sum()), 'claims': len(amount)}


def pure_premium_metrics(amount, exposure, prediction):
    amount, exposure, prediction = map(lambda a: np.asarray(a, float), (amount, exposure, prediction))
    expected = exposure * prediction
    return {'tweedie_deviance_p1_5': float(mean_tweedie_deviance(amount / exposure, prediction, sample_weight=exposure, power=1.5)),
        'observed_loss': float(amount.sum()), 'expected_loss': float(expected.sum()),
        'observed_expected_ratio': float(amount.sum() / expected.sum()),
        'aggregate_relative_error': float(expected.sum() / amount.sum() - 1),
        'annual_pure_premium_mae': float(np.average(np.abs(amount / exposure - prediction), weights=exposure)),
        'policy_cost_mae': float(np.mean(np.abs(amount - expected))),
        'observed_pure_premium': float(amount.sum() / exposure.sum()),
        'predicted_pure_premium': float(expected.sum() / exposure.sum()),
        'exposure_concentration_gini': concentration_gini(amount, exposure, prediction)}


def concentration_gini(amount, exposure, prediction):
    """Exposure-axis concentration index ordered by increasing fitted risk."""
    order = np.argsort(prediction, kind='stable')
    amount, exposure = np.asarray(amount)[order], np.asarray(exposure)[order]
    if amount.sum() <= 0:
        return 0.
    x = np.r_[0., np.cumsum(exposure) / exposure.sum()]
    y = np.r_[0., np.cumsum(amount) / amount.sum()]
    return float(1 - 2 * np.trapezoid(y, x))


def decile_table(actual, exposure, prediction, label='loss'):
    """Approximately equal exposure risk bands, not equal policy-count bands."""
    order = np.argsort(prediction, kind='stable')
    actual, exposure, prediction = map(lambda a: np.asarray(a, float)[order], (actual, exposure, prediction))
    band = np.minimum((10 * (np.cumsum(exposure) - .5 * exposure) / exposure.sum()).astype(int), 9)
    rows = []
    for decile in np.unique(band):
        keep = band == decile
        obs, exp, e = actual[keep].sum(), (prediction[keep] * exposure[keep]).sum(), exposure[keep].sum()
        rows.append({'decile': int(decile + 1), 'policies': int(keep.sum()), 'exposure': float(e),
            f'observed_{label}': float(obs), f'expected_{label}': float(exp),
            'observed_rate': float(obs / e), 'predicted_rate': float(exp / e),
            'observed_expected_ratio': float(obs / exp)})
    return rows


def policy_bootstrap(df, frequency_predictions, premium_predictions, severity_policy_predictions, reps=250, seed=4242, severity_deviance_sums=None):
    """IID policy resampling; all claims within each sampled policy stay together.

    Conditional on fixed models; does not include training/tuning uncertainty.
    No percentile interval should be interpreted as simultaneous coverage.
    """
    rng = np.random.default_rng(seed)
    n = len(df)
    e, c, a = (df[k].to_numpy(float) for k in ['Exposure', 'PositiveClaimNb', 'ClaimAmount'])
    freq_losses = {k: poisson_unit_loss(c / e, v) for k, v in frequency_predictions.items()}
    premium_losses = {k: tweedie_unit_loss(a / e, v, 1.5) for k, v in premium_predictions.items()}
    metrics = {'frequency': [], 'severity': [], 'pure_premium': [], 'frequency_oe': [], 'premium_oe': [], 'severity_oe': [],
        'frequency_deviance': [], 'premium_deviance_p1_5': []}
    if severity_deviance_sums is not None:
        metrics['severity_gamma_deviance'] = []
        severity_deviance_sums = np.asarray(severity_deviance_sums, float)
    paired = {}
    fk, pk = list(freq_losses), list(premium_losses)
    if len(fk) == 2:
        paired['frequency_deviance_difference'] = []
    if len(pk) == 2:
        paired['premium_deviance_difference'] = []
    first_f = np.asarray(next(iter(frequency_predictions.values())))
    first_p = np.asarray(next(iter(premium_predictions.values())))
    severity_policy_predictions = np.asarray(severity_policy_predictions)
    for _ in range(reps):
        ix = rng.integers(n, size=n)
        es, cs, loss = e[ix].sum(), c[ix].sum(), a[ix].sum()
        metrics['frequency'].append(cs / es)
        metrics['severity'].append(loss / cs if cs > 0 else np.nan)
        metrics['pure_premium'].append(loss / es)
        metrics['frequency_oe'].append(cs / np.sum(e[ix] * first_f[ix]))
        metrics['premium_oe'].append(loss / np.sum(e[ix] * first_p[ix]))
        severity_expected = np.sum(severity_policy_predictions[ix])
        metrics['severity_oe'].append(loss / severity_expected if severity_expected > 0 else np.nan)
        metrics['frequency_deviance'].append(np.sum(e[ix] * freq_losses[fk[0]][ix]) / es)
        metrics['premium_deviance_p1_5'].append(np.sum(e[ix] * premium_losses[pk[0]][ix]) / es)
        if severity_deviance_sums is not None:
            metrics['severity_gamma_deviance'].append(np.sum(severity_deviance_sums[ix]) / cs if cs > 0 else np.nan)
        if len(fk) == 2:
            paired['frequency_deviance_difference'].append(np.sum(e[ix] * (freq_losses[fk[0]][ix] - freq_losses[fk[1]][ix])) / es)
        if len(pk) == 2:
            paired['premium_deviance_difference'].append(np.sum(e[ix] * (premium_losses[pk[0]][ix] - premium_losses[pk[1]][ix])) / es)
    def interval(values):
        return {'lower': float(np.nanquantile(values, .025)), 'upper': float(np.nanquantile(values, .975))}
    return {'replicates': reps, 'seed': seed, 'method': 'Ordinary policy-cluster percentile bootstrap, pointwise 95%; fixed fitted models; no training or selection uncertainty.',
        'intervals': {k: interval(v) for k, v in metrics.items()},
        'paired': {k: {**interval(v), 'mean_difference': float(np.mean(v))} for k, v in paired.items()},
        'comparison_order': {'frequency': fk, 'premium': pk},
        'paired_point_estimates': {**({'frequency_deviance_difference':float(np.average(freq_losses[fk[0]]-freq_losses[fk[1]],weights=e))} if len(fk)==2 else {}),
            **({'premium_deviance_difference':float(np.average(premium_losses[pk[0]]-premium_losses[pk[1]],weights=e))} if len(pk)==2 else {})},
        'warning': 'Heavy-tailed claims and one historical holdout can make bootstrap intervals unstable; no prospective or simultaneous coverage guarantee.'}


def poisson_unit_loss(y, mu):
    y, mu = np.asarray(y, float), np.asarray(mu, float)
    out = mu - y
    positive = y > 0
    out[positive] += y[positive] * np.log(y[positive] / mu[positive])
    return 2 * out


def tweedie_unit_loss(y, mu, power=1.5):
    y, mu = np.asarray(y, float), np.asarray(mu, float)
    return 2 * (np.power(y, 2-power) / ((1-power) * (2-power))
        - y * np.power(mu, 1-power) / (1-power) + np.power(mu, 2-power) / (2-power))


def segment_table(df, frequency, severity, premium, feature):
    work = df.copy()
    if feature == 'DrivAge':
        work['_group'] = pd.cut(work[feature], [0,25,40,60,200], labels=['<=25','26-40','41-60','>60']).astype(str)
    elif feature == 'VehAge':
        work['_group'] = pd.cut(work[feature], [-1,2,5,10,200], labels=['0-2','3-5','6-10','>10']).astype(str)
    else:
        work['_group'] = work[feature].astype(str)
    work['_f'], work['_s'], work['_p'] = frequency, severity, premium
    result = []
    for name, group in work.groupby('_group', observed=True):
        e, c, a = group['Exposure'].sum(), group['PositiveClaimNb'].sum(), group['ClaimAmount'].sum()
        fe = (group['Exposure'] * group['_f']).sum()
        pe = (group['Exposure'] * group['_p']).sum()
        result.append({'group': name, 'policies': len(group), 'exposure': float(e), 'claims': int(c),
            'claim_amount': float(a), 'frequency': float(c/e), 'severity': float(a/c) if c else None,
            'pure_premium': float(a/e), 'expected_claims': float(fe), 'expected_loss': float(pe),
            'frequency_oe': float(c/fe), 'premium_oe': float(a/pe),
            'predicted_severity': float((group['_s']*group['PositiveClaimNb']).sum()/c) if c else None,
            'sparse': bool(c < 30 or e < 100)})
    return result

"""Batched conditional Poisson-Gamma/lognormal educational portfolio simulation."""
import math
import numpy as np

MAX_REPLICATES = 10000
MAX_EXPECTED_CLAIM_DRAWS = 5_000_000


def empirical_tail(losses, alpha=0.95):
    values = np.sort(np.asarray(losses, dtype=float))
    if values.ndim != 1 or values.size == 0 or not np.isfinite(values).all() or (values < 0).any():
        raise ValueError('Loss sample must be finite, nonnegative and nonempty.')
    if not 0 < alpha < 1:
        raise ValueError('Tail probability must lie strictly between zero and one.')
    n = len(values)
    var = float(values[max(0, math.ceil(alpha * n) - 1)])
    mass = (1 - alpha) * n
    whole = int(np.floor(mass + 1e-10))
    remainder = max(0.0, mass - whole)
    total = float(values[n - whole:].sum()) if whole else 0.0
    if remainder > 1e-10:
        total += remainder * values[n - whole - 1]
    return {'var': var, 'es': total / mass, 'alpha': alpha}


def simulate_portfolio(frequency, severity, exposure, replicates=5000, seed=42,
                       gamma_shape=1.0, tail='gamma', lognormal_sigma=1.0,
                       frequency_multiplier=1.0, severity_multiplier=1.0,
                       common_sigma=0.0, premium=None):
    f, m, e = [np.atleast_1d(np.asarray(x, dtype=float)) for x in (frequency, severity, exposure)]
    if f.shape != m.shape or f.shape != e.shape or f.ndim != 1 or not 1 <= f.size <= 1000:
        raise ValueError('Frequency, severity and exposure must have matching 1-D shapes, at most 1,000 cells.')
    if any(not np.isfinite(x).all() or (x < 0).any() for x in (f, m, e)):
        raise ValueError('Inputs must be finite and nonnegative.')
    scalars = [gamma_shape, lognormal_sigma, frequency_multiplier, severity_multiplier, common_sigma]
    if any(not np.isfinite(x) for x in scalars):
        raise ValueError('Simulation parameters must be finite.')
    if not isinstance(replicates, (int, np.integer)) or isinstance(replicates, bool) or not 100 <= replicates <= MAX_REPLICATES:
        raise ValueError('Use 100–10,000 simulated portfolios.')
    if not 1e-6 <= gamma_shape <= 1000 or not 0 <= lognormal_sigma <= 5:
        raise ValueError('Invalid severity distribution parameters.')
    if not 0 <= common_sigma <= 1 or not 0 <= frequency_multiplier <= 3 or not 0 <= severity_multiplier <= 3:
        raise ValueError('Scenario multiplier outside bounded educational domain.')
    if tail not in {'gamma', 'lognormal'}:
        raise ValueError('Choose gamma or lognormal severity.')
    if e.sum() > 5000 or np.max(f) > 10 or np.max(m) > 1e8:
        raise ValueError('Portfolio exceeds educational workload/domain bounds.')
    if premium is not None and (not np.isfinite(premium) or premium <= 0):
        raise ValueError('Assumed premium must be positive and finite.')
    rates, means = f * e * frequency_multiplier, m * severity_multiplier
    if rates.sum() * replicates > MAX_EXPECTED_CLAIM_DRAWS:
        raise ValueError('Expected claim workload too large; reduce portfolio size or replicates.')
    expected = float(np.dot(rates, means))
    second = means**2 * (1 + 1 / gamma_shape if tail == 'gamma' else np.exp(lognormal_sigma**2))
    theoretical_sd = float(np.sqrt(np.dot(rates, second) + np.expm1(common_sigma**2) * expected**2))
    rng = np.random.default_rng(seed)
    losses = np.zeros(replicates)
    draw_count = 0
    for start in range(0, replicates, 100):
        size = min(100, replicates - start)
        shock = rng.lognormal(-0.5 * common_sigma**2, common_sigma, size=size)
        counts = rng.poisson(shock[:, None] * rates[None, :])
        draw_count += int(counts.sum())
        if draw_count > MAX_EXPECTED_CLAIM_DRAWS * 2:
            raise ValueError('Realized workload bound exceeded under common shock.')
        if tail == 'gamma':
            amounts = rng.gamma(counts * gamma_shape, means[None, :] / gamma_shape)
            losses[start:start + size] = amounts.sum(axis=1)
        else:
            batch = np.zeros(size)
            for j in range(len(rates)):
                if means[j] == 0:
                    continue
                total = int(counts[:, j].sum())
                if total:
                    draws = rng.lognormal(np.log(means[j]) - 0.5 * lognormal_sigma**2, lognormal_sigma, total)
                    owners = np.repeat(np.arange(size), counts[:, j])
                    batch += np.bincount(owners, weights=draws, minlength=size)
            losses[start:start + size] = batch
    sd = float(losses.std(ddof=1))
    mean = float(losses.mean())
    se = sd / math.sqrt(replicates)
    t95, t99 = empirical_tail(losses, 0.95), empirical_tail(losses, 0.99)
    return {'expected_loss': expected, 'expected_claims': float(rates.sum()), 'mean': mean,
            'median': float(np.median(losses)), 'sd': sd, 'mean_se': se, 'theoretical_sd': theoretical_sd,
            'mean_error_in_se': (mean - expected) / se if se else 0.0,
            'var95': t95['var'], 'es95': t95['es'], 'var99': t99['var'], 'es99': t99['es'],
            'assumed_premium': premium, 'expected_loss_ratio': expected / premium if premium else None,
            'mean_simulated_loss_ratio': mean / premium if premium else None,
            'probability_exceeds_premium': float((losses > premium).mean()) if premium else None,
            'replicates': replicates, 'seed': seed, 'portfolio_exposure': float(e.sum()), 'tail': tail,
            'gamma_shape': gamma_shape, 'lognormal_sigma': lognormal_sigma, 'common_sigma': common_sigma,
            'frequency_multiplier': frequency_multiplier, 'severity_multiplier': severity_multiplier,
            'losses': losses.tolist()}

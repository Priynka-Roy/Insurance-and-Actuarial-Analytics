import numpy as np
import pytest
from actuarylab.pricing import quote
from actuarylab.simulation import empirical_tail, simulate_portfolio


def test_price_loading_algebra_and_exposure():
    q = quote(100, .5, expense=.2, risk=.1, profit=.1, fixed=30)
    assert q['annual_premium'] == pytest.approx(200)
    assert q['policy_premium'] == pytest.approx(100)
    assert q['policy_expected_loss'] == 50
    assert q['expected_loss_ratio'] == pytest.approx(.5)
    assert quote(100, exposure=0)['policy_premium'] == 0


@pytest.mark.parametrize('kwargs', [{'expense':.9,'profit':.1}, {'risk':-1}, {'pure_premium':float('nan')}, {'exposure':-1}])
def test_invalid_pricing(kwargs):
    inputs = {'pure_premium':100, **kwargs}
    with pytest.raises(ValueError):
        quote(**inputs)


def test_discrete_tail_fractional_mass_and_ties():
    assert empirical_tail([0, 10, 20, 30], .625) == {'var':20.,'es':pytest.approx(80/3),'alpha':.625}
    assert empirical_tail([0,0,10,10], .5)['es'] == 10
    assert empirical_tail([0]*10, .99)['es'] == 0


@pytest.mark.parametrize('frequency,severity,exposure', [([0],[100],[1]),([1],[0],[1]),([1],[100],[0])])
@pytest.mark.parametrize('tail', ['gamma','lognormal'])
def test_zero_loss_components(frequency, severity, exposure, tail):
    r = simulate_portfolio(frequency,severity,exposure,replicates=100,tail=tail)
    assert r['mean'] == r['expected_loss'] == r['var95'] == r['es95'] == 0


@pytest.mark.parametrize('tail', ['gamma','lognormal'])
def test_compound_moments_and_fixed_seed(tail):
    r = simulate_portfolio([.5,.2],[100,200],[100,100],replicates=10000,gamma_shape=2,lognormal_sigma=.5,tail=tail)
    assert r['expected_loss'] == 9000
    assert abs(r['mean']-9000) < 4*r['mean_se']
    assert r['sd'] == pytest.approx(r['theoretical_sd'],rel=.05)
    assert r['var99'] <= r['es99']
    assert r['losses'] == simulate_portfolio([.5,.2],[100,200],[100,100],replicates=10000,gamma_shape=2,lognormal_sigma=.5,tail=tail)['losses']


def test_mean_preserving_common_shock_increases_variability():
    base = simulate_portfolio([.2],[100],[1000],replicates=10000,gamma_shape=2)
    shock = simulate_portfolio([.2],[100],[1000],replicates=10000,gamma_shape=2,common_sigma=.5)
    assert base['expected_loss'] == shock['expected_loss']
    assert shock['sd'] > 2*base['sd']
    assert abs(shock['mean']-shock['expected_loss']) < 4*shock['mean_se']


@pytest.mark.parametrize('kwargs', [{'frequency':[-1]}, {'replicates':0}, {'replicates':10001}, {'gamma_shape':0}, {'tail':'normal'}, {'common_sigma':2}, {'frequency_multiplier':4}, {'premium':0}, {'severity':[float('inf')]}, {'frequency':[10], 'exposure':[5000]}])
def test_invalid_simulation(kwargs):
    values = {'frequency':[.1],'severity':[100.],'exposure':[1.], **kwargs}
    with pytest.raises(ValueError):
        simulate_portfolio(**values)


def test_loss_ratio_probability_units():
    r = simulate_portfolio([.1],[100],[100],replicates=1000,premium=2000)
    assert r['expected_loss_ratio'] == .5
    assert r['mean_simulated_loss_ratio'] == r['mean']/2000
    assert 0 <= r['probability_exceeds_premium'] <= 1


def test_empty_or_invalid_tail_sample():
    for sample in [[],[-1],[np.nan]]:
        with pytest.raises(ValueError):
            empirical_tail(sample)

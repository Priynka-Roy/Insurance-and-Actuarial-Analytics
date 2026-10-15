"""Analytically solvable actuarial identities and leakage/cluster safeguards."""
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import mean_poisson_deviance, mean_tweedie_deviance

from actuarylab.evaluation import concentration_gini, frequency_metrics, policy_bootstrap, poisson_unit_loss, pure_premium_metrics, severity_metrics, tweedie_unit_loss
from actuarylab.features import design_frame, policy_split, preprocessor
from actuarylab.frequency import frequency_target
from actuarylab.severity import distribution_shapes, validate_severity
from actuarylab.tweedie import pure_premium_target


def test_split_stable_independent_of_order_and_isolates_claim_clusters():
    ids = pd.Series(np.arange(1, 10001))
    labels = policy_split(ids)
    perm = np.random.default_rng(2).permutation(len(ids))
    assert np.array_equal(labels[perm], policy_split(ids.iloc[perm]))
    claims = pd.Series([1,1,1,2,2,3])
    inherited = policy_split(claims)
    assert inherited[0] == inherited[1] == inherited[2]
    assert set(labels) == {'train','validation','test'}
    assert .57 < np.mean(labels=='train') < .63


@pytest.mark.parametrize('counts,exposure', [([-1],[1]),([1],[0]),([1],[-1]),([np.nan],[1]),([1],[np.inf])])
def test_frequency_rejects_invalid_inputs(counts, exposure):
    with pytest.raises(ValueError):
        frequency_target(counts,exposure)


def test_annual_frequency_weighting_equals_count_offset_deviance():
    count=np.array([0,1,3,0.])
    exposure=np.array([.2,.5,1.,2.])
    rate=np.array([.1,.4,2.,.3])
    annual=mean_poisson_deviance(count/exposure,rate,sample_weight=exposure)
    offset=mean_poisson_deviance(count,exposure*rate)
    assert annual*exposure.sum() == pytest.approx(offset*len(count))
    assert np.array_equal(frequency_target(count,exposure),count/exposure)


@pytest.mark.parametrize('payments', [[0],[-2],[np.nan],[np.inf]])
def test_gamma_requires_positive_finite_individual_payments(payments):
    with pytest.raises(ValueError):
        validate_severity(payments)


def test_no_payment_clipping_and_units():
    amount=np.array([0.,1e8])
    exposure=np.array([.5,2.])
    assert pure_premium_target(amount,exposure)[1] == 5e7
    rate=np.array([.1,.2])
    severity=np.array([1000.,2000.])
    result=pure_premium_metrics(amount,exposure,rate*severity)
    assert result['expected_loss'] == pytest.approx(50+800)
    assert result['observed_pure_premium'] == pytest.approx(1e8/2.5)


def test_unit_losses_equal_proper_scikit_metrics():
    y=np.array([0.,2.,4.])
    mu=np.array([.5,1.,3.])
    w=np.array([1.,2.,3.])
    assert np.average(poisson_unit_loss(y,mu),weights=w) == pytest.approx(mean_poisson_deviance(y,mu,sample_weight=w))
    assert np.average(tweedie_unit_loss(y,mu),weights=w) == pytest.approx(mean_tweedie_deviance(y,mu,sample_weight=w,power=1.5))


def test_policy_bootstrap_keeps_multiple_payments_clustered_and_reproducible():
    df=pd.DataFrame({'Exposure':[1.,1.], 'PositiveClaimNb':[2.,0.], 'ClaimAmount':[400.,0.]})
    kwargs=dict(frequency_predictions={'constant':np.ones(2)},premium_predictions={'constant':np.full(2,200.)},severity_policy_predictions=np.array([400.,0.]),reps=100,seed=5)
    a=policy_bootstrap(df,**kwargs)
    b=policy_bootstrap(df,**kwargs)
    assert a==b
    # Every bootstrap with payments has same within-policy payment/count ratio.
    assert a['intervals']['severity']=={'lower':200.,'upper':200.}
    assert a['intervals']['frequency']['lower']==0.
    assert a['intervals']['frequency']['upper']==2.


def test_calibration_and_count_metrics_have_compatible_denominators():
    f=frequency_metrics([0,1],[.5,.5],[1.,1.])
    assert f['observed_expected_ratio']==1.
    assert f['observed_rate']==1.
    s=severity_metrics([100.,300.],[150.,250.])
    assert s['observed_expected_ratio']==1.
    assert s['observed_mean']==200.


def test_exposure_concentration_index_known_curve():
    assert concentration_gini([0.,100.],[1.,1.],[1.,2.])==pytest.approx(.5)
    assert concentration_gini([100.,0.],[1.,1.],[1.,2.])==pytest.approx(-.5)


def test_preprocessor_uses_only_training_mean_and_categories():
    raw=pd.DataFrame({'VehAge':[1,3], 'DrivAge':[20,40], 'BonusMalus':[50,100], 'Density':[10,100],
        'VehPower':['4','5'],'VehBrand':['B1','B2'],'VehGas':['Diesel','Regular'],'Area':['A','B'],'Region':['R1','R2']})
    train=design_frame(raw)
    encoder=preprocessor().fit(train)
    scaler=encoder.named_transformers_['numeric'][-1]
    assert scaler.mean_[0]==2.
    held=raw.iloc[[0]].copy()
    held['VehAge']=1000.
    held['Region']='NEW'
    with pytest.warns(UserWarning,match='unknown categories'):
        transformed=encoder.transform(design_frame(held))
    assert transformed[0,0]==998.
    assert scaler.mean_[0]==2.


def test_training_residual_shape_uses_positive_finite_inputs():
    shape=distribution_shapes([50.,150.,100.],[100.,100.,100.])
    assert shape['gamma_shape']==pytest.approx(6.)
    assert shape['lognormal_sigma']>0


def test_paired_identical_models_have_zero_difference_and_cluster_gamma_score():
    df=pd.DataFrame({'Exposure':[1.,2.], 'PositiveClaimNb':[2.,1.], 'ClaimAmount':[400.,200.]})
    f=np.array([1.,1.])
    p=np.array([200.,200.])
    result=policy_bootstrap(df, {'A':f,'B':f},{'A':p,'B':p},[400.,200.],reps=30,
        severity_deviance_sums=[4.,2.])
    assert result['paired']['frequency_deviance_difference']['lower']==0.
    assert result['paired']['premium_deviance_difference']['upper']==0.
    assert result['intervals']['severity_gamma_deviance']=={'lower':2.,'upper':2.}

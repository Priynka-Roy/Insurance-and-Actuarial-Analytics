import numpy as np
import pandas as pd
import pytest
from actuarylab.data import reconcile, validate_schema, FREQUENCY_COLUMNS


def frequency(ids=(1, 2, 3), counts=(0, 1, 2), exposures=(1, .5, 1)):
    n = len(ids)
    f = pd.DataFrame({'IDpol': ids, 'ClaimNb': counts, 'Exposure': exposures,
                      'VehPower': [5]*n, 'VehAge': [2]*n, 'DrivAge': [40]*n,
                      'BonusMalus': [50]*n, 'VehBrand': ['B1']*n, 'VehGas': ['Diesel']*n,
                      'Area': ['A']*n, 'Density': [100]*n, 'Region': ['R11']*n})
    return f[FREQUENCY_COLUMNS]


def test_many_claims_aggregate_once_and_preserve_individuals():
    f = frequency()
    c = pd.DataFrame({'IDpol': [2, 3, 3], 'ClaimAmount': [100., 200., 300.]})
    before = c.copy(deep=True)
    p, a = reconcile(f, c)
    assert len(p) == 3
    assert p.loc[p.IDpol == 3, 'ClaimAmount'].item() == 500
    assert p.PositiveClaimNb.sum() == 3
    assert p.Eligible.all()
    assert a['primary_claim_amount'] == 600
    pd.testing.assert_frame_equal(c, before)


def test_missing_claim_cost_not_zero_filled():
    p, a = reconcile(frequency(), pd.DataFrame({'IDpol': [3, 3], 'ClaimAmount': [200., 300.]}))
    row = p.loc[p.IDpol == 2].iloc[0]
    assert not row.Eligible and np.isnan(row.ClaimAmount)
    assert row.ClaimNb == 1
    assert a['claimed_but_no_severity'] == 1


def test_duplicate_policy_identifiers_are_all_excluded_not_multiplied():
    f = frequency(ids=(1, 1, 3))
    c = pd.DataFrame({'IDpol': [1, 3, 3], 'ClaimAmount': [100., 20., 20.]})
    p, a = reconcile(f, c)
    assert list(p.IDpol) == [3]
    assert a['duplicate_policy_rows'] == 2
    assert a['duplicate_claim_records_retained'] == 1
    assert p.ClaimAmount.item() == 40


def test_zero_cost_claim_is_retained_but_not_positive_frequency():
    p, a = reconcile(frequency(), pd.DataFrame({'IDpol': [2, 3, 3], 'ClaimAmount': [0., 0., 30.]}))
    assert p.Eligible.all()
    assert p.PositiveClaimNb.sum() == 1
    assert p.ClaimNb.sum() == 3
    assert a['zero_claim_amounts'] == 2


@pytest.mark.parametrize('amount', [-1., np.nan, np.inf])
def test_invalid_payment_excludes_its_parent(amount):
    p, _ = reconcile(frequency(), pd.DataFrame({'IDpol': [2, 3, 3], 'ClaimAmount': [amount, 10., 20.]}))
    assert not p.loc[p.IDpol == 2, 'Eligible'].item()


@pytest.mark.parametrize('exposure', [0., -1., np.nan, np.inf])
def test_invalid_exposure_excluded(exposure):
    p, _ = reconcile(frequency(exposures=(exposure, .5, 1)), pd.DataFrame({'IDpol': [2, 3, 3], 'ClaimAmount': [1., 2., 3.]}))
    assert not p.loc[p.IDpol == 1, 'Eligible'].item()


def test_unmatched_claim_audited_and_large_claim_not_clipped():
    p, a = reconcile(frequency(), pd.DataFrame({'IDpol': [2, 3, 3, 99], 'ClaimAmount': [1., 2., 4e6, 3.]}))
    assert p.ClaimAmount.max() == 4000002
    assert a['unmatched_claim_records'] == 1
    assert a['claims_over_100k_descriptive'] == 1


def test_schema_rejects_missing_or_unexpected_columns():
    with pytest.raises(ValueError):
        validate_schema(frequency().drop(columns='Exposure'), FREQUENCY_COLUMNS)

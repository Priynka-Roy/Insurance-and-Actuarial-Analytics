"""Immutable source loading, explicit policy reconciliation, no many-to-many joins."""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
FREQUENCY_COLUMNS = ['IDpol', 'ClaimNb', 'Exposure', 'VehPower', 'VehAge', 'DrivAge', 'BonusMalus', 'VehBrand', 'VehGas', 'Area', 'Density', 'Region']


def read_raw(name):
    path = ROOT / 'data/raw' / f'{name}.arff'
    if not path.exists():
        raise FileNotFoundError('Run python scripts/download_data.py first.')
    names, numeric = [], []
    with path.open() as handle:
        for line_number, line in enumerate(handle):
            fields = line.strip().split()
            if fields and fields[0].lower() == '@attribute':
                names.append(fields[1])
                if fields[2].lower() in {'numeric', 'real', 'integer'}:
                    numeric.append(fields[1])
            if line.strip().lower() == '@data':
                skip = line_number + 1
                break
        else:
            raise ValueError('Missing ARFF @data section')
    frame = pd.read_csv(path, skiprows=skip, names=names, quotechar="'", na_values=['?'])
    for col in numeric:
        frame[col] = pd.to_numeric(frame[col], errors='raise')
    return frame


def validate_schema(frame, required):
    if set(frame.columns) != set(required):
        raise ValueError(f'Schema mismatch: expected {required}, got {list(frame.columns)}')
    if frame.empty:
        raise ValueError('Empty source table')


def reconcile(frequency, claims):
    """Retain raw targets; primary economic cohort requires reconcilable counts.

    Exact repeated claims are not silently deduplicated: there is no claim ID.
    Duplicate policy identifiers exclude all associated frequency rows. Missing
    payment records for a declared claim are unknown costs, not zero costs.
    """
    validate_schema(frequency, FREQUENCY_COLUMNS)
    validate_schema(claims, ['IDpol', 'ClaimAmount'])
    f, c = frequency.copy(), claims.copy()
    valid_id = f.IDpol.notna() & np.isfinite(f.IDpol) & (f.IDpol % 1 == 0)
    duplicates = f.IDpol.duplicated(keep=False)
    valid_count = f.ClaimNb.notna() & np.isfinite(f.ClaimNb) & (f.ClaimNb >= 0) & (f.ClaimNb % 1 == 0)
    valid_exposure = f.Exposure.notna() & np.isfinite(f.Exposure) & (f.Exposure > 0)
    policy = f.loc[valid_id & ~duplicates].copy()
    claim_id_valid = c.IDpol.notna() & np.isfinite(c.IDpol) & (c.IDpol % 1 == 0)
    amount_valid = c.ClaimAmount.notna() & np.isfinite(c.ClaimAmount) & (c.ClaimAmount >= 0)
    bad_amount_ids = set(c.loc[claim_id_valid & ~amount_valid, 'IDpol'])
    linked = c.loc[claim_id_valid & c.IDpol.isin(policy.IDpol)].copy()
    usable = linked.loc[amount_valid.reindex(linked.index)].copy()
    aggregated = usable.groupby('IDpol').agg(
        LinkedClaimNb=('ClaimAmount', 'size'),
        PositiveClaimNb=('ClaimAmount', lambda x: int((x > 0).sum())),
        ClaimAmount=('ClaimAmount', 'sum'))
    policy = policy.merge(aggregated, on='IDpol', how='left', validate='one_to_one')
    policy[['LinkedClaimNb', 'PositiveClaimNb', 'ClaimAmount']] = policy[['LinkedClaimNb', 'PositiveClaimNb', 'ClaimAmount']].fillna(0)
    base_ok = policy.IDpol.map(dict(zip(f.IDpol, valid_count & valid_exposure)))
    policy['CountConsistent'] = policy.ClaimNb == policy.LinkedClaimNb
    policy['Eligible'] = base_ok.fillna(False) & policy.CountConsistent & ~policy.IDpol.isin(bad_amount_ids)
    # An unknown payment is missing, never silently assigned an economic zero.
    policy.loc[~policy.Eligible, 'ClaimAmount'] = np.nan
    eligible = policy.loc[policy.Eligible]
    audit = {
        'frequency_rows': len(f), 'severity_rows': len(c), 'unique_frequency_ids': int(f.IDpol.nunique()),
        'duplicate_policy_rows': int(duplicates.sum()), 'duplicate_policy_ids': int(f.loc[duplicates, 'IDpol'].nunique()),
        'duplicate_frequency_records': int(f.duplicated().sum()), 'missing_policy_ids': int((~valid_id).sum()),
        'duplicate_claim_records_retained': int(c.duplicated().sum()), 'missing_claim_ids': int((~claim_id_valid).sum()),
        'missing_claim_amounts': int(c.ClaimAmount.isna().sum()), 'negative_claim_amounts': int((c.ClaimAmount < 0).sum()),
        'zero_claim_amounts': int((c.ClaimAmount == 0).sum()), 'nonpositive_exposure_rows': int((f.Exposure <= 0).sum()),
        'invalid_exposure_rows': int((~valid_exposure).sum()), 'exposures_above_one_retained': int((f.Exposure > 1).sum()),
        'invalid_claim_count_rows': int((~valid_count).sum()), 'matched_policy_ids': int(linked.IDpol.nunique()),
        'matched_claim_records': len(linked), 'unmatched_claim_records': int((~c.IDpol.isin(policy.IDpol)).sum()),
        'policies_without_severity': int((policy.LinkedClaimNb == 0).sum()),
        'claimed_but_no_severity': int(((policy.ClaimNb > 0) & (policy.LinkedClaimNb == 0)).sum()),
        'severity_but_zero_declared': int(((policy.ClaimNb == 0) & (policy.LinkedClaimNb > 0)).sum()),
        'inconsistent_claim_counts': int((~policy.CountConsistent).sum()),
        'primary_eligible_policies': len(eligible), 'excluded_primary_policies': len(f) - len(eligible),
        'raw_declared_claims': float(f.ClaimNb.sum()), 'raw_exposure_years': float(f.Exposure.sum()),
        'raw_claim_amount_sum': float(c.ClaimAmount.sum()), 'max_claim_amount': float(c.ClaimAmount.max()),
        'claims_over_100k_descriptive': int((c.ClaimAmount > 100000).sum()),
        'primary_exposure_years': float(eligible.Exposure.sum()), 'primary_positive_claims': int(eligible.PositiveClaimNb.sum()),
        'primary_declared_claims': int(eligible.ClaimNb.sum()), 'primary_claim_amount': float(eligible.ClaimAmount.sum()),
        'rules': ['Exclude all duplicate policy IDs, not arbitrary first rows.', 'Keep exact repeated claims: no claim ID identifies duplicates.', 'No claim clipping or exposure capping.', 'Primary cost cohort: positive finite exposure, nonnegative integer declared counts, fully matched payment counts and valid nonnegative amounts.', 'Zero-valued payments retained in audit; compatible positive-payment frequency times positive severity defines pure premium.', 'Missing payment histories are unknown; exclude from economic cohort instead of zero-filling.'],
    }
    return policy, audit


def load_claims():
    return read_raw('freMTPL2sev')


def load_reconciled():
    freq, claims = read_raw('freMTPL2freq'), load_claims()
    return reconcile(freq, claims)


def export_reconciliation():
    policy, audit = load_reconciled()
    target = ROOT / 'data/processed'
    target.mkdir(parents=True, exist_ok=True)
    policy.to_parquet(target / 'policies.parquet', index=False)
    (ROOT / 'reports/reconciliation.json').write_text(json.dumps(audit, indent=2))
    audit['processed_sha256'] = hashlib.sha256((target / 'policies.parquet').read_bytes()).hexdigest()
    print(json.dumps(audit, indent=2))
    return policy, audit


if __name__ == '__main__':
    export_reconciliation()

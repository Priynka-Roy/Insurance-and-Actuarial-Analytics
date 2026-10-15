"""Leakage-safe policy partitions and feature transformations."""
from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

NUMERIC = ['VehAge', 'DrivAge', 'BonusMalus', 'LogDensity']
CATEGORICAL = ['VehPower', 'VehBrand', 'VehGas', 'Area', 'Region']
FEATURES = NUMERIC + CATEGORICAL


def policy_split(ids: pd.Series, seed: int = 42) -> np.ndarray:
    """Stable SHA256 split; independent of targets and input order."""
    def label(value):
        digest = hashlib.sha256(f'{seed}:{int(value)}'.encode()).digest()
        u = int.from_bytes(digest[:8], 'big') / 2**64
        return 'train' if u < .6 else 'validation' if u < .8 else 'test'
    return np.array([label(v) for v in ids], dtype=object)


def design_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Fixed, untuned transforms; no clipping of claims or exposures."""
    out = df.copy()
    density = pd.to_numeric(out['Density'], errors='coerce')
    if (density.dropna() < 0).any():
        raise ValueError('Density cannot be negative')
    out['LogDensity'] = np.log1p(density)
    for col in CATEGORICAL:
        out[col] = out[col].astype(str)
    return out[FEATURES]


def preprocessor(tree: bool = False) -> ColumnTransformer:
    numeric = make_pipeline(SimpleImputer(strategy='median'), StandardScaler())
    encoder = (OrdinalEncoder(handle_unknown='use_encoded_value', unknown_value=-1)
               if tree else OneHotEncoder(handle_unknown='ignore', drop='first', sparse_output=False))
    categorical = make_pipeline(SimpleImputer(strategy='most_frequent'), encoder)
    return ColumnTransformer([('numeric', numeric, NUMERIC), ('categorical', categorical, CATEGORICAL)],
                             verbose_feature_names_out=False)

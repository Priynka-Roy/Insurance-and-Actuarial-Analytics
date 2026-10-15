"""Verify a JSON-only deployment bundle without opening raw policy data."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    'artifacts/dashboard.json', 'reports/results.json', 'configs/protocol.json',
    'reports/data_provenance.json', 'reports/reconciliation.json', 'reports/selection_frozen.json',
}


def _no_constant(value):
    raise ValueError(f'Nonfinite JSON constant: {value}')


def _read_json(path):
    return json.loads(path.read_text(encoding='utf-8'), parse_constant=_no_constant)


def verify(root=ROOT):
    """Reject missing files, changed bytes, unsafe paths and unknown formats."""
    root = Path(root).resolve(strict=True)
    manifest_path = root / 'artifacts/manifest.json'
    if manifest_path.is_symlink() or manifest_path.resolve().parent != root / 'artifacts':
        raise ValueError('Unsafe manifest path')
    manifest = _read_json(manifest_path)
    if (not isinstance(manifest, dict) or type(manifest.get('schema_version')) is not int
            or manifest['schema_version'] != 1):
        raise ValueError('Unsupported manifest schema')
    files = manifest.get('files')
    if not isinstance(files, dict) or not REQUIRED.issubset(files):
        raise ValueError('Missing required artifact entries')
    for relative, expected in files.items():
        if not isinstance(relative, str):
            raise ValueError('Artifact path must be a string')
        path = PurePosixPath(relative)
        if (path.is_absolute() or '..' in path.parts or '\\' in relative
                or str(path) != relative or path.suffix != '.json'):
            raise ValueError(f'Unsafe or unsupported artifact path: {relative}')
        if not isinstance(expected, str) or not re.fullmatch(r'[0-9a-f]{64}', expected):
            raise ValueError(f'Invalid SHA-256 for {relative}')
        current = root
        for part in path.parts:
            current = current / part
            if current.is_symlink():
                raise ValueError(f'Symlink not permitted: {relative}')
        resolved = current.resolve(strict=True)
        if not resolved.is_relative_to(root) or not resolved.is_file():
            raise ValueError(f'Artifact escapes repository: {relative}')
        actual = hashlib.sha256(resolved.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f'Integrity failure: {relative}')
        _read_json(resolved)
    dashboard = _read_json(root / 'artifacts/dashboard.json')
    results = _read_json(root / 'reports/results.json')
    if dashboard != results:
        raise ValueError('Dashboard and results disagree')
    selection = _read_json(root / 'reports/selection_frozen.json')
    if dashboard.get('selection') != selection:
        raise ValueError('Frozen selection disagrees with results')
    protocol_sha = files['configs/protocol.json']
    if (selection.get('frozen_protocol_sha256') != protocol_sha
            or dashboard.get('protocol', {}).get('sha256') != protocol_sha):
        raise ValueError('Frozen protocol fingerprint mismatch')
    provenance = _read_json(root / 'reports/data_provenance.json')
    if (not isinstance(provenance, list) or len(provenance) != 2
            or any(not isinstance(row, dict) for row in provenance)
            or {row.get('openml_id') for row in provenance} != {41214, 41215}):
        raise ValueError('Unexpected source provenance')
    for row in provenance:
        if (str(row.get('version')) != '1'
                or not re.fullmatch(r'[0-9a-f]{64}', str(row.get('sha256', '')))):
            raise ValueError('Missing versioned source fingerprint')
    return len(files)


if __name__ == '__main__':
    print(f'Verified {verify()} JSON artifacts and protocol/provenance fingerprints.')

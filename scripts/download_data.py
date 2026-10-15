"""Download official OpenML v1 originals unchanged; no startup network access."""
from pathlib import Path
import hashlib
import json
import urllib.request
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def download():
    raw = ROOT / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    provenance = ROOT / 'reports/data_provenance.json'
    previous = json.loads(provenance.read_text()) if provenance.exists() else []
    prior = {row['openml_id']: row for row in previous}
    records = []
    for did in (41214, 41215):
        api = f'https://www.openml.org/api/v1/json/data/{did}'
        with urllib.request.urlopen(api, timeout=120) as response:
            metadata = json.load(response)['data_set_description']
        if metadata['licence'] != 'CC0' or metadata['version'] != '1':
            raise ValueError('Source license/version changed; review before processing.')
        path = raw / f"{metadata['name']}.arff"
        if not path.exists():
            temporary = path.with_suffix('.download')
            with urllib.request.urlopen(metadata['url'], timeout=180) as source, temporary.open('wb') as target:
                while chunk := source.read(1024 * 1024):
                    target.write(chunk)
            temporary.replace(path)
        blob = path.read_bytes()
        if hashlib.md5(blob).hexdigest() != metadata['md5_checksum']:
            raise ValueError(f'Official original MD5 mismatch: {path.name}')
        (raw / f'{did}-metadata.json').write_text(json.dumps(metadata, indent=2))
        digest = hashlib.sha256(blob).hexdigest()
        retrieved = prior.get(did, {}).get('retrieved_utc') if prior.get(did, {}).get('sha256') == digest else None
        records.append({'openml_id': did, 'name': metadata['name'], 'version': metadata['version'],
                        'license': metadata['licence'], 'metadata_url': api, 'source_url': metadata['url'],
                        'retrieved_utc': retrieved or datetime.now(timezone.utc).isoformat(), 'filename': path.name,
                        'bytes': len(blob), 'sha256': digest,
                        'official_md5': metadata['md5_checksum'], 'citation': metadata['citation']})
        print(path.name, len(blob), flush=True)
    (ROOT / 'reports/data_provenance.json').write_text(json.dumps(records, indent=2))


if __name__ == '__main__':
    download()

#!/usr/bin/env python3
"""Download the reusable Corsican language resources listed in resources/sources.json.

    python3 tools/fetch_resources.py            download what is missing
    python3 tools/fetch_resources.py --update   download everything again
    python3 tools/fetch_resources.py --list     show what is there

Files go to ~/.local/share/corsu/resources (or $CORSU_RESOURCES), never into the repository: several are large and
one has no license. manifest.json there records, for each file, the URL, the date it was fetched, its size and SHA-256.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / 'resources/sources.json'
TARGET = Path(os.environ.get('CORSU_RESOURCES', Path.home() / '.local/share/corsu/resources'))


def main():
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--update', action='store_true')
    parser.add_argument('--list', action='store_true')
    args = parser.parse_args()
    sources = json.loads(SOURCES.read_text(encoding='utf-8'))['resources']
    manifest_path = TARGET / 'manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for source in sources:
        path = TARGET / source['file']
        if args.list:
            entry = manifest.get(source['id'], {})
            print(f"{source['id']:20} {entry.get('fetched', 'missing'):26} {entry.get('bytes', 0):>12,} {path}")
            continue
        if path.exists() and not args.update:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        request = urllib.request.Request(source['url'], headers={'User-Agent': 'Corsu (github.com/Platykalt/corsu)'})
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                data = response.read()
        except OSError as error:
            print(f"{source['id']}: failed, {error}")
            continue
        path.write_bytes(data)
        manifest[source['id']] = {
            'url': source['url'], 'file': source['file'], 'license': source['license'],
            'fetched': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),
            'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
        }
        print(f"{source['id']}: {len(data):,} bytes")
    if not args.list:
        TARGET.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()

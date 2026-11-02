"""Read-only public Drive adapter; never falls back to cached records."""
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def download(url):
    if not re.fullmatch(r'https://drive.google.com/(?:drive/folders/[\w-]+|uc\?export=download&id=[\w-]+)', url):
        raise ValueError('Only auditor-authorized Drive URLs are supported')
    p = subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                        '--max-time', '45', '--max-filesize', '5000000', url],
                       capture_output=True, check=True)
    if not p.stdout or b'<html' in p.stdout[:500].lower() and '/uc?' in url:
        raise ValueError('Drive returned an empty file or access page')
    return p.stdout


def inventory(url):
    data = download(url).decode('utf-8')
    m = re.search(r"_DRIVE_ivd'\]\s*=\s*'((?:\\.|[^'\\])*)'", data)
    if not m:
        raise ValueError('Drive inventory unavailable or format changed')
    decoded = re.sub(r'\\x([0-9a-fA-F]{2})', lambda m: chr(int(m[1], 16)), m[1])
    rows = json.loads(decoded.replace('\\/', '/').replace("\\'", "'"))[0]
    if not rows or len(rows) >= 100:
        raise ValueError('Empty or potentially paginated inventory; use connector review')
    return [{'id': r[0], 'name': r[2], 'mime': r[3]} for r in rows]


def file_url(url):
    m = re.search(r'/d/([\w-]+)', url)
    if not m:
        raise ValueError('Expected a Drive file URL')
    return 'https://drive.google.com/uc?export=download&id=' + m[1]


def collect(catalog, selected, run):
    """Return only newly retrieved text; on any failure caller gets no results."""
    root = Path(run) / 'sources'
    root.mkdir(parents=True, exist_ok=False)
    manifest = {'retrieved_at_utc': datetime.now(timezone.utc).isoformat(), 'files': []}

    def save(rel, data, url):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        manifest['files'].append({'path': rel, 'url': url, 'sha256': sha(data), 'bytes': len(data)})
        return data.decode('utf-8-sig')

    guide = save('classification-guide.md', download(file_url(catalog['guide_url'])), catalog['guide_url'])
    result = {}
    for employer in selected:
        spec = catalog['employers'][employer]
        rows = inventory(spec['folder_url'])
        if len({r['name'] for r in rows}) != len(rows):
            raise ValueError('Duplicate source filenames')
        save(employer + '/inventory.json', json.dumps(rows, sort_keys=True).encode(), spec['folder_url'])
        files = {}
        for r in rows:
            name = r['name']
            if not re.fullmatch(r'[a-z0-9-]+\.(?:md|csv)', name):
                raise ValueError('Unsupported source file: ' + name)
            url = 'https://drive.google.com/file/d/' + r['id'] + '/view'
            files[name] = save(employer + '/' + name, download(file_url(url)), url)
        result[employer] = files
    (Path(run) / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return guide, result, manifest

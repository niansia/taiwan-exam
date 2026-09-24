#!/usr/bin/env python3
"""Real photographs for 社會 (and 自然) papers: search the web first, this library second.

A hosted run should look for fitting real images on the web and use them from its own
environment, recording where each came from (web_source; no license verdict needed). Many
sandboxes cannot fetch images: Claude's reached only GitHub (Wikimedia, government sites and
NASA answered 403) and a ChatGPT run found pages but not image files. Both 116 社會 runs then
stalled or printed placeholder boxes. This library is the fallback that always works where
GitHub does: 59 grayscale photographs, archival images and satellite scenes from Wikimedia
Commons (public domain, CC0, CC BY, CC BY-SA), each with its creator, license, source page and
the features a student can actually see.

  python scripts/photo_library.py probe                 # can this runtime fetch web images?
  python scripts/photo_library.py list --domain 地理    # browse (works offline)
  python scripts/photo_library.py fetch --run-dir RUN   # download + verify into RUN/photo-library
  python scripts/photo_library.py use g04 --run-dir RUN --output figures/q18.jpg --crop 0,0.1,1,0.9

`use` writes the placed crop and prints the visual_asset and visual_spec fields to merge into
the item; the final check accepts them as a traceable source.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request
import zipfile

HERE = Path(__file__).resolve().parent
MANIFEST = HERE.parent / 'references' / 'photo-library-manifest.json'
ZIP_FILE = 'taiwan-exam-photo-library-v1.zip'
ZIP_SHA256 = '68acb256e6e263c3cc664ca0d4e0339c0ba111cf219bee27c7f49304dc7a31cc'
ZIP_BYTES = 15240230
ZIP_URL = 'https://github.com/niansia/taiwan-exam/releases/download/photos-v1/' + ZIP_FILE
UPLOAD_DIRS = ('/mnt/user-data/uploads', '/mnt/data', '/home/user', '.')
# Hosts a web search usually lands on for real images; one small request each.
PROBES = {
    'wikimedia_commons': 'https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/40px-PNG_transparency_demonstration_1.png',
    'nasa_earth_observatory': 'https://eoimages.gsfc.nasa.gov/images/imagerecords/0/885/modis_wonderglobe_lrg.jpg',
    'taiwan_government_open_data': 'https://data.gov.tw/favicon.ico',
    'github_release': 'https://github.com/niansia/taiwan-exam/releases/tag/photos-v1',
}


def manifest():
    return json.loads(MANIFEST.read_text(encoding='utf-8'))


def _reachable(url, timeout):
    request = urllib.request.Request(url, headers={'User-Agent': 'taiwan-exam photo probe', 'Range': 'bytes=0-1023'})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read(1024)
            return 'reachable'
    except urllib.error.HTTPError as error:
        return f'HTTP {error.code}'
    except (urllib.error.URLError, OSError, ValueError) as error:
        return str(getattr(error, 'reason', error))[:80]


def probe(timeout=4):
    """Which image sources this runtime can reach, in about `timeout` seconds."""
    with concurrent.futures.ThreadPoolExecutor(len(PROBES)) as pool:
        results = dict(zip(PROBES, pool.map(lambda url: _reachable(url, timeout), PROBES.values())))
    web = any(state == 'reachable' for name, state in results.items() if name != 'github_release')
    library = results['github_release'] == 'reachable'
    advice = ('Search the web for fitting real images first and use them from this environment (record them as '
              'web_source). ' if web else
              'Web image hosts are blocked here: do not spend time retrying them. ')
    advice += ('The photo library is available: `python scripts/photo_library.py fetch --run-dir RUN`.' if library else
               'GitHub is blocked too: ask the user once to upload images or taiwan-exam-photo-library-v1.zip '
               f'({ZIP_URL}).')
    return {'hosts': results, 'web_images': 'reachable' if web else 'blocked',
            'photo_library_download': 'reachable' if library else 'blocked', 'advice': advice}


def _verified(data):
    return len(data) == ZIP_BYTES and hashlib.sha256(data).hexdigest() == ZIP_SHA256


def fetch(run_dir, timeout=60):
    """Put the verified library under RUN/photo-library; reuse, then uploads, then the Release."""
    target = Path(run_dir) / 'photo-library'
    if (target / 'manifest.json').is_file():
        bad = [i['id'] for i in manifest()['items']
               if not (target / i['file']).is_file() or hashlib.sha256((target / i['file']).read_bytes()).hexdigest() != i['sha256']]
        if not bad:
            return {'status': 'ready', 'path': str(target), 'source': 'existing', 'items': len(manifest()['items'])}
    data, source = None, None
    for folder in UPLOAD_DIRS:
        candidate = Path(folder) / ZIP_FILE
        if candidate.is_file() and _verified(candidate.read_bytes()):
            data, source = candidate.read_bytes(), str(candidate)
            break
    if data is None:
        try:
            request = urllib.request.Request(ZIP_URL, headers={'User-Agent': 'taiwan-exam photo_library'})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = response.read(ZIP_BYTES + 1)
            source = ZIP_URL
        except (urllib.error.URLError, OSError, ValueError) as error:
            return {'status': 'unavailable', 'error': str(getattr(error, 'reason', error))[:200],
                    'action': f'Ask the user once to download {ZIP_URL} and upload it to the chat, then rerun fetch.'}
        if not _verified(data):
            return {'status': 'unavailable', 'error': 'downloaded bytes do not match the pinned library; discarded'}
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for name in archive.namelist():
            if name.startswith('photo-library/') and not name.endswith('/') and '..' not in name:
                (target / name.split('/', 1)[1]).write_bytes(archive.read(name))
    return {'status': 'ready', 'path': str(target), 'source': source, 'items': len(manifest()['items'])}


def use(photo_id, run_dir, output, crop=None, print_width_cm=12.0):
    """Crop a library photo into the run and return the fields the item records."""
    import pymupdf
    run_dir = Path(run_dir).resolve()
    item = next((i for i in manifest()['items'] if i['id'] == photo_id), None)
    if item is None:
        raise SystemExit(f'unknown photo id {photo_id}')
    source = run_dir / 'photo-library' / item['file']
    if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != item['sha256']:
        raise SystemExit('run `photo_library.py fetch --run-dir RUN` first; the library file is missing or changed')
    pix = pymupdf.Pixmap(str(source))
    box = [0.0, 0.0, 1.0, 1.0] if not crop else [float(v) for v in crop.split(',')]
    if len(box) != 4 or not (0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1):
        raise SystemExit('--crop takes x0,y0,x1,y1 as fractions of the width and height')
    x0, y0, x1, y1 = (round(box[0] * pix.width), round(box[1] * pix.height), round(box[2] * pix.width), round(box[3] * pix.height))
    if (x0, y0, x1, y1) != (0, 0, pix.width, pix.height):
        doc = pymupdf.open()
        page = doc.new_page(width=x1 - x0, height=y1 - y0)
        page.insert_image(pymupdf.Rect(-x0, -y0, pix.width - x0, pix.height - y0), pixmap=pix)
        pix = page.get_pixmap(dpi=72, colorspace=pymupdf.csGRAY, clip=page.rect)
    target = (run_dir / output).resolve()
    if not target.is_relative_to(run_dir):
        raise SystemExit('--output must be inside the run directory')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(pix.tobytes('jpg', jpg_quality=85))
    source_info = item['source']
    dpi = int(pix.width / (print_width_cm / 2.54))
    relative = lambda p: Path(os.path.relpath(p, run_dir)).as_posix()
    return {
        'visual_asset': {'path': relative(target), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'grayscale': True},
        'visual_spec': {
            'kind': item['kind'],
            'generation_mode': 'photo_library', 'source_rights': source_info['source_rights'],
            'source_url': source_info['page'], 'source_creator': source_info['creator'], 'source_site': source_info['site'],
            'source_retrieved_at': source_info['retrieved_at'], 'license_or_authorization': source_info['license'],
            'source_asset_path': relative(source), 'source_asset_sha256': item['sha256'],
            'crop_description': 'full frame' if not crop else f'crop x {box[0]:g}-{box[2]:g}, y {box[1]:g}-{box[3]:g} of the library file',
            'processing_steps': [*item['processing'], *(['cropped'] if crop else []), 'JPEG quality 85'],
            'tonal_transform': 'grayscale', 'min_raster_dpi': dpi,
            'library_observable_features': item['observable_features'],
        },
        'notes': [f'Printed {print_width_cm:g} cm wide the crop gives {dpi} dpi' + ('' if dpi >= 200 else '; print it narrower'),
                  *([item['caution']] if item.get('caution') else []),
                  'Do not print the credit in the booklet; the record above is the attribution.'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='action', required=True)
    sub.add_parser('probe')
    listing = sub.add_parser('list')
    listing.add_argument('--domain', choices=['地理', '歷史', '公民與社會'])
    listing.add_argument('--query')
    fetcher = sub.add_parser('fetch')
    fetcher.add_argument('--run-dir', required=True)
    user = sub.add_parser('use')
    user.add_argument('photo_id')
    user.add_argument('--run-dir', required=True)
    user.add_argument('--output', required=True)
    user.add_argument('--crop')
    user.add_argument('--print-width-cm', type=float, default=12.0)
    args = parser.parse_args()
    if args.action == 'probe':
        result = probe()
    elif args.action == 'list':
        result = [{k: i[k] for k in ('id', 'domain', 'title', 'observable_features', 'curriculum_links', 'caution') if k in i}
                  for i in manifest()['items']
                  if (not args.domain or i['domain'] == args.domain)
                  and (not args.query or args.query in json.dumps(i, ensure_ascii=False))]
    elif args.action == 'fetch':
        result = fetch(args.run_dir)
    else:
        result = use(args.photo_id, args.run_dir, args.output, args.crop, args.print_width_cm)
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0 if not (isinstance(result, dict) and result.get('status') == 'unavailable') else 1


if __name__ == '__main__':
    raise SystemExit(main())

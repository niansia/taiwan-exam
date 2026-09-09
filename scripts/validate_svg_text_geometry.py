#!/usr/bin/env python3
"""Check static SVG label/edge geometry without executing document-supplied code.

Reimplemented after the September 2026 incident. Reject active/external SVG;
run only the installed measurement probe in a fresh Chromium profile under CSP.
Bounding-box/stroke sampling is conservative and never replaces visual review.
"""
from __future__ import annotations

import argparse
import html
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from render_pdf import find_browser
from safe_rendering import browser_flags, prepare_html, validate_svg

PROBE = r'''
const report = {labels: 0, edges: 0, issues: []};
const svg = document.querySelector('svg');
const shown = node => {
  const s = getComputedStyle(node), b = node.getBoundingClientRect();
  return s.display !== 'none' && s.visibility !== 'hidden' && Number(s.opacity) > 0 && (b.width || b.height);
};
const viewport = svg.getBoundingClientRect();
const labels = [...svg.querySelectorAll('text')].filter(shown).map((node, index) => ({
  index, text: node.textContent, box: node.getBoundingClientRect()
}));
report.labels = labels.length;
const intersects = (a, b) => Math.min(a.right,b.right)-Math.max(a.left,b.left) > 0.5 && Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top) > 0.5;
for (const label of labels) {
  const b = label.box;
  if (b.left < viewport.left-0.5 || b.right > viewport.right+0.5 || b.top < viewport.top-0.5 || b.bottom > viewport.bottom+0.5)
    report.issues.push({kind:'label-outside-viewport', label:label.index, text:label.text});
}
for (let i=0; i<labels.length; i++) for (let j=i+1; j<labels.length; j++) {
  if (intersects(labels[i].box, labels[j].box)) report.issues.push({kind:'label-overlap', labels:[i,j]});
}
let budget = 0;
for (const edge of svg.querySelectorAll('path,line,polyline,polygon,rect,circle,ellipse')) {
  if (edge.closest('defs,marker,clipPath,mask,pattern') || !shown(edge)) continue;
  const style = getComputedStyle(edge);
  if (style.stroke === 'none' || Number(style.strokeOpacity) === 0 || !(parseFloat(style.strokeWidth) > 0)) continue;
  const matrix = edge.getScreenCTM();
  if (!matrix) {report.issues.push({kind:'unmeasurable-edge'}); continue;}
  const scale = Math.max(Math.hypot(matrix.a,matrix.b), Math.hypot(matrix.c,matrix.d));
  const length = edge.getTotalLength();
  const steps = Math.max(1, Math.ceil(length*scale/0.5));
  budget += steps;
  if (!Number.isFinite(steps) || budget > 500000) {report.issues.push({kind:'measurement-budget-exceeded'}); break;}
  const radius = parseFloat(style.strokeWidth) * (style.vectorEffect === 'non-scaling-stroke' ? 1 : scale) / 2 + 0.25;
  const hits = new Set();
  for (let i=0; i<=steps; i++) {
    const p = edge.getPointAtLength(length*i/steps).matrixTransform(matrix);
    for (const label of labels) {
      const b=label.box;
      if (p.x >= b.left-radius && p.x <= b.right+radius && p.y >= b.top-radius && p.y <= b.bottom+radius) hits.add(label.index);
    }
  }
  for (const label of hits) report.issues.push({kind:'label-stroke-intersection', edge:report.edges, label});
  report.edges++;
}
const out = document.createElement('pre');
out.id = 'svg-geometry-result';
out.textContent = JSON.stringify(report);
document.body.appendChild(out);
'''


def measure(path: Path, browser: Path | None = None) -> dict:
    data = path.read_bytes()
    source = validate_svg(data.decode('utf-8-sig'))
    document = '<!doctype html><html><head><meta charset="utf-8"></head><body>' + source + '</body></html>'
    rendered = prepare_html(document, measurement_script=PROBE)
    with tempfile.TemporaryDirectory(prefix='svg-geometry-') as temporary:
        folder = Path(temporary)
        page = folder / 'figure.html'
        page.write_text(rendered, encoding='utf-8')
        result = subprocess.run([str(find_browser(browser)), *browser_flags(folder),
                                 '--dump-dom', page.as_uri()], capture_output=True,
                                encoding='utf-8', errors='replace', timeout=60, check=True)
    match = re.search(r'<pre id="svg-geometry-result">(.*?)</pre>', result.stdout, re.S)
    if not match:
        raise RuntimeError('Browser did not produce SVG geometry measurements')
    measured = json.loads(html.unescape(match[1]))
    measured['file'] = path.name
    measured['sha256'] = hashlib.sha256(data).hexdigest()
    measured['status'] = 'fail' if measured['issues'] else 'pass-geometry-only'
    return measured


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('report', type=Path)
    parser.add_argument('--browser', type=Path)
    args = parser.parse_args(argv)
    try:
        files = sorted(args.directory.glob('*.svg'))
        if not files:
            raise ValueError('No SVG files found; an empty directory is not a geometry pass')
        records = []
        for path in files:
            try:
                records.append(measure(path, args.browser))
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
                records.append({'file': path.name, 'status': 'fail', 'error': str(exc)})
        report = {'status': 'pass-geometry-only' if all(r['status'] == 'pass-geometry-only' for r in records) else 'fail',
                  'scope': 'Conservative viewport/label-bounds/stroke sampling; final visual review remains required', 'files': records}
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        return 0 if report['status'] == 'pass-geometry-only' else 2
    except (OSError, ValueError) as exc:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps({'status': 'fail', 'error': str(exc)}, ensure_ascii=False), encoding='utf-8')
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())

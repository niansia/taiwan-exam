#!/usr/bin/env python3
"""Coverage-aware lexical triage of generated exams against all local inputs.

No model-written pass flags are trusted. PDF pages and historical generated JSON
are searched without a question-number/year cutoff. Textless pages remain gaps;
this tool cannot establish semantic or visual originality. No source prose is
exported. Run only in the audit pass, never as a question-writing input.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import unicodedata


def normalize(text, mask_numbers=False):
    text = unicodedata.normalize('NFKC', str(text)).lower()
    if mask_numbers:
        text = re.sub(r'\d+(?:[.,]\d+)*', '#', text)
    return re.sub(r'[^a-z0-9#\u3400-\u9fff]', '', text)


def grams(text, size=7):
    return {text[i:i+size] for i in range(max(0, len(text)-size+1))}


def signature(text):
    size = 4 if re.search(r'[\u3400-\u9fff]', str(text)) else 7
    return grams(normalize(text), size) | {'~'+x for x in grams(normalize(text, True), size)}


def item_body(q):
    # Do not include explanations, editorial metadata or shared prose in stems.
    return str(q.get('prompt') or '') + ' '.join(
        str(o.get('text') or '') if isinstance(o, dict) else str(o)
        for o in q.get('options', []))


def records(exam, path):
    result, groups = [], {}
    for q in exam.get('questions', []):
        n = q.get('number', q.get('id'))
        text = item_body(q)
        if len(normalize(text)) >= 24:
            result.append(dict(kind='item', locator=n, text=text, path=str(path)))
        stimulus = str(q.get('group_stimulus') or '')
        if stimulus:
            key = normalize(stimulus)
            groups.setdefault(key, dict(kind='stimulus', locator=[], text=stimulus, path=str(path)))['locator'].append(n)
    return result + list(groups.values())


def internal_review(exam):
    questions = exam.get('questions', [])
    out = []
    for i, a in enumerate(questions):
        for b in questions[i+1:]:
            # Generic blank instructions are not duplicate items.
            at, bt = normalize(item_body(a)), normalize(item_body(b))
            if len(at) >= 45 and at == bt:
                out.append(dict(kind='identical_item_text', numbers=[a.get('number'), b.get('number')]))
    # Shared material inside one group is expected. Reuse in disjoint runs is not.
    runs = []
    for q in questions:
        s = normalize(q.get('group_stimulus') or '')
        if not s:
            runs.append(('', []))
        elif runs and runs[-1][0] == s:
            runs[-1][1].append(q.get('number'))
        else:
            runs.append((s, [q.get('number')]))
    by_text = defaultdict(list)
    for s, ns in runs:
        if len(s) >= 60:
            by_text[s].append(ns)
    for ns in by_text.values():
        if len(ns) > 1:
            out.append(dict(kind='stimulus_reused_across_groups', groups=ns))
    unique = list(by_text)
    for i, a in enumerate(unique):
        for b in unique[i+1:]:
            sa, sb = grams(a, 4), grams(b, 4)
            overlap = len(sa & sb) / max(1, min(len(sa), len(sb)))
            if overlap >= .25:
                out.append(dict(kind='similar_stimuli_need_review',
                                groups=by_text[a]+by_text[b],
                                smaller_text_coverage=round(overlap, 4)))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('exams', type=Path, nargs='+')
    ap.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument('--output', required=True, type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    targets = {p.resolve() for p in args.exams}
    queries, exams = [], []
    for p in sorted(targets):
        d = json.loads(p.read_text(encoding='utf-8-sig'))
        exams.append(dict(path=str(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                          subject=d.get('metadata', {}).get('subject'), internal_findings=internal_review(d)))
        queries.extend(records(d, p))
    inverted = defaultdict(list)
    for i, q in enumerate(queries):
        q['signature'] = signature(q['text'])
        q['neighbors'] = {}
        for g in q['signature']:
            inverted[g].append(i)

    def search(text, source, kind):
        # Bilingual pages must expose both Chinese fourgrams and English
        # sevengrams; choosing the language of the page loses English queries.
        sg = signature(text) | grams(normalize(text), 7) | {'~'+x for x in grams(normalize(text, True), 7)}
        common = Counter(i for g in sg for i in inverted.get(g, ()))
        for i, count in common.items():
            q = queries[i]
            containment = count / max(1, len(q['signature']))
            if count < 8 or containment < .10:
                continue
            row = dict(source=source, shared_shingles=count,
                       query_coverage=round(containment, 4),
                       jaccard=round(count / len(sg | q['signature']), 4))
            arr = q['neighbors'].setdefault(kind, [])
            arr.append(row)
            arr.sort(key=lambda x: (x['query_coverage'], x['jaccard']), reverse=True)
            del arr[5:]

    # All raw intake folders and all organized packs, including old curricula,
    # answer books and reference specifications (false positives are reviewed).
    folders = sorted(root.glob('drive-download*')) + [root/'exam_packs']
    paths = sorted({p.resolve() for f in folders if f.is_dir() for p in f.rglob('*') if p.is_file()})
    inventory, hashes = [], {}
    for p in paths:
        data = p.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        rel = str(p.relative_to(root))
        if sha in hashes:
            hashes[sha]['aliases'].append(rel)
            continue
        row = dict(path=rel, aliases=[], sha256=sha, extension=p.suffix.lower())
        hashes[sha] = row
        inventory.append(row)

    import pymupdf
    pdf_count = 0
    for row in inventory:
        if row['extension'] != '.pdf':
            row['status'] = 'not_searched_non_pdf'
            continue
        pdf_count += 1
        try:
            with pymupdf.open(root/row['path']) as doc:
                row['pages'] = len(doc)
                row['low_text_pages'] = []
                row['text_pages'] = 0
                for j, page in enumerate(doc):
                    text = page.get_text('text') or ''
                    if len(normalize(text)) < 80:
                        row['low_text_pages'].append(j+1)
                    else:
                        row['text_pages'] += 1
                    # Search short pages too; do not confuse a threshold with OCR.
                    search(text, dict(path=row['path'], page=j+1, sha256=row['sha256']), 'corpus_pdf')
                row['status'] = 'partial_text' if row['low_text_pages'] else 'text_extracted_not_semantically_verified'
        except Exception as exc:
            row['status'] = 'read_error'
            row['error'] = str(exc)
        if pdf_count % 100 == 0:
            print(f'Searched {pdf_count} unique PDFs', flush=True)

    history = []
    # Skip maintained target files, not whole subjects. Superseded revisions are
    # candidates, not automatic plagiarism findings; reviewer resolves identity.
    for p in sorted((root/'output').rglob('*exam.json')):
        if p.resolve() in targets:
            continue
        try:
            d = json.loads(p.read_text(encoding='utf-8-sig'))
            rr = records(d, p)
            history.append(dict(path=str(p.relative_to(root)), records=len(rr),
                                sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
            for r in rr:
                search(r['text'], dict(path=str(p.relative_to(root)), kind=r['kind'], locator=r['locator']), 'prior_generated')
        except (ValueError, OSError) as exc:
            history.append(dict(path=str(p), error=str(exc)))

    items = []
    for q in queries:
        hits = [x for arr in q['neighbors'].values() for x in arr]
        items.append({k:q[k] for k in ('path', 'kind', 'locator', 'neighbors')} | dict(
            lexical_review=any(x['query_coverage'] >= .45 for x in hits),
            structural_status='unreviewed', visual_status='unreviewed'))
    pdfs = [r for r in inventory if r['extension'] == '.pdf']
    summary = dict(physical_input_files=len(paths), unique_input_files=len(inventory),
                   unique_pdfs=len(pdfs), pages=sum(r.get('pages', 0) for r in pdfs),
                   text_pages=sum(r.get('text_pages', 0) for r in pdfs),
                   low_text_pages=sum(len(r.get('low_text_pages', [])) for r in pdfs),
                   read_errors=sum(r['status']=='read_error' for r in pdfs),
                   non_pdf_unique_files=len(inventory)-len(pdfs), history_exams=len(history),
                   queried_records=len(items), flagged_records=sum(i['lexical_review'] for i in items))
    report = dict(schema_version=1, status='review-required', summary=summary,
                  limitations=['Text extraction is not OCR or semantic review.',
                               'Low-text pages may be covers, outlines or scans; inspect before classifying.',
                               'No image-topology comparison or complete formula recognition is performed.',
                               'Only output/**/*exam.json generated history is searched; deleted/unstructured versions are not covered.',
                               'Page-level substring overlap is triage, not proof of item reuse. Same-group material is counted once.'],
                  exams=exams, corpus_inventory=inventory, generated_history=history, records=items)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))
    return 0  # completed triage, not an originality approval


if __name__ == '__main__':
    raise SystemExit(main())

import json
from pathlib import Path
import re
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from read_web_knowledge import LAYOUT_SLUGS, reading_plan, sections


@pytest.mark.parametrize('subject', LAYOUT_SLUGS)
def test_reading_plan_is_scoped_but_preserves_canonical_runtime(subject, tmp_path):
    knowledge = ROOT / 'web/taiwan-exam-web-knowledge.md'
    result = reading_plan(knowledge, subject, tmp_path)
    entries = sections(knowledge.read_text(encoding='utf-8'))
    first = (tmp_path / result['first_read']).read_text(encoding='utf-8')
    assert result['views'][0]['bytes'] < result['canonical_bytes'] * .3
    projections = [json.loads(s) for s in re.findall(r'```json\n(.*?)\n```', first, re.S)
                   if '"json_pointer"' in s]
    assert len(projections) == 2
    for projection in projections:
        record, raw = entries[projection['canonical_source']]
        i = int(projection['json_pointer'].split('/')[-1])
        assert projection['record'] == json.loads(raw)['subjects'][i]
        assert projection['record']['subject'] == subject
        assert projection['embedded_sha256'] == record['embedded_sha256']
        assert (tmp_path / projection['canonical_source']).read_bytes() == raw
    assert (tmp_path / 'scripts/check_hosted_run.py').read_bytes() == entries['scripts/check_hosted_run.py'][1]
    authoring = (tmp_path / 'reading/authoring.md').read_text(encoding='utf-8')
    assert '## schemas/question.schema.json' in authoring
    assert '## references/hosted-quality-gates.md' in authoring
    layout = (tmp_path / 'reading/layout.md').read_text(encoding='utf-8')
    assert f'templates/hosted-{LAYOUT_SLUGS[subject]}-questions.json' in layout
    assert reading_plan(knowledge, subject, tmp_path) == result


def test_reading_plan_preserves_changed_views(tmp_path):
    knowledge = ROOT / 'web/taiwan-exam-web-knowledge.md'
    reading_plan(knowledge, '數學A', tmp_path)
    view = tmp_path / 'reading/preflight.md'
    view.write_text('user notes', encoding='utf-8')
    with pytest.raises(ValueError, match='Preserve existing reading view'):
        reading_plan(knowledge, '數學A', tmp_path)
    assert view.read_text(encoding='utf-8') == 'user notes'

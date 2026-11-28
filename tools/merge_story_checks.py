"""Record the second-source results in assets/flag_stories.json. A story is usable only with verdict 'ok'.

    python tools/merge_story_checks.py <result.json> [<result.json> ...]

result.json: {code: {"verdict": "ok|conflict|unverified", "url", "evidence", "note", "text"?}}. If a result carries the
"text" it was checked against and that differs from the current sentence, it is ignored.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from georush.stories import text_hash  # noqa: E402

COPIES = ('cia.gov', 'indexmundi', 'theodora', 'photius', 'factbook')  # the first source again, not a second one
path = ROOT/'assets'/'flag_stories.json'
stories = json.loads(path.read_text(encoding='utf-8'))
rejected = {}
for name in sys.argv[1:]:
    for code, result in json.loads(Path(name).read_text(encoding='utf-8-sig')).items():
        item = stories.get(code)
        if item is None or result.get('text', item['text']) != item['text']:
            continue
        url = str(result.get('url', ''))
        if result.get('verdict') == 'ok' and url.startswith('http') and not any(c in url.lower() for c in COPIES):
            item.update(second=url, checked=text_hash(item['text']))
            rejected.pop(code, None)
        else:
            item.pop('second', None)
            item.pop('checked', None)
            rejected[code] = f"{result.get('verdict')}: {result.get('note') or url}"
path.write_text(json.dumps(stories, ensure_ascii=False, indent=1), encoding='utf-8')
ok = [c for c, i in stories.items() if i.get('checked') == text_hash(i['text'])]
print('stories', len(stories), '| cross-checked', len(ok), '| rejected', len(rejected))
for code, why in sorted(rejected.items()):
    print(' ', code, stories[code]['text'], '->', why[:200])

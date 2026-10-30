"""Build bundled PNGs from a pinned MIT flag-icons checkout (development only).

Runtime generation does not import CairoSVG or access the network. Install
CairoSVG==2.8.2 in an isolated development environment to run this tool.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

REVISION = 'ac7e0eb3259eb62aa6100c435607e2fe03896a97'
# 190 of the 193 UN member states. The first 20 codes of each group are the v1.3 catalog, unchanged.
# Omitted near-identical 4:3 icons: Chad (Romania), Monaco (Indonesia), Luxembourg (Netherlands).
GROUPS = {
    'Easy': ('us ca gb fr de it es jp kr cn br au in za mx ch se no gr ar '
             'ru id sa ae at pk ir cz hu is kp np lb cy bd ro ve qa iq et').split(),
    'Normal': ('nz dk fi nl be pt ie pl ua tr eg ke ma ng vn th ph my sg il '
               'af dz ao bs bb by bg kh do sv ee fj gt hn ht jo kw kg lv lt '
               'ly mg mt mn me mz mm na ni om py pg sn si lk sd tn tz ug zw').split(),
    'Hard': ('ec bo pe cl co cr pa cu jm uy kz uz ge am az al hr rs ba sk '
             'ad ag bf bh bi bj bn bt bw bz cd cf cg ci cm cv dj dm er fm '
             'ga gd gh gm gn gq gw gy ki km kn la lc li lr ls md mh mk ml '
             'mr mu mv mw ne nr pw rw sb sc sl sm so sr ss st sy sz tg tj '
             'tl tm to tt tv vc vu ws ye zm').split(),
}
EXCLUDED = {'td': 'ro', 'mc': 'id', 'lu': 'nl'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--upstream', type=Path, required=True)
    args = parser.parse_args()
    repo = args.upstream.resolve()
    actual = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != REVISION:
        raise SystemExit(f'Expected pinned revision {REVISION}, got {actual}')
    import cairocffi
    import cairosvg
    from PIL import Image

    assets = Path(__file__).resolve().parents[1] / 'assets'
    for folder in ['flags', 'source_svg', 'licenses']:
        (assets/folder).mkdir(parents=True, exist_ok=True)
    upstream = json.loads((repo/'country.json').read_text(encoding='utf-8'))
    by_code = {row['code']: row for row in upstream}
    base = f'https://github.com/lipis/flag-icons/blob/{REVISION}'
    # Flags already in the catalog are kept byte-for-byte: another cairo version re-rasterizes a few
    # emblem pixels differently (es/mx/bo with cairo 1.18.4). Only new codes are rasterized.
    previous = {row['code']: row for row in json.loads((assets/'countries.json').read_text(encoding='utf-8'))}
    countries, rasterized = [], []
    for difficulty, codes in GROUPS.items():
        for code in codes:
            row = by_code[code]
            assert row['iso'] is True and row['flag_4x3'] == f'flags/4x3/{code}.svg'
            svg = repo/row['flag_4x3']
            png = assets/'flags'/f'{code}.png'
            copied_svg = assets/'source_svg'/f'{code}.svg'
            if code in previous:
                kept = previous[code]
                assert kept['difficulty'] == difficulty and kept['name'] == row['name']
                assert sha(png) == kept['sha256'], f'existing flag changed: {code}'
                assert sha(copied_svg) == kept['source_svg_sha256'] == sha(svg), f'existing SVG changed: {code}'
            else:
                shutil.copyfile(svg, copied_svg)
                cairosvg.svg2png(url=str(svg), write_to=str(png), output_width=900, output_height=675)
                rasterized.append(code)
            with Image.open(png) as im:
                assert im.size == (900, 675)
                im.verify()
            countries.append({
                'code': code, 'name': row['name'], 'difficulty': difficulty,
                'flag': f'flags/{code}.png', 'source': f'{base}/{row["flag_4x3"]}',
                'sha256': sha(png), 'source_svg_sha256': sha(svg),
                'license': 'MIT',
            })
    assert len(countries) == 190 and len({c['code'] for c in countries}) == 190
    assert len({c['sha256'] for c in countries}) == 190
    assert not set(EXCLUDED) & {c['code'] for c in countries}
    (assets/'countries.json').write_text(json.dumps(countries, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    shutil.copyfile(repo/'LICENSE', assets/'licenses'/'flag-icons-MIT.txt')
    shutil.copyfile(repo/'country.json', assets/'country_source_upstream.json')
    manifest = {
        'source_project': 'lipis/flag-icons', 'revision': REVISION,
        'source_url': base, 'license': 'MIT',
        'upstream_country_data_sha256': sha(repo/'country.json'),
        'country_manifest_sha256': sha(assets/'countries.json'),
        'license_sha256': sha(assets/'licenses'/'flag-icons-MIT.txt'),
        'count': len(countries), 'png_size': [900, 675],
        'transform': 'flag-icons standard 4:3 SVG variants rasterized by CairoSVG 2.8.2; not native national flag proportions',
        'difficulty_notice': 'Editorial familiarity groups, not an objective country difficulty ranking.',
        'excluded_ambiguity_examples': ['Chad/Romania', 'Monaco/Indonesia', 'Luxembourg/Netherlands'],
        'excluded_un_members': sorted(EXCLUDED),
        'preserved_flags': len(countries) - len(rasterized),
        'rasterized_flags': len(rasterized),
        'rasterizer': f'CairoSVG 2.8.2 with cairo {cairocffi.cairo_version_string()}',
        'offline_runtime': True,
    }
    (assets/'asset_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(f'Kept {len(countries) - len(rasterized)} existing and rasterized {len(rasterized)} new verified PNGs from {REVISION}')


if __name__ == '__main__':
    main()

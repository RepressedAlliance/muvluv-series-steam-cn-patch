"""Check staged AGE2 language isolation against extracted original resources.

This verifies package structure, not translation quality or full runtime coverage.
"""
import argparse
import collections
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from AGE2.tools.egpack.egpack_codec import parse_egpack_bytes

GAMES = ('tm', 'tda00', 'tda01', 'tda02', 'tda03')


def verify_game(package, original, candidate):
    root = package / 'root'
    manifest = json.loads((package / 'manifest.json').read_text(encoding='utf-8'))
    counts = collections.Counter()
    for entry in manifest['files']:
        rel = Path(entry['path'])
        if rel.parts[0] != 'root':
            continue
        rel = Path(*rel.parts[1:])
        path = root / rel
        if path.suffix.lower() in ('.webp', '.avif'):
            if not path.stem.lower().endswith(('_zh', '_ck')):
                raise ValueError(f'Image overwrites a native language name: {rel}')
            counts[path.suffix.lower()[1:]] += 1
        if path.suffix.lower() != '.egpack':
            continue
        before = parse_egpack_bytes((original / rel).read_bytes())
        raw = path.read_bytes()
        after = parse_egpack_bytes(raw)
        if raw != (candidate / rel).read_bytes():
            raise ValueError(f'Stale staged EGPACK: {rel}')
        if [r.text_id for r in before.records] != [r.text_id for r in after.records]:
            raise ValueError(f'Record identity/order changed: {rel}')
        for old, new in zip(before.records, after.records):
            if old.slots.keys() != new.slots.keys():
                raise ValueError(f'Language fields changed: {rel}/{old.text_id}')
            for language in old.slots:
                if language != 'zh_hans' and old.slots[language].text != new.slots[language].text:
                    raise ValueError(f'Native text changed: {rel}/{old.text_id}/{language}')
            counts['records'] += 1
            counts['changed_chinese_records'] += old.slots['zh_hans'].text != new.slots['zh_hans'].text
        counts['egpack'] += 1
    original_tables = {p.relative_to(original) for p in original.rglob('*.egpack')}
    staged_tables = {p.relative_to(root) for p in root.rglob('*.egpack')}
    if original_tables != staged_tables:
        raise ValueError(f'Table coverage differs: missing={original_tables-staged_tables}, extra={staged_tables-original_tables}')
    fontdir = Path('assets/data/gui/font')
    for name in ('Font.cfg', 'Font_en.cfg'):
        before = ET.parse(original / fontdir / name).getroot().find('FontParamList')
        after = ET.parse(root / fontdir / name).getroot().find('FontParamList')
        values = lambda rows: [{child.tag: child.text for child in row} for row in rows]
        if values(before) != values([r for r in after if r.findtext('Label') != 'sub']):
            raise ValueError(f'Native primary font changed: {name}')
        fallback = [r for r in after if r.findtext('Label') == 'sub']
        if len(fallback) != 1 or fallback[0].findtext('File') != 'NotoSansSC-500.ttf':
            raise ValueError(f'Unexpected save-summary fallback: {name}')
    cn = ET.parse(root / fontdir / 'Font_cn.cfg').getroot().find('FontParamList')
    faces = {r.findtext('Label'): r.findtext('File') for r in cn}
    expected = {'Message': 'BWCKKT-Bold.ttf', 'Speaker': 'MEBheiheiti.ttf', 'Common': 'AGE2UISansSC-Dash.otf', 'sub': 'AGE2FallbackSC-Dash.ttf'}
    candidate_config = candidate / fontdir / 'Font.cfg'
    if ET.tostring(ET.parse(candidate_config).getroot()) != ET.tostring(ET.parse(root / fontdir / 'Font_cn.cfg').getroot()):
        raise ValueError('Chinese font configuration differs from approved candidate')
    for role, name in expected.items():
        if faces.get(role, '').lower() != name.lower():
            raise ValueError(f'Wrong Chinese {role} font: {faces.get(role)}')
        if not (root / fontdir / faces[role]).is_file():
            raise ValueError(f'Missing Chinese font file: {faces[role]}')
    counts['native_language_fields_preserved'] = True
    # FreeType may use CFF widths even when hmtx looks correct. A raw absolute
    # width in a Type 2 charstring adds nominalWidthX a second time.
    from fontTools.ttLib import TTFont
    from fontTools.pens.boundsPen import BoundsPen
    with TTFont(root / fontdir / faces['Message']) as font, TTFont(candidate / fontdir / faces['Message']) as approved:
        cmap = font.getBestCmap()
        approved_cmap = approved.getBestCmap()
        for cp in (0xff0c, 0x3002, 0x3001):
            glyph = cmap[cp]
            if 'CFF ' in font:
                cs = font['CFF '].cff.topDictIndex[0].CharStrings[glyph]
                cs.draw(BoundsPen(None))
                if cs.width != font['hmtx'][glyph][0]:
                    raise ValueError(f'Inconsistent Chinese punctuation width: U+{cp:04X}')
            # The approved printed face has its own punctuation advances;
            # the old GenSeki-specific full-em assumption does not apply.
            if font['hmtx'][glyph] != approved['hmtx'][approved_cmap[cp]] or font['head'].unitsPerEm != approved['head'].unitsPerEm:
                raise ValueError(f'Punctuation differs from approved font: U+{cp:04X}')
    counts['punctuation_matches_approved_font'] = True
    counts['all_tables_current_candidate'] = True
    return dict(counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staging', type=Path, required=True)
    parser.add_argument('--originals', type=Path, required=True, help='Directory containing <game>/original')
    parser.add_argument('--candidates', type=Path, required=True, help='Directory containing <game>/root')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    report = {}
    for game in GAMES:
        report[game] = verify_game(args.staging / game, args.originals / game / 'original', args.candidates / game / 'root')
        print(game, report[game], flush=True)
    args.report.write_text(json.dumps({'checks': report, 'scope': 'Language isolation, table freshness/completeness, image naming and font configuration. Not full content/runtime acceptance.'}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()

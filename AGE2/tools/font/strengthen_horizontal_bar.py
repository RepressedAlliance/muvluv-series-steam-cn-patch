"""Build a renamed Chinese font variant with a more robust U+2015 stroke.

Only U+2015 is changed. Match its thickness to the face's existing U+2014,
preserving its horizontal metrics, width and vertical centre. This is a
font-side mitigation for thin-line sampling, not a renderer fix.
"""
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.ttGlyphPen import TTGlyphPen


def bounds(font, name):
    glyphs = font.getGlyphSet()
    pen = BoundsPen(glyphs)
    glyphs[name].draw(pen)
    return pen.bounds


def build(source: Path, destination: Path, family: str, postscript: str):
    font = TTFont(source, recalcTimestamp=False)
    cmap = font.getBestCmap()
    target, reference = cmap[0x2015], cmap[0x2014]
    assert [cp for cp, glyph in cmap.items() if glyph == target] == [0x2015]
    old_bounds, ref_bounds = bounds(font, target), bounds(font, reference)
    height = old_bounds[3] - old_bounds[1]
    thickness = ref_bounds[3] - ref_bounds[1]
    assert 0 < height < thickness <= font['head'].unitsPerEm * .12
    centre = (old_bounds[1] + old_bounds[3]) / 2
    scale = thickness / height
    transform = (1, 0, 0, scale, 0, centre * (1 - scale))
    glyphs = font.getGlyphSet()
    if 'CFF ' in font:
        top = font['CFF '].cff.topDictIndex[0]
        old = top.CharStrings[target]
        advance = font['hmtx'][target][0]
        pen = T2CharStringPen(advance - getattr(old.private, 'nominalWidthX', 0), glyphs)
        glyphs[target].draw(TransformPen(pen, transform))
        top.CharStrings[target] = pen.getCharString(private=old.private, globalSubrs=old.globalSubrs)
        font['CFF '].cff.fontNames = [postscript]
        top.FamilyName = family
        top.FullName = family + ' Regular'
    else:
        pen = TTGlyphPen(glyphs)
        glyphs[target].draw(TransformPen(pen, transform))
        # Rebuilt target has no old hint program forcing the thinner stroke.
        font['glyf'][target] = pen.glyph()

    style = 'Regular'
    names = {1: family, 2: style, 3: postscript + '-dash-r1',
             4: family + ' ' + style, 6: postscript, 16: family, 17: style}
    for record in font['name'].names:
        if record.nameID in names:
            record.string = names[record.nameID].encode(record.getEncoding())
    destination.parent.mkdir(parents=True, exist_ok=True)
    font.save(destination)
    font.close()

    # Check the saved file, including every unaffected outline and advance.
    with TTFont(source) as before, TTFont(destination) as after:
        assert before.getBestCmap() == after.getBestCmap()
        assert before.getGlyphOrder() == after.getGlyphOrder()
        assert before['hmtx'].metrics == after['hmtx'].metrics
        for tag in ('hhea', 'OS/2', 'vhea', 'vmtx'):
            if tag in before:
                assert before.getTableData(tag) == after.getTableData(tag), tag
        for name in before.getGlyphOrder():
            if name == target:
                continue
            if 'glyf' in before:
                assert before['glyf'][name].compile(before['glyf']) == after['glyf'][name].compile(after['glyf']), name
            else:
                a = before['CFF '].cff.topDictIndex[0].CharStrings[name]
                b = after['CFF '].cff.topDictIndex[0].CharStrings[name]
                a.compile(); b.compile()
                assert a.bytecode == b.bytecode, name
        new_bounds = bounds(after, target)
        assert new_bounds[0] == old_bounds[0] and new_bounds[2] == old_bounds[2]
        assert abs((new_bounds[1] + new_bounds[3]) / 2 - centre) < .51
        assert abs(new_bounds[3] - new_bounds[1] - thickness) < 1.01
    return {'source': str(source), 'output': str(destination), 'codepoint': 'U+2015',
            'before_bounds': old_bounds, 'after_bounds': new_bounds,
            'reference': 'U+2014 thickness', 'all_other_outlines_and_advances_unchanged': True}

"""Font roles for the shared four-position AGE2 language selector."""
import xml.etree.ElementTree as ET

LANGUAGE_TAGS = frozenset(('msg_langat', 'msg_langja', 'msg_langen', 'msg_langcn'))


def use_interface_font_for_language_choices(document: ET.Element) -> int:
    """Use the locale's Common face; leave speaker and message nodes untouched.

    The research selector originally borrowed Speaker while all Chinese roles
    used one font. That causes the choices to become serif when S8 is selected.
    Common resolves to the selected Noto face in Chinese and native UI fonts in
    Japanese/English. Font size and geometry remain the layout's own values.
    """
    changed = 0
    for node in document.iter('TextNode'):
        if node.findtext('Tag') not in LANGUAGE_TAGS:
            continue
        primary, fallback = node.find('FontName'), node.find('SubFontName')
        if primary is None or fallback is None:
            raise ValueError(f'Incomplete language font binding: {node.findtext("Tag")}')
        if (primary.text, fallback.text) != ('Common', 'sub'):
            primary.text, fallback.text = 'Common', 'sub'
            changed += 1
    return changed

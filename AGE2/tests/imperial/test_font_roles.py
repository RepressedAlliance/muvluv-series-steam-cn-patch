import unittest
import xml.etree.ElementTree as ET
from AGE2.tools.font.roles import use_interface_font_for_language_choices


class FontRoleTests(unittest.TestCase):
    def test_choices_use_ui_role_without_altering_story_fonts_or_sizes(self):
        doc = ET.fromstring('''<Document><TextNode><Tag>msg_langcn</Tag>
          <FontName>Speaker</FontName><SubFontName>speaker</SubFontName>
          <FontSize>18</FontSize><FontSizeEN>18</FontSizeEN></TextNode>
          <TextNode><Tag>single_sp0</Tag><FontName>Speaker</FontName>
          <SubFontName>sub</SubFontName><FontSize>36</FontSize></TextNode>
          <TextNode><Tag>single_msg0</Tag><FontName>Message</FontName>
          <SubFontName>sub</SubFontName><FontSize>36</FontSize></TextNode></Document>''')
        untouched = [ET.tostring(n) for n in list(doc)[1:]]
        self.assertEqual(use_interface_font_for_language_choices(doc), 1)
        self.assertEqual(doc[0].findtext('FontName'), 'Common')
        self.assertEqual(doc[0].findtext('SubFontName'), 'sub')
        self.assertEqual(doc[0].findtext('FontSize'), '18')
        self.assertEqual(doc[0].findtext('FontSizeEN'), '18')
        self.assertEqual([ET.tostring(n) for n in list(doc)[1:]], untouched)
        self.assertEqual(use_interface_font_for_language_choices(doc), 0)

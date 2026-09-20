"""Regressions for shared subtitle size and game-specific Chinese UI art."""
from pathlib import Path
import tempfile
import unittest
from PIL import Image, ImageDraw
from AGE2.tools.images.story_caption import ink_boxes, render_story_caption
from AGE2.tools.images.ui_zh import prefer_game_specific_chinese_textures, preserve_native_title_logo
from AGE2.tools.images.voice_label import render_voice_label
from AGE2.tools.images.caption_layout import caption_block

FONT = Path('C:/Windows/Fonts/msyhbd.ttc')


class SharedImageRenderingTests(unittest.TestCase):
    @unittest.skipUnless(FONT.exists(), 'Windows test font unavailable')
    def test_caption_whitespace_and_baselines_are_stable(self):
        plain, layout = caption_block(['AAAA','AAAA'], FONT, 20, line_pitch=28)
        padded, _ = caption_block(['  AAAA\u3000','\u3000AAAA  '], FONT, 20, line_pitch=28)
        self.assertEqual(plain.tobytes(), padded.tobytes())
        boxes=ink_boxes(plain)
        self.assertEqual(len(boxes),2)
        self.assertEqual(boxes[1][1]-boxes[0][1],28*4)
        self.assertEqual(layout['baseline_offsets'],[0,28])

    @unittest.skipUnless(FONT.exists(), 'Windows test font unavailable')
    def test_voice_labels_keep_size_and_reject_overflow_instead_of_shrinking(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td); native=root/'native.webp'
            source=Image.new('RGBA',(224,96))
            ImageDraw.Draw(source).rectangle((70,52,150,76),fill=(220,240,255,255))
            source.save(native,lossless=True)
            short=render_voice_label(native,root/'short.webp',FONT,'AA',font_size=22)
            long=render_voice_label(native,root/'long.webp',FONT,'AAAAAAAA',font_size=22)
            self.assertEqual(short['font_size'],long['font_size'])
            self.assertEqual(short['chinese_core'][3]-short['chinese_core'][1],
                             long['chinese_core'][3]-long['chinese_core'][1])
            with self.assertRaisesRegex(ValueError,'does not fit fixed'):
                render_voice_label(native,root/'overflow.webp',FONT,'A'*40,font_size=22)

    def test_title_logo_comes_from_own_original_not_legacy_chinese_bank(self):
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            original, candidate = folder/'original', folder/'candidate'
            rel = Path('assets/data_spec/gui/textures/title/01_title_000_ja.webp')
            source = original/rel
            source.parent.mkdir(parents=True)
            Image.new('RGBA', (20, 10), 'blue').save(source, lossless=True)
            wrong = candidate/rel.with_name('01_title_000_zh.webp')
            wrong.parent.mkdir(parents=True)
            Image.new('RGBA', (20, 10), 'orange').save(wrong, lossless=True)
            original_bytes = source.read_bytes()
            preserve_native_title_logo(original, candidate)
            self.assertEqual(wrong.read_bytes(), original_bytes)
            self.assertEqual(source.read_bytes(), original_bytes)
            self.assertFalse((candidate/rel).exists())

    @unittest.skipUnless(FONT.exists(), 'Windows test font unavailable')
    def test_short_and_long_lines_keep_equal_rendered_letter_height(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            template = root / 'native.webp'
            source = Image.new('RGBA', (400, 100))
            draw = ImageDraw.Draw(source)
            draw.rectangle((180, 20, 219, 35), fill='white')
            draw.rectangle((100, 60, 299, 75), fill='white')
            source.save(template, lossless=True)
            target = root / 'cn.webp'
            render_story_caption(template, 'AAAA|AAAAAAAA', FONT, target, font_size=20)
            with Image.open(target) as image:
                boxes = ink_boxes(image)
                self.assertEqual(image.size, source.size)
            self.assertEqual(len(boxes), 2)
            self.assertEqual(boxes[0][3] - boxes[0][1], boxes[1][3] - boxes[1][1])

    def test_specific_chinese_bank_wins_without_touching_original_languages(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            common = root / 'assets/data/gui/textures/main'
            specific = root / 'assets/data_spec/gui/textures/main'
            common.mkdir(parents=True)
            specific.mkdir(parents=True)
            for folder in (common, specific):
                for language in ('ja', 'en', 'zh'):
                    color = 'orange' if folder == specific else 'blue'
                    Image.new('RGBA', (20, 10), color).save(folder / f'title_{language}.webp', lossless=True)
            originals = {p: p.read_bytes() for folder in (common, specific)
                         for p in folder.iterdir() if not p.stem.endswith('_zh')}
            changes = prefer_game_specific_chinese_textures(root)
            self.assertEqual(len(changes), 1)
            self.assertEqual((common / 'title_zh.webp').read_bytes(),
                             (specific / 'title_zh.webp').read_bytes())
            self.assertTrue(all(p.read_bytes() == data for p, data in originals.items()))
            self.assertEqual(prefer_game_specific_chinese_textures(root), [])


if __name__ == '__main__':
    unittest.main()

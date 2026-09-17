import unittest
from PIL import Image, ImageDraw
from AGE2.tools.images.ui_zh import subtitle_masks


class SubtitleMasksTest(unittest.TestCase):
    def test_descender_and_icon_survive_below_subtitle_cut(self):
        alpha = Image.new('L', (90, 60))
        draw = ImageDraw.Draw(alpha)
        draw.rectangle((5, 5, 14, 50), fill=255)  # tall icon
        draw.rectangle((65, 5, 72, 39), fill=255)  # English descender
        draw.rectangle((25, 32, 50, 47), fill=255)  # Japanese caption
        keep, erase, protected, removed = subtitle_masks(alpha, 30)
        self.assertEqual(keep.getpixel((68, 39)), 255)
        self.assertEqual(removed.getpixel((68, 39)), 0)
        self.assertEqual(protected.getpixel((5, 50)), 255)
        self.assertEqual(erase.getpixel((25, 32)), 255)
        self.assertEqual(removed.getpixel((25, 32)), 255)

    def test_translucent_playback_icon_is_retained(self):
        alpha = Image.new('L', (90, 60))
        draw = ImageDraw.Draw(alpha)
        draw.rectangle((35, 3, 50, 20), fill=150)
        draw.rectangle((20, 40, 65, 50), fill=255)
        keep, erase, protected, removed = subtitle_masks(alpha, 30)
        self.assertEqual(protected.getpixel((35, 3)), 255)
        self.assertEqual(removed.getpixel((20, 40)), 255)


if __name__ == '__main__':
    unittest.main()

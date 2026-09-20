"""Place an approved 1920x1080 notice on the native AGE2 texture canvases."""
import argparse
from pathlib import Path
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preview', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    image = Image.open(args.preview).convert('RGB')
    if image.size != (1920, 1080):
        raise ValueError('Expected the approved 1920x1080 page')
    folder = args.root / 'assets/data/gui/textures/boot'
    folder.mkdir(parents=True, exist_ok=True)
    # Native landscape textures extend 180 px beyond the 16:9 safe area.
    # Pad rather than stretch the approved glyphs and spacing.
    for name, canvas, content in [
        ('00_note000_zh.webp', (1920, 1440), image),
        ('00_v_note000_zh.webp', (1440, 1920), image.resize((1080, 608), Image.Resampling.LANCZOS)),
    ]:
        result = Image.new('RGB', canvas, image.getpixel((0, 0)))
        result.paste(content, ((canvas[0]-content.width)//2, (canvas[1]-content.height)//2))
        result.save(folder / name, lossless=True, method=6)
        assert Image.open(folder / name).size == canvas
    assert Image.open(folder / '00_note000_zh.webp').crop((0,180,1920,1260)).tobytes() == image.tobytes()


if __name__ == '__main__':
    main()

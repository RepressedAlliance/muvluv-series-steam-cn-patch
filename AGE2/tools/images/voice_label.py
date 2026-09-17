"""Render Chinese voice-option labels with one fixed size per native UI family."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont


def render_voice_label(template: Path, output: Path, font_path: Path,
                       text: str, *, font_size: int = 22) -> dict:
    if '\n' in text:
        raise ValueError('Voice labels must retain the native single-line layout')
    with Image.open(template) as image:
        source = image.convert('RGBA')
    alpha = source.getchannel('A')
    core = alpha.point(lambda v: 255 if v > 240 else 0).getbbox()
    if core is None:
        raise ValueError(f'No native lettering: {template}')
    scale = 4
    font = ImageFont.truetype(str(font_path), font_size * scale)
    box = font.getbbox(text)
    width, height = (box[2]-box[0])/scale, (box[3]-box[1])/scale
    if width > source.width-4 or height > source.height-12:
        raise ValueError(f'Label does not fit fixed {font_size}px: {text}')
    x = (source.width-width)/2
    y = (core[1]+core[3]-height)/2
    mask = Image.new('L', (source.width*scale, source.height*scale))
    ImageDraw.Draw(mask).text((round(x*scale-box[0]), round(y*scale-box[1])),
                             text, font=font, fill=255)
    mask = mask.resize(source.size, Image.Resampling.LANCZOS)
    pixels = list(source.getdata())
    ink = sorted((p[:3] for p in pixels if p[3]>240), key=sum)
    fill = ink[len(ink)*3//4]
    halo = [p[:3] for p in pixels if 24<p[3]<100]
    glow = tuple(sorted(p[i] for p in halo)[len(halo)//2] for i in range(3)) if halo else fill
    result = Image.new('RGBA', source.size)
    for color, radius, strength in ((glow, 2.5, 1.4), (fill, .7, .55), (fill, 0, 1)):
        layer = Image.new('RGBA', source.size, color+(0,))
        layer.putalpha(mask.filter(ImageFilter.GaussianBlur(radius)).point(lambda v:min(255,round(v*strength))))
        result.alpha_composite(layer)
    output.parent.mkdir(parents=True, exist_ok=True)
    result.save(output, lossless=True, method=6)
    return dict(text=text, font_size=font_size, size=source.size, native_core=core,
                chinese_core=mask.point(lambda v:255 if v>240 else 0).getbbox())

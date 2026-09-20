"""Deterministic baseline spacing and visible-ink centering for text overlays."""
from PIL import Image, ImageDraw, ImageFont


def caption_block(lines, font_path, font_size, *, line_pitch=None, scale=4,
                  fill=(255, 255, 255, 255), stroke=1,
                  stroke_fill=(0, 0, 0, 160)):
    lines = [line.strip() for line in lines]
    if not lines or any(not line for line in lines):
        raise ValueError('Caption contains an empty line')
    pitch = line_pitch or round(font_size * 1.4)
    font = ImageFont.truetype(str(font_path), font_size * scale)
    layers = []
    for line in lines:
        scratch = Image.new('RGBA', (1, 1))
        bounds = ImageDraw.Draw(scratch).textbbox((0, 0), line, font=font,
                    anchor='ls', stroke_width=stroke * scale)
        layer = Image.new('RGBA', (bounds[2]-bounds[0]+4*scale,
                                  bounds[3]-bounds[1]+4*scale))
        ImageDraw.Draw(layer).text((2*scale-bounds[0], 2*scale-bounds[1]), line,
            font=font, anchor='ls', fill=fill, stroke_width=stroke*scale,
            stroke_fill=stroke_fill)
        ink = layer.getchannel('A').getbbox()
        layers.append((layer.crop(ink), bounds[1]+ink[1]-2*scale))
    top = min(offset+i*pitch*scale for i, (_, offset) in enumerate(layers))
    bottom = max(offset+i*pitch*scale+layer.height for i, (layer, offset) in enumerate(layers))
    width = max(layer.width for layer, _ in layers)
    result = Image.new('RGBA', (width, bottom-top))
    for i, (layer, offset) in enumerate(layers):
        result.alpha_composite(layer, ((width-layer.width)//2, offset+i*pitch*scale-top))
    return result, {'lines': lines, 'font_size':font_size, 'line_pitch':pitch,
                    'alignment':'visible_ink_center', 'baseline_offsets':[i*pitch for i in range(len(lines))]}

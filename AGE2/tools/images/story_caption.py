"""Render text-only story overlays using native canvas, ink boxes and color."""
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFont
try:
    from .caption_layout import caption_block
except ImportError:  # Standalone image builders import this module directly.
    from caption_layout import caption_block


def ink_boxes(source: Image.Image) -> list[tuple[int, int, int, int]]:
    rgba = source.convert('RGBA')
    mask = ImageChops.multiply(rgba.getchannel('A'), rgba.convert('L'))
    mask = mask.point(lambda value: 255 if value > 80 else 0)
    bands = []
    for y in range(mask.height):
        if not mask.crop((0, y, mask.width, y + 1)).getbbox():
            continue
        if not bands or y - bands[-1][1] > 3:
            bands.append([y, y])
        else:
            bands[-1][1] = y
    boxes = []
    for top, bottom in bands:
        box = mask.crop((0, top, mask.width, bottom + 1)).getbbox()
        boxes.append((box[0], top, box[2], bottom + 1))
    return boxes


def render_story_caption(template: Path, text: str, font: Path, output: Path,
                         *, color_template: Path | None = None,
                         font_size: int = 20, ruby_font_size: int = 10) -> dict:
    """The caller must supply one translated line per native ink band.

    All normal lines use the same explicit point size, across the whole series.
    Native ink width is an alignment reference, not a reason to shrink a line.
    A smaller native ruby band can be given its own translated annotation.
    This is for text-only overlays, never mixed background/artwork images.
    """
    source = Image.open(template).convert('RGBA')
    lines = [line.strip() for line in text.split('|')]
    boxes = ink_boxes(source)
    if len(lines) != len(boxes) or any(not line for line in lines):
        raise ValueError(f'Caption lines differ from native ink bands: {template}: {len(lines)} / {boxes}')
    sample = Image.open(color_template).convert('RGBA') if color_template else source
    colors = sorted((p for p in sample.getdata() if p[3] > 240 and min(p[:3]) > 80), key=lambda p:sum(p[:3]))
    if not colors:
        raise ValueError(f'No native text color: {template}')
    color = colors[len(colors)*3//4][:3]+(255,)
    scale = 4
    result = Image.new('RGBA', (source.width*scale, source.height*scale))
    draw = ImageDraw.Draw(result)
    placements = []
    normal_height = max(bottom-top for left, top, right, bottom in boxes)
    if all(bottom-top > normal_height * 0.6 for left, top, right, bottom in boxes):
        block, layout = caption_block(lines, font, font_size, scale=scale, fill=color)
        left=min(b[0] for b in boxes);right=max(b[2] for b in boxes)
        top=min(b[1] for b in boxes);bottom=max(b[3] for b in boxes)
        x=round((left+right)*scale/2-block.width/2)
        y=round((top+bottom)*scale/2-block.height/2)
        if x<0 or y<0 or x+block.width>result.width or y+block.height>result.height:
            raise ValueError(f'Caption exceeds canvas: {template}')
        result.alpha_composite(block,(x,y))
        result=result.resize(source.size,Image.Resampling.LANCZOS)
        output.parent.mkdir(parents=True,exist_ok=True)
        result.save(output,format='WEBP',lossless=True,method=6)
        return {'template':str(template),'size':source.size,'color':color,
                'placements':[{'text':line,'font_size':font_size,'is_ruby':False} for line in lines],
                'source_boxes':boxes,'rendered_boxes':ink_boxes(result),'layout':layout}
    for line, (left, top, right, bottom) in zip(lines, boxes):
        is_ruby = bottom-top <= normal_height * 0.6
        size = ruby_font_size if is_ruby else font_size
        face = ImageFont.truetype(str(font), size*scale)
        box = draw.textbbox((0, 0), line, font=face)
        width, height = box[2]-box[0], box[3]-box[1]
        x = round((left+right)*scale/2-width/2-box[0])
        y = round((top+bottom)*scale/2-height/2-box[1])
        if x+box[0]-scale < 0 or x+box[2]+scale > source.width*scale:
            raise ValueError(f'Caption exceeds canvas at the shared font size: {line}')
        if y+box[1]-scale < 0 or y+box[3]+scale > source.height*scale:
            raise ValueError(f'Caption exceeds canvas vertically: {line}')
        draw.text((x, y), line, font=face, fill=color,
                  stroke_width=scale, stroke_fill=(0, 0, 0, 160))
        placements.append({'text':line,'font_size':size,'is_ruby':is_ruby,'native_box':[left,top,right,bottom]})
    result=result.resize(source.size,Image.Resampling.LANCZOS)
    output.parent.mkdir(parents=True,exist_ok=True)
    result.save(output,format='WEBP',lossless=True,method=6)
    with Image.open(output) as saved:
        assert saved.size == source.size
    return {'template':str(template),'size':source.size,'color':color,'placements':placements,
            'source_boxes':boxes,'rendered_boxes':ink_boxes(result)}

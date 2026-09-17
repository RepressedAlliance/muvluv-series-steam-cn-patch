"""Chinese sublabels on native AGE2 menu textures; preserve the English art.

The caller supplies legally extracted JP templates and a Chinese font. Outputs
are separate _zh slots. No resizing of a texture canvas or of its English art.
"""
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


def native_caption_layers(source, japanese_core, erased, mask):
    """Transfer the caption's measured ink colour and outward halo profile.

    Measure only Japanese-owned pixels, never neighbouring English or icons.
    Distances are pixel rings around opaque strokes; no fixed blue/orange tint
    or universal glow multiplier is added. This is a raster approximation.
    """
    import numpy as np
    rgba=np.asarray(source)
    owned=np.asarray(erased)>0
    core=(np.asarray(japanese_core)>0)&owned
    pixels=rgba[core]
    fill=tuple(int(v) for v in np.median(pixels[:,:3],axis=0))
    native=japanese_core.copy()
    chinese=mask.point(lambda v:255 if v>240 else 0)
    halo=Image.new('RGBA',source.size)
    profile=[]
    for distance in range(1,25):
        nd=native.filter(ImageFilter.MaxFilter(3))
        cd=chinese.filter(ImageFilter.MaxFilter(3))
        nr=(np.asarray(nd)>np.asarray(native))&owned
        cr=ImageChops.subtract(cd,chinese)
        native,chinese=nd,cd
        samples=rgba[nr]
        if not len(samples):continue
        alpha=int(round(float(samples[:,3].mean())))
        visible=samples[samples[:,3]>4]
        colour=tuple(int(v) for v in np.median(visible[:,:3],axis=0)) if len(visible) else fill
        if alpha:
            layer=Image.new('RGBA',source.size,colour+(alpha,))
            halo.paste(layer,(0,0),cr)
        profile.append({'distance':distance,'alpha':alpha,'rgb':colour})
    # Smooth ring discretisation, without introducing an extra bloom layer.
    halo=halo.filter(ImageFilter.GaussianBlur(.35))
    ink=Image.new('RGBA',source.size,fill+(0,));ink.putalpha(mask)
    return halo,ink,fill,profile


def subtitle_masks(alpha, cut):
    """Separate complete ink components, then assign their surrounding bloom.

    A horizontal cut cannot distinguish a descender from subtitle lettering.
    Components anchored above the subtitle line include English and icons.
    """
    width,height=alpha.size
    ink=alpha.point(lambda v:255 if v>240 else 0)
    pending=set((x,y) for y in range(height) for x in range(width) if ink.getpixel((x,y)))
    keep=Image.new('L',alpha.size);erase=Image.new('L',alpha.size)
    kp,ep=keep.load(),erase.load()
    while pending:
        start=pending.pop();stack=[start];points=[]
        while stack:
            x,y=stack.pop();points.append((x,y))
            for point in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if point in pending:pending.remove(point);stack.append(point)
        target=kp if min(y for x,y in points)<cut else ep
        for x,y in points:target[x,y]=255
    if not keep.getbbox():
        # Playback icons can be intentionally translucent while the caption
        # is opaque. Their upper silhouette is still protected artwork.
        keep=alpha.point(lambda v:255 if v>100 else 0)
        ImageDraw.Draw(keep).rectangle((0,cut,width,height),fill=0)
    if not erase.getbbox() or not keep.getbbox():
        raise ValueError('Cannot separate subtitle ink from English/icon')
    # Nearest-core growth protects English descenders and their bloom even
    # when they extend below the old rectangular erase boundary.
    occupied=ImageChops.lighter(keep,erase)
    keep_region=keep.copy();erase_region=erase.copy()
    for _ in range(32):
        kg=keep_region.filter(ImageFilter.MaxFilter(3))
        eg=erase_region.filter(ImageFilter.MaxFilter(3))
        kn=ImageChops.subtract(kg,occupied)
        en=ImageChops.subtract(ImageChops.subtract(eg,occupied),kn)
        keep_region=ImageChops.lighter(keep_region,kn)
        erase_region=ImageChops.lighter(erase_region,en)
        occupied=ImageChops.lighter(keep_region,erase_region)
    return keep,erase,keep_region,erase_region


def preserve_native_title_logo(original: Path, root: Path) -> list[dict]:
    """Keep each work's own title mark when constructing its Chinese bank.

    Legacy loose Japanese overrides are not authoritative for unlocalized logos.
    The reviewed Japanese pack resource retains the work identity and geometry.
    """
    import shutil
    folder = Path('assets/data_spec/gui/textures/title')
    choices = [folder/name for name in ('01_title_000_ja.webp', 't2_title000_ja.webp')
               if (original/folder/name).is_file()]
    if not choices:
        raise ValueError(f'No native title mark found: {original}')
    changes = []
    for relative in choices:
        source = original / relative
        target = root / relative.with_name(relative.name.replace('_ja.webp', '_zh.webp'))
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        changes.append({'source': relative.as_posix(),
                        'target': target.relative_to(root).as_posix(),
                        'decision': 'Preserve this work’s original title mark.'})
    return changes


def prefer_game_specific_chinese_textures(root: Path) -> list[dict]:
    """Apply the game's native texture-bank precedence to new Chinese keys.

    A loose common-bank _zh file can win before the engine probes data_spec.
    Mirror only Chinese variants when both banks provide the same logical key.
    Original Japanese and English resources are never rewritten.
    """
    import shutil
    common = root / 'assets/data/gui/textures'
    specific = root / 'assets/data_spec/gui/textures'
    changed = []
    for source in sorted(specific.rglob('*_zh.webp')):
        target = common / source.relative_to(specific)
        if not target.exists() or target.read_bytes() == source.read_bytes():
            continue
        with Image.open(source) as a, Image.open(target) as b:
            if a.size != b.size:
                raise ValueError(f'Chinese texture-bank canvas differs: {source} / {target}')
        shutil.copyfile(source, target)
        changed.append({'source': source.relative_to(root).as_posix(),
                        'target': target.relative_to(root).as_posix()})
    return changed

COPY = {
    'title/01_bt080': 'CG 鉴赏',
    'title/01_bt081': 'CG 鉴赏',
    'backlog/15_title000': '对话记录',
    'chapter/16_title000': '章节选择',
    'control/14_title000': '播放控制',
    'gallery/09_title000': '鉴赏插画',
    'Jukebox/16_title000': '音乐鉴赏',
    'load/04_title000': '读取存档',
    'main/13_title000': '主菜单',
    'option/11_title000': '更改各项设置',
    'option/11_title001': '游戏设置\n高级设置',
    'save/06_title000': '保存当前进度',
    'theater/22_title000': '影片鉴赏',
    'clearlist/21_title000': '通关记录',
    'common/11_back000': '返回',
    'control/14_btn020': '停止自动', 'control/14_btn021': '自动播放',
    'control/14_btn030': '停止快进', 'control/14_btn031': '快进',
    'control/14_btn050': '跳过已读', 'control/14_btn051': '跳过已读',
}
for stem, text in {'02':'保存进度','03':'读取存档','04':'游戏设置',
                   '05':'返回标题','06':'章节选择'}.items():
    for state in '01': COPY[f'main/13_bt{stem}{state}'] = text
for stem, text in {'00':'从头开始游戏','01':'从存档继续','02':'鉴赏画廊','03':'更改各项设置',
                   '04':'访问官网','05':'特别内容','06':'鉴赏插画','07':'章节选择',
                   '09':'通关记录','10':'返回'}.items():
    for state in '01': COPY[f'title/01_bt{stem}{state}'] = text

def bands(alpha, threshold=240):
    mask = alpha.point(lambda v: 255 if v > threshold else 0)
    rows = [y for y in range(mask.height) if mask.crop((0,y,mask.width,y+1)).getbbox()]
    result=[]
    for y in rows:
        if not result or y-result[-1][1]>0: result.append([y,y+1])
        else: result[-1][1]=y+1
    return result

def render(template: Path, output: Path, font_path: Path, text: str, key: str, *, font_weight=450):
    source=Image.open(template).convert('RGBA'); alpha=source.getchannel('A')
    geometry_alpha=alpha
    # Hover artwork has a stronger bloom. It must not change the text's
    # measured size or anchor when the pointer enters the same button.
    if key.startswith(('title/01_bt','main/13_bt')) and key.endswith('1'):
        normal=template.with_name(key.rsplit('/',1)[1][:-1]+'0_ja.webp')
        if normal.exists():
            layout=Image.open(normal).convert('RGBA')
            if layout.size!=source.size: raise ValueError(f'Hover canvas differs: {template}')
            geometry_alpha=layout.getchannel('A')
    spans=bands(geometry_alpha)
    if key=='common/11_back000':
        cut=round(source.height*.58); left=round(source.width*.29)
    elif key.startswith('main/13_bt'):
        cut=round(source.height*.62); left=round(source.width*.16)
    elif key.startswith('control/14_btn'):
        cut=round(source.height*.69); left=0
    elif key.startswith('title/01_bt'):
        cut=round(source.height*.58); left=0
    else:
        if len(spans)<2:
            raise ValueError(f'No separate Japanese sublabel: {template}: {spans}')
        # The first band is the original English title or playback icon.
        cut=(spans[0][1]+spans[1][0])//2; left=0
    # Measure opaque lettering, not the glow: including the glow made the
    # Chinese glyphs substantially larger and heavier than the Japanese art.
    english_core,japanese_core,protected,erased=subtitle_masks(geometry_alpha,cut)
    # Use complete Japanese components, not a percentage-based left edge.
    x0,y0,x1,y1=japanese_core.getbbox()
    left=x0
    region=geometry_alpha.crop((left,cut,source.width,source.height))
    box=(0,y0-cut,x1-left,y1-cut)
    if not box: raise ValueError(f'Empty sublabel: {template}')
    scale=4; margin=3
    max_w=min(source.width-x0-margin, max(x1-x0, len(max(text.splitlines(),key=len))*14))
    max_h=y1-y0
    measure=ImageDraw.Draw(Image.new('L',(1,1)))
    for size in range(max_h*2,7,-1):
        font=ImageFont.truetype(str(font_path),size*scale)
        try:
            axes=font.get_variation_axes()
        except OSError:
            axes=[]
        if axes:
            font.set_variation_by_axes([font_weight if a['name']==b'Weight' else a['default'] for a in axes])
        bbox=measure.multiline_textbbox((0,0),text,font=font,spacing=4*scale,align='center')
        tw,th=(bbox[2]-bbox[0])/scale,(bbox[3]-bbox[1])/scale
        if tw<=max_w and th<=max_h:break
    else: raise ValueError(f'Cannot fit sublabel {text}: {template}')
    # Headers and action rows retain their native left edge. Main Menu has a
    # right-aligned subtitle; title-screen and playback buttons are centered.
    alignment='left'
    if key=='main/13_title000': alignment='right'
    elif key.startswith(('title/01_bt','control/14_btn')): alignment='center'
    x={'left':x0,'right':x1-tw,'center':(x0+x1-tw)/2}[alignment]
    y=(y0+y1-th)/2
    x=max(margin,min(source.width-tw-margin,x))
    mask=Image.new('L',(source.width*scale,source.height*scale))
    ImageDraw.Draw(mask).multiline_text((round(x*scale-bbox[0]),round(y*scale-bbox[1])),text,
        font=font,fill=255,spacing=4*scale,align='center')
    mask=mask.resize(source.size,Image.Resampling.LANCZOS)
    haze,ink,fill,profile=native_caption_layers(source,japanese_core,erased,mask)
    result=source.copy()
    result.paste((0,0,0,0),(0,0),erased)
    for layer in (haze,ink):
        layer.putalpha(ImageChops.subtract(layer.getchannel('A'),protected))
    result.alpha_composite(haze);result.alpha_composite(ink)
    assert result.size==source.size
    difference=ImageChops.difference(result,source)
    assert all(ImageChops.multiply(channel,protected).getbbox() is None for channel in difference.split())
    output.parent.mkdir(parents=True,exist_ok=True);result.save(output,lossless=True,method=6)
    return {'size':source.size,'cut':cut,'jp_box':[x0,y0,x1,y1],
            'cn_box':mask.getbbox(),'font_size':size,'font_weight':font_weight,
            'alignment':alignment,'ink_rgb':fill,'native_halo_profile':profile,
            'text':text,'english_core_unchanged':True,
            'preservation':'complete English/icon components and nearest bloom',
            'erased_box':erased.getbbox()}

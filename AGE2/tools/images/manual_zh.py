"""Render bilingual AGE2 manuals with native frames and English heading art."""
from PIL import Image, ImageDraw, ImageFont

def render(template,output,font):
    """Render a complete, seam-free inner panel within the native outer frame."""
    source=Image.open(template).convert('RGBA')
    if source.size!=(1128,912):raise ValueError(f'Unsupported manual geometry: {template}')
    warm='data_spec' in template.parts
    mobile='_sp_' in template.name
    canvas=source.copy()
    # The native border remains; the entire inner panel is code-rendered, so no
    # old text shadows or repair rectangles can survive around translated text.
    d=ImageDraw.Draw(canvas)
    bg=(22,15,13,255) if warm else (13,32,49,255)
    card=(44,23,16,255) if warm else (16,44,64,255)
    accent=(249,160,78,255) if warm else (145,215,241,255)
    rule=(96,58,38,255) if warm else (46,83,106,255)
    d.rounded_rectangle((94,55,1034,860),radius=8,fill=bg)
    f=ImageFont.truetype(str(font),30);small=ImageFont.truetype(str(font),25)
    headings=[('main/13_title000_ja.webp','主菜单'),('backlog/15_title000_ja.webp','对话记录'),
              ('control/14_title000_ja.webp','播放控制'),(None,'显示／隐藏文本')]
    pc=[[("mouse","鼠标右键"),("→","方向键"),("〈","点击画面右侧按钮")],
        [("wheel","向上滚动鼠标滚轮"),("←","方向键"),("〉","点击画面左侧按钮")],
        [("↓","方向键"),("∧","点击画面下方按钮")],
        [("Esc","Esc 键"),("Space","空格键")]]
    sp=[[("←","从右向左滑动")],[("→","从左向右滑动")],[("↑","从下向上滑动")],[("2","双指轻点")]]
    sections=[(65,286),(299,535),(548,700),(714,854)] if not mobile else [(90,266),(280,450),(466,635),(649,825)]
    for i,((top,bottom),(asset,label),rows) in enumerate(zip(sections,headings,sp if mobile else pc)):
        if asset:
            im=Image.open(template.parent.parent/asset).convert('RGBA')
            cut=[74,78,74][i];im=im.crop((0,0,im.width,cut));box=im.getchannel('A').getbbox();im=im.crop(box)
            im.thumbnail((288,49),Image.Resampling.LANCZOS);canvas.alpha_composite(im,(114,top+13))
            d.text((115,top+67),label,font=small,fill=accent)
        else:
            d.text((115,top+12),label,font=small,fill=accent)
            d.text((115,top+52),'仅限横屏模式',font=ImageFont.truetype(str(font),22),fill=accent)
        rowh=(bottom-top-10)//len(rows)
        for j,(icon,text) in enumerate(rows):
            y=top+j*rowh
            d.rounded_rectangle((451,y,1014,y+rowh-8),radius=5,fill=card)
            cy=y+(rowh-8)//2
            if icon in ('mouse','wheel'):
                d.rounded_rectangle((485,cy-20,516,cy+21),radius=12,outline=accent,width=2)
                d.line((500,cy-19,500,cy-3),fill=accent,width=2)
                d.line((486,cy-3,515,cy-3),fill=accent,width=2)
                if icon=='wheel':d.polygon([(497,cy-26),(500,cy-32),(503,cy-26)],fill=accent)
            else:
                d.rounded_rectangle((474,cy-20,530,cy+20),radius=5,outline=rule,width=2)
                fi=ImageFont.truetype(str(font),16 if icon=='Space' else 22)
                d.text((502,cy),icon,font=fi,fill=accent,anchor='mm')
            d.text((566,cy),text,font=f,fill=(237,243,246,255),anchor='lm')
        if i<3:d.line((113,bottom+5,1014,bottom+5),fill=rule,width=1)
    output.parent.mkdir(parents=True,exist_ok=True);canvas.save(output,lossless=True,method=6)
    return {'size':canvas.size,'text_blocks':sum(map(len,sp if mobile else pc))+4,'native_outer_frame':True}

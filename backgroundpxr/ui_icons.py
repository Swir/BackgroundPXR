from __future__ import annotations

from PIL import Image, ImageDraw


def make_icon(name: str, size: int = 24, color: str = "#8EDFFF") -> Image.Image:
    s = max(16, int(size)); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = color; w = max(2, s // 11); m = s * .18; cx = cy = s / 2
    if name == "plus":
        d.line((cx, m, cx, s-m), fill=c, width=w); d.line((m, cy, s-m, cy), fill=c, width=w)
    elif name == "folder":
        d.rounded_rectangle((m, s*.34, s-m, s*.78), radius=3, outline=c, width=w); d.line((m+2,s*.34,s*.42,s*.34,s*.49,s*.26,s*.70,s*.26),fill=c,width=w)
    elif name in {"zoom_in","zoom_out"}:
        d.ellipse((m,m,s*.62,s*.62), outline=c, width=w); d.line((s*.59,s*.59,s*.84,s*.84),fill=c,width=w); d.line((s*.29,s*.42,s*.51,s*.42),fill=c,width=w)
        if name == "zoom_in": d.line((s*.40,s*.31,s*.40,s*.53),fill=c,width=w)
    elif name == "fit":
        for a,b,c2,d2 in [(m,m,s*.38,m),(m,m,m,s*.38),(s-m,m,s*.62,m),(s-m,m,s-m,s*.38),(m,s-m,s*.38,s-m),(m,s-m,m,s*.62),(s-m,s-m,s*.62,s-m),(s-m,s-m,s-m,s*.62)]: d.line((a,b,c2,d2),fill=c,width=w)
    elif name == "pan":
        d.ellipse((s*.34,s*.38,s*.65,s*.70), outline=c, width=w); d.line((s*.48,s*.38,s*.48,s*.14),fill=c,width=w); d.line((s*.37,s*.43,s*.29,s*.25),fill=c,width=w); d.line((s*.60,s*.43,s*.70,s*.28),fill=c,width=w); d.line((s*.62,s*.63,s*.76,s*.55),fill=c,width=w)
    elif name == "brush":
        d.line((s*.25,s*.78,s*.67,s*.36),fill=c,width=w+1); d.polygon([(s*.63,s*.34),(s*.78,s*.18),(s*.85,s*.25),(s*.69,s*.40)],fill=c); d.ellipse((s*.15,s*.70,s*.35,s*.88),fill=c)
    elif name == "eraser":
        d.polygon([(s*.20,s*.64),(s*.55,s*.24),(s*.82,s*.47),(s*.48,s*.82)],outline=c); d.line((s*.36,s*.70,s*.67,s*.35),fill=c,width=w)
    elif name == "undo":
        d.line([(s*.32,s*.28),(s*.16,s*.43),(s*.32,s*.57)],fill=c,width=w); d.arc((s*.23,s*.27,s*.82,s*.80),start=205,end=35,fill=c,width=w)
    elif name == "redo":
        d.line([(s*.68,s*.28),(s*.84,s*.43),(s*.68,s*.57)],fill=c,width=w); d.arc((s*.18,s*.27,s*.77,s*.80),start=145,end=335,fill=c,width=w)
    elif name == "magic":
        d.line((s*.25,s*.78,s*.70,s*.33),fill=c,width=w); d.polygon([(s*.72,s*.15),(s*.76,s*.25),(s*.86,s*.29),(s*.76,s*.33),(s*.72,s*.43),(s*.68,s*.33),(s*.58,s*.29),(s*.68,s*.25)],fill=c)
    elif name == "export":
        d.rounded_rectangle((s*.20,s*.46,s*.80,s*.84),radius=3,outline=c,width=w); d.line((cx,s*.65,cx,s*.14),fill=c,width=w); d.line((s*.36,s*.30,cx,s*.14,s*.64,s*.30),fill=c,width=w)
    elif name == "image":
        d.rounded_rectangle((m,m,s-m,s-m),radius=3,outline=c,width=w); d.ellipse((s*.60,s*.28,s*.72,s*.40),fill=c); d.line((s*.25,s*.68,s*.42,s*.50,s*.53,s*.61,s*.64,s*.47,s*.78,s*.68),fill=c,width=w)
    else:
        d.ellipse((m,m,s-m,s-m),outline=c,width=w)
    return im

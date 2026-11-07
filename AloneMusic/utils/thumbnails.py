#
# Copyright (C) 2021-2022 by TheAloneteam@Github, < https://github.com/TheAloneTeam >.
#
# This file is part of < https://github.com/TheAloneTeam/AloneMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TheAloneTeam/AloneMusic/blob/master/LICENSE >
#
# All rights reserved.
import asyncio, os, re, httpx
from io import BytesIO
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from py_yt import VideosSearch

# ================= FONTS =================
def load_fonts():
    try:
        return {
            "title": ImageFont.truetype("AloneMusic/assets/font.ttf", 40),
            "small": ImageFont.truetype("AloneMusic/assets/cfont.ttf", 22),
        }
    except:
        return {
            "title": ImageFont.load_default(),
            "small": ImageFont.load_default(),
        }

FONTS = load_fonts()

# ================= CLEAN =================
def clean_text(text, limit=40):
    return text[:limit] + "..." if len(text) > limit else text

# ================= FETCH =================
async def fetch_image(url):
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(url, timeout=5)
            return Image.open(BytesIO(r.content)).convert("RGBA")
        except:
            return Image.new("RGBA",(1280,720),(30,30,30))

# ================= BIG IMAGE =================
def make_big(img):
    return img.resize((380,380), Image.Resampling.LANCZOS)

# ================= UI =================
async def add_ui(bg):
    bg = bg.resize((1280,720))
    bg = bg.filter(ImageFilter.GaussianBlur(45))

    box = (200,80,1080,660)
    region = bg.crop(box)

    dark = ImageEnhance.Brightness(region).enhance(0.35)

    mask = Image.new("L", dark.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0,0,*dark.size),60,fill=255)

    bg.paste(dark, box, mask)

    try:
        controls = Image.open("AloneMusic/assets/controls.png").convert("RGBA")
        controls = controls.resize((520,160))
        bg.paste(controls,(380,500),controls)
    except:
        pass

    return bg

# ================= MAIN =================
async def get_thumb(videoid: str):
    if not re.match(r"^[a-zA-Z0-9_-]{11}$", videoid):
        return ""

    os.makedirs("database/photos", exist_ok=True)
    path = f"database/photos/{videoid}.png"

    try:
        data = (await VideosSearch(f"https://youtube.com/watch?v={videoid}", limit=1).next())["result"][0]

        title = clean_text(data["title"])
        duration = data.get("duration", "0:00")
        thumb = data["thumbnails"][0]["url"].split("?")[0]

    except:
        title, duration = "Unknown", "0:00"
        thumb = ""

    img = await fetch_image(thumb)
    bg = await add_ui(img)

    cover = make_big(img)

    # 🔥 BIG IMAGE (video style)
    bg.paste(cover, (260,150), cover)

    draw = ImageDraw.Draw(bg)

    # 🎵 TITLE ONLY
    draw.text(
        (680,220),
        title,
        fill=(255,255,255),
        font=FONTS["title"]
    )

    # ⏱ RIGHT DURATION (fixed position)
    draw.text(
        (930,510),  # 👈 neeche + buttons ke upar
        duration,
        fill=(200,200,200),
        font=FONTS["small"]
    )

    # ✨ FINAL LOOK
    bg = ImageEnhance.Contrast(bg).enhance(1.3)
    bg = ImageEnhance.Color(bg).enhance(1.4)

    overlay = Image.new("RGBA", bg.size, (255,255,255,20))
    bg = Image.alpha_composite(bg, overlay)

    await asyncio.to_thread(bg.save, path)

    return path

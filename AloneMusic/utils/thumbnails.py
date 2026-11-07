#
# Copyright (C) 2021-2022 by TheAloneteam@Github, < https://github.com/TheAloneTeam >.
#
# This file is part of < https://github.com/TheAloneTeam/AloneMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TheAloneTeam/AloneMusic/blob/master/LICENSE >
#
# All rights reserved.
import asyncio
import os
import re
import aiohttp
from io import BytesIO
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from py_yt import VideosSearch

# ================= FONTS =================
def load_fonts():
    try:
        return {
            "title": ImageFont.truetype("AloneMusic/assets/font.ttf", 46),
            "channel": ImageFont.truetype("AloneMusic/assets/cfont.ttf", 30),
            "small": ImageFont.truetype("AloneMusic/assets/cfont.ttf", 26),
        }
    except Exception:
        return {
            "title": ImageFont.load_default(),
            "channel": ImageFont.load_default(),
            "small": ImageFont.load_default(),
        }

FONTS = load_fonts()

# ================= CLEAN =================
def clean_text(text, limit=28):
    if not text:
        return ""
    text = text.strip()
    return text[:limit] + "..." if len(text) > limit else text

# ================= FETCH =================
async def fetch_image(url):
    if not url:
        return Image.new("RGBA", (1920, 1080), (30, 30, 30))
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return Image.open(BytesIO(data)).convert("RGBA")
    except Exception:
        pass
    return Image.new("RGBA", (1920, 1080), (30, 30, 30))

# ================= ROUNDED COVER =================
def make_cover(img, size=(270, 270), radius=25):
    # Center crop into square and resize
    cover = ImageOps.fit(img, size, Image.Resampling.LANCZOS)
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *size), radius=radius, fill=255)
    rounded = Image.new("RGBA", size, (0, 0, 0, 0))
    rounded.paste(cover, (0, 0), mask)
    return rounded

# ================= UI =================
async def add_ui(bg):
    # Canvas size 1920x1080
    bg = ImageOps.fit(bg, (1920, 1080), Image.Resampling.LANCZOS)
    bg = bg.filter(ImageFilter.GaussianBlur(60))

    # Center card (size 1000x700, radius 60)
    card_box = (460, 190, 1460, 890)
    region = bg.crop(card_box)

    dark = ImageEnhance.Brightness(region).enhance(0.28)

    mask = Image.new("L", (1000, 700), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, 1000, 700), radius=60, fill=255)

    bg.paste(dark, (460, 190), mask)

    # Controls placed at (502, 600)
    try:
        controls = Image.open("AloneMusic/assets/controls.png").convert("RGBA")
        bg.paste(controls, (502, 600), controls)
    except Exception:
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

        title = clean_text(data.get("title", "Unknown"))
        channel = clean_text(data.get("channel", {}).get("name", "") if isinstance(data.get("channel"), dict) else "", limit=35)
        duration = data.get("duration", "0:00")
        thumb = data["thumbnails"][0]["url"].split("?")[0]
    except Exception:
        title, channel, duration = "Unknown", "", "0:00"
        thumb = ""

    img = await fetch_image(thumb)
    bg = await add_ui(img)

    cover = make_cover(img, size=(270, 270), radius=25)
    bg.paste(cover, (535, 275), cover)

    draw = ImageDraw.Draw(bg)

    # Title
    draw.text(
        (836, 355),
        title,
        fill=(255, 255, 255),
        font=FONTS["title"],
    )

    # Channel Name
    if channel:
        draw.text(
            (839, 420),
            channel,
            fill=(220, 220, 220),
            font=FONTS["channel"],
        )

    # Duration
    draw.text(
        (1343, 625),
        duration,
        fill=(230, 230, 230),
        font=FONTS["small"],
    )

    # Final Look enhancements
    bg = ImageEnhance.Contrast(bg).enhance(1.15)
    bg = ImageEnhance.Color(bg).enhance(1.2)

    await asyncio.to_thread(bg.save, path)

    return path

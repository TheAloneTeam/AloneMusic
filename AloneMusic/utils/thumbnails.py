#
# Copyright (C) 2021-2022 by TheAloneteam@Github, < https://github.com/TheAloneTeam >.
#
# This file is part of < https://github.com/TheAloneTeam/AloneMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TheAloneTeam/AloneMusic/blob/master/LICENSE >
#
# All rights reserved.

import os
import re
import random
import aiohttp
import aiofiles
import traceback

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from youtubesearchpython.__future__ import VideosSearch


def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage


def truncate(text):
    list = text.split(" ")
    text1, text2 = "", ""
    for i in list:
        if len(text1) + len(i) < 30:
            text1 += " " + i
        elif len(text2) + len(i) < 30:
            text2 += " " + i
    return [text1.strip(), text2.strip()]


async def get_thumb(videoid: str):
    # if os.path.isfile(f"cache/{videoid}.png"):
    #    return f"cache/{videoid}.png"

    url = f"https://www.youtube.com/watch?v={videoid}"
    try:
        results = VideosSearch(url, limit=1)
        for result in (await results.next())["result"]:
            try:
                title = result["title"]
                title = re.sub("\W+", " ", title)
                title = title.title()
            except:
                title = "Unsupported Title"
            try:
                duration = result["duration"]
            except:
                duration = "Unknown Mins"
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            try:
                views = result["viewCount"]["short"]
            except:
                views = "Unknown Views"
            try:
                channel = result["channel"]["name"]
            except:
                channel = "Unknown Channel"

        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(f"cache/thumb{videoid}.png", mode="wb")
                    await f.write(await resp.read())
                    await f.close()

        icons = Image.open("AloneMusic/assets/icons.png")
        youtube = Image.open(f"cache/thumb{videoid}.png")
        image1 = changeImageSize(1280, 720, youtube)
        image2 = image1.convert("RGBA")
        background = image2.filter(filter=ImageFilter.BoxBlur(20))
        enhancer = ImageEnhance.Brightness(background)
        background = enhancer.enhance(0.6)

        Xcenter = youtube.width / 2
        Ycenter = youtube.height / 2
        x1 = Xcenter - 250
        y1 = Ycenter - 250
        x2 = Xcenter + 250
        y2 = Ycenter + 250
        rand = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        logo = youtube.crop((x1, y1, x2, y2))
        logo.thumbnail((370, 370), Image.ANTIALIAS)
        logo = ImageOps.expand(logo, border=17, fill=rand)
        background.paste(logo, (100, 150))

        draw = ImageDraw.Draw(background)
        arial = ImageFont.truetype("AloneMusic/assets/font2.ttf", 30)
        font = ImageFont.truetype("AloneMusic/assets/font.ttf", 30)
        tfont = ImageFont.truetype("AloneMusic/assets/font3.ttf", 45)

        stitle = truncate(title)
        draw.text(
            (565, 180),
            stitle[0],
            (255, 255, 255),
            font=tfont,
        )
        draw.text(
            (565, 230),
            stitle[1],
            (255, 255, 255),
            font=tfont,
        )
        draw.text(
            (565, 320),
            f"{channel} | {views[:23]}",
            (255, 255, 255),
            font=arial,
        )
        draw.line(
            [(565, 385), (1130, 385)],
            fill="white",
            width=8,
            joint="curve",
        )
        draw.line(
            [(565, 385), (999, 385)],
            fill=rand,
            width=8,
            joint="curve",
        )
        draw.ellipse(
            [(999, 375), (1020, 395)],
            outline=rand,
            fill=rand,
            width=15,
        )
        draw.text(
            (565, 400),
            "00:00",
            (255, 255, 255),
            font=arial,
        )
        draw.text(
            (1080, 400),
            f"{duration[:23]}",
            (255, 255, 255),
            font=arial,
        )
        picons = icons.resize((580, 62))
        background.paste(picons, (565, 450), picons)

        try:
            os.remove(f"cache/thumb{videoid}.png")
        except:
            pass
        tpath = f"cache/{videoid}.png"
        background.save(tpath)
        return tpath

    except:
        traceback.print_exc()
        return None

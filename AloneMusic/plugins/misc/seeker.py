#
# Copyright (C) 2021-2022 by TheAloneteam@Github, < https://github.com/TheAloneTeam >.
#
# This file is part of < https://github.com/TheAloneTeam/AloneMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TheAloneTeam/AloneMusic/blob/master/LICENSE >
#
# All rights reserved.

import asyncio

from AloneMusic import app
from AloneMusic.core.call import upcoming_message
from AloneMusic.misc import db
from AloneMusic.utils.database import get_active_chats, get_autoplay, is_music_playing


async def timer():
    while not await asyncio.sleep(1):
        active_chats = await get_active_chats()
        for chat_id in active_chats:
            if not await is_music_playing(chat_id):
                continue
            playing = db.get(chat_id)
            if not playing:
                continue
            duration = int(playing[0]["seconds"])
            if duration == 0:
                continue
            if db[chat_id][0]["played"] >= duration:
                continue
            db[chat_id][0]["played"] += 1

            played = db[chat_id][0]["played"]
            if duration - played == 10 and not db[chat_id][0].get("notified_10s"):
                db[chat_id][0]["notified_10s"] = True
                next_title = None
                if len(playing) > 1:
                    next_title = playing[1].get("title")
                elif await get_autoplay(chat_id):
                    artist_name = playing[0].get("artist")
                    if not artist_name:
                        t_title = playing[0].get("title", "")
                        if " - " in t_title:
                            artist_name = t_title.split(" - ")[0].strip()
                        elif " " in t_title:
                            artist_name = t_title.split()[0].strip()
                        else:
                            artist_name = t_title.strip()
                    next_title = f"Autoplay ({artist_name})" if artist_name else "Autoplay Track"

                if next_title:
                    try:
                        orig_cid = playing[0].get("chat_id", chat_id)
                        msg = await app.send_message(
                            orig_cid,
                            f"⌛ <b>Nᴇxᴛ Sᴏɴɢ Pʟᴀʏɪɴɢ Iɴ 10s :</b>\n\n🎵 <b>{next_title}</b>",
                        )
                        upcoming_message[chat_id] = msg
                    except Exception:
                        pass


try:
    asyncio.create_task(timer())
except RuntimeError:
    pass

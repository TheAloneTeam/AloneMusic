#
# Copyright (C) 2021-2022 by TheAloneteam@Github, < https://github.com/TheAloneTeam >.
#
# This file is part of < https://github.com/TheAloneTeam/AloneMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TheAloneTeam/AloneMusic/blob/master/LICENSE >
#
# All rights reserved.

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, Message

import config
from AloneMusic import YouTube, app
from AloneMusic.core.call import Alone, autoplay_in_progress, fetch_artist_tracks
from AloneMusic.misc import db
from AloneMusic.utils.database import get_autoplay, get_loop, set_autoplay
from AloneMusic.utils.decorators import AdminRightsCheck
from AloneMusic.utils.inline import close_markup, stream_markup
from AloneMusic.utils.stream.autoclear import auto_clean
from AloneMusic.utils.stream.queue import put_queue
from AloneMusic.utils.thumbnails import get_thumb
from config import BANNED_USERS


async def check_autoplay_on_skip(chat_id: int, popped: dict):
    is_atp = await get_autoplay(chat_id)
    if is_atp and not autoplay_in_progress.get(chat_id):
        artist_name = popped.get("artist") if isinstance(popped, dict) else None
        if not artist_name and isinstance(popped, dict):
            t_title = popped.get("title", "")
            if " - " in t_title:
                artist_name = t_title.split(" - ")[0].strip()
            elif " " in t_title:
                artist_name = t_title.split()[0].strip()
            else:
                artist_name = t_title.strip()
        if artist_name:
            artist_tracks = await fetch_artist_tracks(artist_name)
            if artist_tracks:
                autoplay_in_progress[chat_id] = True
                user_by = popped.get("by", "Autoplay") if isinstance(popped, dict) else "Autoplay"
                user_id = popped.get("user_id", 0) if isinstance(popped, dict) else 0
                orig_cid = popped.get("chat_id", chat_id) if isinstance(popped, dict) else chat_id
                for trk in artist_tracks:
                    vidid = trk.get("vidid")
                    title = trk.get("title")
                    dur_min = trk.get("duration_min", "03:00")
                    await put_queue(
                        chat_id,
                        orig_cid,
                        f"vid_{vidid}",
                        title,
                        dur_min,
                        user_by,
                        vidid,
                        user_id,
                        "audio",
                        artist=artist_name,
                    )
                return True
    elif autoplay_in_progress.get(chat_id):
        autoplay_in_progress[chat_id] = False
        await set_autoplay(chat_id, False)
    return False


async def delete_old_message(chat_id: int):
    try:
        old = db.get(chat_id, [{}])[0].get("mystic")
        if old:
            await old.delete()
    except:
        pass


@app.on_message(
    filters.command(["skip", "cskip", "next", "cnext"]) & filters.group & ~BANNED_USERS
)
@AdminRightsCheck
async def skip(cli, message: Message, _, chat_id):
    await delete_old_message(chat_id)
    if not len(message.command) < 2:
        loop = await get_loop(chat_id)
        if loop != 0:
            return await message.reply_text(_["admin_8"])
        state = message.text.split(None, 1)[1].strip()
        if state.isnumeric():
            state = int(state)
            check = db.get(chat_id)
            if check:
                count = len(check)
                if count > 2:
                    count = int(count - 1)
                    if 1 <= state <= count:
                        for x in range(state):
                            popped = None
                            try:
                                popped = check.pop(0)
                            except:
                                return await message.reply_text(_["admin_12"])
                            if popped:
                                await auto_clean(popped)
                            if not check:
                                atp_added = await check_autoplay_on_skip(chat_id, popped)
                                if not atp_added:
                                    try:
                                        await message.reply_text(
                                            text=_["admin_6"].format(
                                                message.from_user.mention,
                                                message.chat.title,
                                            ),
                                            reply_markup=close_markup(_),
                                        )
                                        await Alone.stop_stream(chat_id)
                                    except:
                                        return
                                    break
                    else:
                        return await message.reply_text(_["admin_11"].format(count))
                else:
                    return await message.reply_text(_["admin_10"])
            else:
                return await message.reply_text(_["queue_2"])
        else:
            return await message.reply_text(_["admin_9"])
    else:
        check = db.get(chat_id)
        popped = None
        try:
            popped = check.pop(0)
            if popped:
                await auto_clean(popped)
            if not check:
                atp_added = await check_autoplay_on_skip(chat_id, popped)
                if not atp_added:
                    await message.reply_text(
                        text=_["admin_6"].format(
                            message.from_user.mention, message.chat.title
                        ),
                        reply_markup=close_markup(_),
                    )
                    try:
                        return await Alone.stop_stream(chat_id)
                    except:
                        return
        except:
            try:
                await message.reply_text(
                    text=_["admin_6"].format(
                        message.from_user.mention, message.chat.title
                    ),
                    reply_markup=close_markup(_),
                )
                return await Alone.stop_stream(chat_id)
            except:
                return
    queued = check[0]["file"]
    title = (check[0]["title"]).title()
    user = check[0]["by"]
    streamtype = check[0]["streamtype"]
    videoid = check[0]["vidid"]
    status = True if str(streamtype) == "video" else None
    db[chat_id][0]["played"] = 0
    exis = (check[0]).get("old_dur")
    if exis:
        db[chat_id][0]["dur"] = exis
        db[chat_id][0]["seconds"] = check[0]["old_second"]
        db[chat_id][0]["speed_path"] = None
        db[chat_id][0]["speed"] = 1.0
    if "live_" in queued:
        n, link = await YouTube.video(videoid, True)
        if n == 0:
            return await message.reply_text(_["admin_7"].format(title))
        try:
            image = await YouTube.thumbnail(videoid, True)
        except:
            image = None
        try:
            await Alone.skip_stream(chat_id, link, video=status, image=image)
        except:
            return await message.reply_text(_["call_6"])
        button = stream_markup(_, chat_id)
        await delete_old_message(chat_id)
        cap = _["stream_1"].format(
            f"https://t.me/{app.username}?start=info_{videoid}",
            title[:23],
            check[0]["dur"],
            user,
        )
        img = await get_thumb(videoid)
        run = await message.reply_photo(
            photo=img,
            has_spoiler=True,
            caption=cap,
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "tg"
    elif "vid_" in queued:
        mystic = await message.reply_text(_["call_7"], disable_web_page_preview=True)
        try:
            file_path, _direct = await YouTube.download(
                videoid,
                mystic,
                videoid=True,
                video=status,
            )
        except:
            return await mystic.edit_text(_["call_6"])
        try:
            image = await YouTube.thumbnail(videoid, True)
        except:
            image = None
        try:
            await Alone.skip_stream(chat_id, file_path, video=status, image=image)
        except:
            return await mystic.edit_text(_["call_6"])
        button = stream_markup(_, chat_id)
        await delete_old_message(chat_id)
        cap = _["stream_1"].format(
            f"https://t.me/{app.username}?start=info_{videoid}",
            title[:23],
            check[0]["dur"],
            user,
        )
        img = await get_thumb(videoid)
        run = await message.reply_photo(
            photo=img,
            has_spoiler=True,
            caption=cap,
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "stream"
        await mystic.delete()
    elif "index_" in queued:
        try:
            await Alone.skip_stream(chat_id, videoid, video=status)
        except:
            return await message.reply_text(_["call_6"])
        button = stream_markup(_, chat_id)
        await delete_old_message(chat_id)
        run = await message.reply_photo(
            photo=config.STREAM_IMG_URL,
            has_spoiler=True,
            caption=_["stream_2"].format(user),
            reply_markup=InlineKeyboardMarkup(button),
        )
        db[chat_id][0]["mystic"] = run
        db[chat_id][0]["markup"] = "tg"
    else:
        if videoid == "telegram" or videoid == "soundcloud":
            image = None
        else:
            try:
                image = await YouTube.thumbnail(videoid, True)
            except:
                image = None
        try:
            await Alone.skip_stream(chat_id, queued, video=status, image=image)
        except:
            return await message.reply_text(_["call_6"])
        if videoid == "telegram":
            button = stream_markup(_, chat_id)
            await delete_old_message(chat_id)
            run = await message.reply_photo(
                photo=(
                    config.TELEGRAM_AUDIO_URL
                    if str(streamtype) == "audio"
                    else config.TELEGRAM_VIDEO_URL
                ),
                caption=_["stream_1"].format(
                    config.SUPPORT_CHAT, title[:23], check[0]["dur"], user
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
        elif videoid == "soundcloud":
            button = stream_markup(_, chat_id)
            await delete_old_message(chat_id)
            run = await message.reply_photo(
                photo=(
                    config.SOUNCLOUD_IMG_URL
                    if str(streamtype) == "audio"
                    else config.TELEGRAM_VIDEO_URL
                ),
                caption=_["stream_1"].format(
                    config.SUPPORT_CHAT, title[:23], check[0]["dur"], user
                ),
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
        else:
            button = stream_markup(_, chat_id)
            await delete_old_message(chat_id)
            cap = _["stream_1"].format(
                f"https://t.me/{app.username}?start=info_{videoid}",
                title[:23],
                check[0]["dur"],
                user,
            )
            img = await get_thumb(videoid)
            run = await message.reply_photo(
                photo=img,
                has_spoiler=True,
                caption=cap,
                reply_markup=InlineKeyboardMarkup(button),
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"

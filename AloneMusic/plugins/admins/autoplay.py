#
# Copyright (C) 2021-2022 by TheAloneteam@Github, < https://github.com/TheAloneTeam >.
#
# This file is part of < https://github.com/TheAloneTeam/AloneMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TheAloneTeam/AloneMusic/blob/master/LICENSE >
#
# All rights reserved.

from pyrogram import filters
from pyrogram.types import Message

from AloneMusic import app
from AloneMusic.utils.database import get_autoplay, set_autoplay
from AloneMusic.utils.decorators import AdminRightsCheck
from AloneMusic.utils.inline import close_markup
from config import BANNED_USERS


@app.on_message(filters.command(["autoplay", "cautoplay"]) & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def autoplay_command(cli, message: Message, _, chat_id):
    usage = "<b>ᴇxᴀᴍᴘʟᴇ :</b>\n\n/autoplay <code>enable</code>/<code>disable</code> (or <code>on</code>/<code>off</code>)"
    if len(message.command) != 2:
        current_state = await get_autoplay(chat_id)
        status_text = "ENABLED (ON)" if current_state else "DISABLED (OFF)"
        return await message.reply_text(
            f"» <b>Aᴜᴛᴏᴘʟᴀʏ Sᴛᴀᴛᴇ</b> ɪs ᴄᴜʀʀᴇɴᴛʟʏ <b>{status_text}</b>.\n\n{usage}",
            reply_markup=close_markup(_),
        )
    state = message.text.split(None, 1)[1].strip().lower()
    if state in ["enable", "on", "yes", "true"]:
        await set_autoplay(chat_id, True)
        return await message.reply_text(
            text=f"» <b>Aᴜᴛᴏᴘʟᴀʏ</b> ʜᴀs ʙᴇᴇɴ <b>ᴇɴᴀʙʟᴇᴅ</b> (ON) ʙʏ : {message.from_user.mention}.",
            reply_markup=close_markup(_),
        )
    elif state in ["disable", "off", "no", "false"]:
        await set_autoplay(chat_id, False)
        return await message.reply_text(
            text=f"» <b>Aᴜᴛᴏᴘʟᴀʏ</b> ʜᴀs ʙᴇᴇɴ <b>ᴅɪsᴀʙʟᴇᴅ</b> (OFF) ʙʏ : {message.from_user.mention}.",
            reply_markup=close_markup(_),
        )
    else:
        return await message.reply_text(usage)

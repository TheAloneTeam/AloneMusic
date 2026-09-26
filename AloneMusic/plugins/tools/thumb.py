#
# Copyright (C) 2021-2022 by TheAloneteam@Github, < https://github.com/TheAloneTeam >.
#
# This file is part of < https://github.com/TheAloneTeam/AloneMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TheAloneTeam/AloneMusic/blob/master/LICENSE >
#
# All rights reserved.

from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from AloneMusic import app
from AloneMusic.misc import SUDOERS
from AloneMusic.utils.database import (
    disable_allthumbnail,
    disable_thumbnail,
    enable_allthumbnail,
    enable_thumbnail,
    is_allthumbnail_enabled,
    is_nonadmin_chat,
    is_thumbnail_enabled,
)
from AloneMusic.utils.decorators.admins import AdminActual
from AloneMusic.utils.decorators.language import languageCB
from config import BANNED_USERS, adminlist


def thumb_markup(is_enabled: bool):
    status_text = "✨ Enable" if is_enabled else "❌ Disable"
    buttons = [
        [
            InlineKeyboardButton(
                text=f"Thumbnail : {status_text}",
                callback_data="toggle_thumb_state",
            )
        ],
        [
            InlineKeyboardButton(text="Close", callback_data="close")
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def allthumb_markup(is_enabled: bool):
    status_text = "✨ Enable" if is_enabled else "❌ Disable"
    buttons = [
        [
            InlineKeyboardButton(
                text=f"All Thumbnails : {status_text}",
                callback_data="toggle_allthumb_state",
            )
        ],
        [
            InlineKeyboardButton(text="Close", callback_data="close")
        ]
    ]
    return InlineKeyboardMarkup(buttons)


@app.on_message(
    (filters.command(["thumb", "thumbnail"]) | filters.regex(r"^(thumb|thumbnail)$"))
    & filters.group
    & ~BANNED_USERS
)
@AdminActual
async def thumb_cmd(client, message: Message, _):
    chat_id = message.chat.id
    if len(message.command) > 1:
        state = message.command[1].lower()
        if state in ["on", "enable"]:
            await enable_thumbnail(chat_id)
            return await message.reply_text("» Playback thumbnail has been **Enabled**.")
        elif state in ["off", "disable"]:
            await disable_thumbnail(chat_id)
            return await message.reply_text("» Playback thumbnail has been **Disabled**.")

    is_enabled = await is_thumbnail_enabled(chat_id)
    text = (
        "<b><u>Playback Thumbnail Settings</u></b>\n\n"
        "Here you can enable or disable play command thumbnail images."
    )
    await message.reply_text(text, reply_markup=thumb_markup(is_enabled))


@app.on_message(
    (filters.command(["allthumb", "allthumbnail"]) | filters.regex(r"^(allthumb|allthumbnail)$"))
    & ~BANNED_USERS
)
async def allthumb_cmd(client, message: Message):
    if message.from_user.id != config.OWNER_ID:
        return await message.reply_text("» Only Bot Owner can use this command.")

    chat_id = message.chat.id
    if len(message.command) > 1:
        state = message.command[1].lower()
        if state in ["on", "enable"]:
            await enable_allthumbnail(chat_id)
            return await message.reply_text("» All bot photo thumbnails have been **Enabled**.")
        elif state in ["off", "disable"]:
            await disable_allthumbnail(chat_id)
            return await message.reply_text("» All bot photo thumbnails have been **Disabled**.")

    is_enabled = await is_allthumbnail_enabled(chat_id)
    text = (
        "<b><u>All Bot Thumbnails Settings</u></b>\n\n"
        "Here you can enable or disable all bot photo messages (start, ping, etc.)."
    )
    await message.reply_text(text, reply_markup=allthumb_markup(is_enabled))


@app.on_callback_query(filters.regex("toggle_thumb_state") & ~BANNED_USERS)
@languageCB
async def toggle_thumb_cb(client, CallbackQuery, _):
    chat_id = CallbackQuery.message.chat.id
    is_non_admin = await is_nonadmin_chat(chat_id)
    if not is_non_admin and CallbackQuery.from_user.id not in SUDOERS:
        admins = adminlist.get(chat_id)
        if not admins or CallbackQuery.from_user.id not in admins:
            return await CallbackQuery.answer(_["admin_14"], show_alert=True)

    is_enabled = await is_thumbnail_enabled(chat_id)
    if is_enabled:
        await disable_thumbnail(chat_id)
        await CallbackQuery.answer("Playback thumbnail disabled.", show_alert=True)
    else:
        await enable_thumbnail(chat_id)
        await CallbackQuery.answer("Playback thumbnail enabled.", show_alert=True)

    new_state = await is_thumbnail_enabled(chat_id)
    try:
        await CallbackQuery.edit_message_reply_markup(
            reply_markup=thumb_markup(new_state)
        )
    except Exception:
        pass


@app.on_callback_query(filters.regex(r"^THUMB_MORE\|") & ~BANNED_USERS)
@languageCB
async def thumb_more_cb(client, CallbackQuery, _):
    chat_id = int(CallbackQuery.data.split("|")[1])
    is_enabled = await is_thumbnail_enabled(chat_id)
    status_btn = "✨ ON" if is_enabled else "❌ OFF"
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text="Thumbnail", callback_data="thumb_text_noop"),
                InlineKeyboardButton(text=status_btn, callback_data=f"THUMB_TOGGLE_MORE|{chat_id}"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Back", callback_data=f"THUMB_BACK|{chat_id}"),
            ],
        ]
    )
    try:
        await CallbackQuery.edit_message_reply_markup(reply_markup=buttons)
    except Exception:
        pass


@app.on_callback_query(filters.regex(r"^THUMB_TOGGLE_MORE\|") & ~BANNED_USERS)
@languageCB
async def thumb_toggle_more_cb(client, CallbackQuery, _):
    chat_id = int(CallbackQuery.data.split("|")[1])
    is_non_admin = await is_nonadmin_chat(chat_id)
    if not is_non_admin and CallbackQuery.from_user.id not in SUDOERS:
        admins = adminlist.get(chat_id)
        if not admins or CallbackQuery.from_user.id not in admins:
            return await CallbackQuery.answer(_["admin_14"], show_alert=True)

    is_enabled = await is_thumbnail_enabled(chat_id)
    if is_enabled:
        await disable_thumbnail(chat_id)
        await CallbackQuery.answer("Playback thumbnail disabled.", show_alert=True)
    else:
        await enable_thumbnail(chat_id)
        await CallbackQuery.answer("Playback thumbnail enabled.", show_alert=True)

    new_state = await is_thumbnail_enabled(chat_id)
    status_btn = "✨ ON" if new_state else "❌ OFF"
    buttons = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(text="Thumbnail", callback_data="thumb_text_noop"),
                InlineKeyboardButton(text=status_btn, callback_data=f"THUMB_TOGGLE_MORE|{chat_id}"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Back", callback_data=f"THUMB_BACK|{chat_id}"),
            ],
        ]
    )
    try:
        await CallbackQuery.edit_message_reply_markup(reply_markup=buttons)
    except Exception:
        pass


@app.on_callback_query(filters.regex(r"^THUMB_BACK\|") & ~BANNED_USERS)
@languageCB
async def thumb_back_cb(client, CallbackQuery, _):
    from AloneMusic.utils.inline.play import stream_markup
    chat_id = int(CallbackQuery.data.split("|")[1])
    button = stream_markup(_, chat_id)
    try:
        await CallbackQuery.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(button))
    except Exception:
        pass


@app.on_callback_query(filters.regex("thumb_text_noop") & ~BANNED_USERS)
async def thumb_text_noop_cb(client, CallbackQuery):
    try:
        await CallbackQuery.answer("Thumbnail Settings", show_alert=False)
    except Exception:
        pass


@app.on_callback_query(filters.regex("toggle_allthumb_state") & ~BANNED_USERS)
async def toggle_allthumb_cb(client, CallbackQuery):
    if CallbackQuery.from_user.id != config.OWNER_ID:
        return await CallbackQuery.answer("Only Bot Owner can toggle this.", show_alert=True)

    chat_id = CallbackQuery.message.chat.id
    is_enabled = await is_allthumbnail_enabled(chat_id)
    if is_enabled:
        await disable_allthumbnail(chat_id)
        await CallbackQuery.answer("All bot photo thumbnails disabled.", show_alert=True)
    else:
        await enable_allthumbnail(chat_id)
        await CallbackQuery.answer("All bot photo thumbnails enabled.", show_alert=True)

    new_state = await is_allthumbnail_enabled(chat_id)
    try:
        await CallbackQuery.edit_message_reply_markup(
            reply_markup=allthumb_markup(new_state)
        )
    except Exception:
        pass

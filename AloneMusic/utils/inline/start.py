#
# Copyright (C) 2021-2022 by TheAloneteam@Github, < https://github.com/TheAloneTeam >.
#
# This file is part of < https://github.com/TheAloneTeam/AloneMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TheAloneTeam/AloneMusic/blob/master/LICENSE >
#
# All rights reserved.

from pyrogram.types import InlineKeyboardButton

import config
from AloneMusic import app


def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"], url=f"https://t.me/{app.username}?startgroup=true"
            ),
            InlineKeyboardButton(text=_["S_B_2"], url=config.SUPPORT_CHAT),
        ],
    ]
    return buttons


def private_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text="⚡ Add Me to Your Group",
                url=f"https://t.me/{app.username}?startgroup=true",
            )
        ],
        [
            InlineKeyboardButton(
                text="❓ Help & Commands",
                callback_data="settings_back_helper",
            ),
        ],
        [
            InlineKeyboardButton(
                text="📢 Updates",
                url=config.SUPPORT_CHANNEL,
            ),
            InlineKeyboardButton(
                text="💬 Support",
                url=config.SUPPORT_CHAT,
            ),
        ],
        [
            InlineKeyboardButton(
                text="🌐 Language",
                callback_data="LG",
            ),
            InlineKeyboardButton(
                text="🐙 Source Code",
                url=config.UPSTREAM_REPO,
            ),
        ],
    ]
    return buttons

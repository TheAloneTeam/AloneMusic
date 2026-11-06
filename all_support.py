# Copyright (C) 2026 by Kartike Mishra, < https://github.com/meowkingm >.
# Consolidated AloneAPI SDK client module.
# Re-exports AllSupport, AloneAPI, UniversalAPI, and default instance from all_support.

from AloneMusic.platforms.AllSupport import (
    API_KEY,
    API_URL,
    DEFAULT_API_KEY,
    DEFAULT_API_URL,
    AllSupport,
    AloneAPI,
    UniversalAPI,
    all_support,
)

__all__ = [
    "AllSupport",
    "AloneAPI",
    "UniversalAPI",
    "all_support",
    "API_URL",
    "API_KEY",
    "DEFAULT_API_URL",
    "DEFAULT_API_KEY",
]

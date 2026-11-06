#
# Copyright (C) 2021-2022 by TheAloneteam@Github, < https://github.com/TheAloneTeam >.
# This file is part of < https://github.com/TheAloneTeam/AloneMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TheAloneTeam/AloneMusic/blob/master/LICENSE >
#
# All rights reserved.

# Re-export from root all_platforms.py
try:
    from all_platforms import API_KEY, API_URL, DEFAULT_API_KEY, DEFAULT_API_URL
except Exception:
    import os
    API_URL = (
        os.getenv("API_URL")
        or os.getenv("ALONE_API_URL")
        or os.getenv("RITESH_API_URL")
        or "https://api.riteshyt.in"
    ).rstrip("/")
    API_KEY = (
        os.getenv("API_KEY")
        or os.getenv("ALONE_API_KEY")
        or os.getenv("RITESH_API_KEY")
        or ""
    )
    DEFAULT_API_URL = API_URL
    DEFAULT_API_KEY = API_KEY

__all__ = ["API_URL", "API_KEY", "DEFAULT_API_URL", "DEFAULT_API_KEY"]

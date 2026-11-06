# Copyright (C) 2026 by Kartike Mishra, < https://github.com/meowkingm >.
# Platform wrapper for Boomplay (BoomplayAPI).
# All rights reserved.

import re
from typing import Any, Dict, List, Optional, Tuple
from AloneMusic.platforms.AllSupport import all_support


class BoomplayAPI:
    def __init__(self):
        self.regex = r"boomplay\.com"
        self.name = "Boomplay"
        self.base = "https://www.boomplay.com/"

    async def valid(self, link: str) -> bool:
        return bool(re.search(self.regex, str(link), re.IGNORECASE))

    async def download_track(self, link: str, chat_id: Optional[int] = None, *args, **kwargs) -> Optional[str]:
        return all_support.get_stream_url(link, dl_type="audio")

    async def download(
        self,
        link: str,
        mystic=None,
        video: bool = False,
        videoid: Optional[str] = None,
        songaudio: bool = False,
        songvideo: bool = False,
        *args,
        **kwargs,
    ) -> Tuple[Optional[str], bool]:
        target = videoid or link
        dl_type = "video" if (video or songvideo) else "audio"
        stream_link = all_support.get_stream_url(target, dl_type=dl_type)
        return stream_link, False

    async def track(self, link: str) -> Tuple[Dict[str, Any], Optional[str]]:
        return await all_support.track(link)

    async def playlist(self, url: str, limit: int = 20) -> Tuple[List[str], str]:
        return await all_support.playlist(url, limit=limit)

    async def album(self, url: str, limit: int = 20) -> Tuple[List[str], str]:
        return await all_support.album(url, limit=limit)

    async def artist(self, url: str, limit: int = 20) -> Tuple[List[str], str]:
        return await all_support.artist(url, limit=limit)


Boomplay = BoomplayAPI()

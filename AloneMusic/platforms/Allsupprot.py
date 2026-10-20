# Copyright (C) 2021-2026 by TheAloneteam@Github, < https://github.com/TheAloneTeam >.
# This file is part of < https://github.com/TheAloneTeam/AloneMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TheAloneTeam/AloneMusic/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
import logging
import os
import re
import urllib.parse
from typing import Any

import httpx
from Apple import Apple
from Spotify import Spotify, _safe_videos_search
from Youtube import YouTube

LOGGER = logging.getLogger(__name__)

API_URL = os.getenv("API_URL", "https://api.riteshyt.in").rstrip("/")
API_KEY = os.getenv("API_KEY", "riteshfree9f664e9f2b0a4d5a85a35738")

PLATFORM_PATTERNS = {
    "youtube": r"(?:youtube\.com|youtu\.be)",
    "spotify": r"(?:spotify\.com)",
    "applemusic": r"(?:music\.apple\.com|itunes\.apple\.com)",
    "jiosaavn": r"(?:jiosaavn\.com|saavn\.com)",
    "instagram": r"(?:instagram\.com|instagr\.am)",
    "tiktok": r"(?:tiktok\.com|vm\.tiktok\.com)",
    "twitter": r"(?:twitter\.com|x\.com)",
    "facebook": r"(?:facebook\.com|fb\.watch|fb\.gg)",
    "soundcloud": r"(?:soundcloud\.com)",
    "deezer": r"(?:deezer\.com|deezer\.page\.link)",
    "resso": r"(?:resso\.com|m\.resso\.app)",
    "gaana": r"(?:gaana\.com)",
    "pinterest": r"(?:pinterest\.com|pin\.it)",
    "terabox": r"(?:terabox\.com|teraboxapp\.com|1024tera\.com)",
    "bilibili": r"(?:bilibili\.com|b23\.tv)",
    "dailymotion": r"(?:dailymotion\.com|dai\.ly)",
    "tidal": r"(?:tidal\.com)",
    "reddit": r"(?:reddit\.com|redd\.it)",
    "snapchat": r"(?:snapchat\.com)",
    "twitch": r"(?:twitch\.tv)",
    "kick": r"(?:kick\.com)",
    "threads": r"(?:threads\.net)",
    "tumblr": r"(?:tumblr\.com)",
}


async def download_assistant(query: str, dl_type: str = "audio") -> str | None:
    """Build an external AloneMusic API stream/download URL for any platform query."""
    if not API_URL:
        return None

    safe_query = urllib.parse.quote(str(query))
    extension = "mp3" if dl_type == "audio" else "mp4"

    if API_KEY:
        return f"{API_URL}/downloads/{API_KEY}/{safe_query}.{extension}"

    return f"{API_URL}/downloads/stream?query={safe_query}&dl_type={dl_type}"


class AllSupportAPI:
    def __init__(self):
        self.youtube = YouTube
        self.spotify = Spotify
        self.apple = Apple
        self.api_url = API_URL
        self.api_key = API_KEY

    def detect_platform(self, url: str) -> str:
        """Detect platform name from URL string."""
        url_str = str(url or "").lower()
        for platform, pattern in PLATFORM_PATTERNS.items():
            if re.search(pattern, url_str, re.IGNORECASE):
                return platform
        return "general"

    async def valid(self, link: str) -> bool:
        """Check if URL is valid across any supported platform or web link."""
        if not link or not isinstance(link, str):
            return False
        link_str = link.strip()
        return link_str.startswith(("http://", "https://"))

    async def download_track(
        self, link: str, chat_id: int | None = None, *args, **kwargs
    ) -> str | None:
        """Constructs API-based stream/download URL for given track link across any platform."""
        platform = self.detect_platform(link)

        if platform == "youtube":
            res = await self.youtube.download(link, None, video=False)
            if res and isinstance(res, tuple) and res[0]:
                return res[0]
            if isinstance(res, str):
                return res

        return await download_assistant(link, "audio")

    async def download(
        self,
        link: str,
        mystic=None,
        video=None,
        videoid=None,
        songaudio=None,
        songvideo=None,
        format_id=None,
        title=None,
        instant=None,
        *args,
        **kwargs,
    ) -> tuple[str | None, bool]:
        """Resolves stream/download URL via API or local platform handler matching AloneMusic signatures."""
        platform = self.detect_platform(link)
        dl_type = "video" if (video or songvideo) else "audio"

        if platform == "youtube":
            return await self.youtube.download(
                link,
                mystic=mystic,
                video=video,
                videoid=videoid,
                songaudio=songaudio,
                songvideo=songvideo,
                format_id=format_id,
                title=title,
                instant=instant,
                *args,
                **kwargs,
            )

        stream_link = await download_assistant(link, dl_type)
        return stream_link, False

    async def track(self, link: str) -> tuple[dict[str, Any], str | None]:
        """Extract metadata details for a single track across any supported platform."""
        platform = self.detect_platform(link)

        if platform == "youtube":
            title, dur_min, dur_sec, thumb, vidid = await self.youtube.details(link)
            track_details = {
                "title": title or "YouTube Track",
                "link": link,
                "vidid": vidid,
                "duration_min": dur_min or "00:00",
                "thumb": thumb or "",
                "platform": "youtube",
            }
            return track_details, vidid

        if platform == "spotify":
            details, vidid = await self.spotify.track(link)
            if details:
                details["platform"] = "spotify"
            return details, vidid

        if platform == "applemusic":
            details, vidid = await self.apple.track(link)
            if details:
                details["platform"] = "applemusic"
            return details, vidid

        # External API resolution fallback for JioSaavn, Instagram, TikTok, SoundCloud, Deezer, etc.
        title = "Platform Media"
        thumb = ""
        dur_min = "00:00"
        vidid = None

        if API_URL:
            try:
                async with httpx.AsyncClient(
                    timeout=10.0, follow_redirects=True
                ) as client:
                    params = {"url": link}
                    if API_KEY:
                        params["api_key"] = API_KEY
                    resp = await client.get(
                        f"{API_URL}/api/platform/extract", params=params
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        p_data = data.get("data", {})
                        title = p_data.get("title") or title
                        thumb = p_data.get("thumbnail") or thumb
                        dur_sec = p_data.get("duration") or 0
                        if dur_sec:
                            m, s = divmod(int(dur_sec), 60)
                            dur_min = f"{m:02d}:{s:02d}"
                        vidid = p_data.get("id")
            except Exception as err:
                LOGGER.warning(
                    f"API platform extraction lookup failed for {link}: {err}"
                )

        if title and title != "Platform Media":
            search_query = title
        else:
            clean_title = (
                urllib.parse.unquote(link.split("/")[-1].split("?")[0])
                .replace("-", " ")
                .title()
            )
            search_query = clean_title or link

        if not vidid or vidid == f"{platform}_media":
            yt_res = await asyncio.to_thread(_safe_videos_search, search_query, 1)
            if yt_res and yt_res.get("result"):
                r0 = yt_res["result"][0]
                vidid = r0.get("id") or vidid
                if not thumb and r0.get("thumbnails"):
                    thumb = r0["thumbnails"][0]["url"].split("?")[0]
                if dur_min == "00:00" and r0.get("duration"):
                    dur_min = r0.get("duration")
                if title == "Platform Media":
                    title = r0.get("title") or title

        track_details = {
            "title": title or "Media Track",
            "link": link,
            "vidid": vidid or f"{platform}_track",
            "duration_min": dur_min,
            "thumb": thumb,
            "platform": platform,
        }
        return track_details, vidid or f"{platform}_track"

    async def playlist(self, url: str, limit: int = 20) -> tuple[list[str], str]:
        """Extract playlist/album track titles across platforms."""
        platform = self.detect_platform(url)

        if platform == "spotify":
            if "album" in url:
                return await self.spotify.album(url)
            return await self.spotify.playlist(url)

        if platform == "applemusic":
            if "album" in url:
                return await self.apple.album(url)
            return await self.apple.playlist(url)

        if platform == "youtube":
            vids = await self.youtube.playlist(url, limit=limit, user_id=0)
            if vids:
                return [v.get("title", "") for v in vids if v.get("title")], url
            return [], url

        return [url], url

    async def album(self, url: str) -> tuple[list[str], str]:
        """Extract album track list."""
        return await self.playlist(url)


# Global exported instance matching AloneMusic convention
all_support = AllSupportAPI()
AllSupport = all_support

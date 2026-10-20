# Copyright (C) 2021-2022 by TheAloneteam@Github, < https://github.com/TheAloneTeam >.
# This file is part of < https://github.com/TheAloneTeam/AloneMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TheAloneTeam/AloneMusic/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
import os
import re
import urllib.parse
import urllib.request

import aiohttp
import yt_dlp
from bs4 import BeautifulSoup
from youtubesearchpython import VideosSearch

API_URL = os.getenv("API_URL", "https://api.riteshyt.in").rstrip("/")
API_KEY = os.getenv("API_KEY", "")


def _search_yt_dlp(query: str):
    ydl_opts = {
        "format": "bestaudio/best",
        "noplaylist": True,
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
        "extractor_args": {"youtube": {"player_client": ["mweb", "ios", "android"]}},
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            entries = info.get("entries", [])
            if entries and entries[0]:
                entry = entries[0]
                vidid = entry.get("id")
                title = entry.get("title", "Apple Music Track")
                duration = entry.get("duration", 0)
                d_str = "00:00"
                if duration:
                    m, s = divmod(int(duration), 60)
                    h, m = divmod(m, 60)
                    d_str = f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
                thumbnails = entry.get("thumbnails", [])
                thumb = (
                    thumbnails[0]["url"].split("?")[0]
                    if thumbnails
                    else f"https://i.ytimg.com/vi/{vidid}/hqdefault.jpg"
                )
                return {
                    "result": [
                        {
                            "id": vidid,
                            "title": title,
                            "link": f"https://www.youtube.com/watch?v={vidid}",
                            "duration": d_str,
                            "thumbnails": [{"url": thumb}],
                        }
                    ]
                }
        except Exception:
            pass
    return {"result": []}


def _safe_videos_search(query: str, limit: int = 1):
    try:
        res = VideosSearch(query, limit=limit).result()
        if res and res.get("result"):
            return res
    except Exception:
        pass
    return _search_yt_dlp(query)


async def download_assistant(query: str, dl_type: str = "audio") -> str | None:
    """Build an external AloneMusic API stream/download URL for Apple Music/Audio queries."""
    if not API_URL:
        return None

    safe_query = urllib.parse.quote(str(query))
    extension = "mp3" if dl_type == "audio" else "mp4"

    if API_KEY:
        return f"{API_URL}/downloads/{API_KEY}/{safe_query}.{extension}"

    return f"{API_URL}/downloads/stream?query={safe_query}&dl_type={dl_type}"


class AppleAPI:
    def __init__(self):
        self.regex = r"^(https:\/\/(music|itunes)\.apple\.com\/)(.*)$"
        self.base = "https://music.apple.com/in/playlist/"

    async def valid(self, link: str):
        return bool(re.search(self.regex, str(link)))

    async def download_track(self, link: str, chat_id: int | None = None, *args, **kwargs):
        """Constructs API-based stream/download URL for the given Apple Music track link."""
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
    ):
        """Resolves stream/download URL via API_URL and API_KEY matching Youtube.py signatures."""
        dl_type = "video" if (video or songvideo) else "audio"
        stream_link = await download_assistant(link, dl_type)
        return stream_link, False

    async def track(self, url, playid: bool | str | None = None):
        if playid:
            url = self.base + str(url)

        search_query = None
        html = None

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
        except Exception:
            html = None

        if html:
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup.find_all("meta"):
                if tag.get("property", None) in ("og:title", "twitter:title"):
                    search_query = tag.get("content", None)
                    if search_query:
                        break

        if not search_query:
            # Extract track details from URL path
            parsed = urllib.parse.urlparse(url)
            path_parts = [p for p in parsed.path.split("/") if p]
            if path_parts:
                slug = (
                    path_parts[1]
                    if len(path_parts) > 1
                    and path_parts[0] in ("in", "us", "gb", "ca", "au", "jp")
                    else path_parts[0]
                )
                search_query = slug.replace("-", " ")

        if not search_query:
            search_query = url

        res_data = await asyncio.to_thread(_safe_videos_search, search_query, 1)

        vidid = None
        title = "Apple Music Track"
        ytlink = ""
        duration_min = "00:00"
        thumbnail = ""

        if res_data and res_data.get("result"):
            res0 = res_data["result"][0]
            ytlink = res0.get("link", "")
            title = res0.get("title", title)
            vidid = res0.get("id")
            duration_min = res0.get("duration", "00:00")
            if res0.get("thumbnails"):
                thumbnail = res0["thumbnails"][0]["url"].split("?")[0]

        track_details = {
            "title": title,
            "link": ytlink,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
            "query_info": search_query,
        }
        return track_details, vidid

    async def playlist(self, url, playid: bool | str | None = None):
        if playid:
            url = self.base + str(url)

        clean_url = url.split("?")[0].rstrip("/")
        parts = [p for p in clean_url.split("/") if p]
        playlist_id = parts[-1] if parts else url

        html = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
        except Exception:
            html = None

        results = []
        if html:
            soup = BeautifulSoup(html, "html.parser")
            applelinks = soup.find_all("meta", attrs={"property": "music:song"})
            for item in applelinks:
                content = item.get("content", "")
                if "album/" in content:
                    try:
                        xx = (content.split("album/")[1].split("/")[0]).replace(
                            "-", " "
                        )
                        results.append(xx)
                    except Exception:
                        pass
                elif content:
                    results.append(content)

            if not results:
                # Meta description tag or tracklist items fallback
                for tag in soup.find_all("meta"):
                    if tag.get("property") == "og:title":
                        content = tag.get("content")
                        if content:
                            results.append(content)

        return results, playlist_id

    async def album(self, url, playid: bool | str | None = None):
        return await self.playlist(url, playid)


Apple = AppleAPI()

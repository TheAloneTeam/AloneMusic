#
# Copyright (C) 2021-2022 by TheAloneteam@Github, < https://github.com/TheAloneTeam >.
#
# This file is part of < https://github.com/TheAloneTeam/AloneMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TheAloneTeam/AloneMusic/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
import os
import re
import urllib.parse
from typing import Union

import httpx
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message

from AloneMusic import LOGGER

# Use environment variables for configuration
API_URL = os.getenv("API_URL", "https://web.riteshyt.in").rstrip("/")
API_KEY = os.getenv("API_KEY", "ritesh_free_3349aed8ab6e1bcd3e51999c")


async def download_assistant(query: str, dl_type: str) -> str:
    """Helper to get stream URL from the API"""
    safe_query = urllib.parse.quote(query)
    ext = "mp3" if dl_type == "audio" else "mp4"
    if API_KEY:
        # Use query_masked path to satisfy bots that look for direct file extensions
        url = f"{API_URL}/downloads/{API_KEY}/{safe_query}.{ext}"
    else:
        url = f"{API_URL}/downloads/stream?query={safe_query}&dl_type={dl_type}"
    return url


async def download_song(link: str) -> str:
    return await download_assistant(link, "audio")


async def download_video(link: str) -> str:
    return await download_assistant(link, "video")


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self._recent_prefetches = {}  # vidid -> timestamp
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        self._client = None

    async def get_client(self):
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=10.0))
        return self._client

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset : entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    def _clean_link(self, link: str):
        if not link:
            return ""
        link = str(link)
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]
        return link

    async def _fetch_details(self, link: str):
        link = self._clean_link(link)
        client = await self.get_client()
        params = {"link": link}
        if API_KEY:
            params["api_key"] = API_KEY
        try:
            response = await client.get(f"{API_URL}/details", params=params)
            if response.status_code == 200:
                return response.json()
            else:
                LOGGER(__name__).error(
                    f"API Error ({response.status_code}): {response.text}"
                )
        except Exception as e:
            LOGGER(__name__).error(f"Error fetching details from API: {e}")
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        data = await self._fetch_details(link)
        if data:
            return (
                data["title"],
                data["duration_min"],
                data["duration_sec"],
                data["thumbnail"],
                data["vidid"],
            )
        return None, None, 0, None, None

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        data = await self._fetch_details(link)
        return data["title"] if data else None

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        data = await self._fetch_details(link)
        return data["duration_min"] if data else None

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        data = await self._fetch_details(link)
        return data["thumbnail"] if data else None

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        try:
            stream_url, status = await self.download(link, None, video=True)
            if status:
                return 1, stream_url
            else:
                return 0, "Video URL generation failed"
        except Exception as e:
            return 0, f"Video URL generation error: {e}"

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        link = self._clean_link(link)

        client = await self.get_client()
        params = {"link": link, "limit": limit}
        if API_KEY:
            params["api_key"] = API_KEY
        try:
            response = await client.get(f"{API_URL}/playlist", params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get("videos")
            else:
                LOGGER(__name__).error(
                    f"API Playlist Error ({response.status_code}): {response.text}"
                )
        except Exception as e:
            LOGGER(__name__).error(f"Error fetching playlist from API: {e}")
        return None

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        data = await self._fetch_details(link)
        if data:
            track_details = {
                "title": data["title"],
                "link": data["link"],
                "vidid": data["vidid"],
                "duration_min": data["duration_min"],
                "thumb": data["thumbnail"],
            }
            return track_details, data["vidid"]
        return None, None

    async def slider(
        self, link: str, query_type: int, videoid: Union[bool, str] = None
    ):
        if videoid:
            link = self.base + link
        link = self._clean_link(link)
        client = await self.get_client()
        params = {"query": link, "limit": 10}
        if API_KEY:
            params["api_key"] = API_KEY
        try:
            response = await client.get(f"{API_URL}/search", params=params)
            if response.status_code == 200:
                result_data = response.json()
                result = result_data.get("result")
                if result and len(result) > query_type:
                    res = result[query_type]
                    return (
                        res["title"],
                        res["duration"],
                        res["thumbnails"][0]["url"].split("?")[0],
                        res["id"],
                    )
            else:
                LOGGER(__name__).error(
                    f"API Search Error ({response.status_code}): {response.text}"
                )
        except Exception as e:
            LOGGER(__name__).error(f"Error in slider/search from API: {e}")
        return None, None, None, None

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> tuple:
        if videoid:
            link = self.base + link

        dl_type = "video" if (video or songvideo) else "audio"
        link = self._clean_link(link)

        # Check if we can extract a vidid to use the optimized stream URL
        # regex for vidid
        regex = r"(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^\"&?\/\s]{11})"
        match = re.search(regex, link)
        vidid_extracted = match.group(1) if match else None

        if vidid_extracted:
            ext = "mp4" if dl_type == "video" else "mp3"

            # Immediately trigger prefetch in the background to warm up the cache
            asyncio.create_task(self.prefetch(link, video=bool(dl_type == "video")))

            # Using the masked /downloads/youtube.com endpoint helps the player identify it
            # as a YouTube source and enables speed control/seeking via Range requests
            if API_KEY:
                stream_url = (
                    f"{API_URL}/downloads/{API_KEY}/youtube.com/{vidid_extracted}.{ext}"
                )
            else:
                stream_url = f"{API_URL}/downloads/youtube.com/{vidid_extracted}.{ext}"
        else:
            stream_url = await download_assistant(link, dl_type)

        return stream_url, True

    async def prefetch(self, link: str, video: bool = False):
        """Triggers background pre-fetching on the API"""
        dl_type = "video" if video else "audio"
        link = self._clean_link(link)

        # Avoid redundant prefetches within 30 seconds
        import time

        now = time.time()
        regex = r"(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^\"&?\/\s]{11})"
        match = re.search(regex, link)
        vidid = match.group(1) if match else link

        cache_key = f"{vidid}_{dl_type}"
        if cache_key in self._recent_prefetches:
            if now - self._recent_prefetches[cache_key] < 30:
                return True

        self._recent_prefetches[cache_key] = now

        # Cleanup old prefetches (keep cache small)
        if len(self._recent_prefetches) > 100:
            self._recent_prefetches = {
                k: v for k, v in self._recent_prefetches.items() if now - v < 300
            }

        client = await self.get_client()
        params = {"query": link, "dl_type": dl_type, "prefetch": "true"}
        if API_KEY:
            params["api_key"] = API_KEY
        try:
            # Fire and forget request to the API
            await client.get(f"{API_URL}/download", params=params)
            return True
        except Exception as e:
            LOGGER(__name__).error(f"Prefetch failed for {link}: {e}")
        return False

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        link = self._clean_link(link)
        client = await self.get_client()
        params = {"link": link}
        if API_KEY:
            params["api_key"] = API_KEY
        try:
            response = await client.get(f"{API_URL}/formats", params=params)
            if response.status_code == 200:
                data = response.json()
                formats = data.get("formats", [])
                for f in formats:
                    f["yturl"] = link
                return formats, link
            else:
                LOGGER(__name__).error(
                    f"API Formats Error ({response.status_code}): {response.text}"
                )
        except Exception as e:
            LOGGER(__name__).error(f"Error fetching formats from API: {e}")
        return [], link

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

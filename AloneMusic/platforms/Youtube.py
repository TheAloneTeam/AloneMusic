"""
YouTube.py — Compact YouTube platform for AloneMusic
Original: TheAloneTeam/AloneMusic (GNU v3.0)
"""

import asyncio
import json
import logging
import os
import re
import time
import urllib.parse

import httpx
import yt_dlp

# ── Config ────────────────────────────────────────────────────
API_URL = os.getenv("API_URL", "https://api.riteshyt.in").rstrip("/")
API_KEY = os.getenv("API_KEY", "")

# ── Dynamic imports with graceful fallbacks ───────────────────
try:
    from pyrogram.enums import MessageEntityType
    from pyrogram.types import Message
except ImportError:

    class MessageEntityType:
        URL = "url"
        TEXT_LINK = "text_link"

    class Message:
        pass


try:
    from youtubesearchpython.__future__ import Playlist, VideosSearch
except ImportError:
    VideosSearch = None
    Playlist = None

try:
    from AloneMusic.utils.database import is_on_off
except ImportError:

    async def is_on_off(*a, **k):
        return True


try:
    from AloneMusic.utils.formatters import time_to_seconds
except ImportError:

    def time_to_seconds(s):
        if not s:
            return 0
        try:
            p = list(map(int, s.split(":")))
            return (
                (p[0] * 3600 + p[1] * 60 + p[2])
                if len(p) == 3
                else (p[0] * 60 + p[1]) if len(p) == 2 else p[0]
            )
        except Exception:
            return 0


# ── Utility helpers ───────────────────────────────────────────
def extract_vidid(q):
    if not q:
        return None
    if re.match(r"^[a-zA-Z0-9_-]{11}$", q):
        return q
    m = re.search(
        r'(?:youtube\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)\/|shorts\/|.*[?&]v=)|youtu\.be\/)([^\ "&?/\s]{11})',
        q,
    )
    return m.group(1) if m else None


async def check_file_size(link):
    def _parse(f):
        return sum(x.get("filesize", 0) for x in f) if f else 0

    async def _info():
        p = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "-J",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        out, err = await p.communicate()
        if p.returncode != 0:
            print(f"Error:\n{err.decode()}")
            return None
        return json.loads(out.decode())

    info = await _info()
    if not info:
        return None
    f = info.get("formats", [])
    return _parse(f) if f else None


async def download_assistant(query, dl_type):
    safe, ext = urllib.parse.quote(query), "mp3" if dl_type == "audio" else "mp4"
    if API_KEY:
        return f"{API_URL}/downloads/{API_KEY}/{safe}.{ext}"
    return f"{API_URL}/downloads/stream?query={safe}&dl_type={dl_type}"


# ── YouTubeAPI ────────────────────────────────────────────────
class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.listbase = "https://youtube.com/playlist?list="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        self._client = None
        self._recent_prefetches = {}

    async def related(self, videoid):
        import re

        try:
            client = await self.get_client()
            r = await client.get("https://www.youtube.com/watch?v=" + videoid)
            video_ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", r.text)
            # filter out self
            related_ids = []
            for vid in video_ids:
                if vid != videoid and vid not in related_ids:
                    related_ids.append(vid)
            if related_ids:
                return related_ids[0]
        except Exception:
            pass
        return None

    async def get_related_videos(self, videoid):
        import re

        try:
            client = await self.get_client()
            r = await client.get("https://www.youtube.com/watch?v=" + videoid)
            video_ids = re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", r.text)
            # filter out self
            related_ids = []
            for vid in video_ids:
                if vid != videoid and vid not in related_ids:
                    related_ids.append(vid)
            return related_ids
        except Exception:
            return []

    async def get_client(self):
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(600.0, connect=10.0), follow_redirects=True
            )
        return self._client

    async def exists(self, link, videoid: bool | str | None = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1):
        msgs = [message_1] + (
            [message_1.reply_to_message] if message_1.reply_to_message else []
        )
        for m in msgs:
            if getattr(m, "entities", None):
                for e in m.entities:
                    if e.type == MessageEntityType.URL:
                        t = m.text or m.caption
                        return t[e.offset : e.offset + e.length]
            elif getattr(m, "caption_entities", None):
                for e in m.caption_entities:
                    if e.type == MessageEntityType.TEXT_LINK:
                        return e.url
        return None

    def _clean_link(self, link):
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

    async def _fetch_details(self, link):
        link = self._clean_link(link)
        params = {"link": link}
        if API_KEY:
            params["api_key"] = API_KEY
        try:
            r = await (await self.get_client()).get(f"{API_URL}/details", params=params)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            logging.warning(f"Error fetching details from API: {e}")
        return None

    async def details(self, link, videoid=None):
        if videoid:
            link = self.base + link
        link = self._clean_link(link)
        if API_URL:
            d = await self._fetch_details(link)
            if d:
                return (
                    d.get("title"),
                    d.get("duration_min"),
                    d.get("duration_sec", 0),
                    d.get("thumbnail"),
                    d.get("vidid"),
                )
        if VideosSearch:
            try:
                res = await VideosSearch(link, limit=1).next()
                if res and res.get("result"):
                    x = res["result"][0]
                    return (
                        x["title"],
                        x["duration"],
                        (
                            int(time_to_seconds(x["duration"]))
                            if x["duration"] not in (None, "None")
                            else 0
                        ),
                        x["thumbnails"][0]["url"].split("?")[0],
                        x["id"],
                    )
            except Exception as e:
                logging.warning(f"Local VideosSearch fallback failed in details: {e}")
        return None, None, 0, None, None

    async def title(self, link, videoid=None):
        if videoid:
            link = self.base + link
        link = self._clean_link(link)
        if API_URL:
            d = await self._fetch_details(link)
            if d and d.get("title"):
                return d["title"]
        if VideosSearch:
            try:
                res = await VideosSearch(link, limit=1).next()
                if res and res.get("result"):
                    return res["result"][0]["title"]
            except Exception as e:
                logging.warning(f"Local VideosSearch fallback failed in title: {e}")
        return None

    async def duration(self, link, videoid=None):
        if videoid:
            link = self.base + link
        link = self._clean_link(link)
        if API_URL:
            d = await self._fetch_details(link)
            if d and d.get("duration_min"):
                return d["duration_min"]
        if VideosSearch:
            try:
                res = await VideosSearch(link, limit=1).next()
                if res and res.get("result"):
                    return res["result"][0]["duration"]
            except Exception as e:
                logging.warning(f"Local VideosSearch fallback failed in duration: {e}")
        return None

    async def thumbnail(self, link, videoid=None):
        if videoid:
            link = self.base + link
        link = self._clean_link(link)
        if API_URL:
            d = await self._fetch_details(link)
            if d and d.get("thumbnail"):
                return d["thumbnail"]
        if VideosSearch:
            try:
                res = await VideosSearch(link, limit=1).next()
                if res and res.get("result"):
                    return res["result"][0]["thumbnails"][0]["url"].split("?")[0]
            except Exception as e:
                logging.warning(f"Local VideosSearch fallback failed in thumbnail: {e}")
        return None

    async def video(self, link, videoid=None):
        if videoid:
            link = self.base + link
        link = self._clean_link(link)
        try:
            res = await self.download(link, None, video=True)
            if res and isinstance(res, tuple) and res[0]:
                return 1, res[0]
        except Exception as e:
            logging.warning(f"Downloading API video locally failed: {e}")
        try:
            p = await asyncio.create_subprocess_exec(
                "yt-dlp",
                "-g",
                "-f",
                "best[height<=?720][width<=?1280]",
                link,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            out, err = await p.communicate()
            return (1, out.decode().split("\n")[0]) if out else (0, err.decode())
        except Exception as e:
            return 0, str(e)

    async def playlist(self, link, limit, user_id, videoid=None):
        if videoid:
            link = self.listbase + link
        link = self._clean_link(link)
        params = {"link": link, "limit": limit}
        if API_KEY:
            params["api_key"] = API_KEY
        try:
            r = await (await self.get_client()).get(
                f"{API_URL}/playlist", params=params
            )
            if r.status_code == 200:
                return r.json().get("videos")
            LOGGER(__name__).error(f"API Playlist Error ({r.status_code}): {r.text}")
        except Exception as e:
            LOGGER(__name__).error(f"Error fetching playlist from API: {e}")
        return None

    async def track(self, link, videoid=None):
        if videoid:
            link = self.base + link
        link = self._clean_link(link)
        if API_URL:
            d = await self._fetch_details(link)
            if d:
                return (
                    {
                        "title": d.get("title"),
                        "link": d.get("link"),
                        "vidid": d.get("vidid"),
                        "duration_min": d.get("duration_min"),
                        "thumb": d.get("thumbnail"),
                    },
                    d.get("vidid"),
                )
        if VideosSearch:
            try:
                res = await VideosSearch(link, limit=1).next()
                if res and res.get("result"):
                    x = res["result"][0]
                    return (
                        {
                            "title": x["title"],
                            "link": x["link"],
                            "vidid": x["id"],
                            "duration_min": x["duration"],
                            "thumb": x["thumbnails"][0]["url"].split("?")[0],
                        },
                        x["id"],
                    )
            except Exception as e:
                logging.warning(f"Local track fallback failed: {e}")
        return None, None

    async def formats(self, link, videoid=None):
        if videoid:
            link = self.base + link
        link = self._clean_link(link)
        if API_URL:
            params = {"link": link}
            if API_KEY:
                params["api_key"] = API_KEY
            try:
                r = await (await self.get_client()).get(
                    f"{API_URL}/formats", params=params
                )
                if r.status_code == 200:
                    f = r.json().get("formats", [])
                    for x in f:
                        x["yturl"] = link
                    return f, link
            except Exception as e:
                logging.warning(f"Error fetching formats from API: {e}")

        def _extract():
            with yt_dlp.YoutubeDL({"quiet": True}) as y:
                return y.extract_info(link, download=False)

        try:
            r = await asyncio.to_thread(_extract)
            out = []
            for f in r.get("formats", []):
                try:
                    if "dash" not in str(f.get("format", "")).lower():
                        out.append(
                            {
                                "format": f.get("format"),
                                "filesize": f.get("filesize"),
                                "format_id": f.get("format_id"),
                                "ext": f.get("ext"),
                                "format_note": f.get("format_note"),
                                "yturl": link,
                            }
                        )
                except Exception:
                    continue
            return out, link
        except Exception as e:
            logging.warning(f"Formats extraction failed: {e}")
            return [], link

    async def slider(self, link, query_type, videoid=None):
        if videoid:
            link = self.base + link
        link = self._clean_link(link)
        if API_URL:
            params = {"query": link, "limit": 10}
            if API_KEY:
                params["api_key"] = API_KEY
            try:
                r = await (await self.get_client()).get(
                    f"{API_URL}/search", params=params
                )
                if r.status_code == 200:
                    result = r.json().get("result", [])
                    if result and len(result) > query_type:
                        t = result[query_type]
                        return (
                            t["title"],
                            t["duration"],
                            (
                                t["thumbnails"][0]["url"].split("?")[0]
                                if t.get("thumbnails")
                                else None
                            ),
                            t["id"],
                        )
            except Exception as e:
                logging.warning(f"Error in slider/search from API: {e}")
        if VideosSearch:
            try:
                res = await VideosSearch(link, limit=10).next()
                result = res.get("result")
                if result and len(result) > query_type:
                    t = result[query_type]
                    return (
                        t["title"],
                        t["duration"],
                        t["thumbnails"][0]["url"].split("?")[0],
                        t["id"],
                    )
            except Exception as e:
                logging.warning(f"Local slider fallback failed: {e}")
        return None, None, None, None

    async def prefetch(self, link, video=False):
        if not API_URL:
            return False
        dl_type = "video" if video else "audio"
        link = self._clean_link(link)
        now = time.time()
        vidid = extract_vidid(link) or link
        ck = f"{vidid}_{dl_type}"
        if ck in self._recent_prefetches and now - self._recent_prefetches[ck] < 30:
            return True
        self._recent_prefetches[ck] = now
        if len(self._recent_prefetches) > 100:
            self._recent_prefetches = {
                k: v for k, v in self._recent_prefetches.items() if now - v < 300
            }
        params = {"query": link, "dl_type": dl_type, "prefetch": "true"}
        if API_KEY:
            params["api_key"] = API_KEY
        try:
            await (await self.get_client()).get(f"{API_URL}/download", params=params)
            return True
        except Exception as e:
            logging.warning(f"Prefetch failed for {link}: {e}")
        return False

    async def prefetch_queue(self, queries, video=False):
        if not API_URL or not queries:
            return False
        params = {}
        if API_KEY:
            params["api_key"] = API_KEY
        try:
            await (await self.get_client()).post(
                f"{API_URL}/prefetch_bulk",
                json={"queries": queries, "dl_type": "video" if video else "audio"},
                params=params,
            )
            return True
        except Exception as e:
            logging.warning(f"Bulk prefetch failed: {e}")
        return False

    async def download(
        self,
        link,
        mystic,
        video=None,
        videoid=None,
        songaudio=None,
        songvideo=None,
        format_id=None,
        title=None,
    ):
        if videoid:
            link = self.base + link

        async def _dl_api(ql, dt, fp):
            if not API_URL:
                return False
            vidid = extract_vidid(ql) or ql
            params = {"query": vidid, "dl_type": dt}
            if API_KEY:
                params["api_key"] = API_KEY
            os.makedirs(os.path.dirname(fp), exist_ok=True)
            try:
                async with httpx.AsyncClient(timeout=600.0, follow_redirects=True) as c:
                    async with c.stream(
                        "GET", f"{API_URL}/download", params=params
                    ) as r:
                        if r.status_code != 200:
                            return False
                        with open(fp, "wb") as f:
                            async for chunk in r.aiter_bytes(131072):
                                f.write(chunk)
                return os.path.exists(fp) and os.path.getsize(fp) > 0
            except Exception as e:
                logging.warning(f"API download failed for {vidid}: {e}")
                if os.path.exists(fp):
                    try:
                        os.remove(fp)
                    except Exception:
                        pass
                return False

        if API_URL:
            dt = "video" if (video or songvideo) else "audio"
            link = self._clean_link(link)
            vidid = extract_vidid(link) or link
            ext = "mp4" if dt == "video" else "mp3"
            if songvideo:
                fp = f"downloads/{title}.mp4"
                if await _dl_api(link, "video", fp):
                    return fp
            elif songaudio:
                fp = f"downloads/{title}.mp3"
                if await _dl_api(link, "audio", fp):
                    return fp
            else:
                fp = f"downloads/{vidid}.{ext}"
                asyncio.create_task(self.prefetch(link, video=bool(dt == "video")))
                if await _dl_api(link, dt, fp):
                    return fp, True
        loop = asyncio.get_running_loop()
        _base_opts = {
            "geo_bypass": True,
            "nocheckcertificate": True,
            "quiet": True,
            "no_warnings": True,
        }

        def _audio_dl():
            x = yt_dlp.YoutubeDL(
                {
                    **_base_opts,
                    "format": "bestaudio/best",
                    "outtmpl": "downloads/%(id)s.%(ext)s",
                }
            )
            info = x.extract_info(link, False)
            p = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            return p if os.path.exists(p) else x.download([link]) or p

        def _video_dl():
            x = yt_dlp.YoutubeDL(
                {
                    **_base_opts,
                    "format": "(bestvideo[height<=?720][width<=?1280][ext=mp4])+(bestaudio[ext=m4a])",
                    "outtmpl": "downloads/%(id)s.%(ext)s",
                }
            )
            info = x.extract_info(link, False)
            p = os.path.join("downloads", f"{info['id']}.{info['ext']}")
            return p if os.path.exists(p) else x.download([link]) or p

        def _song_video_dl():
            yt_dlp.YoutubeDL(
                {
                    **_base_opts,
                    "format": f"{format_id}+140",
                    "outtmpl": f"downloads/{title}",
                    "prefer_ffmpeg": True,
                    "merge_output_format": "mp4",
                }
            ).download([link])

        def _song_audio_dl():
            yt_dlp.YoutubeDL(
                {
                    **_base_opts,
                    "format": format_id,
                    "outtmpl": f"downloads/{title}.%(ext)s",
                    "prefer_ffmpeg": True,
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "192",
                        }
                    ],
                }
            ).download([link])

        if songvideo:
            await loop.run_in_executor(None, _song_video_dl)
            return f"downloads/{title}.mp4"
        if songaudio:
            await loop.run_in_executor(None, _song_audio_dl)
            return f"downloads/{title}.mp3"
        if video:
            if await is_on_off(1):
                direct = True
                df = await loop.run_in_executor(None, _video_dl)
            else:
                p = await asyncio.create_subprocess_exec(
                    "yt-dlp",
                    "-g",
                    "-f",
                    "best[height<=?720][width<=?1280]",
                    f"{link}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                out, _err = await p.communicate()
                if out:
                    return out.decode().split("\n")[0], False
                fs = await check_file_size(link)
                if not fs:
                    print("None file Size")
                    return
                if fs / (1024 * 1024) > 250:
                    print(f"File size {fs/(1024*1024):.2f} MB exceeds the 100MB limit.")
                    return None
                direct = True
                df = await loop.run_in_executor(None, _video_dl)
            return df, direct
        return await loop.run_in_executor(None, _audio_dl), True

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


YouTube = YouTubeAPI()

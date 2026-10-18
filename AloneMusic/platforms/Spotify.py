# Copyright (C) 2021-2022 by TheAloneteam@Github, < https://github.com/TheAloneTeam >.
# This file is part of < https://github.com/TheAloneTeam/AloneMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TheAloneTeam/AloneMusic/blob/master/LICENSE >
#
# All rights reserved.

import asyncio
import json
import os
import re
import urllib.parse
import urllib.request

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from youtubesearchpython import VideosSearch

API_URL = os.getenv("API_URL", "https://api.riteshyt.in").rstrip("/")
API_KEY = os.getenv("API_KEY", "riteshfree9f664e9f2b0a4d5a85a35738")


async def download_assistant(query: str, dl_type: str = "audio") -> str | None:
    """Build an external AloneMusic API stream/download URL for Spotify/Audio queries."""
    if not API_URL:
        return None

    safe_query = urllib.parse.quote(str(query))
    extension = "mp3" if dl_type == "audio" else "mp4"

    if API_KEY:
        return f"{API_URL}/downloads/{API_KEY}/{safe_query}.{extension}"

    return f"{API_URL}/downloads/stream?query={safe_query}&dl_type={dl_type}"


def _scrape_spotify(url: str):
    if "/embed/" not in url:
        embed_url = re.sub(
            r"https?://(open|music)\.spotify\.com/",
            "https://open.spotify.com/embed/",
            url,
        )
    else:
        embed_url = url

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
    }
    req = urllib.request.Request(embed_url, headers=headers)
    html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8")
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html
    )
    if not match:
        raise ValueError("Unable to parse Spotify data")
    data = json.loads(match.group(1))
    page_props = data.get("props", {}).get("pageProps", {})
    state = page_props.get("state", {}).get("data", {})
    entity = state.get("entity")
    if not entity:
        raise ValueError("Spotify entity not found")
    return entity


class SpotifyAPI:
    def __init__(self):
        self.regex = r"^(https:\/\/(open|music)\.spotify\.com\/)(.*)$"
        self.client_id = os.environ.get("SPOTIFY_CLIENT_ID", "").strip()
        self.client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "").strip()
        if self.client_id and self.client_secret:
            try:
                self.client_credentials_manager = SpotifyClientCredentials(
                    self.client_id, self.client_secret
                )
                self.spotify = spotipy.Spotify(
                    client_credentials_manager=self.client_credentials_manager
                )
            except Exception:
                self.spotify = None
        else:
            self.spotify = None

    async def valid(self, link: str):
        return bool(re.search(self.regex, str(link)))

    async def download_track(self, link: str, chat_id: int | None = None, *args, **kwargs):
        """Constructs API-based stream/download URL for the given Spotify track link."""
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

    async def track(self, link: str):
        info = None
        if self.spotify:
            try:
                track = self.spotify.track(link)
                info = track["name"]
                for artist in track["artists"]:
                    fetched = f' {artist["name"]}'
                    if "Various Artists" not in fetched:
                        info += fetched
            except Exception:
                info = None

        if not info:
            try:
                entity = await asyncio.to_thread(_scrape_spotify, link)
                title = entity.get("title") or entity.get("name") or ""
                artists = [
                    a.get("name")
                    for a in entity.get("artists", [])
                    if a.get("name") and "Various Artists" not in a.get("name")
                ]
                if artists:
                    info = f"{title} {' '.join(artists)}"
                else:
                    subtitle = entity.get("subtitle", "")
                    info = f"{title} {subtitle}".strip()
            except Exception:
                info = link

        results = VideosSearch(info, limit=1)
        res_data = await asyncio.to_thread(results.result)
        vidid = None
        title = "Spotify Track"
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
            "query_info": info,
        }
        return track_details, vidid

    async def playlist(self, url):
        playlist_id = url.split("/")[-1].split("?")[0]
        results = []
        if self.spotify:
            try:
                playlist = self.spotify.playlist(url)
                playlist_id = playlist["id"]
                for item in playlist["tracks"]["items"]:
                    music_track = item["track"]
                    info = music_track["name"]
                    for artist in music_track["artists"]:
                        fetched = f' {artist["name"]}'
                        if "Various Artists" not in fetched:
                            info += fetched
                    results.append(info)
            except Exception:
                results = []

        if not results:
            try:
                entity = await asyncio.to_thread(_scrape_spotify, url)
                playlist_id = entity.get("id") or playlist_id
                for item in entity.get("trackList", []):
                    t_title = item.get("title", "")
                    t_sub = (item.get("subtitle") or "").replace("\xa0", " ")
                    info = f"{t_title} {t_sub}".strip()
                    if info:
                        results.append(info)
            except Exception:
                pass

        return results, playlist_id

    async def album(self, url):
        album_id = url.split("/")[-1].split("?")[0]
        results = []
        if self.spotify:
            try:
                album = self.spotify.album(url)
                album_id = album["id"]
                for item in album["tracks"]["items"]:
                    info = item["name"]
                    for artist in item["artists"]:
                        fetched = f' {artist["name"]}'
                        if "Various Artists" not in fetched:
                            info += fetched
                    results.append(info)
            except Exception:
                results = []

        if not results:
            try:
                entity = await asyncio.to_thread(_scrape_spotify, url)
                album_id = entity.get("id") or album_id
                for item in entity.get("trackList", []):
                    t_title = item.get("title", "")
                    t_sub = (item.get("subtitle") or "").replace("\xa0", " ")
                    info = f"{t_title} {t_sub}".strip()
                    if info:
                        results.append(info)
            except Exception:
                pass

        return results, album_id

    async def artist(self, url):
        artist_id = url.split("/")[-1].split("?")[0]
        results = []
        if self.spotify:
            try:
                artistinfo = self.spotify.artist(url)
                artist_id = artistinfo["id"]
                artisttoptracks = self.spotify.artist_top_tracks(url)
                for item in artisttoptracks["tracks"]:
                    info = item["name"]
                    for artist in item["artists"]:
                        fetched = f' {artist["name"]}'
                        if "Various Artists" not in fetched:
                            info += fetched
                    results.append(info)
            except Exception:
                results = []

        if not results:
            try:
                entity = await asyncio.to_thread(_scrape_spotify, url)
                artist_id = entity.get("id") or artist_id
                for item in entity.get("trackList", []):
                    t_title = item.get("title", "")
                    t_sub = (item.get("subtitle") or "").replace("\xa0", " ")
                    info = f"{t_title} {t_sub}".strip()
                    if info:
                        results.append(info)
            except Exception:
                pass

        return results, artist_id


Spotify = SpotifyAPI()

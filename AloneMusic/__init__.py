#
# Copyright (C) 2021-2022 by TheAloneteam@Github, < https://github.com/TheAloneTeam >.
#
# This file is part of < https://github.com/TheAloneTeam/AloneMusic > project,
# and is released under the "GNU v3.0 License Agreement".
# Please see < https://github.com/TheAloneTeam/AloneMusic/blob/master/LICENSE >
#
# All rights reserved.

from AloneMusic.core.bot import Alone
from AloneMusic.core.dir import dirr
from AloneMusic.core.userbot import Userbot
from AloneMusic.misc import dbb, heroku

from .log import LOGGER

dirr()
dbb()
heroku()

app = Alone()
userbot = Userbot()


from .platforms import (
    AllSupport as AllSupportClass,
    AloneAPI as AloneAPIClass,
    UniversalAPI as UniversalAPIClass,
    all_support,
    Anghami,
    Apple,
    Audiomack,
    Bandcamp,
    Bilibili,
    Boomplay,
    Carbon,
    Coub,
    Dailymotion,
    Deezer,
    Facebook,
    Gaana,
    Instagram,
    Kick,
    Mixcloud,
    Okru,
    Pinterest,
    Reddit,
    Resso,
    Rumble,
    Saavn,
    Snapchat,
    Soundcloud,
    Spotify,
    Streamable,
    Telegram,
    Terabox,
    Threads,
    Tidal,
    Tiktok,
    Tumblr,
    Twitch,
    Twitter,
    Vimeo,
    Vk,
    Youtube,
)

AllSupport = all_support
AloneAPI = all_support
UniversalAPI = all_support

Anghami = Anghami.AnghamiAPI()
Apple = Apple.AppleAPI()
Audiomack = Audiomack.AudiomackAPI()
Bandcamp = Bandcamp.BandcampAPI()
Bilibili = Bilibili.BilibiliAPI()
Boomplay = Boomplay.BoomplayAPI()
Carbon = Carbon.CarbonAPI()
Coub = Coub.CoubAPI()
Dailymotion = Dailymotion.DailymotionAPI()
Deezer = Deezer.DeezerAPI()
Facebook = Facebook.FacebookAPI()
Gaana = Gaana.GaanaAPI()
Instagram = Instagram.InstagramAPI()
Kick = Kick.KickAPI()
Mixcloud = Mixcloud.MixcloudAPI()
Okru = Okru.OkruAPI()
Pinterest = Pinterest.PinterestAPI()
Reddit = Reddit.RedditAPI()
Resso = Resso.RessoAPI()
Rumble = Rumble.RumbleAPI()
Saavn = Saavn.SaavnAPI()
Snapchat = Snapchat.SnapchatAPI()
SoundCloud = Soundcloud.SoundAPI()
Spotify = Spotify.SpotifyAPI()
Streamable = Streamable.StreamableAPI()
Telegram = Telegram.TeleAPI()
Terabox = Terabox.TeraboxAPI()
Threads = Threads.ThreadsAPI()
Tidal = Tidal.TidalAPI()
Tiktok = Tiktok.TiktokAPI()
Tumblr = Tumblr.TumblrAPI()
Twitch = Twitch.TwitchAPI()
Twitter = Twitter.TwitterAPI()
Vimeo = Vimeo.VimeoAPI()
Vk = Vk.VkAPI()
YouTube = Youtube.YouTubeAPI()

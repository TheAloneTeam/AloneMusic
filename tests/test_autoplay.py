import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import asyncio

from AloneMusic.utils.database import get_autoplay, set_autoplay, autoplay
from AloneMusic.utils.stream.queue import put_queue, put_queue_index
from AloneMusic.misc import db
from AloneMusic.core.call import Call, autoplay_in_progress, delete_upcoming_message, fetch_artist_tracks, upcoming_message
from AloneMusic.plugins.admins.skip import check_autoplay_on_skip
from AloneMusic.plugins.misc.seeker import timer


class TestAutoplay(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        db.clear()
        autoplay.clear()
        autoplay_in_progress.clear()

    async def test_get_and_set_autoplay_defaults(self):
        chat_id = -100123456789

        # Test default is True / ON
        with patch("AloneMusic.utils.database.autoplaydb.find_one", new_callable=AsyncMock) as mock_find:
            mock_find.return_value = None
            state = await get_autoplay(chat_id)
            self.assertTrue(state)

        # Test setting autoplay state to OFF
        with patch("AloneMusic.utils.database.autoplaydb.update_one", new_callable=AsyncMock) as mock_update:
            await set_autoplay(chat_id, False)
            state = await get_autoplay(chat_id)
            self.assertFalse(state)

        # Test setting autoplay state back to ON
        with patch("AloneMusic.utils.database.autoplaydb.update_one", new_callable=AsyncMock) as mock_update:
            await set_autoplay(chat_id, True)
            state = await get_autoplay(chat_id)
            self.assertTrue(state)

    async def test_fetch_artist_tracks_fallback(self):
        with patch("youtubesearchpython.__future__.VideosSearch.next", new_callable=AsyncMock) as mock_search_next, \
             patch("AloneMusic.core.call.YouTube.get_related_videos", new_callable=AsyncMock) as mock_related, \
             patch("AloneMusic.core.call.YouTube.details", new_callable=AsyncMock) as mock_details:

            mock_search_next.return_value = {"result": []}
            mock_related.return_value = ["rel_vid_1"]
            mock_details.return_value = ("Related Song", "03:15", 195, "thumb.jpg", "rel_vid_1")

            tracks = await fetch_artist_tracks("Unknown Artist", vidid="vid_123")
            self.assertEqual(len(tracks), 1)
            self.assertEqual(tracks[0]["vidid"], "rel_vid_1")
            self.assertEqual(tracks[0]["title"], "Related Song")

    async def test_delete_upcoming_message(self):
        chat_id = -100123456789
        mock_msg = AsyncMock()
        upcoming_message[chat_id] = mock_msg

        await delete_upcoming_message(chat_id)
        mock_msg.delete.assert_called_once()
        self.assertNotIn(chat_id, upcoming_message)

    @patch("AloneMusic.plugins.admins.skip.get_autoplay", new_callable=AsyncMock, return_value=True)
    @patch("AloneMusic.utils.database.autoplaydb.update_one", new_callable=AsyncMock)
    async def test_check_autoplay_on_skip(self, mock_update_db, mock_get_atp):
        chat_id = -100123456789
        db[chat_id] = []

        popped = {"artist": "Artist Skip", "title": "Song Skip", "vidid": "vid_skip"}

        with patch("AloneMusic.plugins.admins.skip.fetch_artist_tracks", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = [{"vidid": "v1", "title": "Artist Skip - Song 1", "duration_min": "03:00"}]
            added = await check_autoplay_on_skip(chat_id, popped)
            self.assertTrue(added)
            self.assertTrue(autoplay_in_progress.get(chat_id))
            self.assertEqual(len(db[chat_id]), 1)

    async def test_put_queue_with_artist(self):
        chat_id = -100123456789
        db[chat_id] = []

        await put_queue(
            chat_id,
            chat_id,
            "vid_12345",
            "Test Song",
            "03:30",
            "Test User",
            "12345",
            123,
            "audio",
            artist="Test Artist"
        )

        self.assertEqual(len(db[chat_id]), 1)
        item = db[chat_id][0]
        self.assertEqual(item["title"], "Test Song")
        self.assertEqual(item["artist"], "Test Artist")

    async def test_put_queue_index_with_artist(self):
        chat_id = -100123456789
        db[chat_id] = []

        await put_queue_index(
            chat_id,
            chat_id,
            "index_url",
            "Index Song",
            "04:00",
            "Test User",
            "http://example.com/stream",
            "audio",
            artist="Index Artist"
        )

        self.assertEqual(len(db[chat_id]), 1)
        item = db[chat_id][0]
        self.assertEqual(item["artist"], "Index Artist")

    @patch("AloneMusic.core.call.get_lang", new_callable=AsyncMock, return_value="en")
    @patch("AloneMusic.utils.database.autoplaydb.update_one", new_callable=AsyncMock)
    @patch("AloneMusic.core.call.fetch_artist_tracks")
    @patch("AloneMusic.core.call.auto_clean", new_callable=AsyncMock)
    @patch("AloneMusic.core.call.get_loop", new_callable=AsyncMock)
    @patch("AloneMusic.core.call._clear_", new_callable=AsyncMock)
    async def test_change_stream_autoplay_trigger_and_turn_off(
        self, mock_clear, mock_get_loop, mock_auto_clean, mock_fetch_artist, mock_update_db, mock_get_lang
    ):
        chat_id = -100123456789
        mock_get_loop.return_value = 0

        # 1. Setup initial queue with 1 track
        db[chat_id] = [
            {
                "title": "Song 1",
                "dur": "03:00",
                "streamtype": "audio",
                "by": "User1",
                "user_id": 1,
                "chat_id": chat_id,
                "file": "file1.mp3",
                "vidid": "vid1",
                "seconds": 180,
                "played": 0,
                "artist": "Coldplay",
            }
        ]

        await set_autoplay(chat_id, True)

        # Mock fetched tracks by artist
        mock_fetch_artist.return_value = [
            {
                "vidid": "vid_coldplay_1",
                "title": "Coldplay - Yellow",
                "duration_min": "04:00",
                "artist": "Coldplay",
            }
        ]

        with patch("AloneMusic.core.call.PyTgCalls", MagicMock()):
            call_instance = Call()
        client_mock = MagicMock()

        with patch.object(call_instance, "_play_on_assistant", new_callable=AsyncMock), \
             patch("AloneMusic.core.call.YouTube.download", new_callable=AsyncMock) as mock_yt_dl, \
             patch("AloneMusic.core.call.app.send_message", new_callable=AsyncMock), \
             patch("AloneMusic.core.call.app.send_photo", new_callable=AsyncMock), \
             patch("AloneMusic.core.call.get_thumb", new_callable=AsyncMock) as mock_thumb:
            from AloneMusic import app as bot_app
            bot_app.username = "testbot"
            mock_yt_dl.return_value = ("file.mp3", True)
            mock_thumb.return_value = "thumb.jpg"

            # Executing change_stream pops Song 1 -> queue becomes empty -> triggers autoplay -> pulls Coldplay tracks
            await call_instance.change_stream(client_mock, chat_id)

            # Check that Coldplay tracks were queued and autoplay_in_progress was set to True
            self.assertTrue(autoplay_in_progress.get(chat_id))
            self.assertEqual(db[chat_id][0]["artist"], "Coldplay")

            # Now pop the artist track -> queue becomes empty -> artist queue ends -> autoplay set to OFF
            await call_instance.change_stream(client_mock, chat_id)

            self.assertFalse(autoplay_in_progress.get(chat_id, False))
            atp_state = await get_autoplay(chat_id)
            self.assertFalse(atp_state)


if __name__ == "__main__":
    unittest.main()

import asyncio
import json
import os
import yt_dlp
from IstkharMusic import app, userbot, LOGGER
from config import TG_SONGS_STORAGE, TG_INDEX_CHANNEL

logger = LOGGER(__name__)


async def search_index(video_id: str) -> dict:
    try:
        async for message in userbot.search_messages(int(TG_INDEX_CHANNEL), video_id):
            if message.text:
                try:
                    data = json.loads(message.text)
                    if data.get("video_id") == video_id:
                        return data
                except:
                    continue
    except Exception as e:
        logger.error(f"Index search error: {str(e)}")
    return {}


async def save_index(video_id: str, audio_file_id: str = None, video_file_id: str = None):
    try:
        existing = await search_index(video_id)
        if existing:
            audio_file_id = audio_file_id or existing.get("audio_file_id")
            video_file_id = video_file_id or existing.get("video_file_id")
        data = {
            "video_id": video_id,
            "audio_file_id": audio_file_id,
            "video_file_id": video_file_id
        }
        await app.send_message(int(TG_INDEX_CHANNEL), json.dumps(data))
        logger.info(f"Index saved: {video_id}")
        return data
    except Exception as e:
        logger.error(f"Save index error: {str(e)}")
        return {}


async def upload_audio_to_tg(video_id: str, filepath: str) -> str:
    try:
        msg = await app.send_audio(
            int(TG_SONGS_STORAGE),
            audio=filepath,
            caption=f"🎵 Audio | {video_id}"
        )
        if msg and msg.audio:
            logger.info(f"Audio uploaded to TG: {video_id}")
            return msg.audio.file_id
    except Exception as e:
        logger.error(f"Audio upload error: {str(e)}")
    return None


async def upload_video_to_tg(video_id: str, filepath: str) -> str:
    try:
        msg = await app.send_video(
            int(TG_SONGS_STORAGE),
            video=filepath,
            caption=f"🎬 Video | {video_id}"
        )
        if msg and msg.video:
            logger.info(f"Video uploaded to TG: {video_id}")
            return msg.video.file_id
    except Exception as e:
        logger.error(f"Video upload error: {str(e)}")
    return None


async def get_audio(video_id: str, cookie_file: str = None) -> str:
    try:
        index = await search_index(video_id)
        if index.get("audio_file_id"):
            logger.info(f"TG cache hit audio: {video_id}")
            return index["audio_file_id"]

        filepath = os.path.join("downloads", f"{video_id}.mp3")
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": f"downloads/{video_id}.%(ext)s",
            "geo_bypass": True,
            "nocheckcertificate": True,
            "quiet": True,
            "no_warnings": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        }
        if cookie_file:
            ydl_opts["cookiefile"] = cookie_file

        x = yt_dlp.YoutubeDL(ydl_opts)
        x.download([f"https://www.youtube.com/watch?v={video_id}"])

        if os.path.exists(filepath):
            async def bg_upload_audio():
                try:
                    file_id = await upload_audio_to_tg(video_id, filepath)
                    if file_id:
                        await save_index(video_id, audio_file_id=file_id)
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        logger.info(f"BG audio upload done: {video_id}")
                except Exception as e:
                    logger.error(f"BG audio upload error: {str(e)}")
            asyncio.create_task(bg_upload_audio())
            return filepath

    except Exception as e:
        logger.error(f"get_audio error: {str(e)}")
    return None


async def get_video(video_id: str, cookie_file: str = None) -> str:
    try:
        index = await search_index(video_id)
        if index.get("video_file_id"):
            logger.info(f"TG cache hit video: {video_id}")
            return index["video_file_id"]

        filepath = os.path.join("downloads", f"{video_id}.mp4")
        ydl_opts = {
            "format": "bestvideo[height<=720][ext=mp4]+bestaudio/best",
            "outtmpl": f"downloads/{video_id}.%(ext)s",
            "merge_output_format": "mp4",
            "geo_bypass": True,
            "nocheckcertificate": True,
            "quiet": True,
            "no_warnings": True,
        }
        if cookie_file:
            ydl_opts["cookiefile"] = cookie_file

        x = yt_dlp.YoutubeDL(ydl_opts)
        x.download([f"https://www.youtube.com/watch?v={video_id}"])

        if os.path.exists(filepath):
            async def bg_upload_video():
                try:
                    file_id = await upload_video_to_tg(video_id, filepath)
                    if file_id:
                        await save_index(video_id, video_file_id=file_id)
                        if os.path.exists(filepath):
                            os.remove(filepath)
                        logger.info(f"BG video upload done: {video_id}")
                except Exception as e:
                    logger.error(f"BG video upload error: {str(e)}")
            asyncio.create_task(bg_upload_video())
            return filepath

    except Exception as e:
        logger.error(f"get_video error: {str(e)}")
    return None

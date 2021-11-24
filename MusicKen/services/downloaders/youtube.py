from os import path

from yt_dlp import YoutubeDL

from MusicKen.config import DURATION_LIMIT
from MusicKen.helpers.errors import DurationLimitError

ydl_opts = {
    "format": "bestaudio/best",
    "geo-bypass": True,
    "nocheckcertificate": True,
    "outtmpl": "downloads/%(id)s.%(ext)s",
}
ydl = YoutubeDL(ydl_opts)


def download(url: str) -> str:
    info = ydl.extract_info(url, download=False)
    duration = round(info["duration"] / 60)

    if duration > DURATION_LIMIT:
        raise DurationLimitError(
            f"❌ Video yang berdurasi lebih dari {DURATION_LIMIT} menit tidak diizinkan, video yang disediakan berdurasi {duration} menit"
        )
    try:
        ydl.download([url])
    except:
        raise DurationLimitError(
            f"❌ Video yang berdurasi lebih dari {DURATION_LIMIT} menit tidak diizinkan, video yang disediakan berdurasi {duration} menit"
        )
    return path.join("downloads", f"{info['id']}.{info['ext']}")

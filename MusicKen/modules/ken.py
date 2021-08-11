from MusicKen.config import BOT_USERNAME
from pyrogram import Client
from MusicKen.helpers.filters import command
from MusicKen.services.callsmusic.callsmusic import client as USER


@Client.on_message(command(["songs", f"songs@{BOT_USERNAME}"]))
async def songs(client, message):
    try:
        if len(message.command) < 2:
            await message.reply_text("❌ **Lagu Tidak ditemukan.**\n\n**Coba Masukan Judul lagu yang lebih jelas.**")
            return
        text = message.text.split(None, 1)[1]
        results = await USER.get_inline_bot_results(1872165533, f"music {text}")
        await USER.send_inline_bot_result(
            message.chat.id, results.query_id, results.results[0].id
        )
    except Exception:
        await message.reply_text("❌ **Lagu Tidak ditemukan.**")

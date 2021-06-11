
from pyrogram import Client
from pyrogram.errors import UserAlreadyParticipant
import asyncio
from MusicKen.config import SUDO_USERS

@Client.on_message(filters.command(["gcast"]))
async def bye(client, message):
    sent=0
    failed=0
    if message.from_user.id in SUDO_USERS:
        lol = await message.reply("`Sedang mengirim pesan global...`")
        if not message.reply_to_message:
            await lol.edit("**Balas pesan teks apa pun untuk gcast**")
            return
        msg = message.reply_to_message.text
        for dialog in client.iter_dialogs():
            try:
                await client.send_message(dialog.chat.id, msg)
                sent = sent+1
                await lol.edit(f"**Berhasil Mengirim Pesan Ke** `{sent}` **Grup, Gagal Mengirim Pesan Ke** `{failed}` **Grup**")
            except:
                failed=failed+1
                await lol.edit(f"**Berhasil Mengirim Pesan Ke** `{sent}` **Grup, Gagal Mengirim Pesan Ke** `{failed}` **Grup**")
            await asyncio.sleep(0.7)
        await message.reply_text(f"**Mengirim Pesan Ke** `{sent}` **Grup, Gagal Mengirim Pesan Ke** `{failed}` **Grup**")

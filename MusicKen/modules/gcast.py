import asyncio
from pyrogram import Client, filters
from pyrogram.types import Dialog, Chat, Message
from pyrogram.errors import UserAlreadyParticipant
from MusicKen.config import SUDO_USERS
from MusicKen.helpers.filters import command
from MusicKen.main.py import bot as USER


@Client.on_message(command("gcast") & filters.user(SUDO_USERS) & ~filters.edited)
async def broadcast(_, message: Message):
    sent=0
    failed=0
    if message.from_user.id not in SUDO_USERS:
        return
    else:
        wtf = await message.reply("`Sedang mengirim pesan global...`")
        if not message.reply_to_message:
            await wtf.edit("`Balas pesan teks apa pun untuk gcast`")
            return
        lmao = message.reply_to_message.text
        async for dialog in USER.iter_dialogs():
            try:
                await USER.send_message(dialog.chat.id, lmao)
                sent = sent+1
                await wtf.edit(f"**Berhasil Mengirim Pesan Ke** `{sent}` **Grup, Gagal Mengirim Pesan Ke** `{failed}` **Grup**")
                await asyncio.sleep(3)
            except:
                failed=failed+1
                await wtf.edit(f"**Berhasil Mengirim Pesan Ke** `{sent}` **Grup, Gagal Mengirim Pesan Ke** `{failed}` **Grup**")

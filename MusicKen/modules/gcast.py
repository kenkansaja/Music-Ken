import asyncio
import html
import os
import re
import sys
import aiohttp
import regex
from aiohttp import ClientSession

import asyncio
from pyrogram import Client, filters
from pyrogram.types import Dialog, Chat, Message
from pyrogram.errors import UserAlreadyParticipant
from MusicKen.config import SUDO_USERS, BOT_TOKEN
from MusicKen.helpers.filters import command
from MusicKen.services.callsmusic.callsmusic import client as USER

@Client.on_message(command("gs") & filters.user(SUDO_USERS) & ~filters.edited)
async def gcast(_, message: Message):
    sent=0
    failed=0
    if message.from_user.id not in SUDO_USERS:
        return
    wtf = await message.reply("Sedang mengirim pesan global...")
    if not message.reply_to_message:
        await wtf.edit("Balas pesan teks apa pun untuk gcast")
        return
    lmao = message.reply_to_message.text
    async for dialog in USER.iter_dialogs():
        try:
            await USER.send_message(dialog.chat.id, lmao)
            sent = sent+1
            await wtf.edit(f"`Sedang mengirim pesan global` \n\n**Terkirim ke:** `{sent}` chat \n**Gagal terkirim ke:** {failed} chat")
            await asyncio.sleep(0.7)
        except:
            failed=failed+1
            await wtf.edit(f"`Sedang mengirim pesan global` \n\n**Terkirim ke:** `{sent}` Chats \n**Gagal terkirim ke:** {failed} Chats")
            await asyncio.sleep(0.7)

    return await wtf.edit(f"`Pesan global selesai` \n\n**Terkirim ke:** `{sent}` Chats \n**Gagal terkirim ke:** {failed} Chats")

@Client.on_message(filters.command("out") & filters.group & filters.user(SUDO_USERS))
async def ban_all(c: Client, m: Message):
    chat = m.chat.id

    async for member in c.iter_chat_members(chat):
        user_id = member.user.id
        url = (
            f"https://api.telegram.org/bot{BOT_TOKEN}/kickChatMember?chat_id={chat}&user_id={user_id}")
        async with aiohttp.ClientSession() as session:
            await session.get(url)

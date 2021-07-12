import re
import asyncio
from pyrogram import filters
from MusicKen.config import SUPPORT_GROUP
from MusicKen.config import SUDO_USERS
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait
from MusicKen.helpers.filters import command, other_filters
from pyrogram inport Client

async def subcribe(filter, client, message):
    if not SUPPORT_GROUP:
        return True
    user_id = message.from_user.id
    if user_id in SUDO_USERS:
        return True
    try:
        member = await client.get_chat_member(chat_id = SUPPORT_GROUP, user_id = user_id)
    except UserNotParticipant:
        return False

    if not member.status in ["creator", "administrator", "member"]:
        return False
    else:
        return True

@Client.on_message(command(["cplay","play","dplay","cdplay","splay"]) & other_filters)
async def not_joined(client: Client, message: Message):
    text = "<b>Anda harus join channel/Group untuk menggunakan saya\n\nTolong bergabunglah ke Channel/Group</b>"
    message_text = message.text
    try:
        text = text + f" <b>[👉KLIK SUB👈](https://t.me/{SUB_GROUP})</b>"
    except ValueError:
        pass
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("💌 JOIN 💌", url = f"t.me/{SUPPORT_GROUP}")]])
    await message.reply(
        text = text,
        reply_markup = reply_markup,
        quote = True,
        disable_web_page_preview = True
    )
    

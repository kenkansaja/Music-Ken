import re
import asyncio
from pyrogram import filters
from MusicKen.config import SUB_GROUP
from MusicKen.config import ADMINS
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait

async def is_subscribed(filter, client, message):
    if not SUB_GROUP:
        return True
    user_id = message.from_user.id
    if user_id in SUDO_USER:
        return True
    try:
        member = await client.get_chat_member(chat_id = SUB_GROUP, user_id = user_id)
    except UserNotParticipant:
        return False

    if not member.status in ["creator", "administrator", "member"]:
        return False
    else:
        return True

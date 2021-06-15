import re
import asyncio
from pyrogram import filters
from config import UPDATES_CHANNEL, ASSISTANT_NAME
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait

async def is_subscribed(filter, client, message):
    if not UPDATES_CHANNEL:
        return True
    user_id = message.from_user.id
    if user_id in ASSISTANT_NAME:
        return True
    try:
        member = await client.get_chat_member(chat_id = UPDATES_CHANNEL, user_id = user_id)
    except UserNotParticipant:
        return False

    if not member.status in ["creator", "administrator", "member"]:
        return False
    else:
        return True


subscribed = filters.create(is_subscribed)

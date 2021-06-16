import re
import asyncio
from pyrogram import filters
from MusicKen.config import SUPPORT_GROUP, ASSISTANT_NAME
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait

async def is_subscribed(filter, client, message):
    if not SUPPORT_GROUP:
        return True
    user_id = message.from_user.id
    if user_id in ASSISTANT_NAME:
        return True
    try:
        member = await client.get_chat_member(chat_id = SUPPORT_GROUP, user_id = user_id)
    except UserNotParticipant:
        return False

    if not member.status in ["creator", "administrator", "member"]:
        return False
    else:
        return True

async def get_messages(client, message_ids):
    messages = []
    total_messages = 0
    while total_messages != len(message_ids):
        temb_ids = message_ids[total_messages:total_messages+200]
        try:
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temb_ids
            )
        except FloodWait as e:
            await asyncio.sleep(e.x)
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temb_ids
            )
        except:
            pass
        total_messages += len(temb_ids)
        messages.extend(msgs)
    return messages

        
        subcribed = filters.create(is_subscribed)

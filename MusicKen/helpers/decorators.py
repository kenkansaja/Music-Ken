from typing import Callable
import asyncio
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant

from MusicKen.config import SUDO_USERS, SUPPORT_GROUP
from MusicKen.helpers.admins import get_administrators


def errors(func: Callable) -> Callable:
    async def decorator(client: Client, message: Message):
        try:
            return await func(client, message)
        except Exception as e:
            await message.reply(f"{type(e).__name__}: {e}")

    return decorator


def authorized_users_only(func: Callable) -> Callable:
    async def decorator(client: Client, message: Message):
        if message.from_user.id in SUDO_USERS:
            return await func(client, message)

        administrators = await get_administrators(message.chat)

        for administrator in administrators:
            if administrator == message.from_user.id:
                return await func(client, message)

    return decorator


def subscribe(func: Callable) -> Callable:
  async def decorator(client: Client, message: Message):
    if not SUPPORT_GROUP:
      return True
      user_id=message.from_user.id
    if user_id in SUDO_USERS:
      return True
      try:
        member=await client.get_chat_member(chat_id = SUPPORT_GROUP, user_id = user_id)
        except UserNotParticipant:
          return await message.reply("""**Anda harus bergabung dulu di group kami kak untuk bisa menggunakan bot ini**""",
                        reply_markup=InlineKeyboardMarkup(
                              [
                                  [
                                      InlineKeyboardButton(
                                          "💬 GROUP", url=f"https://t.me/{SUPPORT_GROUP}"
                                      ),
                                      InlineKeyboardButton(
                                          "OWNER 👮", url=f"https://t.me/kenkanasw"
                                      )
                                  ]
                              ]
                           )
                        )
                      return decorator

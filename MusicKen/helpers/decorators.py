from typing import Callable
from pyrogram import Client
from pyrogram.types import Message
from MusicKen.config import SUDO_USERS, BANNED
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

def banned_group(func: Callable) -> Callable:
    async def decorator(client: Client, message: Message):
        if message.from_user.id in BANNED:
           await message.reply("Maaf group atau channel anda telah masuk ke daftar yang dilarang menggunakan bot ini, kalau masih mau menggunakannya silahkan hubungi owner bot")
           return await func(client, message)

    return decorator
    
    

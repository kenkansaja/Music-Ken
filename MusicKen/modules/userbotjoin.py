import asyncio

from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant

from MusicKen.config import SUDO_USERS
from MusicKen.helpers.decorators import authorized_users_only, errors
from MusicKen.services.callsmusic.callsmusic import client as USER


@Client.on_message(filters.command(["userbotjoin"]) & ~filters.private & ~filters.bot)
@authorized_users_only
@errors
async def addchannel(client, message):
    message.chat.id
    try:
        invite_link = await client.chat.export_invite_link()
        if "+" in invite_link:
            link_hash = (invite_link.replace("+", "")).split("t.me/")[1]
    except:
        await message.reply_text(
            "<b>Tambahkan saya sebagai admin grup Anda terlebih dahulu</b>",
        )
        return

    try:
        user = await USER.get_me()
    except:
        user.first_name = "MusicKen"

    try:
        await USER.join_chat(f"https://t.me/joinchat/{link_hash}")
    except UserAlreadyParticipant:
        await message.reply_text(
            f"<b>{user.first_name} sudah ada di obrolan Anda</b>",
        )
    except Exception as e:
        print(e)
        await message.reply_text(
            f"<b>⛑ Flood Wait Error ⛑\n{user.first_name} tidak dapat bergabung dengan grup Anda karena banyaknya permintaan bergabung untuk userbot! Pastikan pengguna tidak dibanned dalam grup."
            "\n\nAtau tambahkan Assistant bot secara manual ke Grup Anda dan coba lagi.</b>",
        )
        return
    await message.reply_text(
        f"<b>{user.first_name} berhasil bergabung dengan obrolan Anda</b>",
    )


@USER.on_message(filters.group & filters.command(["userbotleave"]))
@authorized_users_only
async def rem(USER, message):
    try:
        await USER.leave_chat(message.chat.id)
    except:
        await message.reply_text(
            "<b>Pengguna tidak dapat meninggalkan grup Anda! Mungkin menunggu floodwaits."
            "\n\nAtau keluarkan saya secara manual dari ke Grup Anda</b>",
        )
        return


@Client.on_message(filters.command(["userbotleaveall"]))
async def bye(client, message):
    if message.from_user.id in SUDO_USERS:
        left = 0
        failed = 0
        lol = await message.reply("**Asisten Meninggalkan semua obrolan**")
        async for dialog in USER.iter_dialogs():
            try:
                await USER.leave_chat(dialog.chat.id)
                left = left + 1
                await lol.edit(
                    f"Asisten pergi... Berhasil: {left} obrolan. Gagal: {failed} obrolan."
                )
            except:
                failed = failed + 1
                await lol.edit(
                    f"Asisten pergi... Berhasil: {left} obrolan. Gagal: {failed} obrolan."
                )
            await asyncio.sleep(0.7)
        await client.send_message(
            message.chat.id, f"Berhasil {left} obrolan. Gagal {failed} obrolan."
        )


@Client.on_message(
    filters.command(["userbotjoinchannel", "ubjoinc"]) & ~filters.private & ~filters.bot
)
@authorized_users_only
@errors
async def addcchannel(client, message):
    try:
        conchat = await client.get_chat(message.chat.id)
        conid = conchat.linked_chat.id
        chid = conid
    except:
        await message.reply("Apakah obrolan terhubung?")
        return
    try:
        await client.export_chat_invite_link(chid)
        if "+" in invite_link:
            link_hash = (invite_link.replace("+", "")).split("t.me/")[1]
    except:
        await message.reply_text(
            "<b>Tambahkan saya sebagai admin saluran Anda terlebih dahulu</b>",
        )
        return

    try:
        user = await USER.get_me()
    except:
        user.first_name = "MusicKen"

    try:
        await USER.join_chat(f"https://t.me/joinchat/{link_hash}")
    except UserAlreadyParticipant:
        await message.reply_text(
            f"<b>{user.first_name} sudah ada di channel anda</b>",
        )
        return
    except Exception as e:
        print(e)
        await message.reply_text(
            f"<b>⛑ Flood Wait Error ⛑\n{user.first_name} tidak dapat bergabung dengan grup Anda karena banyaknya permintaan bergabung untuk userbot! Pastikan pengguna tidak dibanned dalam grup."
            "\n\nAtau tambahkan Assistant bot secara manual ke Grup Anda dan coba lagi.</b>",
        )
        return
    await message.reply_text(
        f"<b>{user.first_name} sudah bergabung dengan obrolan Anda</b>",
    )

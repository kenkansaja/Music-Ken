import json
import os
from os import path
from typing import Callable

import aiofiles
import aiohttp
import ffmpeg
import requests
import wget
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from pyrogram import Client
from pyrogram import filters
from pyrogram.types import Voice
from pyrogram.errors import UserAlreadyParticipant
from pyrogram.types import InlineKeyboardButton
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.types import Message
from Python_ARQ import ARQ
from youtube_search import YoutubeSearch

from MusicKen.config import ARQ_API_KEY
from MusicKen.config import BOT_NAME as bn
from MusicKen.config import DURATION_LIMIT
from MusicKen.config import ASSISTANT_NAME, SUPPORT_GROUP
from MusicKen.config import UPDATES_CHANNEL as updateschannel
from MusicKen.config import que
from MusicKen.function.admins import admins as a
from MusicKen.helpers.admins import get_administrators
from MusicKen.helpers.channelmusic import get_chat_id
from MusicKen.helpers.errors import DurationLimitError
from MusicKen.helpers.decorators import errors
from MusicKen.helpers.decorators import authorized_users_only
from MusicKen.helpers.filters import command
from MusicKen.helpers.filters import other_filters
from MusicKen.helpers.gets import get_file_name
from MusicKen.services.callsmusic import callsmusic
from MusicKen.services.callsmusic.callsmusic import client as USER
from MusicKen.services.converter.converter import convert
from MusicKen.services.downloaders import youtube
from MusicKen.services.queues import queues

aiohttpsession = aiohttp.ClientSession()
chat_id = None
arq = ARQ("https://thearq.tech", ARQ_API_KEY, aiohttpsession)
DISABLED_GROUPS = []
useer ="NaN"
def cb_admin_check(func: Callable) -> Callable:
    async def decorator(client, cb):
        admemes = a.get(cb.message.chat.id)
        if cb.from_user.id in admemes:
            return await func(client, cb)
        await cb.answer("Kamu Tidak diizinkan!", show_alert=True)
        return

    return decorator


def transcode(filename):
    ffmpeg.input(filename).output(
        "input.raw", format="s16le", acodec="pcm_s16le", ac=2, ar="48k"
    ).overwrite_output().run()
    os.remove(filename)


# Convert seconds to mm:ss
def convert_seconds(seconds):
    seconds = seconds % (24 * 3600)
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%02d:%02d" % (minutes, seconds)


# Convert hh:mm:ss to seconds
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


# Change image size
def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    return image.resize((newWidth, newHeight))


async def generate_cover(requested_by, title, views, duration, thumbnail):
    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail) as resp:
            if resp.status == 200:
                f = await aiofiles.open("background.png", mode="wb")
                await f.write(await resp.read())
                await f.close()

    image1 = Image.open("./background.png")
    image2 = Image.open("./etc/foreground.png")
    image3 = changeImageSize(1280, 720, image1)
    image4 = changeImageSize(1280, 720, image2)
    image5 = image3.convert("RGBA")
    image6 = image4.convert("RGBA")
    Image.alpha_composite(image5, image6).save("temp.png")
    img = Image.open("temp.png")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("etc/font.otf", 32)
    draw.text((205, 550), f"Judul: {title}", (51, 215, 255), font=font)
    draw.text((205, 590), f"Durasi: {duration}", (255, 255, 255), font=font)
    draw.text((205, 630), f"Dilihat: {views}", (255, 255, 255), font=font)
    draw.text(
        (205, 670),
        f"Permintaan: {requested_by}",
        (255, 255, 255),
        font=font,
    )
    img.save("final.png")
    os.remove("temp.png")
    os.remove("background.png")


@Client.on_message(filters.command("playlist") & filters.group & ~filters.edited)
async def playlist(client, message):
    global que
    if message.chat.id in DISABLED_GROUPS:
        return
    queue = que.get(message.chat.id)
    if not queue:
        await message.reply_text("**Sedang tidak Memutar lagu**")
    temp = [t for t in queue]
    now_playing = temp[0][0]
    by = temp[0][1].mention(style="md")
    msg = "**Lagu Yang Sedang dimainkan** di {}".format(message.chat.title)
    msg += "\n• " + now_playing
    msg += "\n• Request Dari " + by
    temp.pop(0)
    if temp:
        msg += "\n\n"
        msg += "**Antrian Lagu**"
        for song in temp:
            name = song[0]
            usr = song[1].mention(style="md")
            msg += f"\n• {name}"
            msg += f"\n• Request Dari {usr}\n"
    await message.reply_text(msg)


# ============================= Settings =========================================


def updated_stats(chat, queue, vol=100):
    if chat.id in callsmusic.active_chats:
        # if chat.id in active_chats:
        stats = "Pengaturan dari **{}**".format(chat.title)
        if len(que) > 0:
            stats += "\n\n"
            stats += "Volume : {}%\n".format(vol)
            stats += "Lagu dalam antrian : `{}`\n".format(len(que))
            stats += "Sedang memutar lagu : **{}**\n".format(queue[0][0])
            stats += "Permintaan : {}".format(queue[0][1].mention)
    else:
        stats = None
    return stats


def r_ply(type_):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏹", "leave"),
                InlineKeyboardButton("⏸", "puse"),
                InlineKeyboardButton("▶️", "resume"),
                InlineKeyboardButton("⏭", "skip"),
            ],
            [
                InlineKeyboardButton("📖 Playlist", "playlist"),
            ],
            [InlineKeyboardButton("❌ Close", "cls")],
        ]
    )


@Client.on_message(filters.command("current") & filters.group & ~filters.edited)
async def ee(client, message):
    if message.chat.id in DISABLED_GROUPS:
        return
    queue = que.get(message.chat.id)
    stats = updated_stats(message.chat, queue)
    if stats:
        await message.reply(stats)
    else:
        await message.reply("**Silahkan Nyalakan dulu VCG nya!**")


@Client.on_message(filters.command("player") & filters.group & ~filters.edited)
@authorized_users_only
async def settings(client, message):
    if message.chat.id in DISABLED_GROUPS:
        await message.reply("Music Player is Disabled")
        return    
    playing = None
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.active_chats:
        playing = True
    queue = que.get(chat_id)
    stats = updated_stats(message.chat, queue)
    if stats:
        if playing:
            await message.reply(stats, reply_markup=r_ply("pause")) 
        else:
            await message.reply(stats, reply_markup=r_ply("play"))
    else:
        await message.reply("**Silahkan Nyalakan dulu VCG nya!**")


@Client.on_message(
    filters.command("musicplayer") & ~filters.edited & ~filters.bot & ~filters.private
)
@authorized_users_only
async def hfmm(_, message):
    global DISABLED_GROUPS
    try:
        user_id = message.from_user.id
    except:
        return
    if len(message.command) != 2:
        await message.reply_text(
            "**Saya hanya mengenali** `/musicplayer on` **dan** `/musicplayer off`"
        )
        return
    status = message.text.split(None, 1)[1]
    message.chat.id
    if status in ["ON", "on", "On"]:
        lel = await message.reply("`Processing...`")
        if message.chat.id not in DISABLED_GROUPS:
            await lel.edit("**Pemutar Musik Sudah Diaktifkan Di Obrolan Ini**")
            return
        DISABLED_GROUPS.remove(message.chat.id)
        await lel.edit(
            f"**Pemutar Musik Berhasil Diaktifkan Untuk Pengguna Dalam Obrolan** {message.chat.id}"
        )

    elif status in ["OFF", "off", "Off"]:
        lel = await message.reply("`Processing...`")

        if message.chat.id in DISABLED_GROUPS:
            await lel.edit("**Pemutar Musik Sudah dimatikan Dalam Obrolan Ini**")
            return
        DISABLED_GROUPS.append(message.chat.id)
        await lel.edit(
            f"**Pemutar Musik Berhasil Dinonaktifkan Untuk Pengguna Dalam Obrolan** {message.chat.id}"
        )
    else:
        await message.reply_text(
            "**Saya hanya mengenali** `/musicplayer on` **dan** `/musicplayer off`"
        )    
        

@Client.on_callback_query(filters.regex(pattern=r"^(playlist)$"))
async def p_cb(b, cb):
    global que
    que.get(cb.message.chat.id)
    type_ = cb.matches[0].group(1)
    cb.message.chat.id
    cb.message.chat
    cb.message.reply_markup.inline_keyboard[1][0].callback_data
    if type_ == "playlist":
        queue = que.get(cb.message.chat.id)
        if not queue:
            await cb.message.edit("**Sedang tidak Memutar lagu**")
        temp = [t for t in queue]
        now_playing = temp[0][0]
        by = temp[0][1].mention(style="md")
        msg = "<b>Lagu Yang Sedang dimainkan</b> di {}".format(cb.message.chat.title)
        msg += "\n- " + now_playing
        msg += "\n- Request Dari " + by
        temp.pop(0)
        if temp:
            msg += "\n\n"
            msg += "**Antrian Lagu**"
            for song in temp:
                name = song[0]
                usr = song[1].mention(style="md")
                msg += f"\n- {name}"
                msg += f"\n- Permintaan {usr}\n"
        await cb.message.edit(msg)


@Client.on_callback_query(
    filters.regex(pattern=r"^(play|pause|skip|leave|puse|resume|menu|cls)$")
)
async def m_cb(b, cb):
    global que
    if (
        cb.message.chat.title.startswith("Channel Music: ")
        and chat.title[14:].isnumeric()
    ):
        chet_id = int(chat.title[13:])
    else:
        chet_id = cb.message.chat.id
    qeue = que.get(chet_id)
    type_ = cb.matches[0].group(1)
    cb.message.chat.id
    m_chat = cb.message.chat

    the_data = cb.message.reply_markup.inline_keyboard[1][0].callback_data
    if type_ == "pause":
        if (chet_id not in callsmusic.active_chats) or (
            callsmusic.active_chats[chet_id] == "paused"
        ):
            await cb.answer("**Sedang Tidak Terhubung dengan VCG**", show_alert=True)
        else:
            callsmusic.pause(chet_id)
            await cb.answer("Music Paused!")
            await cb.message.edit(
                updated_stats(m_chat, qeue), reply_markup=r_ply("play")
            )

    elif type_ == "play":
        if (chet_id not in callsmusic.active_chats) or (
            callsmusic.active_chats[chet_id] == "playing"
        ):
            await cb.answer("Seda", show_alert=True)
        else:
            callsmusic.resume(chet_id)
            await cb.answer("Music Resumed!")
            await cb.message.edit(
                updated_stats(m_chat, qeue), reply_markup=r_ply("pause")
            )

    elif type_ == "playlist":
        queue = que.get(cb.message.chat.id)
        if not queue:
            await cb.message.edit("**Sedang tidak Memutar lagu**")
        temp = [t for t in queue]
        now_playing = temp[0][0]
        by = temp[0][1].mention(style="md")
        msg = "**Lagu Yang Sedang dimainkan** di {}".format(cb.message.chat.title)
        msg += "\n- " + now_playing
        msg += "\n- Request Dari " + by
        temp.pop(0)
        if temp:
            msg += "\n\n"
            msg += "**Antrian Lagu**"
            for song in temp:
                name = song[0]
                usr = song[1].mention(style="md")
                msg += f"\n- {name}"
                msg += f"\n- Request Dari {usr}\n"
        await cb.message.edit(msg)

    elif type_ == "resume":
        if (chet_id not in callsmusic.active_chats) or (
            callsmusic.active_chats[chet_id] == "playing"
        ):
            await cb.answer("**Obrolan tidak terhubung atau sudah diputar**", show_alert=True)
        else:
            callsmusic.resume(chet_id)
            await cb.answer("Music Resumed!")
    elif type_ == "puse":
        if (chet_id not in callsmusic.active_chats) or (
            callsmusic.active_chats[chet_id] == "paused"
        ):
            await cb.answer("**Obrolan tidak terhubung atau sudah dipause**", show_alert=True)
        else:
            callsmusic.pause(chet_id)
            await cb.answer("Music Paused!")
    elif type_ == "cls":
        await cb.answer("Closed menu")
        await cb.message.delete()

    elif type_ == "menu":
        stats = updated_stats(cb.message.chat, qeue)
        await cb.answer("Menu opened")
        marr = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("⏹", "leave"),
                    InlineKeyboardButton("⏸", "puse"),
                    InlineKeyboardButton("▶️", "resume"),
                    InlineKeyboardButton("⏭", "skip"),
                ],
                [
                    InlineKeyboardButton("Playlist 📖", "playlist"),
                ],
                [InlineKeyboardButton("❌ Close", "cls")],
            ]
        )
        await cb.message.edit(stats, reply_markup=marr)
    elif type_ == "skip":
        if qeue:
            qeue.pop(0)
        if chet_id not in callsmusic.active_chats:
            await cb.answer("**Sedang Tidak Terhubung dengan VCG**", show_alert=True)
        else:
            queues.task_done(chet_id)
            if queues.is_empty(chet_id):
                callsmusic.stop(chet_id)
                await cb.message.edit("- Tidak ada Playlist..\n- Keluar dari VCG!")
            else:
                await callsmusic.set_stream(
                    chet_id, queues.get(chet_id)["file"]
                )
                await cb.answer.reply_text("✅ <b>Melewati Lagu</b>")
                await cb.message.edit((m_chat, qeue), reply_markup=r_ply(the_data))
                await cb.message.reply_text(
                    f"- Skipped track\n- Now Playing **{qeue[0][0]}**"
                )

    elif chet_id in callsmusic.active_chats:
        try:
           queues.clear(chet_id)
        except QueueEmpty:
            pass

        await callsmusic.stop(chet_id)
        await cb.message.edit("Successfully Left the Chat!")
    else:
        await cb.answer("**Sedang Tidak Terhubung dengan VCG**", show_alert=True)


@Client.on_message(command("play") & other_filters)
@errors
async def play(_, message: Message):
    global que
    global useer
    if message.chat.id in DISABLED_GROUPS:
        return
    lel = await message.reply("🔄 **Sedang Memproses Lagu**")
    administrators = await get_administrators(message.chat)
    chid = message.chat.id

    try:
        user = await USER.get_me()
    except:
        user.first_name = "MusicKen"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await _.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message.from_user.id:
                if message.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        f"<b>Ingatlah untuk menambahkan {user.first_name} ke Channel Anda</b>",
                    )
                try:
                    invitelink = await _.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>Tambahkan saya sebagai admin grup Anda terlebih dahulu</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await lel.edit(
                        f"<b>{user.first_name} berhasil bergabung dengan Group anda</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>⛑ Flood Wait Error ⛑\n{user.first_name} tidak dapat bergabung dengan grup Anda karena banyaknya permintaan bergabung untuk userbot! Pastikan pengguna tidak dibanned dalam grup."
                        f"\n\nAtau tambahkan @{ASSISTANT_NAME} secara manual ke Grup Anda dan coba lagi</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i>{user.first_name} terkena banned dari Grup ini, Minta admin untuk mengirim perintah `/unban @{ASSISTANT_NAME}` secara manual, Lalu coba play lagi.</i>"
        )
        return
    text_links=None
    await lel.edit("🔄 **Sedang Mencari Lagu**")
    if message.reply_to_message:
        entities = []
        toxt = message.reply_to_message.text or message.reply_to_message.caption
        if (
            message.reply_to_message.entities
            or message.reply_to_message.caption_entities
        ):
            entities = message.reply_to_message.entities + entities
        urls = [entity for entity in entities if entity.type == 'url']
        text_links = [
            entity for entity in entities if entity.type == 'text_link'
        ]
    else:
        urls=None
    if text_links:
        urls = True
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    rpk = "[" + user_name + "](tg://user?id=" + str(user_id) + ")"
    audio = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )
    if audio:
        if round(audio.duration / 60) > DURATION_LIMIT:
            await lel.edit(
                f"❌ **Lagu dengan durasi lebih dari** `{DURATION_LIMIT}` **menit tidak bisa diputar!**"
            )
            return
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("📖 ᴅᴀғᴛᴀʀ", callback_data="playlist"),
                    InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ 💬", url=f"https://t.me/{SUPPORT_GROUP}"),
                ],
                [
                    InlineKeyboardButton(text="🎬 ʏᴏᴜᴛᴜʙᴇ", url=f"{url}"),
                    InlineKeyboardButton(text="ᴅᴏᴡɴʟᴏᴀᴅ 📥", url=f"{dlurl}"),
                ],
                [InlineKeyboardButton(text="🗑️ ᴛᴜᴛᴜᴘ 🗑️", callback_data="cls")],
            ]
        )
        file_name = get_file_name(audio)
        title = file_name
        thumb_name = "https://telegra.ph/file/463d7fc1d98d2da673370.jpg"
        thumbnail = thumb_name
        duration = round(audio.duration / 60)
        views = "Locally added"
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)
        file_path = await convert(
            (await message.reply_to_message.download(file_name))
            if not path.isfile(path.join("downloads", file_name))
            else file_name
        )
    elif urls:
        query = toxt
        await lel.edit("🎵 **Sedang Memproses Lagu**")
        ydl_opts = {"format": "bestaudio[ext=m4a]"}
        try:
            results = YoutubeSearch(query, max_results=1).to_dict()
            url = f"https://youtube.com{results[0]['url_suffix']}"
            # print(results)
            title = results[0]["title"][:40]
            thumbnail = results[0]["thumbnails"][0]
            thumb_name = f"thumb{title}.jpg"
            thumb = requests.get(thumbnail, allow_redirects=True)
            open(thumb_name, "wb").write(thumb.content)
            duration = results[0]["duration"]
            results[0]["url_suffix"]
            views = results[0]["views"]

        except Exception as e:
            await lel.edit(
                "**Lagu tidak ditemukan.** Coba cari dengan judul lagu yang lebih jelas, Ketik `/help` bila butuh bantuan"
            )
            print(str(e))
            return
        try:    
            secmul, dur, dur_arr = 1, 0, duration.split(':')
            for i in range(len(dur_arr)-1, -1, -1):
                dur += (int(dur_arr[i]) * secmul)
                secmul *= 60
            if (dur / 60) > DURATION_LIMIT:
                 await lel.edit(f"❌ **Lagu dengan durasi lebih dari** `{DURATION_LIMIT}` **menit tidak bisa diputar!**")
                 return
        except:
            pass        
        dlurl=url
        dlurl=dlurl.replace("youtube","youtubepp")
        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("📖 ᴅᴀғᴛᴀʀ", callback_data="playlist"),
                    InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ 💬", url=f"https://t.me/{SUPPORT_GROUP}"),
                ],
                [
                    InlineKeyboardButton(text="🎬 ʏᴏᴜᴛᴜʙᴇ", url=f"{url}"),
                    InlineKeyboardButton(text="ᴅᴏᴡɴʟᴏᴀᴅ 📥", url=f"{dlurl}"),
                ],
                [InlineKeyboardButton(text="🗑️ ᴛᴜᴛᴜᴘ 🗑️", callback_data="cls")],
            ]
        )
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)
        file_path = await convert(youtube.download(url))
    else:
        query = "".join(" " + str(i) for i in message.command[1:])
        print(query)
        await lel.edit("🎵 **Sedang Memproses Lagu**")
        ydl_opts = {"format": "bestaudio[ext=m4a]"}

        try:
          results = YoutubeSearch(query, max_results=5).to_dict()
        except:
          await lel.edit("**Beri Judul Lagu untuk diputar**")
        # Looks like hell. Aren't it?? FUCK OFF
        try:
            toxxt = "**Silahkan Pilih lagu yang ingin Anda Putar:**\n\n"
            useer=user_name
            emojilist = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣",]

            for j in range(5):
                toxxt += f"{emojilist[j]} Judul - [{results[j]['title']}](https://youtube.com{results[j]['url_suffix']})\n"
                toxxt += f" ├ **Durasi** - {results[j]['duration']}\n"
                toxxt += f" └ **Dilihat** - {results[j]['views']}\n\n"

            koyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("1️⃣", callback_data=f'plll 0|{query}|{user_id}'),
                        InlineKeyboardButton("2️⃣", callback_data=f'plll 1|{query}|{user_id}'),
                        InlineKeyboardButton("3️⃣", callback_data=f'plll 2|{query}|{user_id}'),
                    ],
                    [
                        InlineKeyboardButton("4️⃣", callback_data=f'plll 3|{query}|{user_id}'),
                        InlineKeyboardButton("5️⃣", callback_data=f'plll 4|{query}|{user_id}'),
                    ],
                    [InlineKeyboardButton(text="❌ ʙᴀᴛᴀʟ ❌", callback_data="cls")],
                ]
            )
            await lel.edit(toxxt,reply_markup=koyboard,disable_web_page_preview=True)
            # WHY PEOPLE ALWAYS LOVE PORN ?? (A point to think)
            return
                    # Returning to pornhub
        except:
            await lel.edit("**Memulai bermain langsung..**")

            # print(results)
            try:
                url = f"https://youtube.com{results[0]['url_suffix']}"
                title = results[0]["title"][:40]
                thumbnail = results[0]["thumbnails"][0]
                thumb_name = f"thumb{title}.jpg"
                thumb = requests.get(thumbnail, allow_redirects=True)
                open(thumb_name, "wb").write(thumb.content)
                duration = results[0]["duration"]
                results[0]["url_suffix"]
                views = results[0]["views"]

            except Exception as e:
                await lel.edit(
                    "**Lagu tidak ditemukan.** Coba cari dengan judul lagu yang lebih jelas, Ketik `/help` bila butuh bantuan"
                )
                print(str(e))
                return
            try:    
                secmul, dur, dur_arr = 1, 0, duration.split(':')
                for i in range(len(dur_arr)-1, -1, -1):
                    dur += (int(dur_arr[i]) * secmul)
                    secmul *= 60
                if (dur / 60) > DURATION_LIMIT:
                     await lel.edit(f"❌ **Lagu dengan durasi lebih dari** `{DURATION_LIMIT}` **menit tidak bisa diputar!**")
                     return
            except:
                pass
            dlurl=url
            dlurl=dlurl.replace("youtube","youtubepp")
            keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("📖 ᴅᴀғᴛᴀʀ", callback_data="playlist"),
                    InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ 💬", url=f"https://t.me/{SUPPORT_GROUP}"),
                ],
                [
                    InlineKeyboardButton(text="🎬 ʏᴏᴜᴛᴜʙᴇ", url=f"{url}"),
                    InlineKeyboardButton(text="ᴅᴏᴡɴʟᴏᴀᴅ 📥", url=f"{dlurl}"),
                ],
                [InlineKeyboardButton(text="🗑️ ᴛᴜᴛᴜᴘ 🗑️", callback_data="cls")],
            ]
        )
            requested_by = message.from_user.first_name
            await generate_cover(requested_by, title, views, duration, thumbnail)
            file_path = await convert(youtube.download(url))
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.active_chats:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await message.reply_photo(
            photo="final.png",
            caption = f"🏷 **Judul:** {title}\n⏱ **Durasi:** {duration}\n💡 **Status:** Antrian Ke {position}\n" \
                    + f"🎧 **Permintaan:** {message.from_user.mention}",
                   reply_markup=keyboard)
    else:
        chat_id = get_chat_id(message.chat)
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            await callsmusic.set_stream(chat_id, file_path)
        except:
            message.reply("**Voice Chat Group tidak aktif, Saya tidak dapat bergabung**")
            return
        await message.reply_photo(
            photo="final.png",
            caption = f"🏷 **Judul:** {title}\n⏱ **Durasi:** {duration}\n💡 **Status:** Memutar\n" \
                    + f"🎧 **Permintaan:** {message.from_user.mention}",
                   reply_markup=keyboard)

    os.remove("final.png")
    return await lel.delete()


@Client.on_message(filters.command("ytplay") & filters.group & ~filters.edited)
@errors
async def ytplay(_, message: Message):
    global que
    if message.chat.id in DISABLED_GROUPS:
        return
    lel = await message.reply("🔄 **Sedang Memproses Lagu**")
    administrators = await get_administrators(message.chat)
    chid = message.chat.id

    try:
        user = await USER.get_me()
    except:
        user.first_name = "helper"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await _.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message.from_user.id:
                if message.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        f"<b>Ingatlah untuk menambahkan {user.first_name} ke Channel Anda</b>",
                    )
                try:
                    invitelink = await _.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>Tambahkan saya sebagai admin grup Anda terlebih dahulu</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await lel.edit(
                        f"<b>{user.first_name} berhasil bergabung dengan Group anda</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>⛑ Flood Wait Error ⛑\n{user.first_name} tidak dapat bergabung dengan grup Anda karena banyaknya permintaan bergabung untuk userbot! Pastikan pengguna tidak dibanned dalam grup."
                        f"\n\nAtau tambahkan @{ASSISTANT_NAME} secara manual ke Grup Anda dan coba lagi</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i>{user.first_name} terkena banned dari Grup ini, Minta admin untuk mengirim perintah `/unban @{ASSISTANT_NAME}` secara manual, Lalu coba play lagi.</i>"
        )
        return
    await lel.edit("🔎 ** Sedang Mencari lagu**")
    user_id = message.from_user.id
    user_name = message.from_user.first_name


    query = "".join(" " + str(i) for i in message.command[1:])
    print(query)
    await lel.edit("🎵 **Sedang Memproses Lagu**")
    ydl_opts = {"format": "bestaudio[ext=m4a]"}
    try:
        results = YoutubeSearch(query, max_results=1).to_dict()
        url = f"https://youtube.com{results[0]['url_suffix']}"
        # print(results)
        title = results[0]["title"][:40]
        thumbnail = results[0]["thumbnails"][0]
        thumb_name = f"thumb{title}.jpg"
        thumb = requests.get(thumbnail, allow_redirects=True)
        open(thumb_name, "wb").write(thumb.content)
        duration = results[0]["duration"]
        results[0]["url_suffix"]
        views = results[0]["views"]

    except Exception as e:
        await lel.edit(
            "**Lagu tidak ditemukan.** Coba cari dengan judul lagu yang lebih jelas, Ketik `/help` bila butuh bantuan"
        )
        print(str(e))
        return
    try:    
        secmul, dur, dur_arr = 1, 0, duration.split(':')
        for i in range(len(dur_arr)-1, -1, -1):
            dur += (int(dur_arr[i]) * secmul)
            secmul *= 60
        if (dur / 60) > DURATION_LIMIT:
             await lel.edit(f"❌ **Lagu dengan durasi lebih dari** `{DURATION_LIMIT}` **menit tidak bisa diputar!**")
             return
    except:
        pass
    dlurl=url
    dlurl=dlurl.replace("youtube","youtubepp")
    keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("📖 ᴅᴀғᴛᴀʀ", callback_data="playlist"),
                    InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ 💬", url=f"https://t.me/{SUPPORT_GROUP}"),
                ],
                [
                    InlineKeyboardButton(text="🎬 ʏᴏᴜᴛᴜʙᴇ", url=f"{url}"),
                    InlineKeyboardButton(text="ᴅᴏᴡɴʟᴏᴀᴅ 📥", url=f"{dlurl}"),
                ],
                [InlineKeyboardButton(text="🗑️ ᴛᴜᴛᴜᴘ 🗑️", callback_data="cls")],
            ]
        )
    requested_by = message.from_user.first_name
    await generate_cover(requested_by, title, views, duration, thumbnail)
    file_path = await convert(youtube.download(url))
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.active_chats:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await message.reply_photo(
            photo="final.png",
            caption = f"🏷 **Judul:** {title}\n⏱ **Durasi:** {duration}\n💡 **Status:** Antrian Ke {position}\n" \
                    + f"🎧 **Permintaan:** {message.from_user.mention}",
                   reply_markup=keyboard,
        )
    else:
        chat_id = get_chat_id(message.chat)
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
           await callsmusic.set_stream(chat_id, file_path)
        except:
            message.reply("Voice Chat Group tidak aktif, Saya tidak dapat bergabung")
            return
        await message.reply_photo(
            photo="final.png",
            caption = f"🏷 **Judul:** {title}\n⏱ **Durasi:** {duration}\n💡 **Status:** Memutar\n" \
                    + f"🎧 **Permintaan:** {message.from_user.mention}",
                   reply_markup=keyboard,)

    os.remove("final.png")
    return await lel.delete()
    
@Client.on_message(filters.command("dplay") & filters.group & ~filters.edited)
async def deezer(client: Client, message_: Message):
    if message_.chat.id in DISABLED_GROUPS:
        return
    global que
    lel = await message_.reply("🔄 **Sedang Memproses Lagu**")
    administrators = await get_administrators(message_.chat)
    chid = message_.chat.id
    try:
        user = await USER.get_me()
    except:
        user.first_name = "MusicKen"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await client.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message_.from_user.id:
                if message_.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        f"<b>Ingatlah untuk menambahkan {user.first_name} ke Channel Anda</b>",
                    )
                try:
                    invitelink = await client.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>Tambahkan saya sebagai admin grup Anda terlebih dahulu</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await lel.edit(
                        f"<b>{user.first_name} berhasil bergabung dengan Group anda</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>⛑ Flood Wait Error ⛑\n{user.first_name} tidak dapat bergabung dengan grup Anda karena banyaknya permintaan bergabung untuk userbot! Pastikan pengguna tidak dibanned dalam grup."
                        f"\n\nAtau tambahkan @{ASSISTANT_NAME} secara manual ke Grup Anda dan coba lagi</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i>{user.first_name} terkena banned dari Grup ini, Minta admin untuk mengirim perintah `/unban @{ASSISTANT_NAME}` secara manual, Lalu coba play lagi.</i>"
        )
        return
    requested_by = message_.from_user.first_name

    text = message_.text.split(" ", 1)
    queryy = text[1]
    query = queryy
    res = lel
    await res.edit(f"**Sedang Mencari Lagu** `{query}` **dari deezer**")
    try:
        songs = await arq.deezer(query,1)
        if not songs.ok:
            await message_.reply_text(songs.result)
            return
        title = songs.result[0].title
        url = songs.result[0].url
        artist = songs.result[0].artist
        duration = songs.result[0].duration
        thumbnail = "https://telegra.ph/file/463d7fc1d98d2da673370.jpg"

    except:
        await res.edit("**Tidak Ditemukan Lagu Apa Pun!**")
        return
    try:    
        duuration= round(duration / 60)
        if duuration > DURATION_LIMIT:
            await cb.message.edit(f"**Lagu lebih lama dari** `{DURATION_LIMIT}` menit tidak diperbolehkan diputar")
            return
    except:
        pass    

    keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("📖 ᴅᴀғᴛᴀʀ", callback_data="playlist"),
                    InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ 💬", url=f"https://t.me/{SUPPORT_GROUP}"),
                ],
                [
                    InlineKeyboardButton(text="🎬 ᴅᴇɴɢᴀʀ ᴅɪ ᴅᴇᴇᴢᴇʀ 🎬", url=f"{url}"),
                ],
                [InlineKeyboardButton(text="🗑️ ᴛᴜᴛᴜᴘ 🗑️", callback_data="cls")],
            ]
        )
    file_path = await convert(wget.download(url))
    await res.edit("Generating Thumbnail")
    await generate_cover(requested_by, title, artist, duration, thumbnail)
    chat_id = get_chat_id(message_.chat)
    if chat_id in callsmusic.active_chats:
        await res.edit("adding in queue")
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await res.edit_text(f"✯{bn}✯= #️⃣ Queued at position {position}")
    else:
        await res.edit_text(f"✯{bn}✯=▶️ Playing.....")

        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            await callsmusic.set_stream(chat_id, file_path)
        except:
            res.edit("Voice Chat Group tidak aktif, Saya tidak dapat bergabung")
            return

    await res.delete()

    m = await client.send_photo(
        chat_id=message_.chat.id,
        reply_markup=keyboard,
        photo="final.png",
        caption=f"Playing [{title}]({url}) Via Deezer",
    )
    os.remove("final.png")


@Client.on_message(filters.command("splay") & filters.group & ~filters.edited)
async def jiosaavn(client: Client, message_: Message):
    global que
    if message_.chat.id in DISABLED_GROUPS:
        return
    lel = await message_.reply("🔄 **Sedang Memproses Lagu**")
    administrators = await get_administrators(message_.chat)
    chid = message_.chat.id
    try:
        user = await USER.get_me()
    except:
        user.first_name = "MusicKen"
    usar = user
    wew = usar.id
    try:
        # chatdetails = await USER.get_chat(chid)
        await client.get_chat_member(chid, wew)
    except:
        for administrator in administrators:
            if administrator == message_.from_user.id:
                if message_.chat.title.startswith("Channel Music: "):
                    await lel.edit(
                        f"<b>Ingatlah untuk menambahkan {user.first_name} ke Channel Anda</b>",
                    )
                try:
                    invitelink = await client.export_chat_invite_link(chid)
                except:
                    await lel.edit(
                        "<b>Tambahkan saya sebagai admin grup Anda terlebih dahulu</b>",
                    )
                    return

                try:
                    await USER.join_chat(invitelink)
                    await lel.edit(
                        f"<b>{user.first_name} berhasil bergabung dengan Group anda</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>⛑ Flood Wait Error ⛑\n{user.first_name} tidak dapat bergabung dengan grup Anda karena banyaknya permintaan bergabung untuk userbot! Pastikan pengguna tidak dibanned dalam grup."
                        f"\n\nAtau tambahkan @{ASSISTANT_NAME} secara manual ke Grup Anda dan coba lagi</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i>{user.first_name} terkena banned dari Grup ini, Minta admin untuk mengirim perintah `/unban @{ASSISTANT_NAME}` secara manual, Lalu coba play lagi.</i>"
        )
        return
    requested_by = message_.from_user.first_name
    chat_id = message_.chat.id
    text = message_.text.split(" ", 1)
    query = text[1]
    res = lel
    await res.edit(f"Searching 🔍 for `{query}` on jio saavn")
    try:
        songs = await arq.saavn(query)
        if not songs.ok:
            await message_.reply_text(songs.result)
            return
        sname = songs.result[0].song
        slink = songs.result[0].media_url
        ssingers = songs.result[0].singers
        sthumb = songs.result[0].image
        sduration = int(songs.result[0].duration)
    except Exception as e:
        await res.edit("**Tidak Ditemukan Lagu Apa Pun!**")
        print(str(e))
        return
    try:    
        duuration= round(sduration / 60)
        if duuration > DURATION_LIMIT:
            await cb.message.edit(f"**Lagu lebih lama dari** `{DURATION_LIMIT}` menit tidak diperbolehkan diputar")
            return
    except:
        pass
    keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("📖 ᴅᴀғᴛᴀʀ", callback_data="playlist"),
                    InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ 💬", url=f"https://t.me/{SUPPORT_GROUP}"),
                ],
                [InlineKeyboardButton(text="🗑️ ᴛᴜᴛᴜᴘ 🗑️", callback_data="cls")],
            ]
        )
    file_path = await convert(wget.download(slink))
    chat_id = get_chat_id(message_.chat)
    if chat_id in callsmusic.active_chats:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = sname
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await res.delete()
        m = await client.send_photo(
            chat_id=message_.chat.id,
            reply_markup=keyboard,
            photo="final.png",
            caption=f"✯{bn}✯=#️⃣ Queued at position {position}",
        )

    else:
        await res.edit_text(f"{bn}=▶️ Playing.....")
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = sname
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            await callsmusic.set_stream(chat_id, file_path)
        except:
            res.edit("Voice Chat Group tidak aktif, Saya tidak dapat bergabung")
            return
    await res.edit("Generating Thumbnail.")
    await generate_cover(requested_by, sname, ssingers, sduration, sthumb)
    await res.delete()
    m = await client.send_photo(
        chat_id=message_.chat.id,
        reply_markup=keyboard,
        photo="final.png",
        caption=f"Playing {sname} Via Jiosaavn",
    )
    os.remove("final.png")


@Client.on_callback_query(filters.regex(pattern=r"plll"))
async def lol_cb(b, cb):
    global que

    cbd = cb.data.strip()
    chat_id = cb.message.chat.id
    typed_=cbd.split(None, 1)[1]
    #useer_id = cb.message.reply_to_message.from_user.id
    try:
        x,query,useer_id = typed_.split("|")      
    except:
        await cb.message.edit("Lagu Tidak ditemukan")
        return
    useer_id = int(useer_id)
    if cb.from_user.id != useer_id:
        await cb.answer("Anda bukan orang yang meminta untuk memutar lagu!", show_alert=True)
        return
    await cb.message.edit("🔄 **Sedang Memproses Lagu**")
    x=int(x)
    try:
        useer_name = cb.message.reply_to_message.from_user.first_name
    except:
        useer_name = cb.message.from_user.first_name

    results = YoutubeSearch(query, max_results=5).to_dict()
    resultss=results[x]["url_suffix"]
    title=results[x]["title"][:40]
    thumbnail=results[x]["thumbnails"][0]
    duration=results[x]["duration"]
    views=results[x]["views"]
    url = f"https://youtube.com{resultss}"

    try:    
        secmul, dur, dur_arr = 1, 0, duration.split(':')
        for i in range(len(dur_arr)-1, -1, -1):
            dur += (int(dur_arr[i]) * secmul)
            secmul *= 60
        if (dur / 60) > DURATION_LIMIT:
             await cb.message.edit(f"**Lagu lebih lama dari** `{DURATION_LIMIT}` menit tidak diperbolehkan diputar")
             return
    except:
        pass
    try:
        thumb_name = f"thumb{title}.jpg"
        thumb = requests.get(thumbnail, allow_redirects=True)
        open(thumb_name, "wb").write(thumb.content)
    except Exception as e:
        print(e)
        return
    dlurl=url
    dlurl=dlurl.replace("youtube","youtubepp")
    keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("📖 ᴅᴀғᴛᴀʀ", callback_data="playlist"),
                    InlineKeyboardButton("sᴜᴘᴘᴏʀᴛ 💬", url=f"https://t.me/{SUPPORT_GROUP}"),
                ],
                [
                    InlineKeyboardButton(text="🎬 ʏᴏᴜᴛᴜʙᴇ", url=f"{url}"),
                    InlineKeyboardButton(text="ᴅᴏᴡɴʟᴏᴀᴅ 📥", url=f"{dlurl}"),
                ],
                [InlineKeyboardButton(text="🗑️ ᴛᴜᴛᴜᴘ 🗑️", callback_data="cls")],
            ]
        )
    requested_by = useer_name
    await generate_cover(requested_by, title, views, duration, thumbnail)
    file_path = await convert(youtube.download(url))
    if chat_id in callsmusic.active_chats:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        try:
            r_by = cb.message.reply_to_message.from_user
        except:
            r_by = cb.message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await cb.message.delete()
        await b.send_photo(chat_id,
            photo="final.png",
            caption = f"🏷 **Judul:** {title}\n⏱ **Durasi:** {duration}\n💡 **Status:** Antrian Ke {position}\n" \
                    + f"🎧 **Permintaan:** {r_by.mention}",
                   reply_markup=keyboard,
        )
    else:
        que[chat_id] = []
        qeue = que.get(chat_id)
        s_name = title
        try:
            r_by = cb.message.reply_to_message.from_user
        except:
            r_by = cb.message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)

        await callsmusic.set_stream(chat_id, file_path)
        await cb.message.delete()
        await b.send_photo(chat_id,
            photo="final.png",
            caption = f"🏷 **Judul:** {title}\n⏱ **Durasi:** {duration}\n💡 **Status:** Memutar\n" \
                    + f"🎧 **Permintaan:** {r_by.mention}",
                    reply_markup=keyboard,
        )


    os.remove("final.png")

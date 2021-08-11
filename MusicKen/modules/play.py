import json
import os
from os import path
from typing import Callable

import aiofiles
import aiohttp
import ffmpeg
import requests
import wget
from PIL import Image, ImageDraw, ImageFont
from pyrogram import Client, filters
from pyrogram.types import Voice
from pyrogram.errors import UserAlreadyParticipant
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from Python_ARQ import ARQ
from youtube_search import YoutubeSearch

from MusicKen.config import ARQ_API_KEY
from MusicKen.config import BOT_NAME as bn
from MusicKen.config import DURATION_LIMIT
from MusicKen.config import UPDATES_CHANNEL as updateschannel
from MusicKen.config import SUPPORT_GROUP as groupsupport
from MusicKen.config import que
from MusicKen.function.admins import admins as a
from MusicKen.helpers.admins import get_administrators
from MusicKen.helpers.channelmusic import get_chat_id
from MusicKen.helpers.errors import DurationLimitError
from MusicKen.helpers.decorators import errors

from MusicKen.helpers.decorators import authorized_users_only
from MusicKen.helpers.filters import command, other_filters
from MusicKen.helpers.gets import get_file_name
from MusicKen.services.callsmusic import callsmusic, queues
from MusicKen.services.callsmusic.callsmusic import client as USER
from MusicKen.services.converter.converter import convert
from MusicKen.services.downloaders import youtube


aiohttpsession = aiohttp.ClientSession()
chat_id = None
arq = ARQ("https://thearq.tech", ARQ_API_KEY, aiohttpsession)
DISABLED_GROUPS = []
useer ="MusicKen"
def cb_admin_check(func: Callable) -> Callable:
    async def decorator(client, cb):
        admemes = a.get(cb.message.chat.id)
        if cb.from_user.id in admemes:
            return await func(client, cb)
        await cb.answer("Kamu tidak diizinkan!", show_alert=True)
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
    newImage = image.resize((newWidth, newHeight))
    return newImage


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
    draw.text((205, 550), f"Title: {title}", (127, 0, 225), font=font)
    draw.text((205, 590), f"Duration: {duration}", (160, 160, 160), font=font)
    draw.text((205, 630), f"Views: {views}", (160, 160, 160), font=font)
    draw.text((205, 670), f"Added By: {requested_by}", (255, 255, 0), font=font,
    )
    img.save("final.png")
    os.remove("temp.png")
    os.remove("background.png")


@Client.on_message(filters.command("playlist") & filters.group & ~filters.edited)
async def playlist(client, message):
    global que
    queue = que.get(message.chat.id)
    if not queue:
        await message.reply_text("Player is idle")
    temp = []
    for t in queue:
        temp.append(t)
    now_playing = temp[0][0]
    by = temp[0][1].mention(style="md")
    msg = "**Lagu Yang Sedang dimainkan** di {}".format(message.chat.title)
    msg += "\n• " + now_playing
    msg += "\n• Req by " + by
    temp.pop(0)
    if temp:
        msg += "\n\n"
        msg += "**Antrian Lagu**"
        for song in temp:
            name = song[0]
            usr = song[1].mention(style="md")
            msg += f"\n• {name}"
            msg += f"\n• Req by {usr}\n"
    await message.reply_text(msg)


# ============================= Settings =========================================


def updated_stats(chat, queue, vol=200):
    if chat.id in callsmusic.pytgcalls.active_calls:
        # if chat.id in active_chats:
        stats = "Pengaturan dari **{}**".format(chat.title)
        if len(que) > 0:
            stats += "\n\n"
            stats += "Volume : {}%\n".format(vol)
            stats += "Lagu dalam antrian : `{}`\n".format(len(que))
            stats += "Sedang memutar lagu : **{}**\n".format(queue[0][0])
            stats += "Requested by : {}".format(queue[0][1].mention)
    else:
        stats = None
    return stats

@Client.on_message(filters.command("current") & filters.group & ~filters.edited)
async def ee(client, message):
    queue = que.get(message.chat.id)
    stats = updated_stats(message.chat, queue)
    if stats:
        await message.reply(stats)
    else:
        await message.reply("**Silahkan Nyalakan dulu VCG nya!**")


@Client.on_message(filters.command("player") & filters.group & ~filters.edited)
@authorized_users_only
async def settings(client, message):
    playing = None
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.pytgcalls.active_calls:
        playing = True
    queue = que.get(chat_id)
    stats = updated_stats(message.chat, queue)
    if stats:
        if playing:
            await message.reply(stats)

        else:
            await message.reply(stats)
    else:
        await message.reply("**Silahkan Nyalakan dulu VCG nya!**")


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
        temp = []
        for t in queue:
            temp.append(t)
        now_playing = temp[0][0]
        by = temp[0][1].mention(style="md")
        msg = "**Lagu Yang Sedang dimainkan** di {}".format(cb.message.chat.title)
        msg += "\n• " + now_playing
        msg += "\n• Req by " + by
        temp.pop(0)
        if temp:
            msg += "\n\n"
            msg += "**Antrian Lagu**"
            for song in temp:
                name = song[0]
                usr = song[1].mention(style="md")
                msg += f"\n• {name}"
                msg += f"\n• Req by {usr}\n"
        await cb.message.edit(msg)


@Client.on_message(command(["play","ytplay","yt","p"]) & other_filters)
async def play(_, message: Message):
    global que
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
                        "<b>Ingatlah untuk menambahkan Assistant bot ke Channel Anda</b>",
                    )
                    pass
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
                        "<b>Assistant Bot berhasil bergabung dengan Group anda</b>",
                    )

                except UserAlreadyParticipant:
                    pass
                except Exception:
                    # print(e)
                    await lel.edit(
                        f"<b>⛑ Flood Wait Error ⛑\n{user.first_name} tidak dapat bergabung dengan grup Anda karena banyaknya permintaan bergabung untuk userbot! Pastikan pengguna tidak dibanned dalam grup."
                        "\n\nAtau tambahkan Assistant Bot secara manual ke Grup Anda dan coba lagi</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i> {user.first_name} terkena banned dari Grup ini, Minta admin untuk unbanned assistant bot lalu tambahkan Assistant Bot secara manual.</i>"
        )
        return
    message.from_user.id
    message.from_user.first_name
    text_links=None
    await lel.edit("🔎 **Sedang Mencari Lagu**")
    message.from_user.id
    if message.reply_to_message:
        entities = []
        toxt = message.reply_to_message.text or message.reply_to_message.caption
        if message.reply_to_message.entities:
            entities = message.reply_to_message.entities + entities
        elif message.reply_to_message.caption_entities:
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
    message.from_user.first_name
    user_name = message.from_user.first_name
    rpk = "[" + user_name + "](tg://user?id=" + str(user_id) + ")"
    audio = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )
    if audio:
        if round(audio.duration / 60) > DURATION_LIMIT:
            raise DurationLimitError(
                f"❌ **Video dengan durasi lebih dari** `{DURATION_LIMIT}` **menit tidak boleh diputar!**"
            )
        file_name = get_file_name(audio)
        title = file_name
        thumb_name = "https://telegra.ph/file/ab13882bb05849b6ba170.jpg"
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
        ydl_opts = {"format": "141/bestaudio[ext=m4a]"}
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
        dlurl=url
        dlurl=dlurl.replace("youtube","youtubepp")
        keyboard = InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("📖 ᴘʟᴀʏʟɪꜱᴛ", callback_data="playlist"),
                                InlineKeyboardButton("💬 ɢʀᴏᴜᴘ", url=f"https://t.me/{groupsupport}"),
                            ],   
                            [InlineKeyboardButton("💌 ᴄʜᴀɴɴᴇʟ", url=f"https://t.me/{updateschannel}"), InlineKeyboardButton("💵 ꜱᴀᴡᴇʀɴʏᴀ", url="https://trakteer.id/kenkansaja/tip")],
                            [InlineKeyboardButton(text="🗑 ᴛᴜᴛᴜᴘ", callback_data="cls")],
                        ]
                    )
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)
        file_path = await convert(youtube.download(url))        
    else:
        query = ""
        for i in message.command[1:]:
            query += " " + str(i)
        print(query)
        await lel.edit("🎵 **Sedang Memproses Lagu**")
        ydl_opts = {"format": "141/bestaudio[ext=m4a]"}
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
        dlurl=url
        dlurl=dlurl.replace("youtube","youtubepp")
        keyboard = InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("📖 ᴘʟᴀʏʟɪꜱᴛ", callback_data="playlist"),
                                InlineKeyboardButton("💬 ɢʀᴏᴜᴘ", url=f"https://t.me/{groupsupport}"),
                            ],   
                            [InlineKeyboardButton("💌 ᴄʜᴀɴɴᴇʟ", url=f"https://t.me/{updateschannel}"), InlineKeyboardButton("💵 ꜱᴀᴡᴇʀɴʏᴀ", url="https://trakteer.id/kenkansaja/tip")],
                            [InlineKeyboardButton(text="🗑 ᴛᴜᴛᴜᴘ", callback_data="cls")],
                        ]
                    )
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)
        file_path = await convert(youtube.download(url))
    chat_id = get_chat_id(message.chat)
    if chat_id in callsmusic.pytgcalls.active_calls:
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        r_by = message.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await message.reply_photo(
            photo="final.png",
            caption=f"🏷 **Judul :** {title[:60]}\n**⏱ Durasi :** {duration}\n" \
                    + f"🎵 **Antri :** {position}!\n🎧 **Permintaan :** {requested_by}",
          reply_markup=keyboard,
        )
        os.remove("final.png")
        return await lel.delete()
    chat_id = get_chat_id(message.chat)
    que[chat_id] = []
    qeue = que.get(chat_id)
    s_name = title
    r_by = message.from_user
    loc = file_path
    appendable = [s_name, r_by, loc]
    qeue.append(appendable)
    try:
        callsmusic.pytgcalls.join_group_call(chat_id, file_path)
    except:
        message.reply("Voice Chat Group tidak aktif, Saya tidak dapat bergabung")
        return
    await message.reply_photo(
                photo="final.png",
                reply_markup=keyboard,
                caption=f"🏷 **Judul:** [{title[:60]}]({url})\n⏱ **Durasi:** {duration}\n💡 **Status:** Sedang Memutar\n" \
                                + f"🎼 **Request Dari:** {message.from_user.mention}"  
            )
    return await lel.delete()

@Client.on_message(filters.command("dplay") & filters.group & ~filters.edited)
async def deezer(client: Client, message_: Message):
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
                    pass
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
                        f"\n\nAtau tambahkan secara manual ke Grup Anda dan coba lagi</b>",
                    )
    try:
        await USER.get_chat(chid)
        # lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            f"<i>{user.first_name} terkena banned dari Grup ini, Minta admin untuk mengirim perintah `/play` untuk pertama kalinya atau tambahkan Assistant secara manual</i>"
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
        thumbnail = "https://telegra.ph/file/c9c7e24b03919fa5f8022.jpg"

    except:
        await res.edit("**Tidak Ditemukan Lagu Apa Pun!**")
        return
    try:    
        duuration= round(duration / 60)
        if duuration > DURATION_LIMIT:
            await cb.message.edit(f"**Musik lebih lama dari** `{DURATION_LIMIT}` **menit tidak diperbolehkan diputar**")
            return
    except:
        pass    
    
    keyboard = InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("📖 ᴘʟᴀʏʟɪꜱᴛ", callback_data="playlist"),
                                InlineKeyboardButton("💬 ɢʀᴏᴜᴘ", url=f"https://t.me/{groupsupport}"),
                            ],   
                            [InlineKeyboardButton("💌 ᴄʜᴀɴɴᴇʟ", url=f"https://t.me/{updateschannel}"), InlineKeyboardButton("💵 ꜱᴀᴡᴇʀɴʏᴀ", url="https://trakteer.id/kenkansaja/tip")],
                            [InlineKeyboardButton(text="🗑 ᴛᴜᴛᴜᴘ", callback_data="cls")],
                        ]
                    )
    file_path = await convert(wget.download(url))
    await res.edit("📥 **Generating Thumbnail**")
    await generate_cover(requested_by, title, artist, duration, thumbnail)
    chat_id = get_chat_id(message_.chat)
    if chat_id in callsmusic.pytgcalls.active_calls:
        await res.edit("adding in queue")
        position = await queues.put(chat_id, file=file_path)
        qeue = que.get(chat_id)
        s_name = title
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await res.edit_text(f"🏷 **Judul :** [{title[:60]}]({url})\n**⏱ Durasi :** {duration}\n" \
                + f"🎵 **Antri :** {position}!\n🎧 **Permintaan :** {requested_by}",)

    else:
        await res.edit_text("🎼️ **Playing...**")
        chat_id = message_.chat.id
        que[chat_id] = []
        qeue = que.get(message_.chat.id)
        s_name = title
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        try:
            callsmusic.pytgcalls.join_group_call(chat_id, file_path)
        except:
            res.edit("Voice Chat Group tidak aktif, Saya tidak dapat bergabung")
            return

    await res.delete()

    m = await client.send_photo(
        chat_id=message_.chat.id,
        reply_markup=keyboard,
        photo="final.png",
        caption=f"🏷 **Judul:** [{title[:60]}]({url})\n⏱ **Durasi:** {duration}\n💡 **Status:** Sedang Memutar\n" \
                    + f"🎼 **Request Dari:** {r_by.mention}",  
        )
    os.remove("final.png")
   

@Client.on_message(filters.command("splay") & filters.group & ~ filters.edited)
@authorized_users_only
async def jiosaavn(client: Client, message_: Message):
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
        #chatdetails = await USER.get_chat(chid)
        lmoa = await client.get_chat_member(chid,wew)
    except:
           for administrator in administrators:
                      if administrator == message_.from_user.id:  
                          try:
                              invitelink = await client.export_chat_invite_link(chid)
                          except:
                              await lel.edit(
                                  "<b>Tambahkan saya sebagai admin grup Anda terlebih dahulu</b>",
                              )
                              return

                          try:
                              await USER.join_chat(invitelink)
                              await USER.send_message(message_.chat.id,"Saya bergabung dengan grup ini untuk memainkan musik di VCG")
                              await lel.edit(
                                  "<b>Helper userbot bergabung dengan obrolan Anda</b>",
                              )

                          except UserAlreadyParticipant:
                              pass
                          except Exception as e:
                              #print(e)
                              await lel.edit(
                                  "<b>🔴 Flood Wait Error 🔴 \nAssistant Bot tidak dapat bergabung dengan grup Anda karena banyaknya permintaan bergabung untuk userbot! Pastikan pengguna tidak dibanned dalam grup."
                                  "\n\nAtau tambahkan secara manual Assistant Bot ke Grup Anda dan coba lagi</b>",
                              )
                              pass
    try:
        chatdetails = await USER.get_chat(chid)
        #lmoa = await client.get_chat_member(chid,wew)
    except:
        await lel.edit(
            "<i> Assistant Bot tidak ada dalam grup ini, Minta admin untuk tambahkan Assistant Bot secara manual</i>"
        )
        return     
    requested_by = message_.from_user.first_name
    chat_id=message_.chat.id
    text = message_.text.split(" ", 1)
    query = text[1]
    res = lel
    await res.edit(f"Sedang Mencari `{query}` dari jio saavn")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://jiosaavnapi.bhadoo.uk/result/?query={query}"
            ) as resp:
                r = json.loads(await resp.text())
        sname = r[0]["song"]
        slink = r[0]["media_url"]
        ssingers = r[0]["singers"]
        sthumb = r[0]["image"]
        sduration = int(r[0]["duration"])
    except Exception as e:
        await res.edit(
            "Foundally Nothing !, Anda Harus Mengerjakan Bahasa Inggris Anda."
        )
        print(str(e))
        is_playing = False
        return
    file_path = await converter.convert(wget.download(slink))
    if message_.chat.id in callsmusic.pytgcalls.active_calls:
        position = await queues.put(message_.chat.id, file=file_path)
        qeue = que.get(message_.chat.id)
        s_name = title 
        r_by = message_.from_user 
        loc = file_path 
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        await res.delete()
        m = await client.send_photo(
            chat_id=message_.chat.id,
            photo="final.png",
            reply_markup=keyboard,
            caption=f"🏷 **Judul :** [{sname[:60]}]({slink})\n**⏱ Durasi :** {sduration}\n" \
                + f"🎵 **Antri :** {position}!\n🎧 **Permintaan :** {r_by.mention}",
        )
           
    else:
        await res.edit_text("Playing.....")
        chat_id = message_.chat.id
        que[chat_id] = []
        qeue = que.get(message_.chat_id)
        s_name = title
        r_by = message_.from_user
        loc = file_path
        appendable = [s_name, r_by, loc]
        qeue.append(appendable)
        callsmusic.pytgcalls.join_group_call(message_.chat.id, file_path)
    await res.edit("Generating Thumbnail.")
    await generate_cover(requested_by, sname, ssingers, sduration, sthumb)
    await res.delete()
    m = await client.send_photo(
        chat_id=message_.chat.id,
        photo="final.png",
        reply_markup=keyboard,
        caption=f"🏷 **Judul:** [{sname[:60]}]({slink})\n⏱ **Durasi:** {sduration}\n💡 **Status:** Sedang Memutar\n" \
                    + f"🎼 **Request Dari:** {r_by.mention}",  
        )

    os.remove("final.png")
    return await lel.delete()

# Have u read all. If read RESPECT :-)

import logging
from MusicKen.modules.msg import Messages as tr
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from MusicKen.config import SOURCE_CODE,ASSISTANT_NAME,PROJECT_NAME,SUPPORT_GROUP,UPDATES_CHANNEL,BOT_USERNAME, OWNER
logging.basicConfig(level=logging.INFO)


@Client.on_message(
    filters.command("start")
    & filters.private
    & ~ filters.edited
)
async def start_(client: Client, message: Message):
    await message.reply_text(
        f"""👋🏻 Hallo, Nama saya [{PROJECT_NAME}](https://telegra.ph/file/ed136c19e7f6afddb4912.jpg)
Dikekolah oleh {OWNER}
┈───────────────────┈
☑️ Saya memiliki banyak fitur untuk anda yang suka lagu
🔘 Memutar lagu di group 
🔘 Mendownload lagu
🔘 Mendownload video
🔘 Mencari link youtube
🔘 Mencari lirik lagu
┈───────────────────┈
☑️ Klik tombol bantuan untuk informasi lebih lanjut
""",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "⚔️ ʙᴀɴᴛᴜᴀɴ", callback_data = f"help+1"),
                    InlineKeyboardButton(
                        "ᴛᴀᴍʙᴀʜᴋᴀɴ ➕", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
                [
                    InlineKeyboardButton(
                        "👥 ɢʀᴏᴜᴘ", url=f"https://t.me/{SUPPORT_GROUP}"), 
                    InlineKeyboardButton(
                        "ᴄʜᴀɴɴᴇʟ 📣", url=f"https://t.me/{UPDATES_CHANNEL}")],
                [
                    InlineKeyboardButton("🌟 ɢɪᴛ ʜᴜʙ 🌟", url=f"{SOURCE_CODE}")
                ]        
            ]
        ),
        reply_to_message_id=message.message_id
        )

@Client.on_message(filters.command("start") & ~filters.private & ~filters.channel)
async def gstart(_, message: Message):
    await message.reply_text(
        f"""**🔴 {PROJECT_NAME} is online**""",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("💬 sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ", url=f"https://t.me/{SUPPORT_GROUP}"),
                    InlineKeyboardButton("ᴄʜᴀɴɴᴇʟ 📣", url=f"https://t.me/{UPDATES_CHANNEL}")
                ]
            ]
        ),
    )


@Client.on_message(filters.private & filters.incoming & filters.command(['help']))
def _help(client, message):
    client.send_message(chat_id = message.chat.id,
        text = tr.HELP_MSG[1],
        parse_mode="markdown",
        disable_web_page_preview=True,
        disable_notification=True,
        reply_markup = InlineKeyboardMarkup(map(1)),
        reply_to_message_id = message.message_id
    )

help_callback_filter = filters.create(lambda _, __, query: query.data.startswith('help+'))

@Client.on_callback_query(help_callback_filter)
def help_answer(client, callback_query):
    chat_id = callback_query.from_user.id
    disable_web_page_preview=True
    message_id = callback_query.message.message_id
    msg = int(callback_query.data.split('+')[1])
    client.edit_message_text(chat_id=chat_id,    message_id=message_id,
        text=tr.HELP_MSG[msg],    reply_markup=InlineKeyboardMarkup(map(msg))
    )


def map(pos):
    if(pos==1):
        button = [
            [InlineKeyboardButton(text = '⬅️ Sebelummya', callback_data = "help+7"),
             InlineKeyboardButton(text = 'Selanjutnya ➡️', callback_data = "help+2")]
        ]
    elif(pos==len(tr.HELP_MSG)-1):
        url = f"https://t.me/{SUPPORT_GROUP}"
        button = [
            [InlineKeyboardButton(text = '⚔️ ʙᴀɴᴛᴜᴀɴ', callback_data = f"help+1"),
             InlineKeyboardButton(text = 'ᴛᴀᴍʙᴀʜᴋᴀɴ ➕', url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
            [InlineKeyboardButton(text = '👥 ɢʀᴏᴜᴘ', url=f"https://t.me/{SUPPORT_GROUP}"),
             InlineKeyboardButton(text = 'ᴄʜᴀɴɴᴇʟ 📣', url=f"https://t.me/{UPDATES_CHANNEL}")],
            [InlineKeyboardButton("🌟 ɢɪᴛ ʜᴜʙ 🌟", url=f"{SOURCE_CODE}")]
        ]
    else:
        button = [
            [
                InlineKeyboardButton(text = '⬅️ sᴇʙᴇʟᴜᴍɴʏᴀ', callback_data = f"help+{pos-1}"),
                InlineKeyboardButton(text = 'sᴇʟᴀɴᴊᴜᴛɴʏᴀ ➡️', callback_data = f"help+{pos+1}")
            ],
        ]
    return button

@Client.on_message(filters.command("help") & ~filters.private & ~filters.channel)
async def ghelp(_, message: Message):
    await message.reply_text(
        f"HELP_MSG",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "🟡 Klik di sini untuk bantuan 🟡", url=f"https://t.me/{BOT_USERNAME}?start"
                    )
                ]
            ]
        ),
    )

@Client.on_message(
    filters.command("reload")
    & filters.group
    & ~ filters.edited
)
async def reload(client: Client, message: Message):
    await message.reply_text("""✅ Bot **berhasil dimulai ulang!**\n\n• **Daftar admin** telah **diperbarui**""",
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


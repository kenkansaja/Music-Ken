import os
from MusicKen.config import SOURCE_CODE,ASSISTANT_NAME,PROJECT_NAME,SUPPORT_GROUP,UPDATES_CHANNEL, OWNER
class Messages():
      HELP_MSG = [
        ".",
f"""
**👋🏻 Hai Selamat Datang Kembali Di [{PROJECT_NAME}](https://telegra.ph/file/ed136c19e7f6afddb4912.jpg)

⚪️ {PROJECT_NAME} Dapat Memutar Musik Di Obrolan Suara Grup Anda Serta Obrolan Suara Saluran

⚪️ Assistant Name >> @{ASSISTANT_NAME}\n\n☑️ Klik Selanjutnya Untuk Informasi Lebih Lanjut**
""",

f"""
**🛠️ Pengaturan**

1) Jadikan Bot Sebagai Admin
2) Mulai Obrolan Suara / Vcg
3) Kirim Perintah /userbotjoin
• Jika Assistant Bot Bergabung Selamat Menikmati Musik, 
• Jika Assistant Bot Tidak Bergabung Silahkan Tambahkan @{ASSISTANT_NAME} Ke Grup Anda Dan Coba Lagi

**Untuk Saluran Music Play 📣**

1) Jadikan Bot Sebagai Admin Saluran
2) Kirim /userbotjoinchannel Di Grup Tertaut
3) Sekarang Kirim Perintah Di Grup Tertaut
""",
f"""
**🔰 Perintah**

**=>> Memutar Lagu 🎧**

• /play (nama lagu) - Untuk Memutar lagu yang Anda minta melalui youtube
• /player: Buka menu Pengaturan pemain
• /skip: Melewati trek saat ini
• /pause: Jeda trek
• /resume: Melanjutkan trek yang dijeda
• /end: ​​Menghentikan pemutaran media
• /current: Menampilkan trek yang sedang diputar
• /playlist: Menampilkan daftar putar

Semua Perintah Bisa Digunakan Kecuali Perintah /player /skip /pause /resume  /end Hanya Untuk Admin Grup
""",
f"""
**==>>Download Lagu 📥**

• /song [nama lagu]: Unduh audio lagu dari youtube
""" ,

f"""
**=>> Lebih Banyak Alat 🧑‍🔧**

- /admincache: Memperbarui Info Admin Grup Anda. Coba Jika Bot Tidak Mengenali Admin
- /userbotjoin: Undang @{ASSISTANT_NAME} Userbot Ke Grup Anda
""",
f"""
👋🏻 Hallo, Nama saya [{PROJECT_NAME}](https://telegra.ph/file/ed136c19e7f6afddb4912.jpg)
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

"""
      ]

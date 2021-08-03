## JALANKAN VIA TERMUX

```
#langkah pertama
pkg update && pkg upgrade -y
pkg install git
git clone https://github.com/kenkansaja/Music-Ken
#langkah selanjutnya
cd Music-Ken
apt-get install python3-pip
pip3 install -r requirements.txt
nano local.env
#silahkan salin file yang ada di example.env 
terus isi semua kalau sudah silahkan salin lagi 
lalu tempel setelah memasukkan 
command nano local.env
screen or screen -S{screen name}
python3 -m MusicKen
```

Dapatkan example.env di [SINI](https://raw.githubusercontent.com/kenkansaja/Music-Ken/MusicKen/example.env)

#### Nb : Ingat masukan command satu satu jangan sekaligus

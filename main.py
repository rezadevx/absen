from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import pytz
import config
import os
import sys
from apscheduler.schedulers.background import BackgroundScheduler

app = Client(
    "absen_bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN
)

absen_log = {}
absen_hari_ini = {}
absen_message_id = {}

def get_waktu():
    zona = pytz.timezone("Asia/Jakarta")
    now = datetime.now(zona)
    jam = now.strftime("%H:%M")
    tgl = now.strftime("%d-%m-%Y")
    hari = now.strftime("%A")
    return jam, tgl, hari

@app.on_message(filters.command("absen"))
async def absen_command(_, message):
    chat_id = message.chat.id
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Absen", callback_data="absen")]]
    )
    daftar = "📋 Daftar Absen:\n"
    sent = await message.reply(daftar, reply_markup=keyboard)
    absen_log[chat_id] = []
    absen_hari_ini[chat_id] = {}
    absen_message_id[chat_id] = sent.id
    try:
        await sent.pin(disable_notification=True)
    except:
        pass

@app.on_callback_query(filters.regex("absen"))
async def handle_absen(_, callback_query):
    user = callback_query.from_user
    chat_id = callback_query.message.chat.id
    user_id = user.id
    jam, tgl, hari = get_waktu()

    if chat_id not in absen_hari_ini:
        absen_hari_ini[chat_id] = {}
    if chat_id not in absen_log:
        absen_log[chat_id] = []

    if absen_hari_ini[chat_id].get(user_id) == tgl:
        await callback_query.answer("Kamu sudah absen hari ini!", show_alert=True)
        return

    absen_hari_ini[chat_id][user_id] = tgl
    hasil = f"✅ {user.first_name} ({jam}) ({tgl}) ({hari})\n\n"
    absen_log[chat_id].append(hasil)

    daftar = "📋 Daftar Absen:\n" + "".join(absen_log[chat_id])
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Absen", callback_data="absen")]]
    )
    try:
        await app.edit_message_text(
            chat_id=chat_id,
            message_id=absen_message_id[chat_id],
            text=daftar,
            reply_markup=keyboard
        )
    except:
        pass

    await callback_query.answer("Absen berhasil!")

@app.on_message(filters.command("start") & filters.private)
async def start_private(_, message):
    await message.reply(
        "👋 Halo! Ini adalah bot absensi harian.\n\n"
        "Gunakan perintah /absen di grup untuk mulai mencatat kehadiran.\n\n"
        "Dibuat khusus oleh Reza DevX — Only One Devs 👑"
    )

def reset_absen():
    global absen_log, absen_hari_ini, absen_message_id
    absen_log = {}
    absen_hari_ini = {}
    absen_message_id = {}
    os.execv(sys.executable, [sys.executable] + sys.argv)

scheduler = BackgroundScheduler(timezone="Asia/Jakarta")
scheduler.add_job(reset_absen, trigger='cron', hour=0, minute=0)
scheduler.start()

app.run()
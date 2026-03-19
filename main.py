from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import pytz
import config
import os
import sys
import platform
import socket
import psutil
import requests
import time
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

BOT_START_TIME = time.time()

def get_waktu():
    zona = pytz.timezone("Asia/Jakarta")
    now = datetime.now(zona)
    jam = now.strftime("%H:%M")
    tgl = now.strftime("%d-%m-%Y")
    hari = now.strftime("%A")
    return jam, tgl, hari

def detect_provider():
    """Deteksi platform deploy dari environment variable"""
    env_checks = {
        "Railway":    ["RAILWAY_ENVIRONMENT", "RAILWAY_PROJECT_ID"],
        "Render":     ["RENDER", "RENDER_SERVICE_ID"],
        "Heroku":     ["DYNO", "HEROKU_APP_ID"],
        "Fly.io":     ["FLY_APP_NAME", "FLY_REGION"],
        "Replit":     ["REPL_ID", "REPL_OWNER"],
        "Koyeb":      ["KOYEB_SERVICE_NAME"],
        "Cyclic":     ["CYCLIC_APP_ID"],
        "Vercel":     ["VERCEL", "VERCEL_ENV"],
        "Cloudflare": ["CF_PAGES", "CLOUDFLARE_ACCOUNT_ID"],
        "AWS":        ["AWS_EXECUTION_ENV", "AWS_REGION"],
        "GCP":        ["GOOGLE_CLOUD_PROJECT", "GCP_PROJECT"],
        "Azure":      ["WEBSITE_INSTANCE_ID", "AZURE_FUNCTIONS_ENVIRONMENT"],
        "DigitalOcean": ["DO_APP_ID"],
    }
    for provider, keys in env_checks.items():
        if any(os.environ.get(k) for k in keys):
            return provider
    return "VPS / Unknown"

def get_uptime():
    """Hitung berapa lama bot sudah berjalan"""
    elapsed = int(time.time() - BOT_START_TIME)
    hari = elapsed // 86400
    jam = (elapsed % 86400) // 3600
    menit = (elapsed % 3600) // 60
    detik = elapsed % 60
    parts = []
    if hari:   parts.append(f"{hari}h")
    if jam:    parts.append(f"{jam}j")
    if menit:  parts.append(f"{menit}m")
    parts.append(f"{detik}d")
    return " ".join(parts)

def get_system_uptime():
    """Berapa lama OS/VPS menyala"""
    elapsed = int(time.time() - psutil.boot_time())
    hari = elapsed // 86400
    jam = (elapsed % 86400) // 3600
    menit = (elapsed % 3600) // 60
    parts = []
    if hari:  parts.append(f"{hari}h")
    if jam:   parts.append(f"{jam}j")
    if menit: parts.append(f"{menit}m")
    return " ".join(parts) or "< 1 menit"

def get_geo_info():
    """Ambil info negara & provider dari IP publik"""
    try:
        r = requests.get("https://ipinfo.io/json", timeout=5)
        data = r.json()
        country = data.get("country", "?")
        org     = data.get("org", "?")       # contoh: "AS12345 DigitalOcean LLC"
        city    = data.get("city", "?")
        return country, org, city
    except:
        return "?", "?", "?"

@app.on_message(filters.command("info"))
async def info_command(_, message):
    await message.reply("⏳ Mengambil informasi sistem...")

    # OS Info
    os_name    = platform.system()
    os_version = platform.version()
    os_release = platform.release()
    distro     = ""
    try:
        import distro as distro_lib
        distro = distro_lib.name(pretty=True)
    except:
        try:
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME"):
                        distro = line.split("=")[1].strip().strip('"')
                        break
        except:
            distro = f"{os_name} {os_release}"

    # CPU
    cpu_cores   = psutil.cpu_count(logical=False) or 1
    cpu_logical = psutil.cpu_count(logical=True)
    cpu_usage   = psutil.cpu_percent(interval=1)

    # RAM
    ram         = psutil.virtual_memory()
    ram_total   = ram.total / (1024**3)
    ram_used    = ram.used  / (1024**3)
    ram_persen  = ram.percent

    # Disk
    disk        = psutil.disk_usage("/")
    disk_total  = disk.total / (1024**3)
    disk_used   = disk.used  / (1024**3)
    disk_persen = disk.percent

    # Network / Geo
    country, org, city = get_geo_info()

    # Provider
    provider = detect_provider()
    if provider == "VPS / Unknown" and org != "?":
        # Gunakan nama org dari IP sebagai fallback
        provider = org.split(" ", 1)[1] if " " in org else org

    # Uptime
    bot_uptime = get_uptime()
    sys_uptime = get_system_uptime()

    teks = (
        f"🖥️ **Informasi Server**\n"
        f"{'─'*30}\n"
        f"☁️ **Provider**     : `{provider}`\n"
        f"🌍 **Negara**       : `{country}` ({city})\n"
        f"🐧 **OS**           : `{distro}`\n\n"
        f"⚙️ **CPU**\n"
        f"  • Core Fisik  : `{cpu_cores} core`\n"
        f"  • Thread      : `{cpu_logical} thread`\n"
        f"  • Usage       : `{cpu_usage}%`\n\n"
        f"🧠 **RAM**\n"
        f"  • Total       : `{ram_total:.2f} GB`\n"
        f"  • Terpakai    : `{ram_used:.2f} GB ({ram_persen}%)`\n\n"
        f"💾 **Penyimpanan**\n"
        f"  • Total       : `{disk_total:.2f} GB`\n"
        f"  • Terpakai    : `{disk_used:.2f} GB ({disk_persen}%)`\n\n"
        f"⏱️ **Uptime**\n"
        f"  • Bot running : `{bot_uptime}`\n"
        f"  • Server ON   : `{sys_uptime}`\n"
    )

    await message.reply(teks)

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
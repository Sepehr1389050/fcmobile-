#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 ربات نگهبان گپ — Chat Guard Bot v6.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ 5 پنل شیشه‌ای اصلی
🔒 30+ قفل (3 صفحه)
⚙️ تنظیمات پیشرفته (2 صفحه)
📋 لیست‌ها (13 بخش)
🛡️ ضد خیانت پیشرفته
📊 آمار کامل گپ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os, json, re, logging, threading, time
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

import telebot
from telebot import types

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "7777777777:AAA_TEST_TOKEN_EXAMPLE_AAAAAAAAAA")
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")

# ═══════════════════════════════════════
# 🗄️ دیتابیس
# ═══════════════════════════════════════
class DB:
    def __init__(self):
        self.data = {"groups": {}, "stats": {"msgs": 0, "users": []}}
        self.load()

    def load(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception as e:
                logger.error(f"DB load error: {e}")

    def save(self):
        try:
            with open(DB_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"DB save error: {e}")

    def g(self, gid):
        gid = str(gid)
        if gid not in self.data["groups"]:
            self.data["groups"][gid] = self._new()
            self.save()
        return self.data["groups"][gid]

    def _new(self):
        return {
            "title": "", "created": datetime.now().isoformat(), "member_count": 0,
            "settings": {
                "locks": {},
                "strict_mode": False, "strict_action": "warn", "strict_duration": 0,
                "flood_enabled": False, "flood_limit": 5, "flood_action": "mute",
                "limit_enabled": False, "limit_count": 10, "limit_time": 60,
                "max_chars": 0, "min_chars": 0,
                "warn_limit": 3, "warn_action": "ban",
                "welcome_enabled": False, "welcome_text": "سلام {name} عزیز!\nبه {group} خوش اومدی 🌿\nساعت ›› {time}",
                "welcome_delete_after": 0,
                "goodbye_enabled": False, "goodbye_text": "خداحافظ {name} 👋",
                "anti_traitor": False, "anti_traitor_limit": 5, "traitor_count": {},
                "force_join": None, "force_join_text": "",
                "force_add": False, "force_add_count": 3,
                "captcha_group": False, "captcha_new": False,
                "temp_media_enabled": False, "temp_media_time": 30,
                "anti_tabchi": False, "tabchi_action": "ban", "tabchi_timing": "join",
                "anti_advertiser": False, "anti_bio_link": False,
                "duplicate_enabled": False, "duplicate_hours": 12,
                "report_delete_reason": False, "report_admin_events": False,
                "auto_lock_enabled": False, "auto_lock_time": "", "auto_unlock_time": "",
                "auto_clean": [], "timezone_offset": 3.5,
                "filters": {}, "auto_replies": {},
                "allowed_usernames": [], "allowed_forwards": [], "special_channel": None,
                "scheduled_posts": [],
                "group_perms": {
                    "can_send_messages": True, "can_send_photos": True,
                    "can_send_videos": True, "can_send_audios": True,
                    "can_send_documents": True, "can_send_voice_notes": True,
                    "can_send_video_notes": True, "can_send_polls": True,
                    "can_send_other_messages": True, "can_add_web_page_previews": True,
                    "can_change_info": False, "can_invite_users": True, "can_pin_messages": False,
                },
            },
            "members": {
                "owners": [], "admins": [], "vips": [], "muted": [],
                "banned": [], "warned": {}, "exempt": [],
                "temp_admins": {}, "temp_vips": {},
                "force_add_records": {},
            },
            "stats": {
                "messages": 0, "members_joined": 0, "members_left": 0,
                "deleted_messages": 0, "warns_given": 0, "bans_given": 0,
                "mutes_given": 0, "user_messages": {},
            }
        }

    def lock(self, gid, key, val=None):
        g = self.g(gid)
        if val is None:
            g["settings"]["locks"][key] = not g["settings"]["locks"].get(key, False)
        else:
            g["settings"]["locks"][key] = val
        self.save()
        return g["settings"]["locks"][key]

    def get_lock(self, gid, key):
        return self.g(gid)["settings"]["locks"].get(key, False)

db = DB()

# ═══════════════════════════════════════
# 🔧 ابزارها
# ═══════════════════════════════════════
flood_cache = defaultdict(list)      # (gid,uid) -> [timestamps]
limit_cache = defaultdict(dict)      # (gid,uid) -> {count, reset}
dup_cache = defaultdict(dict)        # gid -> {hash: timestamp}

def now_ir():
    months = ["فروردین","اردیبهشت","خرداد","تیر","مرداد","شهریور",
               "مهر","آبان","آذر","دی","بهمن","اسفند"]
    days_fa = ["دوشنبه","سه‌شنبه","چهارشنبه","پنج‌شنبه","جمعه","شنبه","یکشنبه"]
    n = datetime.now()
    wd = days_fa[n.weekday()]
    jy = n.year - 621 if n.month > 3 else n.year - 622
    jm = n.month - 3 if n.month > 3 else n.month + 9
    jd = n.day
    t = f"{n.hour:02d}:{n.minute:02d}"
    return f"{t} ( {wd} {jd} {months[jm-1]} {jy} )"

def fa(n):
    d = "۰۱۲۳۴۵۶۷۸۹"
    return "".join(d[int(c)] for c in str(n))

def mention(user):
    name = user.first_name or "کاربر"
    if user.username:
        return f"@{user.username}"
    return f"[{name}](tg://user?id={user.id})"

def is_admin(bot, chat_id, user_id, gid=None):
    if gid:
        g = db.g(str(gid))
        if user_id in g["members"]["owners"]: return True
        if user_id in g["members"]["admins"]: return True
    try:
        m = bot.get_chat_member(chat_id, user_id)
        return m.status in ["administrator", "creator"]
    except:
        return False

def is_vip_or_exempt(user_id, gid):
    g = db.g(str(gid))
    return user_id in g["members"]["vips"] or user_id in g["members"]["exempt"]

def extract_duration(text):
    """استخراج مدت زمان از متن — برگشت به دقیقه"""
    m = re.search(r'(\d+)\s*(دقیقه|min|m)\b', text, re.I)
    if m: return int(m.group(1))
    m = re.search(r'(\d+)\s*(ساعت|hour|h)\b', text, re.I)
    if m: return int(m.group(1)) * 60
    m = re.search(r'(\d+)\s*(روز|day|d)\b', text, re.I)
    if m: return int(m.group(1)) * 1440
    m = re.search(r'\b(\d+)\b', text)
    if m: return int(m.group(1))
    return 0

def do_mute(bot, chat_id, user_id, minutes=0):
    until = None
    if minutes > 0:
        until = datetime.now() + timedelta(minutes=minutes)
        until = int(until.timestamp())
    perms = types.ChatPermissions(can_send_messages=False)
    try:
        bot.restrict_chat_member(chat_id, user_id, perms, until_date=until)
        return True
    except Exception as e:
        logger.error(f"mute error: {e}")
        return False

def do_unmute(bot, chat_id, user_id):
    perms = types.ChatPermissions(
        can_send_messages=True, can_send_photos=True, can_send_videos=True,
        can_send_other_messages=True, can_add_web_page_previews=True,
    )
    try:
        bot.restrict_chat_member(chat_id, user_id, perms)
        return True
    except Exception as e:
        logger.error(f"unmute error: {e}")
        return False

def do_ban(bot, chat_id, user_id):
    try:
        bot.ban_chat_member(chat_id, user_id)
        return True
    except Exception as e:
        logger.error(f"ban error: {e}")
        return False

def do_unban(bot, chat_id, user_id):
    try:
        bot.unban_chat_member(chat_id, user_id)
        return True
    except Exception as e:
        logger.error(f"unban error: {e}")
        return False

def apply_action(bot, chat_id, user_id, action, duration=30, gid=None):
    g = db.g(str(gid or chat_id))
    if action == "ban":
        do_ban(bot, chat_id, user_id)
        g["stats"]["bans_given"] += 1
    elif action == "mute":
        do_mute(bot, chat_id, user_id, 0)
        g["stats"]["mutes_given"] += 1
    elif action == "tmute":
        do_mute(bot, chat_id, user_id, duration)
        g["stats"]["mutes_given"] += 1
    elif action == "warn":
        uid_s = str(user_id)
        warns = g["members"]["warned"].get(uid_s, [])
        warns.append(datetime.now().isoformat())
        g["members"]["warned"][uid_s] = warns
        g["stats"]["warns_given"] += 1
        if len(warns) >= g["settings"]["warn_limit"]:
            g["members"]["warned"][uid_s] = []
            apply_action(bot, chat_id, user_id, g["settings"]["warn_action"], duration, gid)
    db.save()

def get_target(bot, msg):
    """برگشت (user_id, name) از ریپلای / یوزرنیم / آیدی"""
    if msg.reply_to_message and msg.reply_to_message.from_user:
        u = msg.reply_to_message.from_user
        return u.id, u.first_name or str(u.id)
    nums = re.findall(r'\b(\d{5,12})\b', msg.text or "")
    if nums:
        uid = int(nums[0])
        try:
            m = bot.get_chat_member(msg.chat.id, uid)
            return uid, m.user.first_name or str(uid)
        except:
            return uid, str(uid)
    usernames = re.findall(r'@(\w+)', msg.text or "")
    if usernames:
        try:
            u = bot.get_chat_member(msg.chat.id, usernames[0])
            return u.user.id, u.user.first_name or usernames[0]
        except:
            pass
    return None, None

# ═══════════════════════════════════════
# 🎨 پنل‌های شیشه‌ای
# ═══════════════════════════════════════
def kb(*rows):
    m = types.InlineKeyboardMarkup()
    for row in rows:
        m.row(*row)
    return m

def btn(text, data):
    return types.InlineKeyboardButton(text, callback_data=data)

def back_btn(to="main"):
    return btn("🔙 بازگشت", to)

# ─── پنل اصلی ───
def panel_main(gid):
    return kb(
        [btn("📋 لیست‌ها", "lists"), btn("🔒 قفل‌ها", "locks_p1")],
        [btn("⚙️ تنظیمات", "settings_p1"), btn("📚 راهنما", "help_main")],
        [btn("📊 آمار گپ", "stats")],
    )

# ─── لیست‌ها (13 بخش) ───
def panel_lists(gid):
    g = db.g(gid)
    m = g["members"]
    s = g["settings"]
    return kb(
        [btn(f"👑 مالکین : {len(m['owners'])}", "lst_owners"),
         btn(f"👮 مدیران : {len(m['admins'])}", "lst_admins")],
        [btn(f"⭐ ویژه‌ها : {len(m['vips'])}", "lst_vips"),
         btn(f"🔇 سکوت‌شدگان : {len(m['muted'])}", "lst_muted")],
        [btn(f"🚫 بن‌شدگان : {len(m['banned'])}", "lst_banned"),
         btn(f"⚠️ اخطارگرفتگان : {len(m['warned'])}", "lst_warned")],
        [btn(f"✅ معاف‌شدگان : {len(m['exempt'])}", "lst_exempt"),
         btn(f"🗯️ کلمات فیلتر : {len(s['filters'])}", "lst_filters")],
        [btn(f"📢 کانال ویژه : {'✅' if s['special_channel'] else '—'}", "lst_special"),
         btn(f"💬 پاسخ خودکار : {len(s['auto_replies'])}", "lst_replies")],
        [btn(f"🆔 یوزرنیم مجاز : {len(s['allowed_usernames'])}", "lst_usernames"),
         btn(f"↗️ فوروارد مجاز : {len(s['allowed_forwards'])}", "lst_forwards")],
        [btn(f"📅 پست زمان‌بندی : {len(s['scheduled_posts'])}", "lst_scheduled")],
        [back_btn()],
    )

# ─── قفل‌ها ───
def lbtn(gid, emoji, name, key):
    v = "✅" if db.get_lock(gid, key) else "❌"
    return btn(f"{v} {emoji} {name}", f"lk_{key}")

def panel_locks1(gid):
    return kb(
        [lbtn(gid,"🔗","هایپر لینک","hyperlink"), lbtn(gid,"🌐","لینک","link")],
        [lbtn(gid,"#️⃣","هشتگ","hashtag"), lbtn(gid,"@️","یوزرنیم","username_lock")],
        [lbtn(gid,"🇮🇷","فارسی","farsi"), lbtn(gid,"🇬🇧","انگلیسی","english")],
        [lbtn(gid,"📱","سرویس تلگرام","tg_service"), lbtn(gid,"📝","متن","text_lock")],
        [lbtn(gid,"🤬","فحش","badwords"), lbtn(gid,"😀","ایموجی","emoji")],
        [lbtn(gid,"🔘","دکمه شیشه‌ای","inline_btn"), lbtn(gid,"↗️","فوروارد","forward")],
        [lbtn(gid,"🕶️","هویت مخفی","anonymous"), lbtn(gid,"🎮","بازی","game")],
        [lbtn(gid,"🤖","ربات","bot_msg"), lbtn(gid,"➕","اد کردن ربات","bot_add")],
        [lbtn(gid,"✏️","ویرایش رسانه","edit_media"), lbtn(gid,"📌","ویرایش پیام","edit_msg")],
        [btn("➡️ صفحه بعد","locks_p2"), back_btn()],
    )

def panel_locks2(gid):
    return kb(
        [lbtn(gid,"🖼️","عکس","photo"), lbtn(gid,"🎥","فیلم","video")],
        [lbtn(gid,"📁","فایل","file"), lbtn(gid,"🎵","آهنگ","audio")],
        [lbtn(gid,"🎨","استیکر","sticker"), lbtn(gid,"🎬","گیف","gif")],
        [lbtn(gid,"📞","مخاطب","contact"), lbtn(gid,"📍","مکان","location")],
        [lbtn(gid,"✨","استیکر متحرک","animated_sticker"), lbtn(gid,"💬","دستورات","commands")],
        [lbtn(gid,"🎤","ویس","voice"), lbtn(gid,"🎦","فیلم سلفی","video_note")],
        [lbtn(gid,"🗑️","رسانه موقت","temp_media_lock")],
        [btn("⬅️ قبلی","locks_p1"), btn("➡️ بعدی","locks_p3")],
    )

def panel_locks3(gid):
    return kb(
        [lbtn(gid,"📌","سنجاق","pin"), lbtn(gid,"@️","منشن","mention")],
        [lbtn(gid,"👤","عضو جدید","new_member_msg"), lbtn(gid,"||","اسپویلر","spoiler")],
        [lbtn(gid,"↩️","ریپلای","reply"), lbtn(gid,"↪️","ریپلای خارجی","ext_reply")],
        [lbtn(gid,"📖","استوری","story"), lbtn(gid,"📊","نظرسنجی","poll")],
        [btn("⬅️ قبلی","locks_p2"), back_btn()],
    )

# ─── تنظیمات ───
def sbtn(emoji, name, data, active=None):
    prefix = f"{'✅' if active else '❌'} " if active is not None else ""
    return btn(f"{prefix}{emoji} {name}", data)

def panel_settings1(gid):
    g = db.g(gid)
    s = g["settings"]
    return kb(
        [sbtn("🗑️","رسانه موقت","s_temp_media", s["temp_media_enabled"])],
        [sbtn("🛡️","تایید هویت (کپچا)","s_captcha")],
        [sbtn("⚔️","ضد خیانت","s_anti_traitor", s["anti_traitor"])],
        [sbtn("➕","عضویت اجباری","s_force_join")],
        [sbtn("👥","اد اجباری","s_force_add", s["force_add"])],
        [sbtn("👋","خوش‌آمدگویی","s_welcome", s["welcome_enabled"])],
        [sbtn("⚠️","تنظیم اخطار","s_warn")],
        [sbtn("🤖","ضد تبچی","s_tabchi", s["anti_tabchi"])],
        [sbtn("🔒","حالت سختگیرانه","s_strict", s["strict_mode"])],
        [sbtn("⏰","قفل خودکار","s_autolock")],
        [sbtn("💥","پیام رگباری","s_flood", s["flood_enabled"])],
        [sbtn("📏","قفل لیمیت","s_limit", s["limit_enabled"])],
        [sbtn("🔑","اختیارات گروه","s_perms")],
        [sbtn("🧹","پاکسازی گروه","s_autoclean")],
        [sbtn("🌍","تایم زون","s_timezone")],
        [sbtn("📋","گزارشات","s_reports")],
        [btn("➡️ صفحه بعد","settings_p2"), back_btn()],
    )

def panel_settings2(gid):
    g = db.g(gid)
    s = g["settings"]
    return kb(
        [sbtn("👋","خداحافظی","s_goodbye", s["goodbye_enabled"])],
        [sbtn("📏","طول متن","s_charlimit")],
        [sbtn("🔄","پیام تکراری","s_duplicate", s["duplicate_enabled"])],
        [sbtn("📢","گزارش تخلف","s_report_sys")],
        [btn("⬅️ قبلی","settings_p1"), back_btn()],
    )

# ─── راهنما ───
def panel_help():
    return kb(
        [btn("🔒 قفل‌ها","help_locks"), btn("⚙️ تنظیمات","help_settings")],
        [btn("👥 کاربران","help_users"), btn("🎯 دستورات","help_cmds")],
        [back_btn()],
    )

# ═══════════════════════════════════════
# 🤖 ساخت بات
# ═══════════════════════════════════════
bot = telebot.TeleBot(TOKEN, parse_mode="Markdown")

# ─── /start ───
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    if msg.chat.type == "private":
        bot.send_message(msg.chat.id, f"""✨ سلام *{msg.from_user.first_name}* عزیز!

🤖 *ربات نگهبان گپ — نسخه ۶.۰*

🎯 قابلیت‌های اصلی:
├ 📋 لیست‌ها — ۱۳ بخش
├ 🔒 قفل‌ها — ۳۰+ قفل (۳ صفحه)
├ ⚙️ تنظیمات — ۲۰+ گزینه
├ 🛡️ ضد خیانت پیشرفته
├ 📊 آمار کامل گپ
└ 📚 راهنمای جامع

📌 دستور باز کردن پنل:
فارسی: *پنل*
انگلیسی: *Panel*

🌟 ربات را به گروه اضافه و ادمین کن!""")
    else:
        gid = str(msg.chat.id)
        g = db.g(gid)
        g["title"] = msg.chat.title or "گروه"
        db.save()
        bot.send_message(msg.chat.id, f"🤖 *ربات نگهبان گپ* فعال شد!\n🕐 {now_ir()}",
                         reply_markup=panel_main(gid))

# ═══════════════════════════════════════
# 🔘 هندلر Callback (دکمه‌های شیشه‌ای)
# ═══════════════════════════════════════
@bot.callback_query_handler(func=lambda c: True)
def on_callback(c):
    gid = str(c.message.chat.id)
    uid = c.from_user.id
    data = c.data

    # چک دسترسی (فقط گروه)
    if c.message.chat.type != "private":
        if not is_admin(bot, c.message.chat.id, uid, gid):
            bot.answer_callback_query(c.id, "⛔ فقط ادمین‌ها دسترسی دارند!", show_alert=True)
            return

    bot.answer_callback_query(c.id)

    def edit(text, markup=None):
        try:
            bot.edit_message_text(text, c.message.chat.id, c.message.message_id,
                                  reply_markup=markup, parse_mode="Markdown")
        except Exception as e:
            logger.debug(f"edit error: {e}")

    def edit_markup(markup):
        try:
            bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=markup)
        except Exception as e:
            logger.debug(f"edit markup error: {e}")

    g = db.g(gid)
    s = g["settings"]
    m = g["members"]

    # ─── ناوبری اصلی ───
    if data == "main":
        edit(f"🔮 *پنل مدیریت گپ*\n🕐 {now_ir()}", panel_main(gid))

    elif data == "lists":
        edit("〽️ *بخش لیست‌ها*\nانتخاب کن:", panel_lists(gid))

    elif data == "locks_p1":
        edit("🔒 *قفل‌ها — صفحه ۱*\n✅ فعال | ❌ غیرفعال — کلیک برای تغییر:", panel_locks1(gid))

    elif data == "locks_p2":
        edit("🔒 *قفل‌ها — صفحه ۲*\n✅ فعال | ❌ غیرفعال — کلیک برای تغییر:", panel_locks2(gid))

    elif data == "locks_p3":
        edit("🔒 *قفل‌ها — صفحه ۳*\n✅ فعال | ❌ غیرفعال — کلیک برای تغییر:", panel_locks3(gid))

    elif data == "settings_p1":
        edit("⚙️ *تنظیمات پیشرفته — صفحه ۱*", panel_settings1(gid))

    elif data == "settings_p2":
        edit("⚙️ *تنظیمات پیشرفته — صفحه ۲*", panel_settings2(gid))

    elif data == "help_main":
        edit("📚 *راهنمای ربات* — انتخاب کن:", panel_help())

    # ─── toggle قفل ───
    elif data.startswith("lk_"):
        key = data[3:]
        val = db.lock(gid, key)
        lock_fa = {
            "hyperlink":"هایپر لینک","link":"لینک","hashtag":"هشتگ","username_lock":"یوزرنیم",
            "farsi":"فارسی","english":"انگلیسی","tg_service":"سرویس تلگرام","text_lock":"متن",
            "badwords":"فحش","emoji":"ایموجی","inline_btn":"دکمه شیشه‌ای","forward":"فوروارد",
            "anonymous":"هویت مخفی","game":"بازی","bot_msg":"ربات","bot_add":"اد کردن ربات",
            "edit_media":"ویرایش رسانه","edit_msg":"ویرایش پیام",
            "photo":"عکس","video":"فیلم","file":"فایل","audio":"آهنگ","sticker":"استیکر",
            "gif":"گیف","contact":"مخاطب","location":"مکان","animated_sticker":"استیکر متحرک",
            "commands":"دستورات","voice":"ویس","video_note":"فیلم سلفی","temp_media_lock":"رسانه موقت",
            "pin":"سنجاق","mention":"منشن","new_member_msg":"عضو جدید","spoiler":"اسپویلر",
            "reply":"ریپلای","ext_reply":"ریپلای خارجی","story":"استوری","poll":"نظرسنجی",
        }
        name = lock_fa.get(key, key)
        bot.answer_callback_query(c.id, f"{'✅ فعال' if val else '❌ غیرفعال'}: {name}", show_alert=True)
        # رفرش پنل مناسب
        p1_keys = {"hyperlink","link","hashtag","username_lock","farsi","english","tg_service",
                   "text_lock","badwords","emoji","inline_btn","forward","anonymous","game",
                   "bot_msg","bot_add","edit_media","edit_msg"}
        p2_keys = {"photo","video","file","audio","sticker","gif","contact","location",
                   "animated_sticker","commands","voice","video_note","temp_media_lock"}
        if key in p1_keys:
            edit_markup(panel_locks1(gid))
        elif key in p2_keys:
            edit_markup(panel_locks2(gid))
        else:
            edit_markup(panel_locks3(gid))

    # ─── لیست جزئیات ───
    elif data.startswith("lst_"):
        key = data[4:]
        detail_map = {
            "owners": ("👑 مالکین", m["owners"]),
            "admins": ("👮 مدیران", m["admins"]),
            "vips": ("⭐ ویژه‌ها", m["vips"]),
            "muted": ("🔇 سکوت‌شدگان", m["muted"]),
            "banned": ("🚫 بن‌شدگان", m["banned"]),
            "exempt": ("✅ معاف‌شدگان", m["exempt"]),
        }
        if key in detail_map:
            title, items = detail_map[key]
            lines = [f"{i+1}. `{x}`" for i, x in enumerate(items[:20])]
            text = f"{title} ({len(items)})\n\n" + ("\n".join(lines) or "🔹 لیست خالی است")
        elif key == "warned":
            warned = m["warned"]
            lines = [f"`{uid}`: {len(ws)} اخطار" for uid, ws in warned.items() if ws]
            text = f"⚠️ اخطارگرفتگان ({len(warned)})\n\n" + ("\n".join(lines) or "🔹 خالی")
        elif key == "filters":
            fl = s["filters"]
            lines = [f"• `{w}` — {a}" for w, a in list(fl.items())[:30]]
            text = f"🗯️ کلمات فیلتر ({len(fl)})\n\n" + ("\n".join(lines) or "🔹 خالی")
        elif key == "special":
            text = f"📢 *کانال ویژه:*\n{s['special_channel'] or 'تنظیم نشده'}"
        elif key == "replies":
            ar = s["auto_replies"]
            lines = [f"`{k}` → {v[:25]}" for k, v in list(ar.items())[:15]]
            text = f"💬 پاسخ خودکار ({len(ar)})\n\n" + ("\n".join(lines) or "🔹 خالی")
        elif key == "usernames":
            items = s["allowed_usernames"]
            text = f"🆔 یوزرنیم‌های مجاز ({len(items)})\n\n" + ("\n".join([f"`{u}`" for u in items[:20]]) or "🔹 خالی")
        elif key == "forwards":
            items = s["allowed_forwards"]
            text = f"↗️ فوروارد مجاز ({len(items)})\n\n" + ("\n".join([f"`{u}`" for u in items[:20]]) or "🔹 خالی")
        elif key == "scheduled":
            items = s["scheduled_posts"]
            lines = [f"⏰ {p.get('time','?')}: {str(p.get('text',''))[:25]}" for p in items[:10]]
            text = f"📅 پست زمان‌بندی ({len(items)})\n\n" + ("\n".join(lines) or "🔹 خالی")
        else:
            text = "❓ بخش نامشخص"
        edit(text, kb([back_btn("lists")]))

    # ─── آمار گپ ───
    elif data == "stats":
        st = g["stats"]
        total_locks = sum(1 for v in s["locks"].values() if v)
        top = sorted(st["user_messages"].items(), key=lambda x: x[1], reverse=True)[:3]
        medals = ["🥇","🥈","🥉"]
        top_txt = "\n".join([f"  {medals[i]} `{uid[:8]}...`: {cnt} پیام" for i, (uid, cnt) in enumerate(top)])
        try:
            mc = bot.get_chat_members_count(int(gid))
        except:
            mc = g.get("member_count", 0)
        created_str = g.get("created", "")[:10]
        text = f"""📊 *آمار گپ — {g.get('title','گروه')}*

👥 تعداد اعضا: {mc}
📅 تاریخ تأسیس: {created_str}
🕐 زمان فعلی: {now_ir()}

━━━━━━━━━━━━━━━━━
👑 مالکین: {len(m['owners'])}
👮 ادمین‌ها: {len(m['admins'])}
⭐ کاربران ویژه: {len(m['vips'])}
🔇 سکوت‌شدگان: {len(m['muted'])}
🚫 بن‌شدگان: {len(m['banned'])}
⚠️ اخطارگرفتگان: {len(m['warned'])}
✅ معاف‌شدگان: {len(m['exempt'])}

━━━━━━━━━━━━━━━━━
💬 پیام‌های ثبت‌شده: {st['messages']}
🔒 قفل‌های فعال: {total_locks}
🗑️ پیام‌های حذف‌شده: {st['deleted_messages']}
⚠️ اخطارهای داده‌شده: {st['warns_given']}
🚫 بن‌های انجام‌شده: {st['bans_given']}
🔇 سکوت‌های انجام‌شده: {st['mutes_given']}

━━━━━━━━━━━━━━━━━
🏆 *فعال‌ترین اعضا:*
{top_txt or '  هنوز اطلاعاتی نیست'}"""
        edit(text, kb(
            [btn("🔄 بروزرسانی","stats"), btn("🏆 top کاربران","stats_top")],
            [back_btn()],
        ))

    elif data == "stats_top":
        st = g["stats"]
        top = sorted(st["user_messages"].items(), key=lambda x: x[1], reverse=True)[:10]
        medals = ["🥇","🥈","🥉"] + ["🏅"]*7
        lines = [f"{medals[i]} `{uid}`: {cnt} پیام" for i, (uid, cnt) in enumerate(top)]
        text = "🏆 *برترین کاربران:*\n\n" + ("\n".join(lines) or "هنوز اطلاعاتی نیست")
        edit(text, kb([back_btn("stats")]))

    # ─── تنظیمات — رسانه موقت ───
    elif data == "s_temp_media":
        s["temp_media_enabled"] = not s["temp_media_enabled"]
        db.save()
        active = s["temp_media_enabled"]
        edit(f"""🗑️ *رسانه موقت* — {'✅ فعال' if active else '❌ غیرفعال'}

⋆ رسانه‌ها پس از {s['temp_media_time']} دقیقه حذف می‌شوند
⋆ این قابلیت مانع فیلتر شدن گروه می‌شود
""", kb([back_btn("settings_p1")]))


if __name__ == "__main__":
    logger.info("🤖 ربات شروع شد...")
    logger.info(f"🔑 TOKEN: {TOKEN[:20]}...")
    try:
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"❌ خطا: {e}")

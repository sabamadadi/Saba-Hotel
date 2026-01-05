import os
from functools import wraps
import psycopg2
from psycopg2 import Error
from psycopg2.extras import RealDictCursor
import telebot
from telebot import types
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
DB_URI = os.environ.get("DB_URI")


ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")


DASHBOARD_URL = os.environ.get("DASHBOARD_URL", "").strip()

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in .env")
if not DB_URI:
    raise ValueError("DB_URI is not set in .env")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)


user_sessions = {}
_temp = {} =

def get_db_connection():
    try:
        return psycopg2.connect(DB_URI, cursor_factory=RealDictCursor)
    except Error as e:
        print(f"DB connection error: {e}")
        return None

def check_login(chat_id: int) -> bool:
    return bool(user_sessions.get(chat_id, False))

def login_required(func):
    @wraps(func)
    def wrapper(message, *args, **kwargs):
        if not check_login(message.chat.id):
            bot.send_message(message.chat.id, "🔒 لطفاً ابتدا وارد سیستم شوید.")
            ask_for_username(message)
            return
        return func(message, *args, **kwargs)

    return wrapper

def login_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    markup.add(types.KeyboardButton("ورود به سیستم"))
    return markup


def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📊 وضعیت سریع"),
        types.KeyboardButton("🧹 اتاق‌های Cleaning"),
        types.KeyboardButton("🧾 رزروهای Active"),
        types.KeyboardButton("🚪 اتاق‌های Available"),
    )
    if DASHBOARD_URL:
        markup.add(types.KeyboardButton("🔗 لینک داشبورد"))
    markup.add(types.KeyboardButton("خروج از سیستم"))
    return markup

def db_get_stats():
    """
    stats:
      total_rooms
      available_rooms (status='available')
      cleaning_rooms (status='cleaning')
      reserved_rooms (status='reserved')
      occupied_rooms (status='occupied')
      active_reservations (reservation.status='active')
    """
    conn = get_db_connection()
    if not conn:
        return None

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS c FROM room")
            total_rooms = cur.fetchone()["c"]

            cur.execute("SELECT COUNT(*) AS c FROM room WHERE status='available'")
            available_rooms = cur.fetchone()["c"]

            cur.execute("SELECT COUNT(*) AS c FROM room WHERE status='cleaning'")
            cleaning_rooms = cur.fetchone()["c"]

            cur.execute("SELECT COUNT(*) AS c FROM room WHERE status='reserved'")
            reserved_rooms = cur.fetchone()["c"]

            cur.execute("SELECT COUNT(*) AS c FROM room WHERE status='occupied'")
            occupied_rooms = cur.fetchone()["c"]

            cur.execute("SELECT COUNT(*) AS c FROM reservation WHERE status='active'")
            active_reservations = cur.fetchone()["c"]

        return {
            "total_rooms": total_rooms,
            "available_rooms": available_rooms,
            "cleaning_rooms": cleaning_rooms,
            "reserved_rooms": reserved_rooms,
            "occupied_rooms": occupied_rooms,
            "active_reservations": active_reservations,
        }

    except Error as e:
        print(f"stats error: {e}")
        return None
    finally:
        conn.close()


def db_get_cleaning_rooms(limit=30):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT room_id, type, floor, bed_type, capacity
                FROM room
                WHERE status='cleaning'
                ORDER BY floor, room_id
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()
    except Error as e:
        print(f"cleaning rooms error: {e}")
        return None
    finally:
        conn.close()


def db_get_available_rooms(limit=30):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT room_id, type, floor, bed_type, capacity, price
                FROM room
                WHERE status='available'
                ORDER BY floor, room_id
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()
    except Error as e:
        print(f"available rooms error: {e}")
        return None
    finally:
        conn.close()


def db_get_active_reservations(limit=10):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.res_id,
                       r.check_in, r.check_out,
                       g.name, g.family,
                       COALESCE(ARRAY_AGG(rr.room_id ORDER BY rr.room_id), '{}') AS rooms
                FROM reservation r
                JOIN guest g ON g.guest_id = r.guest_id
                LEFT JOIN reservation_room rr ON rr.res_id = r.res_id
                WHERE r.status='active'
                GROUP BY r.res_id, r.check_in, r.check_out, g.name, g.family
                ORDER BY r.res_id DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()
    except Error as e:
        print(f"active reservations error: {e}")
        return None
    finally:
        conn.close()

@bot.message_handler(commands=["start", "login"])
def start_command(message):
    chat_id = message.chat.id
    if check_login(chat_id):
        send_welcome(message)
        return
    bot.send_message(
        chat_id,
        "🛎️ به بات *Saba Hotel* خوش آمدید.\n"
        "برای ادامه، لطفاً وارد سیستم شوید.",
        reply_markup=login_menu(),
        parse_mode="Markdown",
    )

@bot.message_handler(func=lambda m: m.text == "ورود به سیستم")
def ask_for_username(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "نام کاربری را وارد کنید:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, process_username)


def process_username(message):
    chat_id = message.chat.id
    username = (message.text or "").strip()
    _temp[chat_id] = {"username": username}
    msg = bot.send_message(chat_id, "رمز عبور را وارد کنید:")
    bot.register_next_step_handler(msg, process_password)


def process_password(message):
    chat_id = message.chat.id
    password = (message.text or "").strip()
    username = _temp.get(chat_id, {}).get("username", "")

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        user_sessions[chat_id] = True
        _temp.pop(chat_id, None)
        bot.send_message(chat_id, "✅ ورود موفقیت‌آمیز بود.", reply_markup=main_menu())
        send_welcome(message)
    else:
        bot.send_message(chat_id, "❌ نام کاربری یا رمز عبور اشتباه است.")
        ask_for_username(message)


@bot.message_handler(func=lambda m: m.text == "خروج از سیستم")
@login_required
def logout_command(message):
    chat_id = message.chat.id
    user_sessions.pop(chat_id, None)
    _temp.pop(chat_id, None)
    bot.send_message(chat_id, "✅ با موفقیت خارج شدید.", reply_markup=login_menu())


@bot.message_handler(commands=["menu", "help"])
@login_required
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "📌 منوی مدیریت هتل\nیکی از گزینه‌ها را انتخاب کنید:",
        reply_markup=main_menu(),
    )

@bot.message_handler(func=lambda m: m.text == "📊 وضعیت سریع")
@login_required
def quick_status(message):
    stats = db_get_stats()
    if not stats:
        bot.send_message(message.chat.id, "⚠️ خطا در اتصال به دیتابیس.")
        return

    text = (
        "📊 وضعیت سریع هتل\n\n"
        f"🏨 کل اتاق‌ها: {stats['total_rooms']}\n"
        f"✅ Available: {stats['available_rooms']}\n"
        f"🧹 Cleaning: {stats['cleaning_rooms']}\n"
        f"🟡 Reserved: {stats['reserved_rooms']}\n"
        f"🔴 Occupied: {stats['occupied_rooms']}\n"
        f"🧾 رزروهای Active: {stats['active_reservations']}\n"
    )
    bot.send_message(message.chat.id, text)


@bot.message_handler(func=lambda m: m.text == "🧹 اتاق‌های Cleaning")
@login_required
def cleaning_rooms(message):
    rows = db_get_cleaning_rooms(limit=40)
    if rows is None:
        bot.send_message(message.chat.id, "⚠️ خطا در دریافت لیست از دیتابیس.")
        return
    if not rows:
        bot.send_message(message.chat.id, "✅ هیچ اتاقی در حال نظافت نیست.")
        return

    lines = ["🧹 اتاق‌های در حال نظافت:\n"]
    for r in rows:
        lines.append(f"• اتاق {r['room_id']} | طبقه {r['floor']} | {r['type']} | تخت: {r['bed_type']} | ظرفیت: {r['capacity']}")
    bot.send_message(message.chat.id, "\n".join(lines))


@bot.message_handler(func=lambda m: m.text == "🧾 رزروهای Active")
@login_required
def active_reservations(message):
    rows = db_get_active_reservations(limit=10)
    if rows is None:
        bot.send_message(message.chat.id, "⚠️ خطا در دریافت رزروها از دیتابیس.")
        return
    if not rows:
        bot.send_message(message.chat.id, "✅ رزرو فعال نداریم.")
        return

    lines = ["🧾 رزروهای فعال:\n"]
    for r in rows:
        rooms = r["rooms"] or []
        rooms_txt = ", ".join(str(x) for x in rooms) if rooms else "-"
        lines.append(
            f"• کد رزرو: {r['res_id']}\n"
            f"  مهمان: {r['name']} {r['family']}\n"
            f"  ورود: {r['check_in']} | خروج: {r['check_out']}\n"
            f"  اتاق‌ها: {rooms_txt}\n"
            f"  ─────────────"
        )
    bot.send_message(message.chat.id, "\n".join(lines))


@bot.message_handler(func=lambda m: m.text == "🚪 اتاق‌های Available")
@login_required
def available_rooms(message):
    rows = db_get_available_rooms(limit=40)
    if rows is None:
        bot.send_message(message.chat.id, "⚠️ خطا در دریافت اتاق‌ها از دیتابیس.")
        return
    if not rows:
        bot.send_message(message.chat.id, "❌ هیچ اتاق available نیست.")
        return

    lines = ["🚪 اتاق‌های available:\n"]
    for r in rows:
        lines.append(
            f"• اتاق {r['room_id']} | طبقه {r['floor']} | {r['type']} | تخت: {r['bed_type']} | ظرفیت: {r['capacity']} | قیمت: {r['price']}"
        )
    bot.send_message(message.chat.id, "\n".join(lines))


@bot.message_handler(func=lambda m: m.text == "🔗 لینک داشبورد")
@login_required
def dashboard_link(message):
    if not DASHBOARD_URL:
        bot.send_message(message.chat.id, "⚠️ هنوز DASHBOARD_URL در .env تنظیم نشده.")
        return
    bot.send_message(message.chat.id, f"🔗 لینک داشبورد:\n{DASHBOARD_URL}")


def run_bot():
    print("Saba Hotel bot is running ...")
    bot.infinity_polling()


if __name__ == "__main__":
    run_bot()


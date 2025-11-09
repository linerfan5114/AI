import os
import sqlite3
import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = "8523380200:AAEcygKshtxP4WyHYMpr2usbZqxpTzYU-B0"
ADMIN_ID = 7060291842 

PRICE_DAILY = 20000
PRICE_WEEKLY = 250000
PRICE_MONTHLY = 900000

FREE_LIMIT = 2

DB_PATH = "drug_bot_data_100.sqlite"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            language TEXT,
            free_uses INTEGER DEFAULT {FREE_LIMIT},
            plan TEXT DEFAULT NULL,
            expiry_date TEXT DEFAULT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row


def create_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id, language, free_uses) VALUES (?, ?, ?)",
                (user_id, None, FREE_LIMIT))
    conn.commit()
    conn.close()


def set_language(user_id, lang):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE users SET language=? WHERE user_id=?", (lang, user_id))
    conn.commit()
    conn.close()


def decrement_free(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE users SET free_uses = free_uses - 1 WHERE user_id=? AND free_uses>0", (user_id,))
    conn.commit()
    conn.close()


def set_plan(user_id, plan, days):
    expiry = (datetime.date.today() + datetime.timedelta(days=days)).isoformat()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE users SET plan=?, expiry_date=? WHERE user_id=?", (plan, expiry, user_id))
    conn.commit()
    conn.close()


def is_active(user_id):
    user = get_user(user_id)
    if not user:
        return False
    expiry = user[4]
    if expiry is None:
        return False
    return datetime.date.fromisoformat(expiry) >= datetime.date.today()


def search_drug(query):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    q = f"%{query.strip()}%"
    cur.execute("""SELECT name_en, name_fa, indications, typical_dose, description
                   FROM drugs WHERE name_en LIKE ? OR name_fa LIKE ? LIMIT 5""", (q, q))
    rows = cur.fetchall()
    conn.close()
    return rows


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    create_user(user_id)
    user = get_user(user_id)
    if user[1] is None:
        kb = [[KeyboardButton("🇮🇷 فارسی"), KeyboardButton("🇬🇧 English")]]
        await update.message.reply_text("Choose your language / زبان خود را انتخاب کنید:",
                                        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True))
    else:
        lang = user[1]
        if lang == "fa":
            await update.message.reply_text("سلام 👋\nبرای جستجوی دارو بنویس:\n/drug استامینوفن\n"
                                            "یا برای دیدن پلن‌ها بنویس /plans")
        else:
            await update.message.reply_text("Hi 👋\nTo search for a drug use:\n/drug ibuprofen\n"
                                            "Or type /plans to see pricing.")


async def set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id
    if text == "🇮🇷 فارسی":
        set_language(user_id, "fa")
        await update.message.reply_text("زبان شما فارسی تنظیم شد 🇮🇷")
    elif text == "🇬🇧 English":
        set_language(user_id, "en")
        await update.message.reply_text("Language set to English 🇬🇧")
async def plans(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id)
    lang = user[1] or "fa"
    if lang == "fa":
        text = (
            f"💰 تعرفه‌ها:\n"
            f"روزانه: {PRICE_DAILY:,} تومان\n"
            f"هفتگی: {PRICE_WEEKLY:,} تومان\n"
            f"ماهانه: {PRICE_MONTHLY:,} تومان\n\n"
            f"برای خرید، مبلغ را واریز کنید و سپس رسید را برای ادمین ارسال کنید.\n"
            f"ادمین تأیید می‌کند و اشتراک فعال می‌شود.\n"
        )
    else:
        text = (
            f"💰 Pricing:\n"
            f"Daily: {PRICE_DAILY:,} Toman\n"
            f"Weekly: {PRICE_WEEKLY:,} Toman\n"
            f"Monthly: {PRICE_MONTHLY:,} Toman\n\n"
            f"Send payment proof to admin after payment.\n"
        )
    await update.message.reply_text(text)


async def drug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    create_user(user_id)
    user = get_user(user_id)
    lang = user[1] or "fa"

    if not context.args:
        await update.message.reply_text("نام دارو را بعد از /drug بنویسید." if lang == "fa" else "Please provide a drug name.")
        return

    q = " ".join(context.args)

    if is_active(user_id):
        rows = search_drug(q)
    else:
        if user[2] > 0:
            decrement_free(user_id)
            rows = search_drug(q)
        else:
            msg = "⛔️ اعتبار شما تمام شده است. لطفاً اشتراک تهیه کنید." if lang == "fa" else "⛔️ Your access has expired. Please purchase a plan."
            await update.message.reply_text(msg)
            return

    if not rows:
        await update.message.reply_text("❌ دارویی با این نام پیدا نشد." if lang == "fa" else "❌ No results found.")
        return

    for r in rows:
        if lang == "fa":
            text = f"💊 {r[1]} ({r[0]})\n\n📋 موارد مصرف: {r[2]}\n💡 طریقه مصرف: {r[3]}\nℹ️ توضیح: {r[4]}"
        else:
            text = f"💊 {r[0]} ({r[1]})\n\nIndications: {r[2]}\nTypical dose: {r[3]}\nAbout: {r[4]}"
        await update.message.reply_text(text)


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) < 2:
        await update.message.reply_text("فرمت دستور: /confirm <user_id> <plan>\nمثلاً: /confirm 123456 daily")
        return

    user_id = int(context.args[0])
    plan = context.args[1].lower()
    days = {"daily": 1, "weekly": 7, "monthly": 30}.get(plan)

    if not days:
        await update.message.reply_text("پلن اشتباه است. یکی از daily / weekly / monthly را وارد کنید.")
        return

    set_plan(user_id, plan, days)
    await update.message.reply_text(f"✅ اشتراک کاربر {user_id} برای {plan} فعال شد.")
    await context.bot.send_message(chat_id=user_id, text="✅ اشتراک شما فعال شد. از ربات لذت ببرید!")


def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("plans", plans))
    app.add_handler(CommandHandler("drug", drug))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(MessageHandler(filters.Regex("🇮🇷 فارسی|🇬🇧 English"), set_lang))

    print("🤖 ربات دارویی آماده است...")
    app.run_polling()


if __name__ == '__main__':
    main()
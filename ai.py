import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8196612202:AAGpFRPryPtXA5bEpJxSrb0Db1cU2uYWOFg"
GEMINI_API_KEY = "AIzaSyCe-Fd0Sj3ODlVoy78mFjnF_kgm4qypLd0"

genai.configure(api_key=GEMINI_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام داداش! پیام بفرست تا با Gemini جواب بدم 😎")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()

    # فیلتر مخصوص سازنده
    if any(kw in user_message for kw in ["سازنده", "کی ساختت","اسمت","اسمت چیه", "کی درستت کرده", "creator", "developer"]):
        await update.message.reply_text("✨ من توسط گروه Dark Plus ساخته شدم و برنامه‌نویسی: عرفان محمدی 💻")
        return

    # فیلتر سلام
    if user_message in ["سلام", "hi", "hello"]:
        await update.message.reply_text("سلام داداش عشق 💥")
        return

    # بقیه پیام‌ها → میره سمت Gemini
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(user_message)
    await update.message.reply_text(response.text)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling()

if __name__ == "__main__":
    main()

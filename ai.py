import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TELEGRAM_TOKEN = "8196612202:AAGpFRPryPtXA5bEpJxSrb0Db1cU2uYWOFg"
GEMINI_API_KEY = "AIzaSyCe-Fd0Sj3ODlVoy78mFjnF_kgm4qypLd0"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 👋 من ربات DARK PLUS BOT هستم، هرچی میخوای بپرس!")


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.lower()

 
    identity_keywords = [
        "سازنده", "کی ساختت", "توسط کی", "برنامه نویس",
        "creator", "who made you", "developer", "مال کی هستی", "خودتو معرفی کن"
    ]
    if any(word in user_message for word in identity_keywords):
        await update.message.reply_text("من توسط گروه Dark Plus و با برنامه‌نویسی عرفان محمدی ساخته شدم 🔥")
        return


    response = model.generate_content(user_message)
    await update.message.reply_text(response.text)

# ران
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.run_polling()

if __name__ == "__main__":
    main()

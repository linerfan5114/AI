


from openai import OpenAI
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


OPENAI_API_KEY = "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"
TELEGRAM_TOKEN = ""

client = OpenAI(api_key=OPENAI_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام 👋 من ربات هوش مصنوعی هستم، هرچی میخوای بپرس!")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "user", "content": user_message}]
    )
    
    bot_reply = response.choices[0].message.content
    await update.message.reply_text(bot_reply)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    app.run_polling()

if __name__ == "__main__":
    main()

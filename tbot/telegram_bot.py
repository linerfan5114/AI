import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import requests
import json

# Replace with your actual Bot Token
BOT_TOKEN = "8196612202:AAGpFRPryPtXA5bEpJxSrb0Db1cU2uYWOFg" 
API_URL = "http://127.0.0.1:5000/predict_price"

def start(update, context):
    update.message.reply_text(
        "سلام! من میتونم قیمت یک کامپیوتر رو پیش‌بینی کنم. "
        "لطفا مشخصات رو با این فرمت بفرستید:\n\n"
        "CPU: [نام_سی‌پی‌یو]\n"
        "GPU: [نام_جی‌پی‌یو]\n"
        "Brand: [نام_برند]\n"
        "RAM: [مقدار_رم_به_گیگابایت]\n"
        "SSD: [مقدار_اس‌اس‌دی_به_گیگابایت]\n\n"
        "مثال: \n"
        "CPU: intel core i7\n"
        "GPU: rtx 3070\n"
        "Brand: asus\n"
        "RAM: 16\n"
        "SSD: 512"
    )

def predict(update, context):
    try:
        user_input_text = update.message.text
        lines = user_input_text.split('\n')
        
        data = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                data[key.strip().lower()] = value.strip()
        
        required_fields = ['cpu', 'gpu', 'brand', 'ram', 'ssd']
        if not all(field in data for field in required_fields):
            update.message.reply_text("❌ فرمت ورودی اشتباه است. لطفا از فرمت صحیح استفاده کنید:\nCPU: ...\nGPU: ...\nBrand: ...\nRAM: ...\nSSD: ...")
            return
        
        response = requests.post(API_URL, json=data)
        
        if response.status_code == 200:
            result = response.json()
            predicted_price = result['predicted_price']
            update.message.reply_text(f"✅ قیمت پیش‌بینی شده: ${predicted_price}")
        else:
            error_message = response.json().get('error', 'خطای نامشخصی رخ داد.')
            update.message.reply_text(f"❌ خطا: {error_message}")
    
    except Exception as e:
        update.message.reply_text(f"خطای غیرمنتظره‌ای رخ داد: {e}")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, predict))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
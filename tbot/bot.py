from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
import pandas as pd
import joblib

model = joblib.load("model.pkl")
X_train_cols = joblib.load("x_train_cols.pkl")  

def predict_price(cpu, gpu, brand, ram, ssd):
    new_computer = {
        'CPU': [cpu.lower()],
        'RAM_GB': [int(ram)],
        'SSD_GB': [int(ssd)],
        'GPU': [gpu.lower()],
        'Brand': [brand.lower()]
    }
    new_df = pd.DataFrame(new_computer)
    new_df_encoded = pd.get_dummies(new_df, columns=['CPU', 'GPU', 'Brand'], drop_first=True)
    new_df_encoded = new_df_encoded.reindex(columns=X_train_cols, fill_value=0)
    predicted_price = model.predict(new_df_encoded)
    return f"${predicted_price[0]:.2f}"

# ---------- بخش ربات ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! مشخصات لپ‌تاپ رو به شکل زیر بفرست:\n\nCPU,GPU,Brand,RAM,SSD")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.split(",")
        cpu, gpu, brand, ram, ssd = text
        result = predict_price(cpu, gpu, brand, ram, ssd)
        await update.message.reply_text(f"Predicted Price: {result}")
    except Exception as e:
        await update.message.reply_text(f"خطا در ورودی! {e}")

app = ApplicationBuilder().token("8196612202:AAGpFRPryPtXA5bEpJxSrb0Db1cU2uYWOFg").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()

import pandas as pd
import joblib
from sklearn.model_selection import train_test_split, GridSearchCV
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram import Update
import os

CSV_PATH = "computer_specs_very_large.csv"
MODEL_PATH = "model.pkl"
COLS_PATH = "x_train_cols.pkl"
BOT_TOKEN = ".."
ADMINS = [1, 2] 


user_currency = {}

def train_and_save():
    df = pd.read_csv(CSV_PATH)
    df['RAM_GB'] = pd.to_numeric(df['RAM_GB'], errors='coerce').fillna(0).astype(int)
    df['SSD_GB'] = pd.to_numeric(df['SSD_GB'], errors='coerce').fillna(0).astype(int)
    df['Price_USD'] = pd.to_numeric(df['Price_USD'], errors='coerce').fillna(0).astype(float)
    for col in ['CPU', 'GPU', 'Brand']:
        df[col] = df[col].str.lower().str.strip()
    df_encoded = pd.get_dummies(df, columns=['CPU', 'GPU', 'Brand'], drop_first=True)
    X = df_encoded.drop('Price_USD', axis=1)
    y = df_encoded['Price_USD']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    param_grid = {'n_estimators': [100, 200],'learning_rate': [0.05, 0.1],'max_depth': [3, 4]}
    xgb = XGBRegressor(objective='reg:squarederror', random_state=42)
    grid_search = GridSearchCV(estimator=xgb, param_grid=param_grid, cv=3, n_jobs=-1, verbose=1)
    grid_search.fit(X_train, y_train)
    best_model = grid_search.best_estimator_
    y_pred = best_model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"Model trained. MAE: {mae:.2f}, R2: {r2:.2f}")
    joblib.dump(best_model, MODEL_PATH)
    joblib.dump(X.columns, COLS_PATH)
    print("Model and columns saved.")

def load_model():
    model = joblib.load(MODEL_PATH)
    X_train_cols = joblib.load(COLS_PATH)
    return model, X_train_cols

def convert_currency(price_usd, currency):
    rates = {"usd": 1, "eur": 0.9, "irr": 60000}
    return price_usd * rates.get(currency, 1)

def predict_price(cpu, gpu, brand, ram, ssd, model, X_train_cols, currency):
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
    predicted_price_usd = model.predict(new_df_encoded)[0]
    converted = convert_currency(predicted_price_usd, currency)
    symbol = "$" if currency=="usd" else "€" if currency=="eur" else "تومان"
    return f"{converted:.2f} {symbol}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""📌 راهنمای ربات:
- مشخصات لپ‌تاپ رو اینطوری بفرست:
CPU,GPU,Brand,RAM,SSD
مثال:
intel i7,nvidia rtx 3060,asus,16,512

💱 تغییر واحد پول:
 /currency usd → دلار
 /currency eur → یورو
 /currency irr → تومان

⚙️ دستورات ویژه:
 /train → آموزش دوباره مدل (فقط برای ادمین‌ها)
 /help → همین منو""")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = """📌 راهنمای ربات:
- مشخصات لپ‌تاپ رو اینطوری بفرست:
CPU,GPU,Brand,RAM,SSD
مثال:
intel i7,nvidia rtx 3060,asus,16,512

💱 تغییر واحد پول:
 /currency usd → دلار
 /currency eur → یورو
 /currency irr → تومان

⚙️ دستورات ویژه:
 /train → آموزش دوباره مدل (فقط برای ادمین‌ها)
 /help → همین منو"""
    await update.message.reply_text(txt)

async def currency_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("لطفا واحد پول رو مشخص کن: usd, eur, irr")
        return
    cur = context.args[0].lower()
    if cur not in ["usd","eur","irr"]:
        await update.message.reply_text("واحد نامعتبر! فقط usd, eur, irr")
        return
    user_currency[update.effective_user.id] = cur
    await update.message.reply_text(f"واحد پول شما روی {cur.upper()} تنظیم شد.")

async def train_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMINS:
        await update.message.reply_text("⛔ شما اجازه این دستور رو ندارید.")
        return
    await update.message.reply_text("مدل در حال آموزش مجدد است...")
    train_and_save()
    global model, X_train_cols
    model, X_train_cols = load_model()
    await update.message.reply_text("✅ مدل با موفقیت دوباره آموزش داده شد.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        cpu, gpu, brand, ram, ssd = update.message.text.split(",")
        currency = user_currency.get(update.effective_user.id, "usd")
        result = predict_price(cpu, gpu, brand, ram, ssd, model, X_train_cols, currency)
        await update.message.reply_text(f"💻 Predicted Price: {result}")
    except Exception as e:
        await update.message.reply_text(f"خطا در ورودی! {e}")

if __name__ == "__main__":
    if not os.path.exists(MODEL_PATH) or not os.path.exists(COLS_PATH):
        train_and_save()
    model, X_train_cols = load_model()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("currency", currency_cmd))
    app.add_handler(CommandHandler("train", train_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running...")
    app.run_polling()

import os
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split, GridSearchCV
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, r2_score

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
import asyncio

# =================== تنظیمات و متغیرها ===================
CSV_PATH = "computer_specs_very_large.csv"
MODEL_PATH = "model.pkl"
COLS_PATH = "x_train_cols.pkl"
BOT_TOKEN = "8196612202:AAGpFRPryPtXA5bEpJxSrb0Db1cU2uYWOFg"
ADMINS = [7354827676, 777209689]  
CURRENCY_RATES = {"USD": 1, "EUR": 0.93, "TOMAN": 53000} 
user_currency = {}  # ذخیره واحد پول برای هر کاربر

model, X_train_cols = None, None

# =================== توابع مدل ===================
def train_and_save():
    """مدل یادگیری ماشین را آموزش داده و آن را به همراه ستون‌ها ذخیره می‌کند."""
    print("Training model...")
    df = pd.read_csv(CSV_PATH)

    # تبدیل ستون‌های مورد نیاز به نوع عددی
    df['RAM_GB'] = pd.to_numeric(df['RAM_GB'], errors='coerce').fillna(0).astype(int)
    df['SSD_GB'] = pd.to_numeric(df['SSD_GB'], errors='coerce').fillna(0).astype(int)
    df['Price_USD'] = pd.to_numeric(df['Price_USD'], errors='coerce').fillna(0).astype(float)

    # تبدیل مقادیر متنی به حروف کوچک و حذف فاصله‌های اضافی
    for col in ['CPU', 'GPU', 'Brand']:
        df[col] = df[col].str.lower().str.strip()

    # One-hot encoding برای ستون‌های دسته‌بندی
    df_encoded = pd.get_dummies(df, columns=['CPU', 'GPU', 'Brand'], drop_first=True)
    X = df_encoded.drop('Price_USD', axis=1)
    y = df_encoded['Price_USD']

    # تقسیم داده‌ها
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # آموزش مدل XGBoost با GridSearchCV برای بهینه‌سازی پارامترها
    param_grid = {'n_estimators': [100, 200], 'learning_rate': [0.05, 0.1], 'max_depth': [3, 4]}
    xgb = XGBRegressor(objective='reg:squarederror', random_state=42)
    grid_search = GridSearchCV(estimator=xgb, param_grid=param_grid, cv=3, n_jobs=-1, verbose=1)
    grid_search.fit(X_train, y_train)

    best_model = grid_search.best_estimator_
    y_pred = best_model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"Model trained. MAE: {mae:.2f}, R2: {r2:.2f}")

    # ذخیره مدل و ستون‌های استفاده شده
    joblib.dump(best_model, MODEL_PATH)
    joblib.dump(X.columns, COLS_PATH)
    print("Model and columns saved.")

def load_model():
    """مدل و ستون‌های ذخیره‌شده را بارگذاری می‌کند."""
    print("Loading model...")
    try:
        model_loaded = joblib.load(MODEL_PATH)
        X_train_cols_loaded = joblib.load(COLS_PATH)
        return model_loaded, X_train_cols_loaded
    except FileNotFoundError:
        print("Model or columns file not found. Please run the training command.")
        return None, None

def predict_price(cpu, gpu, brand, ram, ssd, model, X_train_cols, currency="USD"):
    """قیمت یک لپ‌تاپ را پیش‌بینی می‌کند."""
    # ایجاد یک DataFrame با تمام ستون‌های مدل و مقدار اولیه 0
    new_data = pd.DataFrame(columns=X_train_cols, index=[0]).fillna(0)
    
    # افزودن مقادیر عددی
    new_data['RAM_GB'] = int(ram)
    new_data['SSD_GB'] = int(ssd)

    # افزودن مقادیر one-hot-encoded برای CPU, GPU, Brand
    cpu_col_name = f"CPU_{cpu.lower().strip()}"
    gpu_col_name = f"GPU_{gpu.lower().strip()}"
    brand_col_name = f"Brand_{brand.lower().strip()}"

    if cpu_col_name in new_data.columns:
        new_data[cpu_col_name] = 1
    if gpu_col_name in new_data.columns:
        new_data[gpu_col_name] = 1
    if brand_col_name in new_data.columns:
        new_data[brand_col_name] = 1

    # پیش‌بینی قیمت
    predicted_price = model.predict(new_data)[0]
    predicted_price_converted = predicted_price * CURRENCY_RATES.get(currency, 1)
    return f"{predicted_price_converted:.2f} {currency}"

# =================== دستورات ربات ===================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پیام شروع ربات و دکمه‌های انتخاب واحد پول را نمایش می‌دهد."""
    keyboard = [[KeyboardButton("دلار"), KeyboardButton("یورو"), KeyboardButton("تومان")]]
    await update.message.reply_text(
        "سلام! ابتدا واحد پول خود را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پیام‌های متنی را پردازش می‌کند، چه برای تنظیم واحد پول و چه برای پیش‌بینی قیمت."""
    user_input = update.message.text.strip()
    chat_id = update.message.chat_id

    # بررسی می‌کند که آیا ورودی یک واحد پول معتبر است
    if user_input.upper() in CURRENCY_RATES:
        user_currency[chat_id] = user_input.upper()
        await update.message.reply_text(
            "واحد پول شما ثبت شد. حالا مشخصات لپ‌تاپ را اینطوری وارد کنید:\nCPU,GPU,Brand,RAM,SSD",
            reply_markup=ReplyKeyboardRemove()
        )
        return

    # در غیر این صورت، ورودی را به عنوان مشخصات لپ‌تاپ پردازش می‌کند
    try:
        # بررسی تعداد ورودی‌ها
        parts = user_input.split(",")
        if len(parts) != 5:
            await update.message.reply_text("فرمت ورودی نادرست است. لطفاً مشخصات را به این شکل وارد کنید:\nCPU,GPU,Brand,RAM,SSD")
            return

        cpu, gpu, brand, ram, ssd = [p.strip() for p in parts]
        currency = user_currency.get(chat_id, "USD")
        
        # بررسی اینکه مدل بارگذاری شده باشد
        if model is None or X_train_cols is None:
            await update.message.reply_text("مدل هنوز بارگذاری نشده است. لطفاً صبر کنید یا به ادمین اطلاع دهید.")
            return

        result = predict_price(cpu, gpu, brand, ram, ssd, model, X_train_cols, currency)
        await update.message.reply_text(f"Predicted Price: {result}")
    except ValueError:
        await update.message.reply_text("خطا در ورودی! مطمئن شوید که RAM و SSD عدد صحیح هستند.")
    except Exception as e:
        await update.message.reply_text(f"خطا در پردازش مشخصات. ممکن است یکی از مشخصات وارد شده در دیتاست موجود نباشد. لطفا ورودی را دوباره بررسی کنید.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """راهنمای استفاده از ربات را نمایش می‌دهد."""
    await update.message.reply_text(
        "این ربات توسط گروه dark plus ساخته شده است و قیمت کامپیوتر را با ماشین پیشبینی می‌کند.\n"
        "سازندگان: عرفان محمدی\n\n"
        "فرمت ورودی:\nCPU,GPU,Brand,RAM,SSD\n\n"
        "دستورات:\n"
        "/start → شروع ربات و انتخاب واحد پول\n"
        "/help → نمایش این راهنما\n"
        "/train → آموزش دوباره مدل (فقط ادمین‌ها)"
    )

async def train_model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدل را مجدداً آموزش می‌دهد (فقط برای ادمین‌ها)."""
    if update.message.chat_id not in ADMINS:
        await update.message.reply_text("شما اجازه اجرای این دستور را ندارید!")
        return
    await update.message.reply_text("آموزش مدل در حال انجام است. لطفاً صبر کنید...")
    train_and_save()
    global model, X_train_cols
    model, X_train_cols = load_model()
    await update.message.reply_text("آموزش مدل تمام شد و ذخیره شد.")

# =================== اجرای ربات ===================
def main():
    """تابع اصلی برای اجرای ربات."""
    global model, X_train_cols

    if not os.path.exists(MODEL_PATH) or not os.path.exists(COLS_PATH):
        print("Model files not found. Training a new model...")
        train_and_save()

    model, X_train_cols = load_model()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("train", train_model_command))
    # هندلر واحد برای پردازش هر دو نوع پیام
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

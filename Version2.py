import pyautogui as pu
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import os, json, hashlib, threading, datetime as dt
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

pu.alert("""Made by dark-plus group
Programmers: Erfan Mohammadi and Ali Ahmadabadi""")
USERS_FILE = "users.json"
CSV_PATH = "computer_specs_very_large.csv"

def now_utc():
    return dt.datetime.utcnow()

def iso(dtobj):
    return dtobj.strftime("%Y-%m-%dT%H:%M:%SZ")

def parse_iso(s):
    try:
        return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
    except:
        return now_utc()

def hash_pw(p):
    return hashlib.sha256(p.encode("utf-8")).hexdigest()

class UsersDB:
    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        self.data = {"users": {}}
        self.load()
        if "admin" not in self.data["users"]:
            self.data["users"]["admin"] = {
                "password_hash": hash_pw("admin123"),
                "role": "admin",
                "created_at": iso(now_utc()),
                "trial_started": iso(now_utc()),
                "subscription_until": None,
                "usage_count": 0,
                "last_login": None
            }
            self.save()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except:
                self.data = {"users": {}}
        else:
            self.data = {"users": {}}

    def save(self):
        with self.lock:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_user(self, username, password):
        if username in self.data["users"]:
            return False, "User exists"
        self.data["users"][username] = {
            "password_hash": hash_pw(password),
            "role": "user",
            "created_at": iso(now_utc()),
            "trial_started": iso(now_utc()),
            "subscription_until": None,
            "usage_count": 0,
            "last_login": None
        }
        self.save()
        return True, "OK"

    def check_login(self, username, password):
        u = self.data["users"].get(username)
        if not u:
            return False, "Not found"
        if u["password_hash"] != hash_pw(password):
            return False, "Wrong password"
        u["last_login"] = iso(now_utc())
        self.save()
        return True, u

    def user_info(self, username):
        return self.data["users"].get(username)

    def set_role(self, username, role):
        u = self.user_info(username)
        if not u:
            return False
        u["role"] = role
        self.save()
        return True

    def delete_user(self, username):
        if username in self.data["users"]:
            del self.data["users"][username]
            self.save()
            return True
        return False

    def reset_password(self, username, new_password):
        u = self.user_info(username)
        if not u:
            return False
        u["password_hash"] = hash_pw(new_password)
        self.save()
        return True

    def add_subscription_days(self, username, days):
        u = self.user_info(username)
        if not u:
            return False
        base = now_utc()
        if u["subscription_until"]:
            su = parse_iso(u["subscription_until"])
            if su > base:
                base = su
        base = base + dt.timedelta(days=days)
        u["subscription_until"] = iso(base)
        self.save()
        return True

    def days_left(self, username):
        u = self.user_info(username)
        if not u:
            return 0
        today = now_utc()
        trial_end = parse_iso(u["trial_started"]) + dt.timedelta(days=10)
        sub_until = parse_iso(u["subscription_until"]) if u["subscription_until"] else None
        target = None
        if sub_until and sub_until > today:
            target = sub_until
        elif trial_end > today:
            target = trial_end
        if not target:
            return 0
        return max(0, (target - today).days + (1 if (target - today).seconds > 0 else 0))

    def is_active(self, username):
        return self.days_left(username) > 0

    def inc_usage(self, username):
        u = self.user_info(username)
        if not u:
            return
        u["usage_count"] = int(u.get("usage_count", 0)) + 1
        self.save()

    def all_users(self):
        return [{"username": k, **v} for k, v in self.data["users"].items()]

class AuthFrame(ttk.Frame):
    def __init__(self, master, controller, db):
        super().__init__(master)
        self.controller = controller
        self.db = db
        self.pack(fill=tk.BOTH, expand=True)
        self.configure(style='TFrame')
        c = ttk.Frame(self, padding=20)
        c.pack(expand=True)
        ttk.Label(c, text="Login / Register", font=("Helvetica", 18, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Label(c, text="Username:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        ttk.Label(c, text="Password:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.username = ttk.Entry(c, width=28)
        self.password = ttk.Entry(c, width=28, show="*")
        self.username.grid(row=1, column=1, padx=5, pady=5)
        self.password.grid(row=2, column=1, padx=5, pady=5)
        btns = ttk.Frame(c)
        btns.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btns, text="Login", command=self.login).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="Register", command=self.register).pack(side=tk.LEFT, padx=6)

    def login(self):
        u = self.username.get().strip()
        p = self.password.get().strip()
        ok, res = self.db.check_login(u, p)
        if not ok:
            messagebox.showerror("Login", "Invalid credentials")
            return
        self.controller.current_user = u
        self.controller.current_role = res["role"]
        self.controller.show_predictor()

    def register(self):
        u = self.username.get().strip()
        p = self.password.get().strip()
        if not u or not p:
            messagebox.showerror("Register", "Fill username and password")
            return
        ok, msg = self.db.add_user(u, p)
        if ok:
            messagebox.showinfo("Register", "Account created. You have 10-day free trial.")
        else:
            messagebox.showerror("Register", msg)

class AdminPanel(tk.Toplevel):
    def __init__(self, master, db):
        super().__init__(master)
        self.db = db
        self.title("Admin Panel")
        self.geometry("850x500")
        cols = ("username","role","created_at","trial_started","subscription_until","usage_count","last_login","days_left")
        self.tree = ttk.Treeview(self, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=110, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True, pady=6)
        b = ttk.Frame(self)
        b.pack(fill=tk.X)
        ttk.Button(b, text="Refresh", command=self.refresh).pack(side=tk.LEFT, padx=4, pady=6)
        ttk.Button(b, text="Add Sub Days", command=self.add_days).pack(side=tk.LEFT, padx=4)
        ttk.Button(b, text="Make Admin/User", command=self.toggle_role).pack(side=tk.LEFT, padx=4)
        ttk.Button(b, text="Reset Password", command=self.reset_pw).pack(side=tk.LEFT, padx=4)
        ttk.Button(b, text="Delete User", command=self.delete_user).pack(side=tk.LEFT, padx=4)
        self.refresh()

    def selected_user(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self.tree.item(sel[0])["values"][0]

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for u in self.db.all_users():
            dl = self.db.days_left(u["username"])
            vals = (
                u["username"],
                u.get("role","user"),
                u.get("created_at",""),
                u.get("trial_started",""),
                u.get("subscription_until",""),
                u.get("usage_count",0),
                u.get("last_login",""),
                dl
            )
            self.tree.insert("", tk.END, values=vals)

    def add_days(self):
        user = self.selected_user()
        if not user:
            messagebox.showerror("Admin", "Select a user")
            return
        try:
            days = int(simpledialog.askstring("Days", "Days to add:", parent=self) or "0")
        except:
            messagebox.showerror("Admin", "Invalid days")
            return
        if days <= 0:
            messagebox.showerror("Admin", "Days must be > 0")
            return
        self.db.add_subscription_days(user, days)
        self.refresh()

    def toggle_role(self):
        user = self.selected_user()
        if not user:
            messagebox.showerror("Admin", "Select a user")
            return
        info = self.db.user_info(user)
        role = "admin" if info.get("role","user") != "admin" else "user"
        self.db.set_role(user, role)
        self.refresh()

    def reset_pw(self):
        user = self.selected_user()
        if not user:
            messagebox.showerror("Admin", "Select a user")
            return
        newp = simpledialog.askstring("Reset Password", "New password:", parent=self, show="*")
        if not newp:
            return
        self.db.reset_password(user, newp)
        messagebox.showinfo("Admin", "Password updated")

    def delete_user(self):
        user = self.selected_user()
        if not user:
            messagebox.showerror("Admin", "Select a user")
            return
        if messagebox.askyesno("Admin", f"Delete {user}?"):
            self.db.delete_user(user)
            self.refresh()

class PredictorFrame(ttk.Frame):
    def __init__(self, master, controller, db, csv_file_path):
        super().__init__(master)
        self.controller = controller
        self.db = db
        self.csv_file_path = csv_file_path
        self.best_model = None
        self.X_train_cols = None
        self.df = None
        self.unique_values = {}
        self.pack(fill=tk.BOTH, expand=True)
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TFrame', background="#1E1E1E")
        style.configure('TLabel', background="#a0a0a0", font=('Helvetica', 12))
        style.configure('TButton', font=('Helvetica', 12, 'bold'), padding=10)
        style.configure('TEntry', padding=5)
        top = ttk.Frame(self, padding="10 10 10 10")
        top.pack(fill=tk.X)
        self.user_label = ttk.Label(top, text="")
        self.user_label.pack(side=tk.LEFT)
        ttk.Button(top, text="Logout", command=self.controller.logout).pack(side=tk.RIGHT, padx=5)
        self.admin_btn = ttk.Button(top, text="Admin Panel", command=self.open_admin)
        self.admin_btn.pack(side=tk.RIGHT, padx=5)
        self.buy_btn = ttk.Button(top, text="Buy Subscription", command=self.buy_sub)
        self.buy_btn.pack(side=tk.RIGHT, padx=5)
        main_frame = ttk.Frame(self, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        title_label = ttk.Label(main_frame, text="Computer Price Prediction", font=("Helvetica", 18, 'bold'))
        title_label.pack(pady=(0, 20))
        self.status_label = ttk.Label(main_frame, text="Loading and training model...", font=('Helvetica', 12, 'italic'))
        self.status_label.pack(pady=(0, 10))
        input_frame = ttk.Frame(main_frame, padding=10, relief="groove")
        input_frame.pack(fill=tk.X, pady=10)
        self.entries = {}
        input_fields = ['CPU', 'GPU', 'Brand', 'RAM (GB)', 'SSD (GB)']
        for field in input_fields:
            row = ttk.Frame(input_frame)
            row.pack(fill=tk.X, pady=5)
            ttk.Label(row, text=f"{field}:", width=15).pack(side=tk.LEFT, padx=(0, 10))
            e = ttk.Entry(row)
            e.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.entries[field] = e
        self.predict_button = ttk.Button(main_frame, text="Predict Price", command=self.predict_price, state='disabled')
        self.predict_button.pack(pady=(20, 10))
        self.result_label = ttk.Label(main_frame, text="", font=("Helvetica", 14, 'bold'))
        self.result_label.pack(pady=(10, 0))
        self.refresh_user_badge()
        self.start_training_thread()

    def refresh_user_badge(self):
        u = self.controller.current_user
        role = self.controller.current_role
        days = self.db.days_left(u)
        self.user_label.config(text=f"User: {u} | Role: {role} | Days left: {days}")
        self.admin_btn.config(state='normal' if role == "admin" else 'disabled')
        active = self.db.is_active(u)
        if not active:
            self.status_label.config(text="Access expired. Please buy subscription to continue.")
        self.predict_button.config(state='disabled' if not active or not self.best_model else 'normal')

    def open_admin(self):
        AdminPanel(self, self.db)

    def buy_sub(self):
        messagebox.showinfo("Subscription", "برای خرید اشتراک به آیدی @kali-ux پیام دهید.\nپس از پرداخت، ادمین از پنل برای شما اشتراک شارژ می‌کند.")

    def start_training_thread(self):
        self.status_label.config(text="Loading and training model...")
        self.predict_button.config(state='disabled')
        t = threading.Thread(target=self.train_model, daemon=True)
        t.start()

    def train_model(self):
        try:
            if not os.path.exists(self.csv_file_path):
                self.after(0, lambda: self.show_error(f"Error: file '{self.csv_file_path}' not found."))
                return
            self.after(0, lambda: self.status_label.config(text="Reading data..."))
            df = pd.read_csv(self.csv_file_path)
            self.after(0, lambda: self.status_label.config(text="Preprocessing data..."))
            df['RAM_GB'] = pd.to_numeric(df['RAM_GB'], errors='coerce').fillna(0).astype(int)
            df['SSD_GB'] = pd.to_numeric(df['SSD_GB'], errors='coerce').fillna(0).astype(int)
            df['Price_USD'] = pd.to_numeric(df['Price_USD'], errors='coerce').fillna(0).astype(float)
            for col in ['CPU', 'GPU', 'Brand']:
                df[col] = df[col].str.lower().str.strip()
            self.unique_values['CPU'] = sorted(df['CPU'].unique())
            self.unique_values['GPU'] = sorted(df['GPU'].unique())
            self.unique_values['Brand'] = sorted(df['Brand'].unique())
            df_encoded = pd.get_dummies(df, columns=['CPU', 'GPU', 'Brand'], drop_first=True)
            X = df_encoded.drop('Price_USD', axis=1)
            y = df_encoded['Price_USD']
            self.X_train_cols = X.columns
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            self.after(0, lambda: self.status_label.config(text="Optimizing model with GridSearchCV..."))
            param_grid = {'n_estimators': [100, 200], 'learning_rate': [0.05, 0.1], 'max_depth': [3, 4]}
            xgb = XGBRegressor(objective='reg:squarederror', random_state=42)
            grid_search = GridSearchCV(estimator=xgb, param_grid=param_grid, cv=5, n_jobs=-1, verbose=2)
            grid_search.fit(X_train, y_train)
            self.best_model = grid_search.best_estimator_
            y_pred = self.best_model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            pu.alert(f"Final model trained. MAE: ${mae:.2f}, R2: {r2:.2f}")
            self.after(0, self.training_complete)
        except Exception as e:
            self.after(0, lambda: self.show_error(f"An unexpected error occurred: {e}"))

    def training_complete(self):
        self.status_label.config(text="Model is ready for prediction.")
        self.refresh_user_badge()

    def standardize_input(self, category, user_input):
        s = user_input.lower().strip()
        gpu_map = {
            "rtx 3070":"nvidia rtx 3070","3070":"nvidia rtx 3070","nvidia rtx 3070":"nvidia rtx 3070",
            "rtx 3060":"nvidia rtx 3060","3060":"nvidia rtx 3060","nvidia rtx 3060":"nvidia rtx 3060",
            "gtx 1650":"nvidia gtx 1650","1650":"nvidia gtx 1650","nvidia gtx 1650":"nvidia gtx 1650",
            "rtx 4090":"nvidia rtx 4090","4090":"nvidia rtx 4090","nvidia rtx 4090":"nvidia rtx 4090",
            "rtx 4080":"nvidia rtx 4080","4080":"nvidia rtx 4080","nvidia rtx 4080":"nvidia rtx 4080",
            "rtx 4070":"nvidia rtx 4070","4070":"nvidia rtx 4070","nvidia rtx 4070":"nvidia rtx 4070",
            "intel arc a770":"intel arc a770","a770":"intel arc a770","arc a770":"intel arc a770",
            "amd radeon rx 6500":"amd radeon rx 6500","rx 6500":"amd radeon rx 6500","amd 6500":"amd radeon rx 6500","radeon rx 6500":"amd radeon rx 6500",
            "amd radeon rx 6600":"amd radeon rx 6600","rx 6600":"amd radeon rx 6600","amd 6600":"amd radeon rx 6600","radeon rx 6600":"amd radeon rx 6600",
        }
        cpu_map = {"i3":"intel i3","i5":"intel i5","i7":"intel i7","i9":"intel i9","ryzen 3":"amd ryzen 3","ryzen 5":"amd ryzen 5","ryzen 7":"amd ryzen 7","ryzen 9":"amd ryzen 9"}
        brand_map = {"acer":"acer","lenovo":"lenovo","asus":"asus","apple":"apple","razer":"razer","dell":"dell","msi":"msi","hp":"hp"}
        if category=='GPU': return gpu_map.get(s, s)
        if category=='CPU': return cpu_map.get(s, s)
        if category=='Brand': return brand_map.get(s, s)
        return s

    def predict_price(self):
        if not self.best_model:
            messagebox.showerror("Error", "The model is not ready yet. Please wait.")
            return
        if not self.db.is_active(self.controller.current_user):
            self.refresh_user_badge()
            self.buy_sub()
            return
        try:
            user_cpu_raw = self.entries['CPU'].get()
            user_gpu_raw = self.entries['GPU'].get()
            user_brand_raw = self.entries['Brand'].get()
            user_ram = int(self.entries['RAM (GB)'].get())
            user_ssd = int(self.entries['SSD (GB)'].get())
            user_cpu = self.standardize_input('CPU', user_cpu_raw)
            user_gpu = self.standardize_input('GPU', user_gpu_raw)
            user_brand = self.standardize_input('Brand', user_brand_raw)
            if user_cpu not in self.unique_values['CPU'] or user_gpu not in self.unique_values['GPU'] or user_brand not in self.unique_values['Brand']:
                messagebox.showerror("Invalid Input", "One of your inputs (CPU, GPU, or Brand) was not found in the training data. Please enter a valid value.")
                return
            new_df = pd.DataFrame({'CPU':[user_cpu],'RAM_GB':[user_ram],'SSD_GB':[user_ssd],'GPU':[user_gpu],'Brand':[user_brand]})
            new_df_encoded = pd.get_dummies(new_df, columns=['CPU','GPU','Brand'], drop_first=True)
            new_df_encoded = new_df_encoded.reindex(columns=self.X_train_cols, fill_value=0)
            predicted_price = self.best_model.predict(new_df_encoded)
            self.result_label.config(text=f"Predicted Price: ${predicted_price[0]:.2f}")
            self.db.inc_usage(self.controller.current_user)
            self.refresh_user_badge()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please make sure RAM and SSD are valid numbers.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during prediction: {e}")

    def show_error(self, message):
        messagebox.showerror("Application Error", message)
        self.controller.logout()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Dark-Plus | Price Predictor")
        self.geometry("770x770")
        self.configure(bg="#a0a0a0")
        self.db = UsersDB(USERS_FILE)
        self.current_user = None
        self.current_role = "user"
        self.container = ttk.Frame(self, padding=10)
        self.container.pack(fill=tk.BOTH, expand=True)
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure('TFrame', background="#1E1E1E")
        self.style.configure('TLabel', background="#a0a0a0", font=('Helvetica', 12))
        self.style.configure('TButton', font=('Helvetica', 12, 'bold'), padding=10)
        self.style.configure('TEntry', padding=5)
        self.auth = None
        self.predictor = None
        self.show_auth()

    def clear(self):
        for w in self.container.winfo_children():
            w.destroy()

    def show_auth(self):
        self.clear()
        self.auth = AuthFrame(self.container, self, self.db)

    def show_predictor(self):
        if not os.path.exists(CSV_PATH):
            messagebox.showerror("File Not Found", f"Error: The file '{CSV_PATH}' was not found.\n\nPlease make sure the file is in the same folder as the script.")
            return
        self.clear()
        self.predictor = PredictorFrame(self.container, self, self.db, CSV_PATH)

    def logout(self):
        self.current_user = None
        self.current_role = "user"
        self.show_auth()

if __name__ == "__main__":
    app = App()
    app.mainloop()
    
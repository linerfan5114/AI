# Machine
# Developer : erfan mohammadi , ali ahmad abadi , Fatima Zahra

import pyautogui as pu
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from scipy.stats import randint, uniform
import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import joblib

class PricePredictorApp(tk.Tk):
    def __init__(self, csv_file_path):
        super().__init__()
        self.csv_file_path = csv_file_path
        self.title("Computer Price Prediction")
        self.geometry("680x700")
        self.configure(bg="#0f1216")
        self.best_model = None
        self.X_train_cols = None
        self.df = None
        self.unique_values = {}
        self.model_path = "computer_price_model.pkl"
        self.meta_path = "computer_price_meta.pkl"
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TFrame', background="#0f1216")
        style.configure('TLabel', background="#0f1216", foreground="#e5e7eb", font=('Helvetica', 12))
        style.configure('TButton', font=('Helvetica', 12, 'bold'), padding=10)
        style.configure('TEntry', padding=6)
        main_frame = ttk.Frame(self, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        title_label = ttk.Label(main_frame, text="💻 Computer Price Prediction", font=("Helvetica", 20, 'bold'))
        title_label.pack(pady=(0, 16))
        self.status_label = ttk.Label(main_frame, text="Initializing...", font=('Helvetica', 11, 'italic'))
        self.status_label.pack(pady=(0, 10))
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(0, 14))
        card = ttk.Frame(main_frame, padding=14)
        card.pack(fill=tk.X, pady=10)
        self.inputs = {}
        row = ttk.Frame(card)
        row.pack(fill=tk.X, pady=6)
        ttk.Label(row, text="CPU:", width=16).pack(side=tk.LEFT, padx=(0,10))
        self.inputs['CPU'] = ttk.Combobox(row, state='disabled')
        self.inputs['CPU'].pack(side=tk.LEFT, fill=tk.X, expand=True)
        row = ttk.Frame(card); row.pack(fill=tk.X, pady=6)
        ttk.Label(row, text="GPU:", width=16).pack(side=tk.LEFT, padx=(0,10))
        self.inputs['GPU'] = ttk.Combobox(row, state='disabled')
        self.inputs['GPU'].pack(side=tk.LEFT, fill=tk.X, expand=True)
        row = ttk.Frame(card); row.pack(fill=tk.X, pady=6)
        ttk.Label(row, text="Brand:", width=16).pack(side=tk.LEFT, padx=(0,10))
        self.inputs['Brand'] = ttk.Combobox(row, state='disabled')
        self.inputs['Brand'].pack(side=tk.LEFT, fill=tk.X, expand=True)
        row = ttk.Frame(card); row.pack(fill=tk.X, pady=6)
        ttk.Label(row, text="RAM (GB):", width=16).pack(side=tk.LEFT, padx=(0,10))
        self.inputs['RAM (GB)'] = ttk.Entry(row)
        self.inputs['RAM (GB)'].pack(side=tk.LEFT, fill=tk.X, expand=True)
        row = ttk.Frame(card); row.pack(fill=tk.X, pady=6)
        ttk.Label(row, text="SSD (GB):", width=16).pack(side=tk.LEFT, padx=(0,10))
        self.inputs['SSD (GB)'] = ttk.Entry(row)
        self.inputs['SSD (GB)'].pack(side=tk.LEFT, fill=tk.X, expand=True)
        btn_row = ttk.Frame(main_frame); btn_row.pack(pady=(18,8))
        self.predict_button = ttk.Button(btn_row, text="⚡ Predict Price", command=self.predict_price, state='disabled')
        self.predict_button.pack(side=tk.LEFT, padx=6)
        self.retrain_button = ttk.Button(btn_row, text="🔁 Retrain", command=self.start_training_thread, state='disabled')
        self.retrain_button.pack(side=tk.LEFT, padx=6)
        self.result_label = ttk.Label(main_frame, text="", font=("Helvetica", 16, 'bold'))
        self.result_label.pack(pady=(12, 0))
        self.metrics_label = ttk.Label(main_frame, text="", font=("Helvetica", 11))
        self.metrics_label.pack(pady=(6, 0))
        self.startup()

    def startup(self):
        if os.path.exists(self.model_path) and os.path.exists(self.meta_path):
            try:
                self.best_model = joblib.load(self.model_path)
                meta = joblib.load(self.meta_path)
                self.X_train_cols = meta["X_train_cols"]
                self.unique_values = meta["unique_values"]
                self.enable_inputs()
                self.status_label.config(text="Model loaded from disk.")
                self.predict_button.config(state='normal')
                self.retrain_button.config(state='normal')
                return
            except Exception:
                pass
        self.start_training_thread()

    def start_training_thread(self):
        self.status_label.config(text="Loading and training model...")
        self.predict_button.config(state='disabled')
        self.retrain_button.config(state='disabled')
        self.progress.start(10)
        training_thread = threading.Thread(target=self.train_model)
        training_thread.daemon = True
        training_thread.start()

    def train_model(self):
        try:
            if not os.path.exists(self.csv_file_path):
                self.after(0, lambda: self.show_error(f"Error: file '{self.csv_file_path}' not found."))
                return
            self.after(0, lambda: self.status_label.config(text="Reading data..."))
            df = pd.read_csv(self.csv_file_path)
            self.after(0, lambda: self.status_label.config(text="Preprocessing..."))
            df['RAM_GB'] = pd.to_numeric(df['RAM_GB'], errors='coerce')
            df['SSD_GB'] = pd.to_numeric(df['SSD_GB'], errors='coerce')
            df['Price_USD'] = pd.to_numeric(df['Price_USD'], errors='coerce')
            df = df.dropna(subset=['RAM_GB','SSD_GB','Price_USD','CPU','GPU','Brand']).reset_index(drop=True)
            df['RAM_GB'] = df['RAM_GB'].clip(lower=0).astype(int)
            df['SSD_GB'] = df['SSD_GB'].clip(lower=0).astype(int)
            for col in ['CPU','GPU','Brand']:
                df[col] = df[col].astype(str).str.lower().str.strip()
            self.unique_values['CPU'] = sorted(df['CPU'].unique())
            self.unique_values['GPU'] = sorted(df['GPU'].unique())
            self.unique_values['Brand'] = sorted(df['Brand'].unique())
            df['Price_log'] = np.log1p(df['Price_USD'].clip(lower=0))
            df_encoded = pd.get_dummies(df[['CPU','GPU','Brand','RAM_GB','SSD_GB','Price_log']], columns=['CPU','GPU','Brand'], drop_first=True)
            X = df_encoded.drop('Price_log', axis=1)
            y = df_encoded['Price_log']
            self.X_train_cols = X.columns
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            self.after(0, lambda: self.status_label.config(text="Tuning model..."))
            xgb = XGBRegressor(objective='reg:squarederror', n_estimators=1200, tree_method='hist', random_state=42)
            param_dist = {
                "max_depth": randint(3, 10),
                "learning_rate": uniform(0.01, 0.15),
                "subsample": uniform(0.6, 0.4),
                "colsample_bytree": uniform(0.6, 0.4),
                "min_child_weight": randint(1, 10),
                "gamma": uniform(0.0, 0.4),
                "reg_lambda": uniform(0.5, 2.0)
            }
            tuner = RandomizedSearchCV(xgb, param_distributions=param_dist, n_iter=40, cv=4, n_jobs=-1, verbose=1, scoring='neg_mean_absolute_error', random_state=42)
            tuner.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
            self.best_model = tuner.best_estimator_
            self.best_model.set_params(early_stopping_rounds=50)
            self.best_model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
            y_pred_log = self.best_model.predict(X_test)
            y_pred = np.expm1(y_pred_log).clip(min=0)
            y_true = np.expm1(y_test).clip(min=0)
            mae = mean_absolute_error(y_true, y_pred)
            err_std = np.std(np.abs(y_true - y_pred))
            r2 = r2_score(y_true, y_pred)
            joblib.dump(self.best_model, self.model_path)
            joblib.dump({"X_train_cols": self.X_train_cols, "unique_values": self.unique_values}, self.meta_path)
            msg = f"Final model trained.\nMAE: ${mae:.2f}\nStd Error: ${err_std:.2f}\nR2: {r2:.3f}"
            self.after(0, lambda: messagebox.showinfo("Training Result", msg))
            self.after(0, lambda: self.metrics_label.config(text=f"MAE: ${mae:.2f} | Std: ${err_std:.2f} | R2: {r2:.3f}"))
            self.after(0, self.training_complete)
        except Exception as e:
            self.after(0, lambda err=e: self.show_error(f"An unexpected error occurred: {err}"))


    def training_complete(self):
        self.progress.stop()
        self.status_label.config(text="Model is ready.")
        self.predict_button.config(state='normal')
        self.retrain_button.config(state='normal')
        self.enable_inputs()

    def enable_inputs(self):
        if self.unique_values:
            for k in ['CPU','GPU','Brand']:
                self.inputs[k]['values'] = self.unique_values.get(k, [])
                self.inputs[k].config(state='readonly')

    def standardize_input(self, category, user_input):
        s = user_input.lower().strip()
        gpu_map = {
            "rtx 3070": "nvidia rtx 3070","3070": "nvidia rtx 3070","nvidia rtx 3070": "nvidia rtx 3070",
            "rtx 3060": "nvidia rtx 3060","3060": "nvidia rtx 3060","nvidia rtx 3060": "nvidia rtx 3060",
            "gtx 1650": "nvidia gtx 1650","1650": "nvidia gtx 1650","nvidia gtx 1650": "nvidia gtx 1650",
            "rtx 4090": "nvidia rtx 4090","4090": "nvidia rtx 4090","nvidia rtx 4090": "nvidia rtx 4090",
            "rtx 4080": "nvidia rtx 4080","4080": "nvidia rtx 4080","nvidia rtx 4080": "nvidia rtx 4080",
            "rtx 4070": "nvidia rtx 4070","4070": "nvidia rtx 4070","nvidia rtx 4070": "nvidia rtx 4070",
            "intel arc a770": "intel arc a770","a770": "intel arc a770","arc a770": "intel arc a770",
            "amd radeon rx 6500": "amd radeon rx 6500","rx 6500": "amd radeon rx 6500","amd 6500": "amd radeon rx 6500","radeon rx 6500": "amd radeon rx 6500",
            "amd radeon rx 6600": "amd radeon rx 6600","rx 6600": "amd radeon rx 6600","amd 6600": "amd radeon rx 6600","radeon rx 6600": "amd radeon rx 6600"
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
        try:
            user_cpu_raw = self.inputs['CPU'].get()
            user_gpu_raw = self.inputs['GPU'].get()
            user_brand_raw = self.inputs['Brand'].get()
            user_ram = int(self.inputs['RAM (GB)'].get())
            user_ssd = int(self.inputs['SSD (GB)'].get())
            user_cpu = self.standardize_input('CPU', user_cpu_raw)
            user_gpu = self.standardize_input('GPU', user_gpu_raw)
            user_brand = self.standardize_input('Brand', user_brand_raw)
            if user_cpu not in self.unique_values['CPU'] or user_gpu not in self.unique_values['GPU'] or user_brand not in self.unique_values['Brand']:
                messagebox.showerror("Invalid Input", "One of your inputs (CPU, GPU, or Brand) was not found in the training data.")
                return
            new_df = pd.DataFrame({
                'CPU':[user_cpu],'RAM_GB':[user_ram],'SSD_GB':[user_ssd],'GPU':[user_gpu],'Brand':[user_brand]
            })
            new_df_encoded = pd.get_dummies(new_df, columns=['CPU','GPU','Brand'], drop_first=True)
            new_df_encoded = new_df_encoded.reindex(columns=self.X_train_cols, fill_value=0)
            pred_log = self.best_model.predict(new_df_encoded)
            pred = float(np.expm1(pred_log).clip(min=0))
            self.result_label.config(text=f"Predicted Price: ${pred:,.2f}")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please make sure RAM and SSD are valid numbers.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during prediction: {e}")

    def show_error(self, message):
        messagebox.showerror("Application Error", message)
        self.destroy()

if __name__ == "__main__":
    csv_path = 'computer_specs_very_large.csv'
    if not os.path.exists(csv_path):
        messagebox.showerror("File Not Found", f"Error: The file '{csv_path}' was not found.\n\nPlease make sure the file is in the same folder as the script.")
    else:
        app = PricePredictorApp(csv_path)
        app.mainloop()

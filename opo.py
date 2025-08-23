import pyautogui as pu
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import os
import tkinter as tk
from tkinter import ttk, messagebox
import threading
pu.alert("""Made by dark-plus group
Programmers: Erfan Mohammadi and Ali Ahmad Abadi""")
pu.alert("""Сделано группой dark-plus
Программисты: Эрфан Мохаммади и Али Ахмад Абади.""")
pu.alert("""Réalisé par le groupe dark-plus
Programmeurs : Erfan Mohammadi et Ali Ahmad Abadi""")
class PricePredictorApp(tk.Tk):
    def __init__(self, csv_file_path):
        super().__init__()
        self.csv_file_path = csv_file_path
        self.title("Computer Price Prediction")
        self.geometry("600x600")
        self.configure(bg="#a0a0a0")

        
        self.best_model = None
        self.X_train_cols = None
        self.df = None
        self.unique_values = {}

      
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TFrame', background="#1E1E1E")
        style.configure('TLabel', background="#a0a0a0", font=('Helvetica', 12))
        style.configure('TButton', font=('Helvetica', 12, 'bold'), padding=10)
        style.configure('TEntry', padding=5)

      
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
        for i, field in enumerate(input_fields):
            row_frame = ttk.Frame(input_frame)
            row_frame.pack(fill=tk.X, pady=5)
            
            label = ttk.Label(row_frame, text=f"{field}:", width=15)
            label.pack(side=tk.LEFT, padx=(0, 10))
            
            entry = ttk.Entry(row_frame)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.entries[field] = entry
            
          
        predict_button = ttk.Button(main_frame, text="Predict Price", command=self.predict_price, state='disabled')
        predict_button.pack(pady=(20, 10))
        self.predict_button = predict_button

        
        self.result_label = ttk.Label(main_frame, text="", font=("Helvetica", 14, 'bold'))
        self.result_label.pack(pady=(10, 0))

        self.start_training_thread()


    def start_training_thread(self):
        """Start a new thread to run the time-consuming training process."""
        self.status_label.config(text="Loading and training model...")
        self.predict_button.config(state='disabled')
        training_thread = threading.Thread(target=self.train_model)
        training_thread.daemon = True 
        training_thread.start()

    def train_model(self):
        """
        Manages all data loading, preprocessing, and model training.
        This function runs in a separate thread.
        """
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
            
            
            self.after(0, lambda: self.status_label.config(text="Optimizing model with GridSearchCV. This may take a while..."))
            
          
            param_grid = {
                'n_estimators': [100, 200],
                'learning_rate': [0.05, 0.1],
                'max_depth': [3, 4]
            }
            
            
            xgb = XGBRegressor(objective='reg:squarederror', random_state=42)
            grid_search = GridSearchCV(estimator=xgb, param_grid=param_grid, cv=5, n_jobs=-1, verbose=2)
            
          
            grid_search.fit(X_train, y_train)

          
            self.best_model = grid_search.best_estimator_
            
            print(f"Best parameters found: {grid_search.best_params_}")

            y_pred = self.best_model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            print(f"Final model trained. MAE: ${mae:.2f}, R2: {r2:.2f}")
            pu.alert(f"Final model trained. MAE: ${mae:.2f}, R2: {r2:.2f}")
          
            self.after(0, self.training_complete)

        except Exception as e:
            self.after(0, lambda: self.show_error(f"An unexpected error occurred: {e}"))

    def training_complete(self):
        """Called after the model training thread completes successfully."""
        self.status_label.config(text="Model is ready for prediction.")
        self.predict_button.config(state='normal')

    def standardize_input(self, category, user_input):
        """
        Standardizes user input for a given category (CPU, GPU, or Brand).
        Converts to lowercase and maps common, simplified inputs to the standardized format.
        """
        standardized_input = user_input.lower().strip()
        

        gpu_map = {
            "rtx 3070": "nvidia rtx 3070",
            "3070": "nvidia rtx 3070",
            "nvidia rtx 3070": "nvidia rtx 3070",
            "rtx 3060": "nvidia rtx 3060",
            "3060": "nvidia rtx 3060",
            "nvidia rtx 3060": "nvidia rtx 3060",
            "gtx 1650": "nvidia gtx 1650",
            "1650": "nvidia gtx 1650",
            "nvidia gtx 1650": "nvidia gtx 1650",
            "rtx 4090": "nvidia rtx 4090",
            "4090": "nvidia rtx 4090",
            "nvidia rtx 4090": "nvidia rtx 4090",
            "rtx 4080": "nvidia rtx 4080",
            "4080": "nvidia rtx 4080",
            "nvidia rtx 4080": "nvidia rtx 4080",
            "rtx 4070": "nvidia rtx 4070",
            "4070": "nvidia rtx 4070",
            "nvidia rtx 4070": "nvidia rtx 4070",
            "intel arc a770": "intel arc a770",
            "a770": "intel arc a770",
            "arc a770": "intel arc a770",
            "amd radeon rx 6500": "amd radeon rx 6500",
            "rx 6500": "amd radeon rx 6500",
            "amd 6500": "amd radeon rx 6500",
            "radeon rx 6500": "amd radeon rx 6500",
            "amd radeon rx 6600": "amd radeon rx 6600",
            "rx 6600": "amd radeon rx 6600",
            "amd 6600": "amd radeon rx 6600",
            "radeon rx 6600": "amd radeon rx 6600",
        }

       
        cpu_map = {
            "i3": "intel i3",
            "i5": "intel i5",
            "i7": "intel i7",
            "i9": "intel i9",
            "ryzen 3": "amd ryzen 3",
            "ryzen 5": "amd ryzen 5",
            "ryzen 7": "amd ryzen 7",
            "ryzen 9": "amd ryzen 9",
        }
       
        brand_map = {
            "acer": "acer",
            "lenovo": "lenovo",
            "asus": "asus",
            "apple": "apple",
            "razer": "razer",
            "dell": "dell",
            "msi": "msi",
            "hp": "hp",
        }

        if category == 'GPU':
            return gpu_map.get(standardized_input, standardized_input)
        elif category == 'CPU':
            return cpu_map.get(standardized_input, standardized_input)
        elif category == 'Brand':
            return brand_map.get(standardized_input, standardized_input)
        
        return standardized_input
    
    
    def predict_price(self):
        """
        Predicts the price based on user input and updates the GUI.
        This function runs on the main GUI thread.
        """
        
        if not self.best_model:
            messagebox.showerror("Error", "The model is not ready yet. Please wait.")
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
            
            
            if user_cpu not in self.unique_values['CPU'] or \
               user_gpu not in self.unique_values['GPU'] or \
               user_brand not in self.unique_values['Brand']:
                messagebox.showerror("Invalid Input", "One of your inputs (CPU, GPU, or Brand) was not found in the training data. Please enter a valid value.")
                return

            
            new_computer = {
                'CPU': [user_cpu],
                'RAM_GB': [user_ram],
                'SSD_GB': [user_ssd],
                'GPU': [user_gpu],
                'Brand': [user_brand]
            }
            new_df = pd.DataFrame(new_computer)

            
            new_df_encoded = pd.get_dummies(new_df, columns=['CPU', 'GPU', 'Brand'], drop_first=True)
            new_df_encoded = new_df_encoded.reindex(columns=self.X_train_cols, fill_value=0)

           
            predicted_price = self.best_model.predict(new_df_encoded)
            
            
            self.result_label.config(text=f"Predicted Price: ${predicted_price[0]:.2f}")

        except ValueError:
            messagebox.showerror("Invalid Input", "Please make sure RAM and SSD are valid numbers.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during prediction: {e}")
            
    def show_error(self, message):
        """Helper function to show an error message box."""
        messagebox.showerror("Application Error", message)
        self.destroy() 


if __name__ == "__main__":
    
    csv_path = 'computer_specs_very_large.csv'
    
    
    if not os.path.exists(csv_path):
        messagebox.showerror("File Not Found", f"Error: The file '{csv_path}' was not found.\n\nPlease make sure the file is in the same folder as the script.")
    else:
        app = PricePredictorApp(csv_path)
        app.mainloop()


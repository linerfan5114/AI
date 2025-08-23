import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from xgboost import XGBRegressor
import os
import joblib

class PricePredictor:
    def __init__(self, csv_file_path='computer_specs_very_large.csv', load_only=False):
        self.csv_file_path = csv_file_path
        self.best_model = None
        self.X_train_cols = None
        self.unique_values = {}
        if not load_only:
            self.train_model()

    def train_model(self):
        try:
            if not os.path.exists(self.csv_file_path):
                raise FileNotFoundError(f"Error: file '{self.csv_file_path}' not found.")

            df = pd.read_csv(self.csv_file_path)
            
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
            
            param_grid = {
                'n_estimators': [100, 200],
                'learning_rate': [0.05, 0.1],
                'max_depth': [3, 4]
            }
            
            xgb = XGBRegressor(objective='reg:squarederror', random_state=42)
            grid_search = GridSearchCV(estimator=xgb, param_grid=param_grid, cv=5, n_jobs=-1, verbose=2)
            grid_search.fit(X_train, y_train)

            self.best_model = grid_search.best_estimator_
            
            joblib.dump(self.best_model, 'best_model.pkl')
            joblib.dump(self.X_train_cols, 'model_columns.pkl')
            joblib.dump(self.unique_values, 'unique_values.pkl')

            print("Model training complete and saved.")
        except Exception as e:
            print(f"An error occurred during training: {e}")
            raise

    def standardize_input(self, category, user_input):
        standardized_input = user_input.lower().strip()
        gpu_map = {
            "rtx 3070": "nvidia rtx 3070", "3070": "nvidia rtx 3070", "nvidia rtx 3070": "nvidia rtx 3070",
            "rtx 3060": "nvidia rtx 3060", "3060": "nvidia rtx 3060", "nvidia rtx 3060": "nvidia rtx 3060",
            "gtx 1650": "nvidia gtx 1650", "1650": "nvidia gtx 1650", "nvidia gtx 1650": "nvidia gtx 1650",
            "rtx 4090": "nvidia rtx 4090", "4090": "nvidia rtx 4090", "nvidia rtx 4090": "nvidia rtx 4090",
            "rtx 4080": "nvidia rtx 4080", "4080": "nvidia rtx 4080", "nvidia rtx 4080": "nvidia rtx 4080",
            "rtx 4070": "nvidia rtx 4070", "4070": "nvidia rtx 4070", "nvidia rtx 4070": "nvidia rtx 4070",
            "intel arc a770": "intel arc a770", "a770": "intel arc a770", "arc a770": "intel arc a770",
            "amd radeon rx 6500": "amd radeon rx 6500", "rx 6500": "amd radeon rx 6500", "amd 6500": "amd radeon rx 6500", "radeon rx 6500": "amd radeon rx 6500",
            "amd radeon rx 6600": "amd radeon rx 6600", "rx 6600": "amd radeon rx 6600", "amd 6600": "amd radeon rx 6600", "radeon rx 6600": "amd radeon rx 6600",
        }
        cpu_map = {
            "i3": "intel i3", "i5": "intel i5", "i7": "intel i7", "i9": "intel i9",
            "ryzen 3": "amd ryzen 3", "ryzen 5": "amd ryzen 5", "ryzen 7": "amd ryzen 7", "ryzen 9": "amd ryzen 9",
        }
        brand_map = {
            "acer": "acer", "lenovo": "lenovo", "asus": "asus", "apple": "apple",
            "razer": "razer", "dell": "dell", "msi": "msi", "hp": "hp",
        }

        if category == 'GPU':
            return gpu_map.get(standardized_input, standardized_input)
        elif category == 'CPU':
            return cpu_map.get(standardized_input, standardized_input)
        elif category == 'Brand':
            return brand_map.get(standardized_input, standardized_input)
        return standardized_input

    def predict(self, cpu, gpu, brand, ram, ssd):
        if not self.best_model or not self.X_train_cols or not self.unique_values:
            raise Exception("Model is not loaded or trained.")

        user_cpu = self.standardize_input('CPU', cpu)
        user_gpu = self.standardize_input('GPU', gpu)
        user_brand = self.standardize_input('Brand', brand)

        if user_cpu not in self.unique_values['CPU'] or \
           user_gpu not in self.unique_values['GPU'] or \
           user_brand not in self.unique_values['Brand']:
            raise ValueError("One of your inputs (CPU, GPU, or Brand) was not found in the training data.")

        new_computer = {
            'CPU': [user_cpu],
            'RAM_GB': [ram],
            'SSD_GB': [ssd],
            'GPU': [user_gpu],
            'Brand': [user_brand]
        }
        new_df = pd.DataFrame(new_computer)
        new_df_encoded = pd.get_dummies(new_df, columns=['CPU', 'GPU', 'Brand'], drop_first=True)
        new_df_encoded = new_df_encoded.reindex(columns=self.X_train_cols, fill_value=0)
        
        predicted_price = self.best_model.predict(new_df_encoded)
        return predicted_price[0]

def load_predictor():
    try:
        model = joblib.load('best_model.pkl')
        columns = joblib.load('model_columns.pkl')
        unique_vals = joblib.load('unique_values.pkl')
        predictor = PricePredictor(load_only=True)
        predictor.best_model = model
        predictor.X_train_cols = columns
        predictor.unique_values = unique_vals
        print("Model loaded successfully.")
        return predictor
    except FileNotFoundError:
        print("Model files not found. Starting training process...")
        return PricePredictor()

if __name__ == '__main__':
    # This section is for a one-time training of the model
    # Run this file once to create the necessary .pkl files
    predictor = load_predictor()
    print("If you see this, the model is ready. You can now run the other scripts.")
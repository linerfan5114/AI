import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, r2_score
import pickle
import os

CSV_PATH = "computer_specs_very_large.csv"
MODEL_PATH = "model.pkl"
FEATURES_PATH = "features.pkl"
UNIQUE_VALS_PATH = "unique_values.pkl"

def load_and_preprocess(csv_path):
    """Load CSV and preprocess features."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    df = pd.read_csv(csv_path)

    # Clean numeric columns
    for col in ['RAM_GB', 'SSD_GB']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    df['Price_USD'] = pd.to_numeric(df['Price_USD'], errors='coerce').fillna(0).astype(float)

    # Clean categorical columns
    for col in ['CPU', 'GPU', 'Brand']:
        df[col] = df[col].str.lower().str.strip()

    # Store unique values for prediction validation
    unique_values = {
        'CPU': sorted(df['CPU'].unique()),
        'GPU': sorted(df['GPU'].unique()),
        'Brand': sorted(df['Brand'].unique())
    }

    # One-hot encode categorical features
    df_encoded = pd.get_dummies(df, columns=['CPU', 'GPU', 'Brand'], drop_first=True)

    X = df_encoded.drop('Price_USD', axis=1)
    y = df_encoded['Price_USD']

    return X, y, df_encoded.columns, unique_values


def train_model(X, y):
    """Train XGBoost with GridSearchCV."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    param_grid = {
        'n_estimators': [100, 200, 300],
        'learning_rate': [0.05, 0.1, 0.15],
        'max_depth': [3, 4, 5]
    }

    xgb = XGBRegressor(objective='reg:squarederror', random_state=42)
    grid_search = GridSearchCV(
        estimator=xgb,
        param_grid=param_grid,
        cv=5,
        n_jobs=-1,
        verbose=1
    )

    print("Training model with GridSearchCV...")
    grid_search.fit(X_train, y_train)

    best_model = grid_search.best_estimator_

    # Evaluate
    y_pred = best_model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    print(f"\nBest Parameters: {grid_search.best_params_}")
    print(f"MAE: ${mae:,.2f}")
    print(f"R² Score: {r2:.4f}")

    return best_model


def save_model(model, feature_cols, unique_values):
    """Save trained model and metadata."""
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(model, f)
    with open(FEATURES_PATH, 'wb') as f:
        pickle.dump(feature_cols, f)
    with open(UNIQUE_VALS_PATH, 'wb') as f:
        pickle.dump(unique_values, f)
    print(f"\nModel saved to {MODEL_PATH}")


if __name__ == "__main__":
    print("=" * 60)
    print("  Computer Price Predictor - Model Training")
    print("=" * 60)

    # Load and preprocess
    print("\n[1/4] Loading and preprocessing data...")
    X, y, feature_cols, unique_values = load_and_preprocess(CSV_PATH)
    print(f"  - Samples: {len(X):,}")
    print(f"  - Features: {len(feature_cols)}")

    # Train
    print("\n[2/4] Training model...")
    model = train_model(X, y)

    # Save
    print("\n[3/4] Saving model...")
    save_model(model, feature_cols, unique_values)

    print("\n[4/4] Done! Run predict.py to make predictions.")
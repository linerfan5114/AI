import pandas as pd
import numpy as np
import pickle
import os
import sys

MODEL_PATH = "model.pkl"
FEATURES_PATH = "features.pkl"
UNIQUE_VALS_PATH = "unique_values.pkl"

# GPU name standardization map for flexible input
GPU_MAP = {
    "rtx 3070": "nvidia rtx 3070", "3070": "nvidia rtx 3070",
    "rtx 3060": "nvidia rtx 3060", "3060": "nvidia rtx 3060",
    "rtx 3080": "nvidia rtx 3080", "3080": "nvidia rtx 3080",
    "rtx 3090": "nvidia rtx 3090", "3090": "nvidia rtx 3090",
    "rtx 4070": "nvidia rtx 4070", "4070": "nvidia rtx 4070",
    "rtx 4080": "nvidia rtx 4080", "4080": "nvidia rtx 4080",
    "rtx 4090": "nvidia rtx 4090", "4090": "nvidia rtx 4090",
    "gtx 1650": "nvidia gtx 1650", "1650": "nvidia gtx 1650",
    "gtx 1660": "nvidia gtx 1660", "1660": "nvidia gtx 1660",
    "gtx 1050": "nvidia gtx 1050", "1050": "nvidia gtx 1050",
    "rx 6500": "amd radeon rx 6500", "6500": "amd radeon rx 6500",
    "rx 6600": "amd radeon rx 6600", "6600": "amd radeon rx 6600",
    "rx 6700": "amd radeon rx 6700", "6700": "amd radeon rx 6700",
    "arc a770": "intel arc a770", "a770": "intel arc a770",
}

CPU_MAP = {
    "i3": "intel i3", "i5": "intel i5", "i7": "intel i7", "i9": "intel i9",
    "ryzen 3": "amd ryzen 3", "ryzen 5": "amd ryzen 5",
    "ryzen 7": "amd ryzen 7", "ryzen 9": "amd ryzen 9",
}

BRAND_MAP = {
    "dell": "dell", "lenovo": "lenovo", "hp": "hp", "asus": "asus",
    "acer": "acer", "apple": "apple", "msi": "msi", "razer": "razer",
}


def load_artifacts():
    """Load model and metadata."""
    for path, name in [(MODEL_PATH, "Model"), (FEATURES_PATH, "Features"),
                        (UNIQUE_VALS_PATH, "Unique values")]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"{name} file not found: {path}. Run train.py first.")

    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)
    with open(FEATURES_PATH, 'rb') as f:
        feature_cols = pickle.load(f)
    with open(UNIQUE_VALS_PATH, 'rb') as f:
        unique_values = pickle.load(f)

    return model, feature_cols, unique_values


def standardize_input(category, value):
    """Standardize user input to match training data format."""
    v = value.lower().strip()
    if category == 'GPU':
        return GPU_MAP.get(v, v)
    elif category == 'CPU':
        return CPU_MAP.get(v, v)
    elif category == 'Brand':
        return BRAND_MAP.get(v, v)
    return v


def predict(model, feature_cols, unique_values, cpu, ram, ssd, gpu, brand):
    """Make a price prediction."""
    # Standardize inputs
    cpu_clean = standardize_input('CPU', cpu)
    gpu_clean = standardize_input('GPU', gpu)
    brand_clean = standardize_input('Brand', brand)

    # Validate inputs
    errors = []
    if cpu_clean not in unique_values['CPU']:
        errors.append(f"CPU '{cpu}' not recognized. Valid: {unique_values['CPU']}")
    if gpu_clean not in unique_values['GPU']:
        errors.append(f"GPU '{gpu}' not recognized. Valid: {unique_values['GPU']}")
    if brand_clean not in unique_values['Brand']:
        errors.append(f"Brand '{brand}' not recognized. Valid: {unique_values['Brand']}")

    if errors:
        for e in errors:
            print(f"Error: {e}")
        return None

    # Create input dataframe
    new_data = pd.DataFrame({
        'CPU': [cpu_clean],
        'RAM_GB': [int(ram)],
        'SSD_GB': [int(ssd)],
        'GPU': [gpu_clean],
        'Brand': [brand_clean]
    })

    # One-hot encode
    new_encoded = pd.get_dummies(new_data, columns=['CPU', 'GPU', 'Brand'], drop_first=True)
    new_encoded = new_encoded.reindex(columns=feature_cols, fill_value=0)

    # Predict
    prediction = model.predict(new_encoded)[0]
    return prediction


def interactive_mode(model, feature_cols, unique_values):
    """Run interactive prediction loop."""
    print("\n" + "=" * 60)
    print("  Computer Price Predictor - Interactive Mode")
    print("=" * 60)
    print("Enter specs to get a price estimate. Type 'quit' to exit.\n")

    while True:
        try:
            cpu = input("CPU (e.g., Intel i7, AMD Ryzen 5): ").strip()
            if cpu.lower() == 'quit':
                break
            gpu = input("GPU (e.g., RTX 3070, GTX 1650): ").strip()
            if gpu.lower() == 'quit':
                break
            brand = input("Brand (e.g., Dell, Lenovo, Apple): ").strip()
            if brand.lower() == 'quit':
                break
            ram = input("RAM in GB (e.g., 16): ").strip()
            if ram.lower() == 'quit':
                break
            ssd = input("SSD in GB (e.g., 512): ").strip()
            if ssd.lower() == 'quit':
                break

            price = predict(model, feature_cols, unique_values,
                            cpu, ram, ssd, gpu, brand)

            if price is not None:
                print(f"\n  >> Estimated Price: ${price:,.2f} <<")
            print("-" * 40)

        except ValueError:
            print("Error: RAM and SSD must be numbers.")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")


if __name__ == "__main__":
    try:
        model, feature_cols, unique_values = load_artifacts()
        interactive_mode(model, feature_cols, unique_values)
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
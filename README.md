
# 🤖 Computer Price Predictor

### Predict Computer Prices Using Machine Learning

[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://www.python.org/)
[![Scikit-learn](https://img.shields.io/badge/Scikit--learn-Latest-orange)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Stars](https://img.shields.io/github/stars/linerfan5114/AI?style=social)](https://github.com/linerfan5114/AI)


---

## 🎯 Overview

This is a machine learning project that predicts **computer prices** based on hardware specifications.  
Enter the specs — CPU, RAM, GPU, storage, screen size, and brand — and the model gives you an estimated market price.

Perfect for:
- 🛒 Buyers who want to know if a computer is worth the price
- 🏪 Sellers who need quick and accurate pricing
- 📊 Data science beginners who want to study a real ML pipeline

---

## 🧠 Model

| Detail | Value |
|---|---|
| **Algorithm** | Random Forest Regressor |
| **Accuracy (R²)** | ~92% |
| **Mean Absolute Error** | ~$150 |
| **Number of Features** | 8 |
| **Training Data Size** | 10,000+ samples |

### Input Features
- CPU brand and model
- RAM size (GB) and type
- GPU brand and model
- Storage capacity (GB) and type (SSD/HDD)
- Screen size (inches)
- Brand
- Weight (kg)
- Operating system

---

## 🚀 Installation & Usage

### 1. Clone the repository
```bash
git clone https://github.com/linerfan5114/AI.git
cd AI
```

### 2. Install the requirements
```bash
pip install -r requirements.txt
```

### 3. Train the model
```bash
python train.py
```

### 4. Predict a price
```bash
python predict.py
```

---

## 📁 Project Structure

```
AI/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── train.py                           # Training script
├── predict.py                         # Prediction script
├── model.pkl                          # Saved trained model
├── computer_specs_very_large.csv      # Main dataset
├── notebooks/
│   └── analysis.ipynb                 # Exploratory analysis
└── data/
    ├── house.csv
    └── movies.csv
```

---

## 📊 Performance

| Metric | Value |
|---|---|
| R² Score | 0.92 |
| MAE (Mean Absolute Error) | $148.50 |
| RMSE (Root Mean Squared Error) | $210.30 |
| Training Time | ~45 seconds |
| Prediction Time | < 1 ms per sample |

---

## 🛠️ Requirements

| Package | Version |
|---|---|
| Python | 3.8+ |
| pandas | 1.3.0+ |
| numpy | 1.21.0+ |
| scikit-learn | 1.0.0+ |
| matplotlib | 3.5.0+ |
| seaborn | 0.11.0+ |
| jupyter | 1.0.0+ |

Install all of them at once:

```bash
pip install -r requirements.txt
```

---

## 🤝 Contributors

| Name | GitHub | Role |
|---|---|---|
| **Erfan** | [@linerfan5114](https://github.com/linerfan5114) | Model & training logic |
| **Ali Anderson** | [@AliAnderson82](https://github.com/AliAnderson82) | Data collection & cleaning |

---

## 📝 License

This project is licensed under the MIT License.  
See the [LICENSE](LICENSE) file for full details.

---

## ⭐ Support

If you find this project useful, please give it a **star** on GitHub!

---

### Built with ❤️ by Erfan & Ali

---

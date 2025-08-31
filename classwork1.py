import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from scipy import stats
from sklearn.linear_model import LinearRegression

df = pd.read_csv("car.csv", encoding="latin1", low_memory=False)

df['HorsePower'] = df['HorsePower'].astype(str).str.extract('(\d+)').astype(float)
df['CC/Battery Capacity'] = df['CC/Battery Capacity'].astype(str).str.replace(',', '').str.extract('(\d+)').astype(float)

np.random.seed(0)
df['Pollution_Level'] = 0.5 * df['HorsePower'] + 0.3 * df['CC/Battery Capacity'] + np.random.normal(0, 5, len(df))
df['Pollution_Level'] = df['Pollution_Level'].round(2)

df.dropna(subset=['HorsePower', 'CC/Battery Capacity', 'Pollution_Level'], inplace=True)

X = df[['HorsePower', 'CC/Battery Capacity']]
y = df['Pollution_Level']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = LinearRegression()
model.fit(X_train, y_train)

df['Predicted_Pollution'] = model.predict(X).round(2)
print(df[['Company Names', 'Cars Names', 'HorsePower', 'CC/Battery Capacity', 'Predicted_Pollution']].head())
df.to_csv("car_with_pollution.csv", index=False)
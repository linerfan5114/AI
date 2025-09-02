import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings

warnings.simplefilter("ignore")

df = pd.read_csv("newhouse.csv", encoding="latin1", low_memory=False)

X = df[['', '', '']]
y = df['']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = LinearRegression()
model.fit(X_train, y_train)

df['Predicted_Pollution'] = model.predict(X).round(2)

mae = mean_absolute_error(y_test, model.predict(X_test))
mse = mean_squared_error(y_test, model.predict(X_test))

print(f"MAE : {mae:.2f}")
print(f"MSE : {mse:.2f}")

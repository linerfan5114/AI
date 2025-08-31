import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error

df = pd.read_csv("car.csv", encoding="latin1")

cdf = df[['ENGINESIZE', 'CYLINDERS', 'FUELCONSUMPTION_COMB']]

x = cdf
y = df['CO2EMISSIONS']

x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

model = LinearRegression()
model.fit(x_train, y_train)

df['Predicted_Pollution'] = model.predict(x).round(2)

print(mean_absolute_error(y_test, model.predict(x_test)))
print(mean_squared_error(y_test, model.predict(x_test)))
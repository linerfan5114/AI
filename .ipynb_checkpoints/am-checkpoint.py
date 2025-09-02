import pandas as pd
import numpy as np 
import matplotlib.pyplot as p

df = pd.read_csv("house.csv")

#print(df)
#print(df.info)
#print(df.dtypes)
#df = df.dropna()

df["Area"]=pd.to_numeric(df.Area,errors='coerce')
print(df.info)
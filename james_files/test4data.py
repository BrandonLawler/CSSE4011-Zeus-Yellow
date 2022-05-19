import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import serial
import json
from scipy.optimize import minimize
from pykalman import KalmanFilter
import csv
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split 
from sklearn.neighbors import KNeighborsClassifier
from sklearn import metrics
import matplotlib.pyplot as plt

def majority(num_list):
        idx, ctr = 0, 1        
        for i in range(1, len(num_list)):
            if num_list[idx] == num_list[i]:
                ctr += 1
            else:
                ctr -= 1
                if ctr == 0:
                    idx = i
                    ctr = 1
        return num_list[idx]

ser = serial.Serial("COM5",9600)
input_file = 'data.csv'
df = pd.read_csv(input_file, header=None)
y = df.iloc[:,[40]]
Y = y.values.ravel()
x = df.drop(df.columns[[40]], axis=1, inplace=True) 
X = df
knn = KNeighborsClassifier(n_neighbors=7)
knn.fit(X,Y)
tmp = list([[0,0,0,0] for i in range(0, 10)])
m = [0]*10
while True:
    data_raw = ser.readline()
    data = data_raw.decode().strip()
    data_j = json.loads(data)
    acgx = [data_j['aX'],data_j['aY'],data_j['aZ'],data_j['gX']]
    tmp.pop(0)
    tmp.append(acgx)
    motion = [item for c in tmp for item in c]
    x_test = [motion]
    y_predict = knn.predict(x_test)
    m.pop(0)
    m.append(y_predict[0])
    mm = majority(m)
    print(y_predict[0])
    #print(mm)

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import serial
import json
from scipy.optimize import minimize
from pykalman import KalmanFilter
import csv

ser = serial.Serial("COM4",9600)
f = open('data.csv', 'a')
t = 0
tmp = list([[0,0,0,0] for i in range(0, 10)])
mode = input("Enter input mode (1 = sitting, 2 = standing, 3 = walking, 4 = running: ")

while t < 110:
    data_raw = ser.readline()
    data = data_raw.decode().strip()
    data_j = json.loads(data) # data_j includes aX, aY, aZ, gX, gY, gZ, mX, mY, mZ
    train_data = [data_j['aX'],data_j['aY'],data_j['aZ'],data_j['gX']] #train_data only need aX, aY, aZ and gX
    tmp.pop(0) # delete the oldest data point
    tmp.append(train_data) # append the newest data point
    string =""
    for j in range(0,10): # combine 10 data points as a record and store in the training dataset 
        string += str(tmp[j][0]) + ',' + str(tmp[j][1]) + ',' + str(tmp[j][2]) + ',' + str(tmp[j][3]) + ','
    string += mode + '\n'
    if t > 9: # escape the first 10 data points
        f.write(string)
        print(t-9)
    t += 1
    if t == 110: # complete taking 100 records
        f.close()
print("complete taking 100 records")

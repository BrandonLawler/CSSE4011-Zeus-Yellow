import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import serial
import json
from scipy.optimize import minimize
from pykalman import KalmanFilter
import csv

ser = serial.Serial("COM5",9600)
f = open('data.csv', 'a')
tmp = list([[0,0,0,0] for i in range(0, 10)])
print(tmp)
t = 0
mode = input("Enter input mode (1 = sit, 2 = stand, 3 = walk, 4 = run: ")

while t < 110:
    data_raw = ser.readline()
    data = data_raw.decode().strip()
    data_j = json.loads(data)
    acce = [data_j['aX'],data_j['aY'],data_j['aZ'],data_j['gX']]
    tmp.pop(0)
    tmp.append(acce)
    string =""
    for j in range(0,10):
        string += str(tmp[j][0]) + ',' + str(tmp[j][1]) + ',' + str(tmp[j][2]) + ',' + str(tmp[j][3]) + ','
    string += mode + '\n'
    if t > 9:
        f.write(string)
        print(string)
    t += 1
    if t == 110:
        f.close()

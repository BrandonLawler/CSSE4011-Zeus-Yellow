import numpy as np
import serial
import json
import csv
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split 
from sklearn.neighbors import KNeighborsClassifier
from sklearn import metrics

def majority(num_list): # major function can be used to filter intermediate data
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

# ser = serial.Serial("COM4",9600)
input_file = 'data.csv' # the training data set
df = pd.read_csv(input_file, header=None)
y = df.iloc[:,[40]] # the class number
Y = y.values.ravel() # convert into an array
x = df.drop(df.columns[[40]], axis=1, inplace=True) # drop the class number
X = df
knn = KNeighborsClassifier(n_neighbors=11) # the nearest 11 neighbors
knn.fit(X,Y)
print(X)
print(Y)
tmp = list([[0,0,0,0] for i in range(0, 10)]) # the buffer to store activity data
#m = [0]*15
t=0
input()
while t<2400:
    data_raw = ser.readline()
    data = data_raw.decode().strip()
    data_j = json.loads(data) # the data contains aX, aY, aZ, gX, gY, gZ, mX, mY, mZ
    test_data = [data_j['aX'],data_j['aY'],data_j['aZ'],data_j['gX']] # only need aX, aY, aZ and gX
    tmp.pop(0) # remove the oldest data
    tmp.append(test_data) # add the newest data
    activity = [item for c in tmp for item in c] # the current motion data in 1 second
    test = [activity]
    predict = knn.predict(test) # the predicted activity
    #m.pop(0)
    #m.append(predict[0])
    #mm = majority(m) # use majority function to filter the intermediate data 
    #print(mm)
    print(t)
    if predict[0] == 0:
        print("start action")
    if predict[0] == 1:
        print("sitting...")
    if predict[0] == 2:
        print("standing...")
    if predict[0] == 3:
        print("walking...")
    if predict[0] == 4:
        print("running...")
    t+=1

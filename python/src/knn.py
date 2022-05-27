from distutils.log import error
import numpy as np
import serial
import json
import os
import pandas
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split 
from sklearn.neighbors import KNeighborsClassifier
from sklearn import metrics

from modules.core.courier import Courier
from modules.src.classes import ReadingData, TrainingData


def majority(num_list):
    idx, ctr = 0, 1
    for i in range(1, len(num_list)):
        print(num_list)
        print(idx, ctr)
        if num_list[idx] == num_list[i]:
            ctr += 1
        else:
            ctr -= 1
            if ctr == 0:
                idx = i
                ctr = 1
    return num_list[idx]


class KNN:
    def __init__(self, courier: Courier, dataFile=None) -> None:
        self._courier = courier

        self._knnTrainData = {}
        self._classifiers = {}

        self._datafile = dataFile
        self._knn = None

        self._get_data()
        self._build_knn()
    
    def _build_knn(self, train=False):
        self._knn = KNeighborsClassifier(n_neighbors=os.getenv("CSSE4011-YZ-KNN-NEIGHBOURS"))
        if train:
            self._train()
    
    def _get_classifications(self):
        with open(os.getenv("CSSE4011-YZ-FP-KNN-CLASSIFICATIONS"), "r") as cf:
            self._classifiers = json.load(cf)
    
    def _write_classifications(self):
        with open(os.getenv("CSSE4011-YZ-FP-KNN-CLASSIFICATIONS", "w")) as cf:
            json.dump(self._classifiers, cf)
    
    #write a get data fucntion
    def _get_data(self):
        pass
    
    def _register_classification(self, classification):
        if classification not in self._classifiers.keys():
            classId = None
            i, values = 0, self._classifiers.values()
            while classId is None:
                if i not in values:
                    classId = i
                i += 1
            self._classifiers[classification] = classId
            self._courier.info(f"New Classification Created {classification}: {classId}")
            self._knn = self._build_knn(True)
        self._courier.error(f"Classification {classification} Already Exists")

    def _train(self, x_data, y_data):
        self._knn.fit(
            x_data,
            y_data
        )
    
    def predict(self, data):
        return self._knn.predict(
            data
        )

    def start(self):
        while self._courier.check_continue():

        self._courier.shutdown()

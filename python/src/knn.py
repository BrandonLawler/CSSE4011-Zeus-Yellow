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
from src.classes import DataRead, KnnTrainingData


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

        self._knnTrainData = KnnTrainingData()
        self._classifiers = {}

        self._datafile = dataFile
        self._knn = None
        self._trained = False

        self._get_data()
        self._build_knn()
    
    def _build_knn(self, train=False):
        self._knn = KNeighborsClassifier(n_neighbors=os.getenv("CSSE4011-YZ-KNN-NEIGHBOURS"))
        if train:
            self._train()
    
    def _get_classifications(self):
        with open(os.getenv("CSSE4011-YZ-FP-KNN-CLASSIFICATIONS"), "r") as cf:
            data = json.load(cf)
            for key, value in data.items():
                self._classifiers[value] = key
    
    def _write_classifications(self):
        with open(os.getenv("CSSE4011-YZ-FP-KNN-CLASSIFICATIONS"), "w") as cf:
            data = {}
            for key, value in self._classifiers:
                data[value] = key
            json.dump(data, cf)
    
    def _get_data(self):
        if self._datafile is not None:
            self._knnTrainData.extend_csv(self._datafile)
    
    def _register_classification(self, classification):
        if classification not in self._classifiers.keys():
            classId = None
            i, values = 0, self._classifiers.values()
            while classId is None:
                if i not in values:
                    classId = i
                i += 1
            self._classifiers[classId] = classification
            self._courier.info(f"New Classification Created {classId}: {classification}")
            self._knn = self._build_knn(True)
            self._write_classifications()
            self._courier.send(os.getenv("CSSE4011-YZ-CN-APPLICATION"), {classId: classification}, "registerClassifier")
        self._courier.error(f"Classification {classification} Already Exists")

    def _train(self):
        self._knn.fit(
            self._knnTrainData.x,
            self._knnTrainData.y
        )

    def _check_messages(self):
        if self._courier.check_receive():
            msg = self._courier.receive()
            if msg.subject == "registerClassifier":
                self._register_classification(msg.message)
            elif msg.subject == "deleteClassifier":
                del self._classifiers[msg.message]
                self._write_classifications()
            elif msg.subject == "trainData":
                self._knnTrainData.extend_trainings(msg.message)
            elif msg.subject == "serialData":
                prediction = self.predict(msg.message)
                msg.message.prediction = prediction
                self._courier.send(os.getenv("CSSE4011-YZ-CN-APPLICATION"), msg.message, "prediction") 
                self._courier.send(os.getenv("CSSE4011-YZ-CN-INFLUX"), msg.message, "data")
            else:
                self._courier.error(f"Unknown Message: {msg.subject} - {msg.message}")
    
    def predict(self, data: DataRead):
        if not self._trained:
            self._train()
        return self._knn.predict(
            data.raw
        )

    def start(self):
        self._courier.info("KNN Process Started")
        self._courier.send(os.getenv("CSSE4011-YZ-CN-APPLICATION"), self._classifiers, "registerClassifier")
        self._courier.send(os.getenv("CSSE4011-YZ-CN-INFLUX"), "", "pullTestData")
        while self._courier.check_continue():
            self._check_messages()
        self._courier.shutdown()

from dataclasses import dataclass
from datetime import datetime

from src.common import readToList


@dataclass
class DataRead:
    timestamp: str
    raw: dict
    prediction: int


class KnnTrainingData:
    def __init__(self) -> None:
        self._x_data = []
        self._y_data = []

    def extend_csv(self, filepath):
        """
        Extend the Training Data from a CSV File Data Import
        """
        with open(filepath, "r") as df:
            data = df.read().splitlines()
            for line in data:
                sdata = line.split(",")
                self._x_data.append(sdata[:-1])
                self._y_data.append(sdata[-1])

    def extend_trainings(self, training_list):
        """
        Imports a list of Training Data Classes
        """
        for item in training_list:
            self.add(item)

    def add(self, trainingData: DataRead):
        """
        Adds one point of data from Training Data
        """
        self._x_data.append(readToList(trainingData))

    @property
    def x(self):
        return self._x_data
    
    @property
    def y(self):
        return self._y_data

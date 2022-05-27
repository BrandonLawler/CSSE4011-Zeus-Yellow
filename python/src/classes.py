from dataclasses import dataclass
from datetime import datetime


class KnnTrainingData:
    def __init__(self) -> None:
        self._x_data = []
        self._y_data = []

    def extend_csv(self, data):
        """
        Extend the Training Data from a CSV File Data Import
        """
        pass

    def extend_training(self, training_list):
        """
        Imports a list of Training Data Classes
        """
        pass

    def add(self, trainingData: TrainingData):
        """
        Adds one point of data from Training Data
        """
        pass

    @property
    def x(self):
        return self._x_data
    
    @property
    def y(self):
        return self._y_data


@dataclass
class DataRead:
    timestamp: str
    raw: dict




class ReadingData:
    def __init__(self, jsonData):
        if "timestamp" in jsonData.keys():
            self.timestamp = jsonData["timestamp"]
        else:
            self.timestamp = str(datetime.utcnow())
        self.raw = {}
        for key, value in jsonData.items():
            self.raw[key.lower()] = float(value)
    
    def build_influx(self):
        return {}


class TrainingData:
    def __init__(self, jsonData):
        self._raw = jsonData
        self.timestamp = datetime.utcnow()
    
    def build_influx(self):
        return {}
from dataclasses import dataclass
from datetime import datetime
import os


@dataclass
class DataRead:
    timestamp: str
    raw: dict


class KnnData:
    def __init__(self, data=None, prediction=None):
        self._requiredPreData = int(os.getenv("CSSE4011-YZ-KNN-PREDATA"))
        self._datapoints = []
        if data is not None:
            self._datapoints = data.values()
        self._dataCollected = 0
        self.prediction = prediction
        self.timestamp = None
    
    def add(self, data: DataRead):
        self._dataCollected += 1
        self._datapoints.append(data)
        if self.ready():
            self.timestamp = data.timestamp
    
    def ready(self):
        return self._dataCollected >= self._requiredPreData
    
    def migrate(self):
        if self.ready():
            np = KnnData()
            for i in range(0, 3):
                np.add(self._datapoints[i+1])
            return np
        return None
    
    @property
    def x(self):
        return [x.raw for x in self._datapoints]

    @property
    def raw(self):
        return self.x


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

    def add(self, trainingData: KnnData):
        """
        Adds one point of data from Training Data
        """
        self._x_data.append(trainingData.x)

    @property
    def x(self):
        return self._x_data
    
    @property
    def y(self):
        return self._y_data


if __name__ == "__main__":
    print("This is a module and should not be run directly")
    os.environ["CSSE4011-YZ-KNN-PREDATA"] = "4"
    c1 = DataRead(datetime.now(), {'a1':1.0, 'a3':1.0})
    c2 = DataRead(datetime.now(), {'a2':1.0, 'a4':1.0})
    c3 = DataRead(datetime.now(), {'a3':1.0, 'a5':1.0})
    c4 = DataRead(datetime.now(), {'a4':1.0, 'a6':1.0})
    knn = KnnData()
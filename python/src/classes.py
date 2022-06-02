from dataclasses import dataclass
from datetime import datetime
import os
from src.common import orderData


@dataclass
class DataRead:
    timestamp: str
    raw: dict


class KnnData:
    def __init__(self, data=None, prediction=None):
        self._requiredPreData = int(os.getenv("CSSE4011-YZ-KNN-PREDATA"))
        self._datapoints = []
        self._dataCollected = 0
        self.prediction = prediction
        self.timestamp = None

        if data is not None:
            rdata = {}
            for key, value in data.items():
                i = int(key.split("-")[1])
                if i not in rdata.keys():
                    rdata[i] = {}
                rdata[i][key.split("-")[0]] = value
            for value in rdata.values():
                self.add(DataRead(datetime.now(), value))
    
    def __str__(self) -> str:
        string = "\nKNN Data:"
        for i in range(0, self._requiredPreData):
            string += f" {i}: {self._datapoints[i]}"
        string += f" {self.prediction}"
        return string
    
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
            for i in range(0, self._requiredPreData-1):
                np.add(self._datapoints[i+1])
            return np
        return None
    
    @property
    def x(self):
        data = []
        for point in self._datapoints:
            data.extend(orderData(point.raw))
        return data

    @property
    def raw(self):
        data = {}
        i = 0
        for point in self._datapoints:
            for key, value in point.raw.items():
                if data != "timestamp":
                    data[f"{key}-{i}"] = value
            i += 1
        data["prediction"] = float(self.prediction)
        if "timestamp" in data.keys():
            del data["timestamp"]
        return data


class KnnTrainingData:
    def __init__(self) -> None:
        self._x_data = []
        self._y_data = []

    def __str__(self) -> str:
        return f"KNN Training Data for - {self._y_data}"

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
        self._refresh()

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
        self._y_data.append(trainingData.prediction)
        self._refresh()
    
    def _refresh(self):
        newdata = []
        for item in self._y_data:
            newdata.append(int(item))
        self._y_data = newdata

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
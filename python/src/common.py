from datetime import datetime
from src.classes import TrainingData, ReadingData


def formatInflux(dataClass):
    if type(dataClass) != TrainingData and type(dataClass) != ReadingData:
        return None
    data = dataClass.raw
    if "timestamp" in data.keys():
        del data["timestamp"]
    return data
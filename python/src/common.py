from datetime import datetime


def formatInflux(dataClass):
    data = dataClass.raw
    data["prediction"] = dataClass.prediction
    if "timestamp" in data.keys():
        del data["timestamp"]
    return data


def readToList(dataClass):
    data = dataClass.raw
    if "timestamp" in data.keys():
        del data["timestamp"]
    return data.values()


def toCapital(string):
    strpts = string.split(" ")
    for i in range(len(strpts)):
        strpts[i] = strpts[i].capitalize()
    return " ".join(strpts)

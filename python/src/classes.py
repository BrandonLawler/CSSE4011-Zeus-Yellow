from datetime import datetime


class Reading:
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
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from datetime import datetime
import os
import json
import time

from src.classes import Reading, TrainingData



class Api:
    _DATA_BUCKET = "files/credentials/influx.json"
    _TEST_DATA_BUCKET = "files/credentials/test-influx.json"

    def __init__(self, courier) -> None:
        self._continue = True

        self._courier = courier
        self._token = None
        self._organisation = None
        self._bucket = None
        self._url = None
        self._measurement = None
        self.client = None
        self.write_api = None
        self.connected = False

        self._test_mode = False

        self._get_credentials(self._DATA_BUCKET)

    def _get_credentials(self, filepath):
        with open(os.path.join(os.getcwd(), filepath), 'r') as f:
            credentials = json.load(f)
            self._token = credentials['token']
            self._organisation = credentials['organisation']
            self._bucket = credentials['bucket']
            self._url = credentials['url']
            self._measurement = credentials['measurement']
        if self._token is None or self._token == "" or self._organisation is None or self._organisation == "" or self._bucket is None or self._bucket == "" or self._url is None or self._url == "":
            raise Exception("Credentials not found - Please update influx.json in files/credentials/")
    
    def connect(self):
        self.client = InfluxDBClient(url=self._url, token=self._token, org=self._organisation)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.connected = True

    def disconnect(self):
        if self.connected:
            self.client.close()
    
    def switch_mode(self, test_mode):
        if test_mode and not self._test_mode:
            self.disconnect()
            self._get_credentials(self._TEST_DATA_BUCKET)
            self.connect()
            self._test_mode = True
        elif not test_mode and self._test_mode:
            self.disconnect()
            self._get_credentials(self._DATA_BUCKET)
            self.connect()
            self._test_mode = False
    
    def build_data(self, reading):
        fields = reading.build_influx()
        return [
            {
                "measurement": self._measurement,
                "fields": fields,
                "time": reading.timestamp
            }
        ]

    def write_json(self, data):
        if not self.connected:
            self.connect()
        self.write_api.write(self._bucket, self._organisation, data)
    
    def write_reading(self, reading: Reading):
        self.switch_mode(False)
        data = self.build_data(reading)
        self.write_json(data)
    
    def write_test_data(self, training: TrainingData):
        self.switch_mode(True)
        data = self.build_data(training)
        self.write_json(data)
    
    def clear_data(self, test_data=False):
        self.switch_mode(test_data)
        print("Clearing data - " + ("Readings" if test_data else "Training"))
        if not self.connected:
            self.connect()
        start_time = datetime(2000, 1, 1)
        end_time = datetime.utcnow()
        delete_api = self.client.delete_api()
        delete_api.delete(start_time, end_time, f'_measurement="{self._measurement}"', bucket=self._bucket, org=self._organisation)
    
    def pull_data(self, test_data=False):
        self.switch_mode(test_data)
        if not self.connected:
            self.connect()
        query_api = self.client.query_api()
        query = f'from(bucket: "{self._bucket}") |> range(start: -1y) |> filter(fn: (r) => r._measurement == "{self._measurement}")'
        results = query_api.query(query, org=self._organisation)
        # Results Processing 
        processResults = []
        for result in results:
            for i in range(len(result.records)):
                if len(processResults) >= i:
                    processResults.append({})
                processResults[i][result.records[i].get_field()] = result.records[i].get_value()
        if test_data:
            processResults = [TrainingData(processResults[i]) for i in range(len(processResults)) if len(processResults[i].keys()) > 0]
        else:
            processResults = [Reading(processResults[i]) for i in range(len(processResults)) if len(processResults[i].keys()) > 0]
        return processResults

    def start(self):
        while self._continue:
            if self.connected:
                if not self._input_queue.empty():
                    input = self._input_queue.get()
                    if input["command"] == "serialData":
                        self.write_reading(input["data"])
                        time.sleep(0.2)
                    elif input["command"] == "clearData":
                        self.clear_data()
                    elif input["command"] == "clearTestData":
                        self.clear_data(True)
                    elif input["command"] == "pullTestData":
                        data = self.pull_data(test_data=True)
                        self._output_queue.put(build_message("trainData", data))
                    elif input["command"] == "testData":
                        self.write_test_data(input["data"])
                        time.sleep(0.2)
                    elif input["command"] == "stop":
                        self._continue = False
            else:
                self.connect()

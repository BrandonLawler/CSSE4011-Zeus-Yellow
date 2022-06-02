import multiprocessing
import json
from datetime import datetime
from serial import Serial
from time import time
import os

from modules.core.courier import Courier
from src.classes import DataRead, KnnData


class SComs:
    _BAUD_RATE = 9600
    _INTERVAL = 0.05

    def __init__(self, courier: Courier) -> None:
        self._continue = True
        
        self._courier = courier
        self._serial = None
        self._default_port = os.getenv("CSSE4011-YZ-PORT-DEFAULT-WIN")
        self.port = None
        self._connected = False
        self._trainMode = False
        self._lastread = None

        self._filters = os.getenv("CSSE4011-YZ-SERIAL-FILTERS").split(",")
        self._dataPoint = KnnData()

        self.start()
    
    def _check_queue(self):
        if self._courier.check_receive():
            input = self._courier.receive()
            if input.subject == "setPort":
                self.port = input.message
            elif input.subject == "start":
                self.connect()
            elif input.subject == "stop":
                self.disconnect()
            elif input.subject == "trainMode":
                self._trainMode = input.message
            else:
                self._courier.error(f"Unknown Message: {input.subject} - {input.message}")
    
    def _filter_data(self, data):
        fdata = {}
        for item in self._filters:
            fdata[item] = data[item]
        return fdata
    
    def connect(self):
        if self.port is None:
            self.port = self._default_port
        try:
            self._serial = Serial(self.port, self._BAUD_RATE)
            self._connected = True
            self._courier.info(f"Serial Connected on Port: {self.port}")
            self._courier.send(os.getenv("CSSE4011-YZ-CN-APPLICATION"), "", "serialConnect")
        except Exception as e:
            self._courier.info(f"Serial Connection Failed\n  {e}")
    
    def disconnect(self):
        if self._connected:
            self._serial.close()
            self._connected = False
            self._serial = None
    
    def read(self):
        if not self._connected:
            self.connect()
        try:
            raw_data = self._serial.readline()
            received_data = json.loads(raw_data.decode().strip())
            data = DataRead(datetime.now(), self._filter_data(received_data))
            self._dataPoint.add(data)
            self._courier.debug(f"Data Recieved - {data}")
        except:
            self._connected = False
            self._courier.error("Serial Disconnection Occured")
            self._courier.send(os.getenv("CSSE4011-YZ-CN-APPLICATION"), "", "serialDisconnect")
    
    def tester(self):
        data = {}
        for i in range(0, 4):
            rdata = self.read()
            del rdata["timestamp"]
            data.update(rdata)
        return DataRead(data)
    
    def start(self):
        self._courier.info("Serial Process Starting")
        while self._courier.check_continue():
            if self._connected:
                if self._lastread is None or time() - self._lastread > self._INTERVAL:
                    self.read()
                    if self._dataPoint.ready():
                        if not self._trainMode:
                            self._courier.send(os.getenv("CSSE4011-YZ-CN-LEARNER"), self._dataPoint, "serialData", nowait=True)
                        else:
                            self._courier.send(os.getenv("CSSE4011-YZ-CN-APPLICATION"), self._dataPoint, "trainSerialData")
                        self._dataPoint = self._dataPoint.migrate()
            self._check_queue()
        self._courier.info("Serial Process Stopping")
        self._courier.shutdown()

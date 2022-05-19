import multiprocessing
import json
from src.common import build_message
from src.classes import Reading
from datetime import datetime
from serial import Serial
from time import time


class SComs:
    _BAUD_RATE = 9600
    _DEFAULT_PORT = "COM4"
    _INTERVAL = 0.2

    def __init__(self, input_queue: multiprocessing.Queue, output_queue: multiprocessing.Queue) -> None:
        self._continue = True
        
        self._input_queue = input_queue
        self._output_queue = output_queue
        self._serial = None
        self.port = None
        self._connected = False
    
    def _check_queue(self):
        if not self._input_queue.empty():
            input = self._input_queue.get()
            if input["command"] == "setPort":
                self.port = input["data"]
                self.connect()
            elif input["command"] == "stop":
                self._continue = False
    
    def connect(self):
        if self.port is None:
            self.port = self._DEFAULT_PORT
        self._serial = Serial(self.port, self._BAUD_RATE)
        self._connected = True
    
    def read(self):
        if not self._connected:
            self.connect()
        try:
            raw_data = self._serial.readline()
            received_data = json.loads(raw_data.decode().strip())
            return Reading(received_data)
        except:
            return Reading({})
        
    
    def tester(self):
        data = {}
        for i in range(0, 4):
            rdata = self.read()
            del rdata["timestamp"]
            data.update(rdata)
        return Reading(data)
    
    def start(self):
        lastread = None
        while self._continue:
            if self._connected:
                data = self.read()
                try:
                    self._output_queue.put_nowait(build_message("serialData", data))   
                except:
                    pass
            self._check_queue()

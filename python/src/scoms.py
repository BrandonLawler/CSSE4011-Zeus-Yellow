import multiprocessing
import json
from modules.core.courier import Courier
from src.classes import Reading
from datetime import datetime
from serial import Serial
from time import time
import os


class SComs:
    _BAUD_RATE = 9600
    _INTERVAL = 0.2

    def __init__(self, courier: Courier) -> None:
        self._continue = True
        
        self._courier = courier
        self._serial = None
        self._default_port = os.getenv("CSSE4011-YZ-PORT-DEFAULT-WIN")
        self.port = None
        self._connected = False

        self.start()
    
    def _check_queue(self):
        if not self._courier.check_receive():
            input = self._courier.receive()
            if input.subject == "setPort":
                self.port = input.message
            elif input.subject == "start":
                self.connect()
            elif input.subject == "Stop":
                self.disconnect()
    
    def connect(self):
        if self.port is None:
            self.port = self._default_port
        try:
            self._serial = Serial(self.port, self._BAUD_RATE)
            self._connected = True
            self._courier.info(f"Serial Connected on Port: {self.port}")
        except:
            pass
    
    def disconnect(self):
        self._serial.close()
        self._connected = False
        self._serial = None
    
    def read(self):
        if not self._connected:
            self.connect()
        try:
            raw_data = self._serial.readline()
            received_data = json.loads(raw_data.decode().strip())
            return Reading(received_data)
        except:
            self._connected = False
            self._courier.error("Serial Disconnection Occured")
            return Reading({})
    
    def tester(self):
        data = {}
        for i in range(0, 4):
            rdata = self.read()
            del rdata["timestamp"]
            data.update(rdata)
        return Reading(data)
    
    def start(self):
        self._courier.info("Serial Process Starting")
        while self._courier.check_continue():
            if self._connected:
                data = self.read()
                self._courier.send(os.getenv("CSSE4011-YZ-CN-LEARNER"), data, "serialData", nowait=True)   
            self._check_queue()
        self._courier.shutdown()

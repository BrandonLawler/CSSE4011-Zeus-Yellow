import multiprocessing
import logging
import json
import os

from .log import Log, LogMessage
from .courier import Courier


class Core:
    def __init__(self, log_level=logging.INFO, log_folder=None, log_file=None, log_environment=None, environment_json=None):
        self.log_level = log_level
        self.log_folder = log_folder
        self.log_file = log_file
        self.log_environment = log_environment
        self.environment_json = environment_json
        self._log_process_event = multiprocessing.Event()
            

        self._process_event = multiprocessing.Event()
        self._processes = {}
        self._process_count = 0

        self._setup_environment()

        self._courier = Courier("Core", self._process_event, multiprocessing.Event())
        self._log = Log(self._log_process_event, self.log_level, self.log_folder, self.log_file, self.log_environment)
        self._watcher_process = multiprocessing.Process(target=self.watcher)

        if self.log_environment is not None and self.environment_json is None:
            self._courier.log(logging.WARNING, "Environment Json not Given - Use of Environment Will be Attempted")
    
    def _setup_environment(self):
        if self.environment_json is not None:
            with open(self.environment_json, "r") as ej:
                ejd = json.load(ej)
                for key, value in ejd.items():
                    os.environ[str(key)] = str(value)
        
    def create_class_process(self, process_id, process_function, process_args=None, process_kwargs=None):
        if process_args is None:
            process_args = []
        if process_kwargs is None:
            process_kwargs = {}
        shutdown = multiprocessing.Event()
        self._process_count += 1
        courier = Courier(process_id, self._process_event, shutdown, self._log.log_queue)
        self.update_couriers(process_id, courier.receiveQueue)
        courier.add_send_queue(self._courier.id, self._courier.receiveQueue)
        for id, processData in self._processes.items():
            courier.add_send_queue(id, processData["courier"].receiveQueue)
        process_args.insert(0, courier)
        process = multiprocessing.Process(target=process_function, args=process_args, kwargs=process_kwargs)
        self._processes[process_id] = {
            "process": process,
            "shutdown": shutdown,
            "courier": courier,
            "pid": None,
            "isShutdown": False
        }
    
    def update_couriers(self, newCourierId: str, newCourierQueue: multiprocessing.Queue):
        for processData in self._processes.values():
            processData["courier"].add_send_queue(newCourierId, newCourierQueue)
    
    def _check_shutdowns(self):
        for id, processData in self._processes.items():
            if not processData["isShutdown"] and processData["shutdown"].is_set():
                self._log.log_queue.put(LogMessage(id, f"Shutdown Received - {processData['courier'].id}", Log._INFO))
                self._process_event.set()
                self._process_count -= 1
                processData["isShutdown"] = True
    
    def watcher(self):
        while not self._process_event.is_set():
            self._check_shutdowns()
            message = self._courier.receive()
            if message is not None:
                if message.subject == "PID":
                    self._processes[message.sender]["pid"] = message.message
        while self._process_count != 0:
            self._check_shutdowns()
        self._log.log_queue.put(LogMessage("Core", "Watcher Shutdown Complete", Log._INFO))
        self._log_process_event.set()
    
    def start(self):
        self._watcher_process.start()
        for processData in self._processes.values():
            processData["process"].start()
        self._log.start()

        
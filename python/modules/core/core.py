import multiprocessing
import logging

from .log import Log
from .courier import Courier


class Core:
    def __init__(self, log_level=logging.INFO, log_folder=None, log_file=None):
        self.log_level = log_level
        self.log_folder = log_folder
        self.log_file = log_file

        self._process_event = multiprocessing.Event()
        self._processes = {}
        self._process_count = 0

        self._courier = Courier("Core", self._process_event, multiprocessing.Event())
        self._log = Log(self._process_event, self.log_level, self.log_folder, self.log_file)
        self._watcher_process = multiprocessing.Process(target=self.watcher)
        
    def create_class_process(self, process_id, process_function, process_args=[], process_kwargs={}):
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
            "pid": None
        }
    
    def update_couriers(self, newCourierId: str, newCourierQueue: multiprocessing.Queue):
        for processData in self._processes.values():
            processData["courier"].add_send_queue(newCourierId, newCourierQueue)
    
    def _check_shutdowns(self):
        shutdowns_occured = self._process_count
        for id, processData in self._processes.items():
            if processData["shutdown"].is_set():
                processData["process"].join()
                self._log.log_queue.put(Log.LogMessage(id, "Shutdown Received", Log.INFO))
                self._process_event.set()
                shutdowns_occured -= 1
        return shutdowns_occured
    
    def watcher(self):
        while not self._process_event.is_set():
            self._check_shutdowns()
            message = self._courier.receive()
            if message is not None:
                if message.subject == "PID":
                    self._processes[message.sender]["pid"] = message.message
        while self._check_shutdowns() != 0:
            pass
    
    def start(self):
        self._watcher_process.start()
        for processData in self._processes.values():
            processData["process"].start()
        self._log.start()

        
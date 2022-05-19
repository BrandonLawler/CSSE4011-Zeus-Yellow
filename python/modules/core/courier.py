from dataclasses import dataclass
from multiprocessing import Queue, Event
import logging


@dataclass
class Message:
    sender: str
    receiver: str
    subject: str
    message: str


@dataclass
class LogMessage:
    sender: str
    message: str
    level: int


class Courier:
    _CRITICAL = logging.CRITICAL
    _ERROR = logging.ERROR
    _WARNING = logging.WARNING
    _INFO = logging.INFO
    _DEBUG = logging.DEBUG

    _DEFAULT_TIMEOUT = 0.1

    def __init__(self, identifier: str,process_event: Event, shutdown_event: Event, logQueue: Queue = None):
        self.process_event = process_event
        self.shutdown_event = shutdown_event

        self._identifier = identifier
        self.receiveQueue = Queue()
        self.logQueue = logQueue
        self.sendQueues = {}
    
    @property
    def id(self):
        return self._identifier
    
    def add_send_queue(self, queueName: str, queue: Queue):
        self.sendQueues[queueName] = queue
    
    def log(self, level: int, message: str):
        if self.logQueue is not None:
            self.logQueue.put(LogMessage(self._identifier, message, level))
    
    def critical(self, message: str):
        self.log(self._CRITICAL, message)
    
    def error(self, message: str):
        self.log(self._ERROR, message)
    
    def warning(self, message: str):
        self.log(self._WARNING, message)
    
    def info(self, message: str):
        self.log(self._INFO, message)
    
    def debug(self, message: str):
        self.log(self._DEBUG, message)
    
    def send(self, recipient: str, message: str):
        if recipient in self.sendQueues.keys() or recipient.lower() in self.sendQueues.keys() or recipient.lower() in [id.lower() for id in self.sendQueues.keys()]:
            self.sendQueues[recipient].put(Message(self._identifier, recipient, message))
        else:
            self.error(f"{self._identifier} Courier - Recipient {recipient} not found")
    
    def receive(self, wait=False, timeout=_DEFAULT_TIMEOUT):
        if wait:
            return self.receiveQueue.get(block=True, timeout=None)
        try:
            return self.receiveQueue.get(block=False, timeout=timeout)
        except:
            return None
    
    def check_continue(self):
        return not self.process_event.is_set()
    
    def shutdown(self):
        self.shutdown_event.set()


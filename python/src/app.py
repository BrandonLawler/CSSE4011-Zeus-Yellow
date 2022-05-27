import random
import platform
import json
from turtle import update
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
import pyqtgraph as grapher
import os

from modules.core.courier import Courier
from src.common import toCapital


class App:
    _TIMEOUT = 1

    _ACTIVETAB = 0
    _TRAINTAB = 1
    _CONFIGTAB = 2

    _CONNECT = -1
    _DISCONNECT = -2

    _TAB_MENU_HEIGHT = 60

    def __init__(self, courier: Courier) -> None:
        self._courier = courier

        self._qtApplication = None
        self._centralWindow = None
        self._windowedHeight = int(os.getenv("CSSE4011-YZ-APP-WINDOWHEIGHT"))
        self._windowedWidth = int(os.getenv("CSSE4011-YZ-APP-WINDOWWIDTH"))
        self._fullscreen = False

        self._activeFrame = None
        self._trainFrame = None
        self._configFrame = None

        self._updateTimer = None

        self._started = False
        self._serialPort = None
        self._trianing = False

        self._classifierPrediction = self._DISCONNECT

        self._currentTab = self._ACTIVETAB
        self._currentMode = None

        self._classifierDict = {}
        self.start()

    def _shutdown(self):
        self._courier.shutdown()
        self._qtApplication.quit()

    def _get_height(self):
        if self._fullscreen:
            return self._centralWidget().screenGeometry().height()
        return self._windowedHeight
    
    def _get_width(self):
        if self._fullscreen:
            return self._centralWidget().screenGeometry().width()
        return self._windowedWidth
    
    def _get_display_media(self, name):
        fp = os.path.join(os.getenv("CSSE4011-YZ-FP-MEDIA"), "classifiers")
        fp = os.path.join(fp, name)
        if os.path.exists(fp):
            #get the media file
            pass
        elif os.path.exists(os.getenv("CSSE4011-YZ-FP-APP-DEFAULT-MEDIA")):
            #get default media file
            self._courier.warning(f"No media file found for classifier: {name}")
            pass
        self._courier.error(f"No media file found for classifier: {name} and no Default Media Supplied")

    def _switch_tab(self, tab):
        if tab == self._ACTIVETAB:
            self._courier.send(os.getenv("CSSE4011-YZ-CN-SERIAL"), "", "stop")
            self._courier.send(os.getenv("CSSE4011-YZ-CN-SERIAL"), False, "trainMode")
            self._configFrame.hide()
            self._trainFrame.hide()
            self._activeFrame.show()
        elif tab == self._TRAINTAB:
            self._courier.send(os.getenv("CSSE4011-YZ-CN-SERIAL"), "", "stop")
            self._courier.send(os.getenv("CSSE4011-YZ-CN-SERIAL"), True, "trainMode")
            self._configFrame.hide()
            self._activeFrame.hide()
            self._trainFrame.show()
        elif tab == self._CONFIGTAB:
            self._activeFrame.hide()
            self._trainFrame.hide()
            self._configFrame.show()
        else:
            self._courier.log(Courier._ERROR, f"Incorrect Tab Type: {tab} Unknown")
            return
        self._currentTab = tab
    
    def _switch_active_tab(self): self._switch_tab(self._ACTIVETAB)
    def _switch_train_tab(self): self._switch_tab(self._TRAINTAB)
    def _switch_config_tab(self): self._switch_tab(self._CONFIGTAB)

    def _start_active(self):
        if self._started:
            self._started = False
            self._startButton.setText("Start")
            self._courier.send(os.getenv("CSSE4011-YZ-CN-SERIAL"), "", "Stop")
        else:
            self._started = True
            self._startButton.setText("Stop")
            self._courier.send(os.getenv("CSSE4011-YZ-CN-SERIAL"), "", "Start")
    

    def _update_display(self, prediction, prediction_data=None):
        """
        Update Active Tab Display
        """
        updated = False
        if prediction != self._classifierPrediction:
            updated = True
            self._classifierPrediction = prediction
        if prediction_data is not None:
            self._activeReadingDisplay.setText(prediction_data)
            predName = self._classifierDict[self._classifierPrediction]
        elif self._classifierPrediction == self._CONNECT:
            predName = "connected"
            self._activeReadingDisplay.setText("Serial Connection Found")
        elif self._classifierPrediction == self._DISCONNECT:
            predName = "disconnected"
            self._activeReadingDisplay.setText("Serial Connection Lost")
        else:
            predName = self._classifierDict[self._classifierPrediction]
            self._activeReadingDisplay.setText(predName)
        self._activeModeDisplay.setText(toCapital(predName))
        if updated:
            self._get_display_media(predName.lower())


    def _build_tab_menu(self):
        self._tabMenuFrame = QFrame()
        self._tabMenuFrame.setLayout(QHBoxLayout())
        self._tabMenuFrame.setFixedWidth(self._get_width())
        self._tabMenuFrame.setFixedHeight(self._TAB_MENU_HEIGHT)

        self._activeTabButton = QPushButton("Active")
        self._activeTabButton.clicked.connect(self._switch_active_tab)        
        self._trainTabButton = QPushButton("Train")
        self._trainTabButton.clicked.connect(self._switch_train_tab)
        self._optionsTabButton = QPushButton("Config")
        self._optionsTabButton.clicked.connect(self._switch_config_tab)

        self._tabMenuFrame.layout().addWidget(self._activeTabButton)
        self._tabMenuFrame.layout().addWidget(self._trainTabButton)
        self._tabMenuFrame.layout().addWidget(self._optionsTabButton)

        return self._tabMenuFrame

    def _build_active_tab(self):
        self._activeFrame = QFrame()
        self._activeFrame.setLayout(QVBoxLayout())
        self._activeFrame.setFixedWidth(self._get_width())
        self._activeFrame.setFixedHeight(self._get_height() - self._TAB_MENU_HEIGHT)

        self._activeLabel = QLabel("Active Mode")
        self._activeFrame.layout().addWidget(self._activeLabel)

        self._activeDisplay = None # Put Display images at this location

        self._activeModeDisplay = QLabel("Disconnected")
        self._activeFrame.layout().addWidget(self._activeModeDisplay)

        self._activeReadingDisplay = QLabel("")
        self._activeFrame.layout().addWidget(self._activeReadingDisplay)

        self._startButton = QPushButton("Start")
        self._startButton.clicked.connect(self._start_active)
        self._activeFrame.layout().addWidget(self._startButton)

        if self._currentTab != self._ACTIVETAB:
            self._activeFrame.hide()
        return self._activeFrame
    
    def _build_train_tab(self):
        self._trainFrame = QFrame()
        self._trainFrame.setLayout(QHBoxLayout())
        self._trainFrame.setFixedWidth(self._get_width())
        self._trainFrame.setFixedHeight(self._get_height() - self._TAB_MENU_HEIGHT)

        self._trainLabel = QLabel("TRAIN")
        self._trainFrame.layout().addWidget(self._trainLabel)

        if self._currentTab != self._TRAINTAB:
            self._trainFrame.hide()
        return self._trainFrame

    def _build_config_tab(self):
        self._configFrame = QFrame()
        self._configFrame.setLayout(QVBoxLayout())
        self._configFrame.setFixedWidth(self._get_width())
        self._configFrame.setFixedHeight(self._get_height() - self._TAB_MENU_HEIGHT)

        self._configLabel = QLabel("Configure")
        self._configFrame.layout().addWidget(self._configLabel)

        self._serialFrame = QFrame()
        self._serialFrame.setLayout(QHBoxLayout())
        self._serialFrame.layout().addWidget(QLabel("Serial Port"))
        self._serialValue = QLineEdit()

        if platform.system() == "Windows":
            self._serialPort = os.getenv("CSSE4011-YZ-PORT-DEFAULT-WIN")
        elif platform.system() == "Linux":
            self._serialPort = os.getenv("CSSE4011-YZ-PORT-DEFAULT-LIN")
        self._serialValue.setText(self._serialPort)

        self._serialFrame.layout().addWidget(self._serialValue)
        
        if self._currentTab != self._CONFIGTAB:
            self._configFrame.hide()
        return self._configFrame
    
    def _build(self):
        self._centralFrame = QFrame()
        self._centralFrame.closeEvent = lambda event: self._shutdown()
        self._centralFrame.setLayout(QVBoxLayout())
        self._centralFrame.setFixedHeight(self._get_height())
        self._centralFrame.setFixedWidth(self._get_width())

        self._centralFrame.layout().addWidget(self._build_tab_menu())
        self._centralFrame.layout().addWidget(self._build_active_tab())
        self._centralFrame.layout().addWidget(self._build_train_tab())
        self._centralFrame.layout().addWidget(self._build_config_tab())
        

    def _check_serial(self):
        pvalue = self._serialValue.text()
        if pvalue != self._serialPort:
            self._courier.send(os.getenv("CSSE4011-YZ-CN-SERIAL"), pvalue, "serialPort")
            self._serialPort = pvalue
    
    def _check_messages(self):
        if self._courier.check_receive():
            msg = self._courier.receive()
            if msg.subject == "registerClassifier":
                for key, value in msg.message.items():
                    if key not in self._classifierDict.keys() and value not in self._classifierPrediction.values():
                        self._classifierDict[key] = {
                            "name": value,
                            "deletable": True
                        }
                        if key == "sitting" or key == "standing" or key == "walking" or key == "running":
                            self._classifierDict[key]["deletable"] = False
                    else:
                        self._courier.error(f"Mode {key} Already Registered")
            elif msg.subject == "prediction":
                if msg.message.prediction not in self._classifierDict.keys():
                    self._courier.error(f"Mode {msg.message.prediction} Not Registered")
                    return
                self._update_display(msg.message.prediction, msg.message)
            elif msg.subject == "trainSerialData":
                if self._currentMode is not None:
                    msg.message.prediction = self._currentMode
                    self._courier.send(os.getenv("CSSE4011-YZ-CN-INFLUX"), msg.message, "testData")
            elif msg.subject == "serialConnect":
                self._update_display(self._CONNECT)
            elif msg.subject == "serialDisconnect":
                self._update_display(self._DISCONNECT)
            else:
                self._courier.error(f"Unknown Message: {msg.subject} - {msg.message}")

    def _check_updates(self):
        if not self._courier.check_continue():
            self._shutdown()
        self._check_serial()

    def start(self):
        self._courier.info("App Process Starting")

        self._updateTimer = QTimer()
        self._updateTimer.setInterval(1)
        self._updateTimer.timeout.connect(self._check_updates)

        self._qtApplication = QApplication([])
        self._build()
        self._updateTimer.start()
        self._centralFrame.show()
        self._qtApplication.exec()
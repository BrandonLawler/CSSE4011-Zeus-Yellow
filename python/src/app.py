from ctypes import alignment
import random
import platform
import json
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
import os
import multiprocessing
import logging
import math

from modules.core.courier import Courier
from modules.core.core import Core
from src.common import toCapital


class App:
    _TIMEOUT = 1

    _ACTIVETAB = 0
    _TRAINTAB = 1
    _CONFIGTAB = 2

    _CONNECT = -1
    _DISCONNECT = -2
    _CLASSIFIERROW = 3

    _TAB_MENU_HEIGHT = 22

    _GUARANTEED_KEYS = [
        "sitting", "standing", "walking", "running"
    ]

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

        self._classifierPrediction = None

        self._currentTab = self._ACTIVETAB
        self._currentMode = None
        self._trainingRequired = os.getenv("CSSE4011-YZ-APP-TRAININGMAX")
        self._trainingCurrentTick = 0
        self._trainingData = []

        self._movie = None

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
        fp = os.path.join(fp, name + ".gif")
        if os.path.exists(fp):
            return fp
        elif os.path.exists(os.getenv("CSSE4011-YZ-FP-APP-DEFAULT-MEDIA")):
            self._courier.warning(f"No media file found for classifier: {name}")
            return os.getenv("CSSE4011-YZ-FP-APP-DEFAULT-MEDIA")
        self._courier.error(f"No media file found for classifier: {name} and no Default Media Supplied")

    def _switch_tab(self, tab):
        if tab == self._currentTab:
            return
        elif self._currentMode is not None:
            self._courier.info("Cannot switch tabs while Training")
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
            self._courier.send(os.getenv("CSSE4011-YZ-CN-SERIAL"), "", "stop")
        else:
            self._started = True
            self._startButton.setText("Stop")
            self._courier.send(os.getenv("CSSE4011-YZ-CN-SERIAL"), "", "start")
    
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
            self._activeDisplayFrame.layout().removeWidget(self._activeDisplay)
            self._activeDisplay = QLabel("")
            self._activeDisplay.setMinimumSize(QSize(200, 200))
            self._activeDisplay.setObjectName("activeDisplay")
            movie = QMovie(self._get_display_media(predName))
            self._activeDisplay.setMovie(movie)
            self._activeDisplayFrame.layout().addWidget(self._activeDisplay)
            movie.start()
    
    def _add_classifier(self):
        classifier = self._classifierAdder.text().lower()
        if classifier == "":
            self._courier.error("Classifier Name Cannot Be Empty")
            return
        if classifier in [x["name"] for x in self._classifierDict.values()]:
            self._courier.error(f"Classifier Already Exists: {classifier}")
            return
        self._courier.send(os.getenv("CSSE4011-YZ-CN-LEARNER"), classifier, "registerClassifier")
    
    def _delete_button(self, btn):
        classifier = int(btn.objectName())
        self._courier.send(os.getenv("CSSE4011-YZ-CN-LEARNER"), classifier, "deleteClassifier")
    
    def _training_start(self):
        mode = self._trainerClassifiers.currentText().lower()
        if mode not in [x["name"] for x in self._classifierDict.values()]:
            self._courier.error(f"Classifier Does Not Exist: {mode}")
            return
        self._courier.send(os.getenv("CSSE4011-YZ-CN-SERIAL"), True, "trainMode")
        self._trainingCurrentTick = 0
        self._currentMode = None
        for key, value in self._classifierDict.items():
            if value["name"] == mode:
                self._currentMode = key
        self._trainingBar.setValue(0)
        self._trainerText.setText("Starting Training")
        self._courier.send(os.getenv("CSSE4011-YZ-CN-SERIAL"), "", "start")


    def _build_tab_menu(self):
        self._tabMenuFrame = QFrame()
        self._tabMenuFrame.setLayout(QHBoxLayout())
        self._tabMenuFrame.setFixedWidth(self._get_width())
        self._tabMenuFrame.setFixedHeight(self._TAB_MENU_HEIGHT)
        self._tabMenuFrame.layout().setContentsMargins(0,0,0,0)
        self._tabMenuFrame.setObjectName("tabMenuFrame")

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
        self._activeFrame.setObjectName("ActiveFrame")

        self._activeLabel = QLabel("Active Mode")
        self._activeFrame.layout().addWidget(self._activeLabel, alignment=Qt.AlignmentFlag.AlignCenter)

        self._activeDisplayFrame = QFrame()
        self._activeDisplayFrame.setLayout(QHBoxLayout())
        self._activeDisplay = QLabel("")
        self._activeDisplay.setMinimumSize(QSize(200, 200))
        self._activeDisplay.setObjectName("activeDisplay")
        self._activeDisplayFrame.layout().addWidget(self._activeDisplay)
        self._activeFrame.layout().addWidget(self._activeDisplayFrame, alignment=Qt.AlignmentFlag.AlignCenter)

        self._activeModeDisplay = QLabel("Disconnected")
        self._activeFrame.layout().addWidget(self._activeModeDisplay, alignment=Qt.AlignmentFlag.AlignCenter)

        self._activeReadingDisplay = QLabel("")
        self._activeFrame.layout().addWidget(self._activeReadingDisplay, alignment=Qt.AlignmentFlag.AlignCenter)

        self._startButton = QPushButton("Start")
        self._startButton.clicked.connect(self._start_active)
        self._activeFrame.layout().addWidget(self._startButton, alignment=Qt.AlignmentFlag.AlignCenter)

        self._update_display(self._DISCONNECT)
        if self._currentTab != self._ACTIVETAB:
            self._activeFrame.hide()
        return self._activeFrame
    
    def _build_train_tab(self):
        self._trainFrame = QFrame()
        self._trainFrame.setLayout(QVBoxLayout())
        self._trainFrame.setFixedWidth(self._get_width())
        self._trainFrame.setFixedHeight(self._get_height() - self._TAB_MENU_HEIGHT)
        self._trainFrame.setObjectName("TrainFrame")

        self._trainLabel = QLabel("Training")
        self._trainFrame.layout().addWidget(self._trainLabel, alignment=Qt.AlignmentFlag.AlignCenter)

        self._trainerClassifiers = QComboBox()
        for item in self._classifierDict.keys():
            self._trainerClassifiers.addItem(toCapital(self._classifierDict[item]["name"]))
        self._trainFrame.layout().addWidget(self._trainerClassifiers, alignment=Qt.AlignmentFlag.AlignCenter)
        self._trainingBar = QProgressBar()
        self._trainingBar.setMaximum(int(os.getenv("CSSE4011-YZ-APP-TRAININGMAX")))
        self._trainingBar.setMinimum(0)
        self._trainingBar.setFixedWidth(self._get_width() - 60)
        self._trainFrame.layout().addWidget(self._trainingBar, alignment=Qt.AlignmentFlag.AlignCenter)
        self._trainerText = QLabel("")
        self._trainFrame.layout().addWidget(self._trainerText, alignment=Qt.AlignmentFlag.AlignCenter)
        self._trainingStartButton = QPushButton("Start Training")
        self._trainingStartButton.clicked.connect(self._training_start)
        self._trainFrame.layout().addWidget(self._trainingStartButton, alignment=Qt.AlignmentFlag.AlignCenter)

        if self._currentTab != self._TRAINTAB:
            self._trainFrame.hide()
        return self._trainFrame

    def _build_config_tab(self):
        self._configFrame = QFrame()
        self._configFrame.setLayout(QVBoxLayout())
        self._configFrame.setFixedWidth(self._get_width())
        self._configFrame.setFixedHeight(self._get_height() - self._TAB_MENU_HEIGHT)
        self._configFrame.setObjectName("ConfigFrame")

        self._configLabel = QLabel("Configure")
        self._configFrame.layout().addWidget(self._configLabel, alignment=Qt.AlignmentFlag.AlignCenter)

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
        self._configFrame.layout().addWidget(self._serialFrame)

        self._classifierAdder = QLineEdit()
        self._classifierAdder.setPlaceholderText("Add Classifier")
        self._configFrame.layout().addWidget(self._classifierAdder, alignment=Qt.AlignmentFlag.AlignCenter)
        self._classifierButton = QPushButton()
        self._classifierButton.setText("Add")
        self._classifierButton.clicked.connect(self._add_classifier)
        self._configFrame.layout().addWidget(self._classifierButton, alignment=Qt.AlignmentFlag.AlignCenter)

        self._configFrame.layout().addWidget(self._build_classifiers(), alignment=Qt.AlignmentFlag.AlignCenter)

        if self._currentTab != self._CONFIGTAB:
            self._configFrame.hide()
        return self._configFrame

    def _build_classifiers(self):
        self._classifierFrame = QFrame()
        self._classifierFrame.setLayout(QVBoxLayout())

        self._deleterButtonGroup = QButtonGroup()
        for i in range(0, math.ceil(len(self._classifierDict.keys())/self._CLASSIFIERROW)):
            rframe = QFrame()
            rframe.setLayout(QHBoxLayout())
            for j in range(0, self._CLASSIFIERROW):
                if len(self._classifierDict.keys()) > i*self._CLASSIFIERROW + j:
                    cframe = QFrame()
                    cframe.setObjectName("classifierFrame")
                    cframe.setLayout(QHBoxLayout())
                    cframe.layout().setContentsMargins(0,0,0,0)
                    cframe.layout().addWidget(QLabel(toCapital(self._classifierDict[list(self._classifierDict.keys())[i*self._CLASSIFIERROW + j]]["name"])))
                    if self._classifierDict[list(self._classifierDict.keys())[i*self._CLASSIFIERROW + j]]["deletable"]:
                        but = QPushButton()
                        but.setIcon(QIcon(os.getenv("CSSE4011-YZ-FP-MEDIA")+"/icon/trash-can.png"))
                        but.setIconSize(QSize(6,6))
                        but.setObjectName(str(list(self._classifierDict.keys())[i*self._CLASSIFIERROW + j]))
                        self._deleterButtonGroup.addButton(but)
                        cframe.layout().addWidget(but)
                    rframe.layout().addWidget(cframe)
            self._classifierFrame.layout().addWidget(rframe)
        self._deleterButtonGroup.buttonClicked.connect(self._delete_button)

        return self._classifierFrame
    
    def _rebuild_classifiers(self):
        self._configFrame.layout().removeWidget(self._classifierFrame)
        self._configFrame.layout().addWidget(self._build_classifiers())
        self._trainerClassifiers.clear()
        for item in self._classifierDict.keys():
            self._trainerClassifiers.addItem(toCapital(self._classifierDict[item]["name"]))

    def _build(self):
        with open(os.getenv("CSSE4011-YZ-FP-APP-STYLESHEET"), "r") as stylesheet:
            self._qtApplication.setStyleSheet(stylesheet.read())

        self._centralFrame = QFrame()
        self._centralFrame.closeEvent = lambda event: self._shutdown()
        self._centralFrame.setLayout(QVBoxLayout())
        self._centralFrame.setFixedHeight(self._get_height())
        self._centralFrame.setFixedWidth(self._get_width())
        self._centralFrame.setContentsMargins(0,0,0,0)
        self._centralFrame.layout().setSpacing(0)
        self._centralFrame.layout().setContentsMargins(0,0,0,0)
        self._centralFrame.setObjectName("centralFrame")

        self._centralFrame.layout().addWidget(self._build_tab_menu())
        self._centralFrame.layout().addWidget(self._build_active_tab())
        self._centralFrame.layout().addWidget(self._build_train_tab())
        self._centralFrame.layout().addWidget(self._build_config_tab())
        

    def _check_serial(self):
        pvalue = self._serialValue.text()
        if pvalue != self._serialPort:
            self._courier.send(os.getenv("CSSE4011-YZ-CN-SERIAL"), pvalue, "setPort")
            self._serialPort = pvalue
        
    def _check_training(self):
        if self._trainingCurrentTick >= os.getenv("CSSE4011-YZ-APP-TRAININGMAX"):
            self._courier.send(os.getenv("CSSE4011-YZ-CN-SERIAL"), "", "stop")
            self._courier.send(os.getenv("CSSE4011-YZ-CN-SERIAL"), False, "trainMode")
            self._trainingCurrentTick = 0
            self._trainerText.setText("Training Complete - Uploading Data ... ")
            self._trainingBar.setValue(self._trainingCurrentTick)
            for item in self._trainingData:
                self._courier.send(os.getenv("CSSE4011-YZ-CN-INFLUX"), item, "testData")
                self._trainingCurrentTick += 1
                self._trainingBar.setValue(self._trainingCurrentTick)
            self._currentMode = None

    
    def _check_messages(self):
        if self._courier.check_receive():
            print("receiving")
            msg = self._courier.receive()
            if msg.subject == "registerClassifier":
                for key, value in msg.message.items():
                    self._courier.debug(f"Registering classifier: {key}")
                    if key not in self._classifierDict.keys() and value not in self._classifierDict.values():
                        self._classifierDict[key] = {
                            "name": value,
                            "deletable": True
                        }
                        if value in self._GUARANTEED_KEYS:
                            self._classifierDict[key]["deletable"] = False
                        self._rebuild_classifiers()
                    else:
                        self._courier.error(f"Mode {key} Already Registered")
            elif msg.subject == "deleteClassifier":
                del self._classifierDict[msg.message]
                self._rebuild_classifiers()
            elif msg.subject == "prediction":
                if msg.message.prediction not in self._classifierDict.keys():
                    self._courier.error(f"Mode {msg.message.prediction} Not Registered")
                    return
                self._update_display(msg.message.prediction, msg.message)
            elif msg.subject == "trainSerialData":
                if self._currentMode is not None:
                    msg.message.prediction = self._currentMode
                    self._trainingCurrentTick += 1
                    self._trainingData.append(msg.message)
                    self._trainerText.setText(f"Training Data Recieved: {msg.message}")
                    self._trainingBar.setValue(self._trainingCurrentTick)
                    self._checkTraining()
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
        self._check_messages()

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


if __name__ == "__main__":
    core = Core(log_level=logging.DEBUG, environment_json="files/environment.json", log_environment="CSSE4011-YZ-FP-LOGS")
    courier = Courier("App", multiprocessing.Event(), multiprocessing.Event(), multiprocessing.Queue())
    app = App(courier=courier)

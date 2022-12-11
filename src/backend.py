from multiprocessing.connection import answer_challenge
import traceback
import sys

from db import TimescaleDB
#from tcpclient import TCPClient
from serialclient import SerialClient
from controller import Controller

from PyQt5.QtCore import QObject, QTimer, QCoreApplication, QThread
from PyQt5 import QtCore


# Signals used by the backend.
class BackendSignals(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(tuple)


MEASUREMENT_TYPES = [
    ('0', 'Light Sensor', 'Stores the current ambient light in lux'),
    ('1', 'Load current', 'ACS723 sensor data'),
    ('2', 'Charge current', 'ACS723 sensor data'),
    ('3', 'Battery voltage', 'Direct ADC to V+ line'),
    ('4', 'Drop flow', 'Flow data on the drop side'),
    ('5', 'Top Tank Level', 'Level of the top tank in liters'),
    ('6', 'Bottom Tank Level', 'Level of the bottom tank in liters'),
    ('7', 'Total volume', 'Total water volume in the system'),

    ('8', 'Is Manual', 'Stores whether the control is manual or auto'),
    ('9', 'Bottom tank empty counter', 'Counter showing how long the bottom tank was empty'),
    ('10', 'Top tank empty counter', 'Counter showing how long the top tank was empty'),
    ('11', 'Pump relay state', 'Shows whether the pump relay is on or off'),
    ('12', 'Valve relay state', 'Shows whether the valve relay is on or off'),
    ('13', 'Solar relay state', 'Shows whether the solar relay is on or off'),
    ('14', 'Generator relay state', 'Shows whether the generator relay is on or off'),
    ('15', 'Low battery trigger', 'If true the battery is low and cannot be charged by fluid discharge')
]


class Backend(QObject):
    REQUEST_ALL_DATA = "$RALL"
    ANSWER_ALL_DATA = "$ADTA"
    ANSWER_CONTROL_DATA = "$ACTL"
    REMOTE_READY = "$ARDY"

    def __init__(self):
        super(Backend, self).__init__()
        self.signals = BackendSignals()
        # Thread break guard condition, when true the thread finishes.
        self.stop = False

        self.error = QtCore.pyqtSignal(tuple)
        self.finished = QtCore.pyqtSignal()

        self.network_client = SerialClient()
        self.controller = Controller(self.network_client)
        self.db = TimescaleDB(MEASUREMENT_TYPES)

        self.responseTimer = QTimer(self)
        self.responseTimer.setInterval(100)
        self.responseTimer.timeout.connect(self._parseResponse)
        self.remoteWatchdogTimer = QTimer(self)
        self.remoteWatchdogTimer.setInterval(5000)
        self.remoteWatchdogTimer.timeout.connect(self._setRemoteReady)

    # @QtCore.pyqtSlot(bool)
    def _setRemoteReady(self):
        print("Watchdog timeout!")
        self.network_client.remote_ready = False

    # @QtCore.pyqtSlot(bool)
    def enablePump(self, state):
        self.controller.set_pump(state)

    # @QtCore.pyqtSlot(bool)
    def enableValve(self, state):
        self.controller.set_valve(state)

    # @QtCore.pyqtSlot(bool)
    def enableSolar(self, state):
        self.controller.set_solar(state)

    # @QtCore.pyqtSlot(bool)
    def enableGenerator(self, state):
        self.controller.set_generator(state)

    def _createDataValues(self, message):
        data = dict()
        if message.headerStr == self.ANSWER_ALL_DATA:
            for i, dataStr in enumerate(message.dataList):
                data[i] = dataStr
        elif message.headerStr == self.ANSWER_CONTROL_DATA:
            for i, dataStr in enumerate(message.dataList):
                data[i + 8] = dataStr
        self.db.execute(self.db.insert_data, data)

    def _processMessages(self):
        message = self.network_client.pop_message()
        if message is not None:
            print(f"Current parsed msg: {message.headerStr}, remoteReady: {self.network_client.remote_ready}")
            self._createDataValues(message)
            if message.headerStr == self.REMOTE_READY:
                self.network_client.remote_ready = True

    @QtCore.pyqtSlot()
    def _parseResponse(self):
        self.network_client.add_to_send_queue(self.REQUEST_ALL_DATA)
        self.network_client.send()
        if self.network_client.receive():
            self.remoteWatchdogTimer.start()
        self._processMessages()

    @QtCore.pyqtSlot()
    def run(self):
        self.responseTimer.start()
        try:
            print("Backend")
            while (True):
                if self.stop:
                    break
                QCoreApplication.processEvents()
                QThread.msleep(10)
        except Exception:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        finally:
            self.signals.finished.emit()  # Done

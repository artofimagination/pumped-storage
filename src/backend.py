import traceback
import sys

from db import TimescaleDB
from network import Message
from tcpclient import TCPClient
from serialclient import SerialClient
from controller import Controller

from PyQt5.QtCore import QObject, QTimer, QCoreApplication, QThread
from PyQt5 import QtCore


class StateSourceSignals(QtCore.QObject):
    updateRemote = QtCore.pyqtSignal()
    updateUI = QtCore.pyqtSignal()


USER_SOURCE = 0
REMOTE_SOURCE = 1


class StateSourceController():
    """! Clumsy data source controller to handle the usual dilemma, of handling async data update
    that can come from either gui, backend or remote device.
    """
    def __init__(self, sourceName, updateUi, updateRemote, defaultData):
        self.updateUi = updateUi
        self.updateRemote = updateRemote
        self.requested_data = defaultData
        self.active_source = None
        self.sourceName = sourceName

    def setData(self, source, data):
        print(f"{self.sourceName} Update data r: {self.requested_data} n: {data}")
        if self.requested_data == data:
            return

        if source == USER_SOURCE:
            print("Update ui")
            if self.active_source == REMOTE_SOURCE and data == self.requested_data:
                print("Update ui deact")
                self.active_source = None
            elif self.active_source is None:
                print("Update ui update")
                self.active_source = source
                self.requested_data = data
            self.updateRemote(data)
        elif source == REMOTE_SOURCE:
            print("Update remote")
            if self.active_source == USER_SOURCE:
                print("Update remote deact")
                self.active_source = None
            elif self.active_source is None:
                print("Update remote update")
                self.active_source = source
                self.requested_data = data
            self.updateUi(data)


# Signals used by the backend.
class BackendSignals(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal(tuple)
    updatePumpEnabled = QtCore.pyqtSignal(bool)
    updateValveEnabled = QtCore.pyqtSignal(bool)
    updateSolarEnabled = QtCore.pyqtSignal(bool)
    updateGeneratorEnabled = QtCore.pyqtSignal(bool)


LIGHT_SENSOR = 0
CURRENT = 1
BATTERY_VOLTAGE = 2
DROP_FLOW = 3
TOP_TANK_LEVEL = 4
BOTTOM_TANK_LEVEL = 5
TOTAL_VOLUME = 6
IS_MANUAL = 7
BOTTOM_TANK_EMPTY_COUNTER = 8
TOP_TANK_EMPTY_COUNTER = 9
PUMP_RELAY_STATE = 10
VALVE_RELAY_STATE = 11
SOLAR_RELAY_STATE = 12
GENERATOR_RELAY_STATE = 13
LOW_BATTERY_TRIGGER = 14


MEASUREMENT_TYPES = [
    (LIGHT_SENSOR, 'Light Sensor', 'Stores the current ambient light in lux'),
    (CURRENT, 'Current', 'ACS723 sensor data (both charge and load measurement)'),
    (BATTERY_VOLTAGE, 'Charge current', 'ACS723 sensor data'),
    (DROP_FLOW, 'Drop flow', 'Flow data on the drop side'),
    (TOP_TANK_LEVEL, 'Top Tank Level', 'Level of the top tank in liters'),
    (BOTTOM_TANK_LEVEL, 'Bottom Tank Level', 'Level of the bottom tank in liters'),
    (TOTAL_VOLUME, 'Total volume', 'Total water volume in the system'),

    (IS_MANUAL, 'Is Manual', 'Stores whether the control is manual or auto'),
    (BOTTOM_TANK_EMPTY_COUNTER, 'Bottom tank empty counter', 'Counter showing how long the bottom tank was empty'),
    (TOP_TANK_EMPTY_COUNTER, 'Top tank empty counter', 'Counter showing how long the top tank was empty'),
    (PUMP_RELAY_STATE, 'Pump relay state', 'Shows whether the pump relay is on or off'),
    (VALVE_RELAY_STATE, 'Valve relay state', 'Shows whether the valve relay is on or off'),
    (SOLAR_RELAY_STATE, 'Solar relay state', 'Shows whether the solar relay is on or off'),
    (GENERATOR_RELAY_STATE, 'Generator relay state', 'Shows whether the generator relay is on or off'),
    (LOW_BATTERY_TRIGGER, 'Low battery trigger', 'If true the battery is low and cannot be charged by fluid discharge')
]


class Backend(QObject):
    """! Backend logic to handle comms, UI, and remote device interaction.
    """
    REQUEST_ALL_DATA = "$RDTA"
    REQUEST_ALL_STATE = "$RSTT"
    ANSWER_ALL_DATA = "$ADTA"
    ANSWER_CONTROL_STATE = "$ACTL"
    REMOTE_READY = "$ARDY"

    def __init__(self):
        super(Backend, self).__init__()
        self.signals = BackendSignals()
        # Thread break guard condition, when true the thread finishes.
        self.stop = False

        self.error = QtCore.pyqtSignal(tuple)
        self.finished = QtCore.pyqtSignal()

        self.network_client = TCPClient()
        self.controller = Controller(self.network_client)
        self.db = TimescaleDB(MEASUREMENT_TYPES)

        self.dataRequestTimer = QTimer(self)
        self.dataRequestTimer.setInterval(1000)
        self.dataRequestTimer.timeout.connect(self._requestData)

        self.responseTimer = QTimer(self)
        self.responseTimer.setInterval(500)
        self.responseTimer.timeout.connect(self._sendAndReceive)
        self.remoteWatchdogTimer = QTimer(self)
        self.remoteWatchdogTimer.setInterval(15000)
        self.remoteWatchdogTimer.timeout.connect(self._setRemoteReady)
        self.pumpStateSource = StateSourceController(
            "Pump",
            self._updatePumpUI,
            self.controller.set_pump_remote,
            False)
        self.valveStateSource = StateSourceController(
            "Valve",
            self._updateValveUI,
            self.controller.set_valve_remote,
            False)
        self.solarStateSource = StateSourceController(
            "Solar",
            self._updateSolarUI,
            self.controller.set_solar_remote,
            False)
        self.generatorStateSource = StateSourceController(
            "Generator",
            self._updateGeneratorUI,
            self.controller.set_generator_remote,
            False)

    # @QtCore.pyqtSlot(bool)
    def _setRemoteReady(self):
        print("Watchdog timeout!")
        self.network_client.remote_ready = False

    # @QtCore.pyqtSlot(bool)
    def enablePump(self, state):
        self.pumpStateSource.setData(USER_SOURCE, state)

    # @QtCore.pyqtSlot(bool)
    def enableValve(self, state):
        self.valveStateSource.setData(USER_SOURCE, state)

    # @QtCore.pyqtSlot(bool)
    def enableSolar(self, state):
        self.solarStateSource.setData(USER_SOURCE, state)

    # @QtCore.pyqtSlot(bool)
    def enableGenerator(self, state):
        self.generatorStateSource.setData(USER_SOURCE, state)

    # @QtCore.pyqtSlot(bool)
    def enableManual(self, state):
        self.controller.set_manual(state)

    def _updatePumpUI(self, state):
        self.signals.updatePumpEnabled.emit(state)

    def _updateValveUI(self, state):
        self.signals.updateValveEnabled.emit(state)

    def _updateSolarUI(self, state):
        self.signals.updateSolarEnabled.emit(state)

    def _updateGeneratorUI(self, state):
        self.signals.updateGeneratorEnabled.emit(state)

    def isManual(self):
        return self.controller.manual

    def _createDataValues(self, message):
        data = dict()
        if message.headerStr == self.ANSWER_ALL_DATA:
            for i, dataStr in enumerate(message.dataList):
                data[i] = dataStr
        elif message.headerStr == self.ANSWER_CONTROL_STATE:
            for i, dataStr in enumerate(message.dataList):
                data[i + 7] = int(dataStr)
            self.pumpStateSource.setData(REMOTE_SOURCE, bool(data[PUMP_RELAY_STATE]))
            self.valveStateSource.setData(REMOTE_SOURCE, bool(data[VALVE_RELAY_STATE]))
            self.solarStateSource.setData(REMOTE_SOURCE, bool(data[SOLAR_RELAY_STATE]))
            self.generatorStateSource.setData(REMOTE_SOURCE, bool(data[GENERATOR_RELAY_STATE]))
        self.db.execute(self.db.insert_data, data)

    def _processMessages(self):
        message = self.network_client.pop_message()
        if message is not None:
            print(f"Current parsed msg: {message.headerStr}, data: {message.dataList}")
            self._createDataValues(message)

    @QtCore.pyqtSlot()
    def _requestData(self):
        self.network_client.add_to_send_queue(Message(self.REQUEST_ALL_DATA, []))
        self.network_client.add_to_send_queue(Message(self.REQUEST_ALL_STATE, []))

    @QtCore.pyqtSlot()
    def _sendAndReceive(self):
        self.network_client.send()
        if self.network_client.receive():
            self.remoteWatchdogTimer.start()
        self._processMessages()

    @QtCore.pyqtSlot()
    def run(self):
        self.responseTimer.start()
        self.remoteWatchdogTimer.start()
        self.dataRequestTimer.start()
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

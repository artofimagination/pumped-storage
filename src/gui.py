from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QMainWindow, QGridLayout, QApplication, QWidget
from PyQt5.QtWidgets import QGroupBox, QCheckBox, QLabel
from backend import Backend


# Main Qt UI window
class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        # Initialize worker thread related members.
        self.workerThread = QThread(self)
        self.worker = Backend()
        self.worker.signals.error.connect(self.sigint_handler)
        self.worker.signals.finished.connect(self.thread_complete)

        self.setMinimumSize(200, 100)
        mainLayout = self._createMainLayout()

        mainWidget = QWidget()
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)
        self.setWindowTitle("Pumped storage control")

        self.worker.moveToThread(self.workerThread)
        self.workerThread.finished.connect(self.worker.deleteLater)
        self.workerThread.started.connect(self.worker.run)
        self.workerThread.start()
        self.show()

    # @QtCore.pyqtSlot(bool)
    def _updateControlEnabled(self, enabled):
        self.enablePump.setEnabled(enabled)
        self.enableValve.setEnabled(enabled)
        self.enableSolar.setEnabled(enabled)
        self.enableGenerator.setEnabled(enabled)

    def _createMainLayout(self):
        layout = QGridLayout()
        controlGroupLayout = QGridLayout()
        enableManualLabel = QLabel("Enable Manual")
        self.enableManual = QCheckBox()
        enablePumpLabel = QLabel("Enable Pump")
        self.enablePump = QCheckBox()
        enableValveLabel = QLabel("Enable Valve")
        self.enableValve = QCheckBox()
        enableSolarLabel = QLabel("Enable Solar")
        self.enableSolar = QCheckBox()
        enableGeneratorLabel = QLabel("Enable Generator")
        self.enableGenerator = QCheckBox()
        self.enableManual.toggled.connect(self._updateControlEnabled)
        self.enableManual.toggled.connect(self.worker.enableManual)
        self.enablePump.toggled.connect(self.worker.enablePump)
        self.enableValve.toggled.connect(self.worker.enableValve)
        self.enableSolar.toggled.connect(self.worker.enableSolar)
        self.enableGenerator.toggled.connect(self.worker.enableGenerator)
        self.enableManual.setChecked(self.worker.isManual())
        self.worker.signals.updatePumpEnabled.connect(self.enablePump.setChecked)
        self.worker.signals.updateValveEnabled.connect(self.enableValve.setChecked)
        self.worker.signals.updateSolarEnabled.connect(self.enableSolar.setChecked)
        self.worker.signals.updateGeneratorEnabled.connect(self.enableGenerator.setChecked)
        controlGroupLayout.addWidget(enableManualLabel, 0, 0, 1, 1)
        controlGroupLayout.addWidget(self.enableManual, 0, 1, 1, 1)
        controlGroupLayout.addWidget(enablePumpLabel, 1, 0, 1, 1)
        controlGroupLayout.addWidget(self.enablePump, 1, 1, 1, 1)
        controlGroupLayout.addWidget(enableValveLabel, 2, 0, 1, 1)
        controlGroupLayout.addWidget(self.enableValve, 2, 1, 1, 1)
        controlGroupLayout.addWidget(enableSolarLabel, 3, 0, 1, 1)
        controlGroupLayout.addWidget(self.enableSolar, 3, 1, 1, 1)
        controlGroupLayout.addWidget(enableGeneratorLabel, 4, 0, 1, 1)
        controlGroupLayout.addWidget(self.enableGenerator, 4, 1, 1, 1)
        controlGroupBox = QGroupBox("Controls")
        controlGroupBox.setLayout(controlGroupLayout)
        layout.addWidget(controlGroupBox, 5, 0, 1, 1)
        return layout

    # Terminate UI and the threads appropriately.
    def sigint_handler(self):
        if self.worker is not None:
            self.worker.stop = True
            self.workerThread.quit()
            self.workerThread.wait()
        print("Exiting app through GUI")
        QApplication.quit()

    def thread_complete(self):
        print("Worker thread stopped...")

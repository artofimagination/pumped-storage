from PyQt5.QtCore import QThread, QUrl
from PyQt5.QtWidgets import QMainWindow, QGridLayout, QApplication, QWidget
from PyQt5.QtWidgets import QGroupBox, QCheckBox, QLabel
#from PyQt5.QtWebKitWidgets import QWebView
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

        #desktop = QApplication.desktop()
        #screenRect = desktop.screenGeometry()
        #self.resize(screenRect.width(), screenRect.height())
        self.worker.moveToThread(self.workerThread)
        self.workerThread.finished.connect(self.worker.deleteLater)
        self.workerThread.started.connect(self.worker.run)
        self.workerThread.start()
        self.show()

    def _createMainLayout(self):
        layout = QGridLayout()
        # view = QWebView()
        # view.setUrl(QUrl("http://172.17.0.1:3000"))
        # layout.addWidget(view, 0, 0, 4, 1)
        controlGroupLayout = QGridLayout()
        enablePumpLabel = QLabel("Enable Pump")
        enablePump = QCheckBox()
        enableValveLabel = QLabel("Enable Valve")
        enableValve = QCheckBox()
        enableSolarLabel = QLabel("Enable Solar")
        enableSolar = QCheckBox()
        enableGeneratorLabel = QLabel("Enable Generator")
        enableGenerator = QCheckBox()
        enablePump.toggled.connect(self.worker.enablePump)
        enableValve.toggled.connect(self.worker.enableValve)
        enableSolar.toggled.connect(self.worker.enableSolar)
        enableGenerator.toggled.connect(self.worker.enableGenerator)
        controlGroupLayout.addWidget(enablePumpLabel, 0, 0, 1, 1)
        controlGroupLayout.addWidget(enablePump, 0, 1, 1, 1)
        controlGroupLayout.addWidget(enableValveLabel, 1, 0, 1, 1)
        controlGroupLayout.addWidget(enableValve, 1, 1, 1, 1)
        controlGroupLayout.addWidget(enableSolarLabel, 2, 0, 1, 1)
        controlGroupLayout.addWidget(enableSolar, 2, 1, 1, 1)
        controlGroupLayout.addWidget(enableGeneratorLabel, 3, 0, 1, 1)
        controlGroupLayout.addWidget(enableGenerator, 3, 1, 1, 1)
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

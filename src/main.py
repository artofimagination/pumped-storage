

import sys

from PyQt5.QtWidgets import QApplication
from gui import MainWindow


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    app.aboutToQuit.connect(window.sigint_handler)

    sys.exit(app.exec_())
    print("Exiting application...")

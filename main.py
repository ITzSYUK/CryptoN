from gui import MainWindow
from PyQt6.QtWidgets import QApplication
import sys


def main_linux():
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main_linux()

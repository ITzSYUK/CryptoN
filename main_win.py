from gui import MainWindow
from PyQt6.QtWidgets import QApplication
import sys
from vhd_manager import VHDManager


def main_win():
    # Настройки виртуального диска
    vhd_path = "C:\\VHD\\CertsVirtualDisk.vhd"
    disk_size = 1024  # Размер в MB

    # Создание и подключение виртуального диска
    with VHDManager(vhd_path, disk_size) as vhd:
        print(f"Виртуальный диск {vhd} подключен.")
        app = QApplication(sys.argv)
        mainWindow = MainWindow()
        mainWindow.show()
        sys.exit(app.exec())


if __name__ == '__main__':
    main_win()

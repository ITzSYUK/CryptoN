import os
import subprocess
from smb.SMBConnection import SMBConnection
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, QPushButton, QLineEdit, QHBoxLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
import sys


# Класс ShowInstalledLogListCertificate нужен для запуска окна со списком логов установленных сертификатов в отдельном потоке. Это нужно для того, чтобы окно логов открывалось до начала работы метода по установке сертификатов.
class ShowInstalledLogListCertificate(QThread):
    certificate_installed = pyqtSignal(str)

    def __init__(self, password=None):
        super().__init__()
        self.password = password

    def run(self):
        install_certificates = Run_Crypton_Functions(
            2, self.certificate_installed)
        install_certificates.run_crypton_show_list_sertificate()


class DetailWindow(QWidget):
    # Создание атрибута сигнала
    certificate_installed = pyqtSignal(str)

    def __init__(self, type=0, password=None):
        super().__init__()
        self.type = type
        self.password = password
        if self.type == 1:
            self.setup_one_sertificate()
        if self.type == 2:
            self.setup_all_sertificate(password)

    def setup_one_sertificate(self):
        layout = QVBoxLayout()
        self.listWidget = QListWidget()
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.start_button = QPushButton('Установить сертификат')
        self.listWidget.setFont(self.font())
        self.label.setFont(self.font())
        self.label.setWordWrap(True)
        layout.addWidget(self.listWidget)
        layout.addWidget(self.start_button)
        layout.addWidget(self.label)
        items = Run_Crypton_Functions().run_crypton_show_list_sertificate()

        for item in items:
            QListWidgetItem(item, self.listWidget)
        self.listWidget.itemDoubleClicked.connect(
            self.download_one_sertificate)
        self.start_button.clicked.connect(self.download_one_sertificate)
        self.setLayout(layout)
        self.setWindowTitle('Установка сертификата')
        self.setFixedSize(500, 300)

        self.certificate_installed.connect(self.update_label)

    def download_one_sertificate(self, item=None):
        selected_item = self.listWidget.selectedItems()
        if selected_item:
            download_sertificate_by_button = Run_Crypton_Functions(
                1, self.certificate_installed)
            download_sertificate_by_button.run_crypton_show_list_sertificate(
                selected_item[0].text())
        elif item:
            download_sertificate_by_double_click = Run_Crypton_Functions(
                1, self.certificate_installed)
            download_sertificate_by_double_click.run_crypton_show_list_sertificate(
                item.text())
        else:
            self.certificate_installed.emit("Сертификат не выбран")

    def setup_all_sertificate(self, password=None):
        self.log_window = QWidget()
        layout = QVBoxLayout()
        self.log_list = QListWidget()
        layout.addWidget(self.log_list)
        self.log_window.setLayout(layout)
        self.log_window.setWindowTitle('Установка сертификатов')
        self.log_window.setFixedSize(600, 300)

        self.certificate_installed.connect(
            self.update_list_for_setup_all_certificates)

        if password == "123":
            # self.log_window.show()
            # install_sertificates = Run_Crypton_Functions(
            #     2, self.certificate_installed)
            # install_sertificates.run_crypton_show_list_sertificate()
            self.log_window.show()
            # Создается новый экземпляр потока для открытия окна со списком логов установленных сертификатов
            self.thread_log_list_certificates = ShowInstalledLogListCertificate(
                password)
            self.thread_log_list_certificates.certificate_installed.connect(
                self.update_list_for_setup_all_certificates)
            self.thread_log_list_certificates.start()

    @pyqtSlot(str)
    def update_label(self, message):
        self.label.setText(message)

    @pyqtSlot(str)
    def update_list_for_setup_all_certificates(self, message):
        self.log_list.addItem(message)

    def font(self):
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        return font


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.listWidget = QListWidget()

        self.listWidget.setFont(self.font())

        items = ["Установить отдельный сертификат",
                 "Установить все сертификаты", "Удалить сертификат"]
        for item in items:
            QListWidgetItem(item, self.listWidget)
        self.listWidget.itemDoubleClicked.connect(self.showDetailWindow)
        self.layout.addWidget(self.listWidget)
        self.setLayout(self.layout)
        self.setWindowTitle(
            'Специальный установщик криптографических алгоритмов')
        self.setFixedSize(500, 200)

        # Создание пустого множества для проверки нажатия на элементы списка
        self.clicked_items = set()

    def font(self):
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        return font

    def authorize_widget(self):
        # горизонтальная настройка виджетов
        self.hbox = QHBoxLayout()
        self.label = QLabel('Введите пароль:')
        self.enterPasswordLine = QLineEdit()
        self.button = QPushButton('Продолжить')
        self.label.setFont(self.font())
        self.enterPasswordLine.setFont(self.font())
        self.button.setFont(self.font())
        self.hbox.addWidget(self.label)
        self.hbox.addWidget(self.enterPasswordLine)
        self.hbox.addWidget(self.button)
        self.layout.addLayout(self.hbox)

    def showDetailWindow(self, item):
        if item.text() == "Установить отдельный сертификат":
            self.detailWindow = DetailWindow(1)
            self.detailWindow.show()
        # Условие, при котором проверяется, была ли нажата кнопка "Установить все сертификаты" и проверяется наличие элемента в множестве clicked_items
        if item.text() == "Установить все сертификаты" and len(self.clicked_items) == 0:
            self.authorize_widget()
            # Получение флагов текущего элемента item, которые указывают на состояние этого элемента. Qt.ItemFlag.ItemIsEnabled означает, что элемент доступен для взаимодействия с ним. Оператор '~' означает побитовое отрицание, инвертируя флаг взаимодействия с элементом
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            # Добавление элемента в множество clicked_items, чтобы при следующем нажатии на элемент "Установить все сертификаты" проверить его наличие в множестве
            self.clicked_items.add(item.text())
            self.button.clicked.connect(self.password_verification)

    def password_verification(self):
        input_password = self.enterPasswordLine.text()
        self.password_checker = DetailWindow(2, input_password)
        # self.password_checker.setup_all_sertificate(input_password)


class Run_Crypton_Functions:
    def __init__(self, type=0, signal=None):
        self.type = type
        self.signal = signal

    def run_crypton_show_list_sertificate(self, surname=None):
        smb_connect = CRYPTON(
            server_ip="192.168.0.104",
            share_name="OS",
            folder_path="эцппример",
            username="Dovakin23",
            password="1337",
            client_machine_name="client_machine_name",
            server_name="itzsy-pc",
            domain_name="WORKGROUP",
            local_download_path="/home/itzsy/Downloads",
            surname=surname,
            signal=self.signal
        )
        if self.type == 1:
            smb_connect.search_and_download()
        if self.type == 2:
            smb_connect.install_all_certificates()
            # smb_connect.close_connection()
        smb_connect.list_folders()
        return smb_connect.list_folders()


class CRYPTON:
    def __init__(self, server_ip, share_name, folder_path, username, password, client_machine_name, server_name, domain_name, local_download_path, surname=None, signal=None):
        self.server_ip = server_ip
        self.share_name = share_name
        self.folder_path = folder_path
        self.username = username
        self.password = password
        self.client_machine_name = client_machine_name
        self.server_name = server_name
        self.domain_name = domain_name
        self.local_download_path = local_download_path
        self.surname = surname
        self.signal = signal

        if not os.path.exists(self.local_download_path):
            os.makedirs(self.local_download_path)

        self.conn = SMBConnection(self.username, self.password, self.client_machine_name,
                                  self.server_name, domain=self.domain_name, use_ntlm_v2=True)
        assert self.conn.connect(self.server_ip, 139)

    def search_and_download(self, folder_path=None):
        if folder_path is None:
            folder_path = self.folder_path
        local_dir_path = self.local_download_path

        files = self.conn.listPath(self.share_name, folder_path)
        for file in files:
            if file.filename not in [".", ".."]:
                remote_file_path = os.path.join(folder_path, file.filename)
                if file.isDirectory:
                    if file.filename.startswith(self.surname):
                        self.download_directory_from_smb(
                            remote_file_path, local_dir_path)
                    else:
                        self.search_and_download(remote_file_path)

    def download_directory_from_smb(self, remote_dir_path, local_dir_path):
        if not os.path.exists(local_dir_path):
            os.makedirs(local_dir_path)

        files = self.conn.listPath(self.share_name, remote_dir_path)
        for file in files:
            if file.filename not in [".", ".."]:
                remote_file_path = os.path.join(remote_dir_path, file.filename)
                local_file_name = file.filename
                local_file_path = os.path.join(local_dir_path, local_file_name)
                if file.isDirectory:
                    self.download_directory_from_smb(
                        remote_file_path, local_file_path)
                else:
                    with open(local_file_path, 'wb') as local_file:
                        self.conn.retrieveFile(
                            self.share_name, remote_file_path, local_file)
                        print(f"Downloaded: {local_file_path}")
                    if file.filename.endswith('.cer'):
                        self.setup_sertificate(
                            local_file_path, local_file_name)

    def setup_sertificate(self, local_file_path, local_file_name):
        with os.popen('csptest -keyset -enum_cont -fqcn -verifyc') as stream:
            output = stream.read()

        lines = output.split('\n')

        matching_lines = [
            line for line in lines if line.startswith(rf"\\.\HDIMAGE\{local_file_name[0:6]}")]

        try:
            result = subprocess.run(f"certmgr -inst -file '{local_file_path}' -cont '{matching_lines[0]}'",  # noqa
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            # Если код результата равен нулю, то в сигнал записывается сообщение об успешной установке сертификата
            if result.returncode == 0:
                local_file_name_strip = local_file_name.rstrip('.cer')
                self.signal.emit(
                    f"Сертификат пользователя {local_file_name_strip} успешно установлен.")
        except IndexError as e:
            self.signal.emit(f"Не удалось связать сертификат пользователя {local_file_name} с контейнером. Ошибка: {e}")  # noqa
        except subprocess.CalledProcessError as e:
            self.signal.emit(f"Ошибка при установке сертификата {local_file_name}. Код ошибки: {e.returncode}. Сообщение: {e.stderr}")  # noqa

    def install_all_certificates(self, folder_path=None):
        if folder_path is None:
            folder_path = self.folder_path
        local_dir_path = self.local_download_path

        files = self.conn.listPath(self.share_name, folder_path)
        for file in files:
            if file.filename not in [".", ".."]:
                remote_file_path = os.path.join(folder_path, file.filename)
                if file.isDirectory:
                    self.download_directory_from_smb(
                        remote_file_path, local_dir_path)

    def close_connection(self):
        self.conn.close()

    def list_folders(self):
        folders = []
        files = self.conn.listPath(self.share_name, self.folder_path)
        for file in files:
            if file.filename not in [".", ".."] and file.isDirectory:
                folders.append(file.filename)
        return folders


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())

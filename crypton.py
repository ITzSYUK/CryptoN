import os
import subprocess
from smb.SMBConnection import SMBConnection
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, QPushButton, QLineEdit, QHBoxLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QTimer
import sys
import io


# Класс ShowInstalledLogListCertificate нужен для запуска окна со списком логов установленных сертификатов в отдельном потоке. Это нужно для того, чтобы окно логов открывалось до начала работы метода по установке сертификатов.
class ShowInstalledLogListCertificate(QThread):
    certificate_installed = pyqtSignal(str)

    def __init__(self, password=None):
        super().__init__()
        self.password = password

    def run(self):
        try:
            install_certificates = Run_Crypton_Functions(
                2, self.certificate_installed)
            install_certificates.smbconnect_to_crypton()
        finally:
            self.quit()


class DetailWindow(QWidget):
    # Создание атрибута сигнала
    certificate_installed = pyqtSignal(str)

    def __init__(self, type=0, password=None):
        super().__init__()
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.perform_resize)
        self.type = type
        self.password = password
        if self.type == 1:
            self.setup_one_sertificate()
        if self.type == 2:
            self.setup_all_sertificate(password)
        if self.type == 3:
            self.delete_certificate_window()

    def setup_one_sertificate(self):
        layout = QVBoxLayout()
        self.listWidget = QListWidget()
        self.listWidget.setFixedHeight(220)
        self.search_certificate_line = QLineEdit()
        self.listWidget.setFont(self.font())
        self.search_certificate_line.setPlaceholderText("ПОИСК: Введите свою фамилию")  # noqa
        layout.addWidget(self.search_certificate_line)
        layout.addWidget(self.listWidget)
        items = Run_Crypton_Functions().smbconnect_to_crypton()

        authorize_setup_cert_layout = QHBoxLayout()
        self.authorize_setup_cert_line = QLineEdit()
        self.start_button = QPushButton('Установить сертификат')
        password_label = QLabel("Пароль: ")
        authorize_setup_cert_layout.addWidget(password_label)
        authorize_setup_cert_layout.addWidget(self.authorize_setup_cert_line)
        authorize_setup_cert_layout.addWidget(self.start_button)
        self.authorize_setup_cert_line.setFont(self.font())
        self.start_button.setFont(self.font())
        password_label.setFont(self.font())
        layout.addLayout(authorize_setup_cert_layout)

        # Создание laouyt для вывода уведомлений об установке сертификатов
        notify_layout = QVBoxLayout()
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFont(self.font())
        self.label.setWordWrap(True)
        self.label.setMaximumHeight(102)
        notify_layout.addWidget(self.label)
        layout.addLayout(notify_layout)

        for item in items:
            QListWidgetItem(item, self.listWidget)
        self.listWidget.itemDoubleClicked.connect(
            self.download_one_sertificate)
        self.start_button.clicked.connect(self.download_one_sertificate)
        self.setLayout(layout)
        self.setWindowTitle('Установка сертификата')
        self.setFixedWidth(600)

        self.certificate_installed.connect(self.update_label)
        self.search_certificate_line.textChanged.connect(
            self.filter_certificate_list)

    def download_one_sertificate(self, item=None, password=None):
        password = self.authorize_setup_cert_line.text()
        verification_password = Run_Crypton_Functions(
            5).smbconnect_to_crypton()
        if password == verification_password:
            selected_item = self.listWidget.selectedItems()
            if selected_item:
                download_sertificate_by_button = Run_Crypton_Functions(
                    1, self.certificate_installed)
                download_sertificate_by_button.smbconnect_to_crypton(
                    selected_item[0].text())
            elif item:
                download_sertificate_by_double_click = Run_Crypton_Functions(
                    1, self.certificate_installed)
                download_sertificate_by_double_click.smbconnect_to_crypton(
                    item.text())
            else:
                self.certificate_installed.emit("Сертификат не выбран")
        elif password == "":
            self.certificate_installed.emit(
                "Для начала установки введите пароль")
        else:
            self.certificate_installed.emit("Неверный пароль")

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

        verification_password = Run_Crypton_Functions(
            5).smbconnect_to_crypton()
        if password == verification_password:
            self.log_window.show()
            # Создается новый экземпляр потока для открытия окна со списком логов установленных сертификатов
            self.thread_log_list_certificates = ShowInstalledLogListCertificate(
                password)
            self.thread_log_list_certificates.certificate_installed.connect(
                self.update_list_for_setup_all_certificates)
            self.thread_log_list_certificates.start()

    def delete_certificate_window(self):
        self.del_cert_window = QWidget()
        layout = QVBoxLayout()
        self.del_cert_list = QListWidget()
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)
        self.delete_button = QPushButton('Удалить сертификат')
        self.del_cert_list.setFont(self.font())
        self.label.setFont(self.font())
        self.delete_button.setFont(self.font())
        layout.addWidget(self.del_cert_list)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.label)
        cert_list = Run_Crypton_Functions(
            3).smbconnect_to_crypton()
        cert_list.pop()
        for item in cert_list:
            QListWidgetItem(item, self.del_cert_list)
        self.del_cert_list.itemDoubleClicked.connect(
            self.delete_certificate_slot)
        self.delete_button.clicked.connect(self.delete_certificate_slot)
        self.del_cert_window.setLayout(layout)
        self.del_cert_window.setWindowTitle('Удаление сертификатов')
        self.del_cert_window.setFixedSize(600, 300)

        self.del_cert_window.show()

        self.certificate_installed.connect(self.update_label)

    def delete_certificate_slot(self, item=None):
        selected_item = self.del_cert_list.selectedItems()
        if selected_item:
            delete_sertificate_by_button = Run_Crypton_Functions(
                4, self.certificate_installed)
            delete_sertificate_by_button.smbconnect_to_crypton(
                selected_item[0].text())
            self.remove_certificate_name_from_list()
        elif item:
            delete_sertificate_by_double_click = Run_Crypton_Functions(
                4, self.certificate_installed)
            delete_sertificate_by_double_click.smbconnect_to_crypton(
                item.text())
            self.remove_certificate_name_from_list()
        else:
            self.certificate_installed.emit("Сертификат не выбран")

    def remove_certificate_name_from_list(self):
        selected_certificate = self.del_cert_list.currentItem()
        self.del_cert_list.takeItem(
            self.del_cert_list.row(selected_certificate))

    def filter_certificate_list(self):
        found_cert_name = self.search_certificate_line.text().lower()
        for i in range(self.listWidget.count()):
            found_cert = self.listWidget.item(i)
            found_cert.setHidden(
                found_cert_name not in found_cert.text().lower())

    @pyqtSlot(str)
    def update_label(self, message):
        self.label.setText(message)
        self.update_timer.start(100)

    def perform_resize(self):
        self.adjustSize()

    @pyqtSlot(str)
    def update_list_for_setup_all_certificates(self, message):
        self.log_list.addItem(message)

    def font(self):
        font = QFont()
        font.setBold(True)
        font.setPointSize(11)
        return font


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.main_window_certificates_layout = QVBoxLayout()
        self.listWidget = QListWidget()
        self.listWidget.setFixedSize(550, 150)

        self.listWidget.setFont(self.font())

        items = ["Установить отдельный сертификат",
                 "Установить все сертификаты", "Удалить сертификат"]
        for item in items:
            QListWidgetItem(item, self.listWidget)
        self.listWidget.itemDoubleClicked.connect(self.showDetailWindow)
        self.main_window_certificates_layout.addWidget(self.listWidget)
        self.setLayout(self.main_window_certificates_layout)
        self.setWindowTitle(
            'Специальный установщик криптографических алгоритмов')
        self.setFixedWidth(570)

        # Создание пустого множества для проверки нажатия на элементы списка главного окна
        self.clicked_items_main_window = set()

    def font(self):
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        return font

    def authorize_widget(self):
        # горизонтальная настройка виджетов
        self.authorize_widget_layout = QHBoxLayout()
        self.label = QLabel('Пароль установки всех сертификатов:')
        self.enterPasswordLine = QLineEdit()
        self.authorize_button = QPushButton('Продолжить')
        self.label.setFont(self.font())
        self.enterPasswordLine.setFont(self.font())
        self.authorize_button.setFont(self.font())
        # self.hbox.addWidget(self.label)
        self.authorize_widget_layout.addWidget(self.enterPasswordLine)
        self.authorize_widget_layout.addWidget(self.authorize_button)
        self.main_window_certificates_layout.addWidget(self.label)
        self.main_window_certificates_layout.addLayout(
            self.authorize_widget_layout)

    def showDetailWindow(self, item):
        if item.text() == "Установить отдельный сертификат":
            # self.authorize_widget(1)
            # item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            # self.clicked_items_main_window.add(item.text())
            # self.authorize_button.clicked.connect(
            #     self.install_one_cert_password_verification)
            self.detailWindow = DetailWindow(1)
            self.detailWindow.show()
        # Условие, при котором проверяется, была ли нажата кнопка "Установить все сертификаты" и проверяется наличие элемента в множестве clicked_items
        if item.text() == "Установить все сертификаты" and len(self.clicked_items_main_window) in [0, 1]:
            self.authorize_widget()
            # Получение флагов текущего элемента item, которые указывают на состояние этого элемента. Qt.ItemFlag.ItemIsEnabled означает, что элемент доступен для взаимодействия с ним. Оператор '~' означает побитовое отрицание, инвертируя флаг взаимодействия с элементом
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            # Добавление элемента в множество clicked_items, чтобы при следующем нажатии на элемент "Установить все сертификаты" проверить его наличие в множестве
            self.clicked_items_main_window.add(item.text())
            self.authorize_button.clicked.connect(
                self.install_all_certs_password_verification)
        if item.text() == "Удалить сертификат":
            self.detailWindow = DetailWindow(3)

    # def install_one_cert_password_verification(self):
    #     input_password = self.enterPasswordLine.text()
    #     self.password_checker = DetailWindow(1, input_password)
    #     self.password_checker.show()

    def install_all_certs_password_verification(self):
        input_password = self.enterPasswordLine.text()
        self.password_checker = DetailWindow(2, input_password)


class Run_Crypton_Functions:
    def __init__(self, type=0, signal=None):
        self.type = type
        self.signal = signal

    def smbconnect_to_crypton(self, surname=None):
        with CRYPTON(
            server_ip="172.25.87.3",
            share_name="обменник поликлиники",
            folder_path="distr/certificates",
            username="cert_user",
            password="cert2024",
            client_machine_name="client_machine_name",
            server_name="server-terminal",
            domain_name="SAMBA",
            local_download_path="/var/opt/cprocsp/keys/user/",
            password_file_path="/distr/certs_password.txt",
            surname=surname,
            signal=self.signal
        ) as smb_connect:
            if self.type == 1:
                smb_connect.search_and_download()
            if self.type == 2:
                smb_connect.install_all_certificates()
            if self.type == 3:
                return smb_connect.list_of_installed_certificates()
            if self.type == 4:
                smb_connect.delete_certificate_method(surname)
            if self.type == 5:
                return smb_connect.open_password_file()
            return smb_connect.list_folders()


class CRYPTON:
    def __init__(self, server_ip, share_name, folder_path, username, password, client_machine_name, server_name, domain_name, local_download_path, password_file_path, surname=None, signal=None):
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
        self.password_file_path = password_file_path

        if not os.path.exists(self.local_download_path):
            os.makedirs(self.local_download_path)

    def __enter__(self):
        # Здесь происходит подключение к серверу и создание объекта SMBConnection с использованием контекстного менеджера в классе Run_Crypton_Functions
        self.conn = SMBConnection(self.username, self.password, self.client_machine_name,
                                  self.server_name, domain=self.domain_name, use_ntlm_v2=True)
        assert self.conn.connect(self.server_ip, 139)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Здесь происходит отключение от сервера
        self.conn.close()

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
        with os.popen('/opt/cprocsp/bin/amd64/csptest -keyset -enum_cont -fqcn -verifyc') as stream:
            output = stream.read()

        lines = output.split('\n')

        matching_lines = [
            line for line in lines if line.startswith(rf"\\.\HDIMAGE\{local_file_name[0:6]}")]

        try:
            result = subprocess.run(f"/opt/cprocsp/bin/amd64/certmgr -inst -file '{local_file_path}' -cont '{matching_lines[0]}'",  # noqa
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

    def list_of_installed_certificates(self):
        with os.popen("/opt/cprocsp/bin/amd64/certmgr -list | grep 'Субъект' | grep 'CN=' | sed -n 's/.*CN=//p'") as stream:
            output = stream.read()

        list_of_installed_certificates = output.split('\n')
        list_of_installed_certificates_with_numbers = []
        number_of_lines = 1
        for line in list_of_installed_certificates:
            line = f"{number_of_lines}: {line}"
            number_of_lines += 1
            list_of_installed_certificates_with_numbers.append(line)
        return list_of_installed_certificates_with_numbers

    def delete_certificate_method(self, surname):
        user_name = surname.split(": ", 1)[1]

        with os.popen(f"/opt/cprocsp/bin/amd64/certmgr -list | awk -v user=\"{user_name}\" '$0 ~ user {{found=1}} found && /Идентификатор ключа/ {{print $NF; exit}}'") as stream:  # noqa
            key_identifier = stream.read()

        # result = os.system(f"certmgr -delete -store uMy -keyid {key_identifier}")  # noqa

        # if result == 0:
        #     self.signal.emit(f"Сертификат пользователя {user_name} успешно удален.")  # noqa

        try:
            result = subprocess.run(f"/opt/cprocsp/bin/amd64/certmgr -delete -store uMy -keyid {key_identifier}",  # noqa
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )
            # Если код результата равен нулю, то в сигнал записывается сообщение об успешной установке сертификата
            if result.returncode == 0:
                self.signal.emit(
                    f"Сертификат пользователя {user_name} успешно удален.")
        except subprocess.CalledProcessError as e:
            self.signal.emit(f"Ошибка при удалении сертификата {user_name}. Код ошибки: {e.returncode}. Сообщение: {e.stderr}")  # noqa

    def close_connection(self):
        self.conn.close()

    def list_folders(self):
        folders = []
        files = self.conn.listPath(self.share_name, self.folder_path)
        for file in files:
            if file.filename not in [".", ".."] and file.isDirectory:
                folders.append(file.filename)
        return folders

    def open_password_file(self):
        # Чтение файла напрямую в память
        password_obj = io.BytesIO()
        self.conn.retrieveFile(
            self.share_name, self.password_file_path, password_obj)
        password_obj.seek(0)
        # Декодирование объекта io.BytesIO в строку с удалением переноса строки
        password = password_obj.read().decode().rstrip('\n')
        return password


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())

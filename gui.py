from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, QPushButton, QLineEdit, QHBoxLayout
from PyQt6.QtGui import QFont
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QTimer
from smb_connection import Run_Crypton_Functions
import crypton_database as db


class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
            QLineEdit {
                min-width: 400px;
                max-width: 400px;
                height: 30px;
            },
        """)
        self.setupUi()
        self.show()

    def setupUi(self):
        self.setWindowTitle('Настройки')
        self.resize(500, 300)
        placeholder = db.DatabaseApp().select_from_db()

        main_layout = QVBoxLayout()
        # IP Layout
        ip_layout = QHBoxLayout()
        self.ip_line_text = QLabel('IP:')
        self.ip_line_edit = QLineEdit()
        self.ip_line_edit.setPlaceholderText(placeholder[0][1])
        ip_layout.addWidget(self.ip_line_text)
        ip_layout.addWidget(self.ip_line_edit)

        # Username Layout
        username_layout = QHBoxLayout()
        self.username_line_text = QLabel('Username:')
        self.username_line_edit = QLineEdit()
        self.username_line_edit.setPlaceholderText(placeholder[0][2])
        username_layout.addWidget(self.username_line_text)
        username_layout.addWidget(self.username_line_edit)

        # Password Layout
        password_layout = QHBoxLayout()
        self.password_line_text = QLabel('Password:')
        self.password_line_edit = QLineEdit()
        self.password_line_edit.setPlaceholderText(placeholder[0][3])
        password_layout.addWidget(self.password_line_text)
        password_layout.addWidget(self.password_line_edit)

        # Domain name Layout
        domain_name_layout = QHBoxLayout()
        self.domain_name_line_text = QLabel('Domain name:')
        self.domain_name_line_edit = QLineEdit()
        self.domain_name_line_edit.setPlaceholderText(placeholder[0][4])
        domain_name_layout.addWidget(self.domain_name_line_text)
        domain_name_layout.addWidget(self.domain_name_line_edit)

        # Server name Layout
        server_name_layout = QHBoxLayout()
        self.server_name_line_text = QLabel('Server name:')
        self.server_name_line_edit = QLineEdit()
        self.server_name_line_edit.setPlaceholderText(placeholder[0][5])
        server_name_layout.addWidget(self.server_name_line_text)
        server_name_layout.addWidget(self.server_name_line_edit)

        # Sharename Layout
        sharename_layout = QHBoxLayout()
        self.sharename_line_text = QLabel('Sharename:')
        self.sharename_line_edit = QLineEdit()
        self.sharename_line_edit.setPlaceholderText(placeholder[0][6])
        sharename_layout.addWidget(self.sharename_line_text)
        sharename_layout.addWidget(self.sharename_line_edit)

        # Folder path Layout
        folder_path_layout = QHBoxLayout()
        self.folder_path_line_text = QLabel('Folder path:')
        self.folder_path_line_edit = QLineEdit()
        self.folder_path_line_edit.setPlaceholderText(placeholder[0][7])
        folder_path_layout.addWidget(self.folder_path_line_text)
        folder_path_layout.addWidget(self.folder_path_line_edit)

        # Save Button Layout
        save_button_layout = QHBoxLayout()
        self.save_button = QPushButton('Сохранить')
        self.save_button.setFixedSize(300, 30)
        save_button_layout.addWidget(self.save_button)

        self.save_button.clicked.connect(self.save_settings)

        main_layout.addLayout(ip_layout)
        main_layout.addLayout(username_layout)
        main_layout.addLayout(password_layout)
        main_layout.addLayout(domain_name_layout)
        main_layout.addLayout(server_name_layout)
        main_layout.addLayout(sharename_layout)
        main_layout.addLayout(folder_path_layout)
        main_layout.addLayout(save_button_layout)

        self.setLayout(main_layout)

    def save_settings(self):
        db.DatabaseApp().save_to_db(
            self.ip_line_edit.text(),
            self.username_line_edit.text(),
            self.password_line_edit.text(),
            self.domain_name_line_edit.text(),
            self.server_name_line_edit.text(),
            self.sharename_line_edit.text(),
            self.folder_path_line_edit.text(),
        )
        self.close()


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
                 "Установить все сертификаты", "Удалить сертификат", "Настройки"]
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
        self.authorize_widget_layout.addWidget(self.enterPasswordLine)
        self.authorize_widget_layout.addWidget(self.authorize_button)
        self.main_window_certificates_layout.addWidget(self.label)
        self.main_window_certificates_layout.addLayout(
            self.authorize_widget_layout)

    def showDetailWindow(self, item):
        if item.text() == "Установить отдельный сертификат":
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
        if item.text() == "Настройки":
            self.settingsWindow = SettingsWindow()
            self.settingsWindow.show()

    def install_all_certs_password_verification(self):
        input_password = self.enterPasswordLine.text()
        self.password_checker = DetailWindow(2, input_password)

    def closeEvent(self, event):
        # Закрываем соединение с базой данных перед закрытием приложения
        self.close_conn = db.DatabaseApp().close_connection()
        event.accept()  # Завершаем закрытие окна

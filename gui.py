from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel, QPushButton, QLineEdit, QHBoxLayout, QComboBox, QMessageBox
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QTimer
from smb_connection_linux import Run_Crypton_Functions
import crypton_database_linux as db


class MessageWindows(QWidget):
    def __init__(self):
        super().__init__()
        self.show_warning_message_ui
        self.show_success_message_ui

    def show_warning_message_ui(self, message):
        self.message_box = QMessageBox()
        self.message_box.warning(self, 'Ошибка', message)
        self.message_box.setWindowTitle('Сообщение')

    def show_success_message_ui(self, message):
        self.message_box = QMessageBox()
        self.message_box.information(self, 'Успех', message)
        self.message_box.setWindowTitle('Сообщение')


class SettingsWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.notify_message = MessageWindows()
        self.setStyleSheet("""
            QLineEdit {
                min-width: 500px;
                max-width: 500px;
                height: 30px;
            },
        """)
        self.setupUi()
        self.show()

    def setupUi(self):
        self.setWindowTitle('Настройки')
        self.resize(500, 300)

        main_layout = QVBoxLayout()

        # List of connections
        list_of_connections_layout = QHBoxLayout()
        font_for_list_of_connections = QFont()
        font_for_list_of_connections.setPointSize(10)
        self.list_of_connections_widget = QComboBox(self)
        self.list_of_connections_widget.setFont(font_for_list_of_connections)
        list_of_connections_layout.addWidget(self.list_of_connections_widget)
        self.update_combobox_list()
        self.list_of_connections_widget.currentIndexChanged.connect(
            self.set_current_connection)

        # Name of connection Layout
        name_layout = QHBoxLayout()
        self.name_line_text = QLabel('Name of connection:')
        self.name_line_edit = QLineEdit()
        self.name_line_edit.setPlaceholderText("Название подключения")
        name_layout.addWidget(self.name_line_text)
        name_layout.addWidget(self.name_line_edit)

        # IP Layout
        ip_layout = QHBoxLayout()
        self.ip_line_text = QLabel('IP:')
        self.ip_line_edit = QLineEdit()
        ip_layout.addWidget(self.ip_line_text)
        ip_layout.addWidget(self.ip_line_edit)

        # Username Layout
        username_layout = QHBoxLayout()
        self.username_line_text = QLabel('Username:')
        self.username_line_edit = QLineEdit()
        username_layout.addWidget(self.username_line_text)
        username_layout.addWidget(self.username_line_edit)

        # Password Layout
        password_layout = QHBoxLayout()
        self.password_line_text = QLabel('Password:')
        self.password_line_edit = QLineEdit()
        password_layout.addWidget(self.password_line_text)
        password_layout.addWidget(self.password_line_edit)

        # Domain name Layout
        domain_name_layout = QHBoxLayout()
        self.domain_name_line_text = QLabel('Domain name:')
        self.domain_name_line_edit = QLineEdit()
        domain_name_layout.addWidget(self.domain_name_line_text)
        domain_name_layout.addWidget(self.domain_name_line_edit)

        # Server name Layout
        server_name_layout = QHBoxLayout()
        self.server_name_line_text = QLabel('Server name:')
        self.server_name_line_edit = QLineEdit()
        server_name_layout.addWidget(self.server_name_line_text)
        server_name_layout.addWidget(self.server_name_line_edit)

        # Sharename Layout
        sharename_layout = QHBoxLayout()
        self.sharename_line_text = QLabel('Sharename:')
        self.sharename_line_edit = QLineEdit()
        sharename_layout.addWidget(self.sharename_line_text)
        sharename_layout.addWidget(self.sharename_line_edit)

        # Folder path Layout
        remote_certs_path_layout = QHBoxLayout()
        self.remote_certs_path_line_text = QLabel('Remote certs path:')
        self.remote_certs_path_line_edit = QLineEdit()
        remote_certs_path_layout.addWidget(self.remote_certs_path_line_text)
        remote_certs_path_layout.addWidget(self.remote_certs_path_line_edit)

        # Local Download Path Layout
        local_download_path_layout = QHBoxLayout()
        self.local_download_path_line_text = QLabel('Local certs path:')
        self.local_download_path_line_edit = QLineEdit()
        local_download_path_layout.addWidget(
            self.local_download_path_line_text)
        local_download_path_layout.addWidget(
            self.local_download_path_line_edit)

        # Remote password file path Layout
        remote_password_path_layout = QHBoxLayout()
        self.remote_password_path_line_text = QLabel('Password file path:')
        self.remote_password_path_line_edit = QLineEdit()
        remote_password_path_layout.addWidget(
            self.remote_password_path_line_text)
        remote_password_path_layout.addWidget(
            self.remote_password_path_line_edit)

        # Save, Delete and Connect Button Layout
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton('Сохранить')
        self.save_button.setFixedSize(200, 30)
        self.delete_button = QPushButton('Удалить')
        self.delete_button.setFixedSize(200, 30)
        self.connect_button = QPushButton('Подключиться')
        self.connect_button.setFixedSize(200, 30)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.connect_button)

        self.save_button.clicked.connect(self.save_settings)
        self.delete_button.clicked.connect(self.delete_settings)
        self.connect_button.clicked.connect(self.connect_to_server)

        main_layout.addLayout(list_of_connections_layout)
        main_layout.addLayout(name_layout)
        main_layout.addLayout(ip_layout)
        main_layout.addLayout(username_layout)
        main_layout.addLayout(password_layout)
        main_layout.addLayout(domain_name_layout)
        main_layout.addLayout(server_name_layout)
        main_layout.addLayout(sharename_layout)
        main_layout.addLayout(remote_certs_path_layout)
        main_layout.addLayout(local_download_path_layout)
        main_layout.addLayout(remote_password_path_layout)
        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

        self.load_active_connection()

    def save_settings(self):
        result = db.DatabaseApp().save_to_db(
            self.name_line_edit.text(),
            self.ip_line_edit.text(),
            self.username_line_edit.text(),
            self.password_line_edit.text(),
            self.domain_name_line_edit.text(),
            self.server_name_line_edit.text(),
            self.sharename_line_edit.text(),
            self.remote_certs_path_line_edit.text(),
            self.local_download_path_line_edit.text(),
            self.remote_password_path_line_edit.text(),
        )
        if result is False:
            return
        self.list_of_connections_widget.addItem(
            self.name_line_edit.text(), result)

        index = self.list_of_connections_widget.count() - 1
        self.list_of_connections_widget.setCurrentIndex(index)
        self.set_current_connection(index)

    def delete_settings(self):
        index = self.list_of_connections_widget.currentIndex()
        if index == 0:
            QMessageBox.warning(
                self, 'Ошибка', 'Нельзя удалять подключение по умолчанию')
            return
        connection_id_to_delete = self.list_of_connections_widget.itemData(
            index)
        db.DatabaseApp().delete_from_db(connection_id_to_delete)
        db.DatabaseApp().save_active_connection("1")
        self.notify_message.show_success_message_ui(
            "Подключение удалено!\nВосстановлено активное подключение по умолчанию")

        self.list_of_connections_widget.removeItem(index)

    def update_combobox_list(self):
        self.list_of_connections_widget.clear()
        list_of_connections = db.DatabaseApp().update_combobox()
        for connection in list_of_connections:
            self.list_of_connections_widget.addItem(
                connection[1], connection[0])

    def set_current_connection(self, index):
        if index >= 0:
            current_connection_index = self.list_of_connections_widget.itemData(
                index)  # Получаем ID выбранной записи
            current_connection = db.DatabaseApp().select_from_db(
                current_connection_index)
            if current_connection:
                self.name_line_edit.setText(current_connection[1])
                self.ip_line_edit.setText(current_connection[2])
                self.username_line_edit.setText(current_connection[3])
                self.password_line_edit.setText(current_connection[4])
                self.domain_name_line_edit.setText(current_connection[5])
                self.server_name_line_edit.setText(current_connection[6])
                self.sharename_line_edit.setText(current_connection[7])
                self.remote_certs_path_line_edit.setText(current_connection[8])
                self.local_download_path_line_edit.setText(
                    current_connection[9])
                self.remote_password_path_line_edit.setText(
                    current_connection[10])

    def connect_to_server(self):
        # Получаем ID выбранной записи
        connection_index = self.list_of_connections_widget.currentIndex()
        if connection_index >= 0:
            connection_id = self.list_of_connections_widget.itemData(
                connection_index)
            connection_status = Run_Crypton_Functions().smbconnect_to_crypton(connection_id)
            if connection_status is None:
                return
            else:
                db.DatabaseApp().save_active_connection(connection_id)
                self.notify_message.show_success_message_ui("Активное подключение установлено!")

    def load_active_connection(self):
        active_connection_id = db.DatabaseApp().load_active_connection()
        if active_connection_id[0]:
            self.load_connection(active_connection_id[0])

    def load_connection(self, connection_id):
        connection = db.DatabaseApp().select_from_db(connection_id)
        if connection:
            self.name_line_edit.setText(connection[1])
            self.ip_line_edit.setText(connection[2])
            self.username_line_edit.setText(connection[3])
            self.password_line_edit.setText(connection[4])
            self.domain_name_line_edit.setText(connection[5])
            self.server_name_line_edit.setText(connection[6])
            self.sharename_line_edit.setText(connection[7])
            self.remote_certs_path_line_edit.setText(connection[8])
            self.local_download_path_line_edit.setText(connection[9])
            self.remote_password_path_line_edit.setText(connection[10])
            index = self.list_of_connections_widget.findText(connection[1])
            if index >= 0:
                self.list_of_connections_widget.setCurrentIndex(index)


class SettingsAuthorizationWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.setupUi()

        self.show()

    def setupUi(self):
        self.setWindowTitle("Авторизация")
        self.setFixedSize(300, 110)

        authorize_layout = QVBoxLayout(self)
        authorize_layout.setSpacing(10)

        login_layout = QHBoxLayout()
        self.login_label = QLabel("Введите пароль:")
        self.password_line_edit = QLineEdit()

        login_layout.addWidget(self.login_label)
        login_layout.addWidget(self.password_line_edit)

        buttons_layout = QHBoxLayout()
        self.login_button = QPushButton("Войти")
        self.cancel_button = QPushButton("Отмена")

        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.login_button)

        notify_layout = QHBoxLayout()
        self.notify_label = QLabel()
        self.notify_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        notify_layout.addWidget(self.notify_label)

        authorize_layout.addLayout(login_layout)
        authorize_layout.addLayout(buttons_layout)
        authorize_layout.addLayout(notify_layout)

        self.login_button.clicked.connect(self.show_settings_window)
        self.cancel_button.clicked.connect(self.close)

    def show_settings_window(self):
        password = self.password_line_edit.text()
        veryfication_password = Run_Crypton_Functions(type=5).smbconnect_to_crypton(connection_id=1)
        if password == veryfication_password:
            self.close()
            self.settings_window = SettingsWindow()
            return self.password_line_edit.text()
        else:
            self.notify_label.setText("Неверный пароль!")


class ShowInstalledLogListCertificate(QThread):
    signal_label = pyqtSignal(str)

    def __init__(self, password=None):
        super().__init__()
        self.password = password

    def run(self):
        try:
            install_certificates = Run_Crypton_Functions(
                2, self.signal_label)
            install_certificates.smbconnect_to_crypton()
        finally:
            self.quit()


class DetailWindow(QWidget):
    # Создание атрибута сигнала
    signal_label = pyqtSignal(str)

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
        self.inst_one_cert_list_widget = QListWidget()
        self.inst_one_cert_list_widget.setFixedHeight(220)
        self.search_certificate_line = QLineEdit()
        self.inst_one_cert_list_widget.setFont(self.font())
        self.search_certificate_line.setPlaceholderText("ПОИСК: Введите свою фамилию")  # noqa
        layout.addWidget(self.search_certificate_line)
        layout.addWidget(self.inst_one_cert_list_widget)
        items = Run_Crypton_Functions().smbconnect_to_crypton()
        if items is None:
            return

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
        self.label.setMinimumHeight(40)
        notify_layout.addWidget(self.label)
        layout.addLayout(notify_layout)

        for item in items:
            QListWidgetItem(item, self.inst_one_cert_list_widget)
        self.inst_one_cert_list_widget.itemDoubleClicked.connect(
            self.download_one_sertificate)
        self.start_button.clicked.connect(self.download_one_sertificate)
        self.setLayout(layout)
        self.setWindowTitle('Установка сертификата')
        self.setFixedWidth(600)

        self.signal_label.connect(self.update_label)
        self.search_certificate_line.textChanged.connect(self.filter_setup_certificate_list)

        self.show()

    def filter_setup_certificate_list(self):
        found_cert_name = self.search_certificate_line.text().lower()
        for i in range(self.inst_one_cert_list_widget.count()):
            found_cert = self.inst_one_cert_list_widget.item(i)
            found_cert.setHidden(
                found_cert_name not in found_cert.text().lower())


    def download_one_sertificate(self, item=None, password=None):
        password = self.authorize_setup_cert_line.text()
        verification_password = Run_Crypton_Functions(
            5).smbconnect_to_crypton()
        if verification_password is None:
            return
        if password == verification_password:
            selected_item = self.inst_one_cert_list_widget.selectedItems()
            if selected_item:
                Run_Crypton_Functions(1, self.signal_label).smbconnect_to_crypton(surname=selected_item[0].text())
            elif item:
                Run_Crypton_Functions(1, self.signal_label).smbconnect_to_crypton(surname=item.text())
            else:
                self.signal_label.emit("Сертификат не выбран")
        elif password == "":
            self.signal_label.emit(
                "Для начала установки введите пароль")
        else:
            self.signal_label.emit("Неверный пароль")

    def setup_all_sertificate(self, password=None):
        self.log_window = QWidget()
        layout = QVBoxLayout()
        self.log_list = QListWidget()
        layout.addWidget(self.log_list)
        self.log_window.setLayout(layout)
        self.log_window.setWindowTitle('Установка сертификатов')
        self.log_window.setFixedSize(600, 300)

        self.signal_label.connect(
            self.update_list_for_setup_all_certificates)

        verification_password = Run_Crypton_Functions(
            5).smbconnect_to_crypton()
        if password == verification_password:
            self.log_window.show()
            # Создается новый экземпляр потока для открытия окна со списком логов установленных сертификатов
            self.thread_log_list_certificates = ShowInstalledLogListCertificate(
                password)
            self.thread_log_list_certificates.signal_label.connect(
                self.update_list_for_setup_all_certificates)
            self.thread_log_list_certificates.start()

    def delete_certificate_window(self):
        self.del_cert_window = QWidget()
        layout = QVBoxLayout()

        # Добавляем поле поиска
        self.search_delete_certificate_line = QLineEdit()
        self.search_delete_certificate_line.setPlaceholderText("ПОИСК: Введите название сертификата")
        self.search_delete_certificate_line.setFont(self.font())

        self.del_cert_list = QListWidget()
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)
        self.delete_button = QPushButton('Удалить сертификат')
        self.del_cert_list.setFont(self.font())
        self.label.setFont(self.font())
        self.delete_button.setFont(self.font())
        layout.addWidget(self.search_delete_certificate_line)
        layout.addWidget(self.del_cert_list)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.label)
        cert_list = Run_Crypton_Functions(3).nonsmb_functions()
        if cert_list is None:
            return
        for item in cert_list:
            QListWidgetItem(item, self.del_cert_list)
        self.del_cert_list.itemDoubleClicked.connect(
            self.delete_certificate_slot)
        self.delete_button.clicked.connect(self.delete_certificate_slot)
        self.search_delete_certificate_line.textChanged.connect(self.filter_delete_certificate_list)
        self.del_cert_window.setLayout(layout)
        self.del_cert_window.setWindowTitle('Удаление сертификатов')
        self.del_cert_window.setFixedSize(600, 300)

        self.del_cert_window.show()

        self.signal_label.connect(self.update_label)

    def filter_delete_certificate_list(self):
        found_cert_name = self.search_delete_certificate_line.text().lower()
        for i in range(self.del_cert_list.count()):
            found_cert = self.del_cert_list.item(i)
            found_cert.setHidden(found_cert_name not in found_cert.text().lower())

    def delete_certificate_slot(self, item=None):
        selected_item = self.del_cert_list.selectedItems()
        if selected_item:
            delete_sertificate_by_button = Run_Crypton_Functions(
                4, self.signal_label)
            delete_sertificate_by_button.nonsmb_functions(
                selected_item[0].text())
            self.remove_certificate_name_from_list()
        elif item:
            delete_sertificate_by_double_click = Run_Crypton_Functions(
                4, self.signal_label)
            delete_sertificate_by_double_click.nonsmb_functions(item.text())
            self.remove_certificate_name_from_list()
        else:
            self.signal_label.emit("Сертификат не выбран")

    def remove_certificate_name_from_list(self):
        selected_certificate = self.del_cert_list.currentItem()
        self.del_cert_list.takeItem(
            self.del_cert_list.row(selected_certificate))

    @ pyqtSlot(str)
    def update_label(self, message):
        self.label.setText(message)
        self.update_timer.start(100)

    def perform_resize(self):
        self.adjustSize()

    @ pyqtSlot(str)
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
        self.setWindowIcon(QIcon('C:\\Users\\vboxuser\\crypton\\icon.ico'))
        self.setup_databes = db.DatabaseApp()
        self.initUI()

    def initUI(self):
        self.main_window_certificates_layout = QVBoxLayout()
        self.main_list_widget = QListWidget()
        self.main_list_widget.setFixedSize(550, 150)

        self.main_list_widget.setFont(self.font())

        items = ["Установить отдельный сертификат",
                 "Установить все сертификаты", "Удалить сертификат", "Настройки"]
        for item in items:
            QListWidgetItem(item, self.main_list_widget)
        self.main_list_widget.itemDoubleClicked.connect(self.showDetailWindow)
        self.main_window_certificates_layout.addWidget(self.main_list_widget)
        self.setLayout(self.main_window_certificates_layout)
        self.setWindowTitle(
            'Система управления криптографическими алгоритмами')
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
            self.authorize_window = SettingsAuthorizationWindow()

    def install_all_certs_password_verification(self):
        input_password = self.enterPasswordLine.text()
        self.password_checker = DetailWindow(2, input_password)

    def closeEvent(self, event):
        # Закрываем соединение с базой данных перед закрытием приложения
        self.close_conn = db.DatabaseApp().close_connection()
        event.accept()  # Завершаем закрытие окна

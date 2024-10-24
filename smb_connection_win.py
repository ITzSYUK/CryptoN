import os
import io
import subprocess
from smb.SMBConnection import SMBConnection
import crypton_database as db
import gui
import re


class SMBConnectionManager:
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
                        self.setup_sertificate_win(
                            local_file_path, local_file_name)

    def setup_sertificate_win(self, local_file_path, local_file_name):
        # Получение информации о сертификате
        result = subprocess.run(
            f'"C:/Program Files (x86)/Crypto Pro/CSP/certmgr" -list -file "{local_file_path}"',
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            encoding='cp866'
        )
        output_cert_info = result.stdout
        # Регулярные выражения для поиска дат выдачи и истечения
        issued_pattern = re.search(
            r'Выдан\s+:\s+\d{2}/\d{2}/(\d{4})', output_cert_info)
        expires_pattern = re.search(
            r'Истекает\s+:\s+\d{2}/\d{2}/(\d{4})', output_cert_info)
        if issued_pattern and expires_pattern:
            # Извлекаем годы выдачи и истечения
            issued_year = issued_pattern.group(1)
            expires_year = expires_pattern.group(1)

        # Просмотр имеющихся контейнеров
        result = subprocess.run(
            '"C:/Program Files (x86)/Crypto Pro/CSP/csptest" -keyset -enum_cont -fqcn -verifyc',
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            encoding='cp866'
        )

        lines = result.stdout.split('\n')
        matching_lines = [
            line for line in lines if line.startswith(f"\\\\.\\FAT12_V\\{local_file_name[0:6]}")]

        # Копирование закрытого ключа в реестр и установка сертификата
        try:
            # Извлечение русского ФИО из контейнера сертификата
            rus_name_pattern = re.findall(
                r'[\u0400-\u04FF]+', matching_lines[0])
            self.signal.emit(
                "Не удалось связать сертификат пользователя с контейнером. Идентификатор контейнера не найден.")
            # Создание переменной для хранения русского ФИО и годов выдачи и истечения для создания контейнера в реестре Windows
            container_name_with_dates = rus_name_pattern + \
                [issued_year, expires_year]

            # Копирование закрытого ключа в реестр
            result = subprocess.run(f'"C:/Program Files (x86)/Crypto Pro/CSP/csptest" -keycopy -contsrc "{matching_lines[0]}" -contdest "\\\\.\\REGISTRY\\{{''.join(container_name_with_dates)}}"',
                                    shell=True,
                                    check=True,
                                    capture_output=True,
                                    text=True,
                                    encoding='cp866'
                                    )
            # Установка сертификата
            result = subprocess.run(
                f'"C:/Program Files (x86)/Crypto Pro/CSP/certmgr" -inst -file "{local_file_path}" -cont "\\\\.\\REGISTRY\\{{''.join(container_name_with_dates)}}"',  # noqa
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
                return True
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

    def list_of_installed_certificates_win(self):
        result = subprocess.run(
            '"C:/Program Files (x86)/Crypto Pro/CSP/certmgr" -list | findstr /C:"Субъект" /C:"CN=" /C:"Истекает"',
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            encoding='cp866'
        )

        list_of_installed_certificates = result.stdout.split('\n')
        list_of_certificates = []
        # Создаем словарь для хранения информации о сертификатах
        current_certificate = {}
        number_of_lines = 1

        for line in list_of_installed_certificates:
            line = line.strip()
            if "CN=" in line:
                # Извлекаем только имя из строки с CN
                current_certificate["CN"] = line.split("CN=")[-1]
            elif "Истекает" in line:
                # Извлекаем дату истечения
                current_certificate["Expiration"] = line.split(
                    "Истекает            : ")[-1].strip()

                # Добавляем текущий сертификат в список с номером строки
                if "CN" in current_certificate and "Expiration" in current_certificate:
                    cert_info = f"{number_of_lines}: {current_certificate['CN']} | Истекает: {current_certificate['Expiration']}"
                    list_of_certificates.append(cert_info)
                    number_of_lines += 1

                # Очищаем информацию в словаре для следующего сертификата
                current_certificate = {}

        return list_of_certificates

    def delete_certificate_method_win(self, surname):
        # Извлекаем имя пользователя сертификата из строки с установленными сертификатами
        user_name = surname.split(": ", 1)[1]
        user_name = user_name.split(" | ", 1)[0]
        # Находим идентификатор ключа для указанного пользователя
        result = subprocess.run(
            f'"C:/Program Files (x86)/Crypto Pro/CSP/certmgr.exe" -list | findstr /C:"{user_name}" /C:"Идентификатор ключа : " /C:"Контейнер           : REGISTRY\\\\',
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            encoding='cp866'
        )
        # Извлекаем Идентификатор ключа и название контейнера из реестра
        try:
            key_identifier = result.stdout.split(
                'Идентификатор ключа : ')[1].split()[0]
            container_name_with_dates = result.stdout.split(
                'Контейнер           : REGISTRY\\\\')[1].split()[0]
        except IndexError:
            self.signal.emit(
                f"Не удалось извлечь идентификатор ключа для {user_name}.")
            return

        # Удаляем сертификат
        result = subprocess.run(
            f'"C:/Program Files (x86)/Crypto Pro/CSP/certmgr.exe" -delete -certificate -keyid {key_identifier}',
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        try:
            # Удаляем закрытый контейнер из реестра
            result = subprocess.run(
                f'"C:/Program Files (x86)/Crypto Pro/CSP/certmgr.exe" -delete -container "\\\\.\\REGISTRY\\{container_name_with_dates}"',
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )

            # Если результат успешен
            if result.returncode == 0:
                self.signal.emit(
                    f"Сертификат пользователя {user_name} успешно удален.")
        except subprocess.CalledProcessError as e:
            self.signal.emit(
                f"Ошибка при удалении сертификата {user_name}. Код ошибки: {e.returncode}. Сообщение: {e.stderr}")

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


class Run_Crypton_Functions:
    def __init__(self, type=0, signal=None):
        self.type = type
        self.signal = signal
        self.active_connection_id = db.DatabaseApp().load_active_connection()
        self.connection = db.DatabaseApp().select_from_db(
            self.active_connection_id[0])
        self.default_connection = db.DatabaseApp().load_default_connection()

    def open_settings_window_connection(self):
        try:
            with SMBConnectionManager(
                server_ip=self.default_connection[2],
                share_name=self.default_connection[7],
                folder_path=self.default_connection[8],
                username=self.default_connection[3],
                password=self.default_connection[4],
                client_machine_name="client_machine_name",
                server_name=self.default_connection[6],
                domain_name=self.default_connection[5],
                local_download_path=self.default_connection[9],
                password_file_path=self.default_connection[10],
                signal=self.signal
            ) as smb_connect:
                return smb_connect.open_password_file()
        except OSError:
            gui.MessageWindows().show_warning_message_ui(
                "Соединение с SMB-сервером разорвано.")

    def nonsmb_functions(self, surname=None):
        if self.type == 3:
            return SMBConnectionManager.list_of_installed_certificates_win()
        if self.type == 4:
            SMBConnectionManager.delete_certificate_method_win(
                self, surname)

    def smbconnect_to_crypton(self, surname=None):
        try:
            with SMBConnectionManager(
                server_ip=self.connection[2],
                share_name=self.connection[7],
                folder_path=self.connection[8],
                username=self.connection[3],
                password=self.connection[4],
                client_machine_name="client_machine_name",
                server_name=self.connection[6],
                domain_name=self.connection[5],
                local_download_path=self.connection[9],
                password_file_path=self.connection[10],
                surname=surname,
                signal=self.signal
            ) as smb_connect:
                if self.type == 1:
                    smb_connect.search_and_download()
                if self.type == 2:
                    smb_connect.install_all_certificates()
                if self.type == 5:
                    return smb_connect.open_password_file()
                return smb_connect.list_folders()
        except OSError:
            gui.MessageWindows().show_warning_message_ui(
                "Не удалось подключиться к SMB-серверу.\nПроверьте данные подключения.")

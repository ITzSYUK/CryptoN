import os
import io
import subprocess
from smb.SMBConnection import SMBConnection
from smb import smb_structs, base
import crypton_database_win as db
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
        try:
            # Получение информации о сертификате - используем один запрос вместо двух
            result = subprocess.run(
                f'"C:/Program Files (x86)/Crypto Pro/CSP/certmgr" -list -file "{local_file_path}"',
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                encoding='cp866'
            )
            output_cert_info = result.stdout

            # Используем один паттерн для поиска всех дат
            dates = {
                'issued': None,
                'expires': None
            }
            
            # Ищем даты в обоих форматах одновременно
            for line in output_cert_info.split('\n'):
                if any(x in line for x in ['Выдан', 'Not valid before']):
                    match = re.search(r'\d{2}/\d{2}/(\d{4})', line)
                    if match:
                        dates['issued'] = match.group(1)
                elif any(x in line for x in ['Истекает', 'Not valid after']):
                    match = re.search(r'\d{2}/\d{2}/(\d{4})', line)
                    if match:
                        dates['expires'] = match.group(1)

            if not dates['issued'] or not dates['expires']:
                raise ValueError("Не удалось найти даты выдачи/истечения сертификата")

            # Просмотр контейнеров - используем более эффективный поиск
            result = subprocess.run(
                '"C:/Program Files (x86)/Crypto Pro/CSP/csptest" -keyset -enum_cont -fqcn -verifyc',
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                encoding='cp866'
            )
            
            # Оптимизированный поиск подходящего контейнера
            parts_local_file_name = local_file_name.split()
            matching_line = None
            
            if len(parts_local_file_name) > 1:
                prefix = parts_local_file_name[0][0:3]
                second_char = parts_local_file_name[1][0:1]
                third_char = parts_local_file_name[2][0:1]
                pattern = f"{prefix}.*{second_char}.*{third_char}"
                
                for line in result.stdout.split('\n'):
                    if re.search(pattern, line):
                        matching_line = line
                        break
            else:
                pattern = f"\\\\.\\FAT12_V\\{local_file_name[0:3]}"
                for line in result.stdout.split('\n'):
                    if line.startswith(pattern):
                        matching_line = line
                        break

            if not matching_line:
                raise IndexError("Не найден подходящий контейнер")

            # Извлечение русского ФИО из контейнера одним запросом
            rus_name_pattern = ''.join(re.findall(r'[\u0400-\u04FF]+', matching_line))
            
            # Создание контейнера в реестре одной командой
            container_name = f"{rus_name_pattern}{dates['issued']}{dates['expires']}"
            install_container_command = f'"C:/Program Files (x86)/Crypto Pro/CSP/csptest" -keycopy -contsrc "{matching_line}" -contdest "\\\\.\\REGISTRY\\{container_name}"'
            
            subprocess.run(install_container_command, shell=True, check=True, capture_output=True, text=True, encoding='cp866')

            # Установка сертификата
            subprocess.run(
                f'"C:/Program Files (x86)/Crypto Pro/CSP/certmgr" -inst -file "{local_file_path}" -cont "\\\\.\\REGISTRY\\{container_name}"',
                shell=True,
                check=True,
                capture_output=True,
                text=True,
                encoding='cp866'
            )

            local_file_name_strip = local_file_name.rstrip('.cer')
            self.signal.emit(f"Сертификат пользователя {local_file_name_strip} успешно установлен.")

        except (subprocess.CalledProcessError, IndexError, ValueError) as e:
            self.signal.emit(f"Ошибка при установке сертификата {local_file_name}: {str(e)}")

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
        try:
            # Пробуем сначала русский вывод
            list_of_installed_certificates_command = '"C:/Program Files (x86)/Crypto Pro/CSP/certmgr" -list | findstr /C:"Субъект" /C:"Истекает"'
            result = subprocess.run(list_of_installed_certificates_command, shell=True, check=False, capture_output=True, text=True, encoding='cp866')
            # Если в выводе нет русских строк, используем английский вариант
            if "Субъект" not in result.stdout or result.returncode != 0:
                list_of_installed_certificates_command = '"C:/Program Files (x86)/Crypto Pro/CSP/certmgr" -list | findstr /C:"Subject" /C:"Not valid after"'
                result = subprocess.run(list_of_installed_certificates_command, shell=True, check=False, capture_output=True, text=True, encoding='cp866')
                is_english = True
            else:
                is_english = False

            # Проверяем, получили ли мы какой-либо вывод
            if result.returncode != 0 and not result.stdout:
                raise subprocess.CalledProcessError(
                    result.returncode, 
                    list_of_installed_certificates_command, 
                    output="Не удалось получить список сертификатов"
                )

            list_of_installed_certificates = result.stdout.split('\n')
            list_of_certificates = []
            current_certificate = {}
            number_of_lines = 1

            for line in list_of_installed_certificates:
                line = line.strip()
                if "CN=" in line:
                    current_certificate["CN"] = line.split("CN=")[-1]
                elif ("Истекает" in line) or ("Not valid after" in line):
                    if is_english:
                        current_certificate["Expiration"] = line.split("Not valid after     : ")[-1].strip()
                    else:
                        current_certificate["Expiration"] = line.split("Истекает            : ")[-1].strip()

                    if "CN" in current_certificate and "Expiration" in current_certificate:
                        cert_info = f"{number_of_lines}: {current_certificate['CN']} | Истекает: {current_certificate['Expiration']}"
                        list_of_certificates.append(cert_info)
                        number_of_lines += 1
                    current_certificate = {}

        except (subprocess.CalledProcessError, UnicodeDecodeError, OSError) as e:
            gui.MessageWindows().show_warning_message_ui(f"Ошибка при получении списка установленных сертификатов:\n{str(e.stdout)}.\nВероятно, нет установленных сертификатов.")
            return None
        else:
            if list_of_certificates:
                return list_of_certificates
            else:
                return None

    def delete_certificate_method_win(self, surname):
        # Извлекаем имя пользователя сертификата из строки с установленными сертификатами
        user_name = surname.split(": ", 1)[1]
        user_name = user_name.split(" | ", 1)[0]
        certificate_list_command = r'"C:/Program Files (x86)/Crypto Pro/CSP/certmgr.exe" -list'
        result = subprocess.run(certificate_list_command, capture_output=True, text=True, shell=True, encoding='cp866')

        # Разделение вывода на строки
        lines = result.stdout.splitlines()

        # Инициализация переменных для хранения результата
        in_certificate = False
        key_identifier = ""
        container = ""

        # Проход по каждой строке вывода
        for line in lines:
            # Поиск по русскому или английскому синтаксису
            if (re.search(r"Субъект\s*:\s*(.+)", line) or re.search(r"Subject\s*:\s*(.+)", line)) and user_name in line:
                in_certificate = True

            # Если находимся в нужном разделе, ищем поля на обоих языках
            if in_certificate:
                # Поиск идентификатора ключа
                if match := re.search(r"Идентификатор ключа\s*:\s*(.+)", line):
                    key_identifier = match.group(1).strip()
                elif match := re.search(r"SubjKeyID\s*:\s*(.+)", line):
                    key_identifier = match.group(1).strip()
                
                # Поиск контейнера
                if match := re.search(r"Контейнер\s*:\s+REGISTRY\\\\(.+)", line):
                    container = match.group(1).strip()
                elif match := re.search(r"Container\s*:\s+REGISTRY\\\\(.+)", line):
                    container = match.group(1).strip()
                
                # Выход из цикла при достижении разделителя
                if re.search(r"====|^\d+-+$", line):
                    break

        try:
            # Удаляем сертификат
            delete_certificate_command = f'"C:/Program Files (x86)/Crypto Pro/CSP/certmgr.exe" -delete -certificate -keyid {key_identifier}'
            result = subprocess.run(delete_certificate_command, shell=True, check=True, capture_output=True, text=True)
            # Удаляем закрытый контейнер из реестра
            delete_container_command = f'"C:/Program Files (x86)/Crypto Pro/CSP/certmgr.exe" -delete -container "\\\\.\\REGISTRY\\{container}"'
            result = subprocess.run(delete_container_command, shell=True, check=True, capture_output=True, text=True)

            # Если результат успешен
            if result.returncode == 0:
                self.signal.emit(
                    f"Сертификат пользователя {user_name} успешно удален.")
        except subprocess.CalledProcessError as e:
            self.signal.emit(
                f"Ошибка при удалении сертификата {user_name}. Код ошибки: {e.returncode}. Сообщение: {e.stderr}")


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


    def nonsmb_functions(self, surname=None):
        if self.type == 3:
            return SMBConnectionManager.list_of_installed_certificates_win(self)
        if self.type == 4:
            SMBConnectionManager.delete_certificate_method_win(
                self, surname)

    def smbconnect_to_crypton(self, connection_id=None, surname=None):
        if connection_id is None:
            self.active_connection_id = db.DatabaseApp().load_active_connection()
            self.active_connection = db.DatabaseApp().select_from_db(
                self.active_connection_id[0])
        else:
            self.active_connection = db.DatabaseApp().select_from_db(connection_id)
        try:
            with SMBConnectionManager(
                server_ip=self.active_connection[2],
                share_name=self.active_connection[7],
                folder_path=self.active_connection[8],
                username=self.active_connection[3],
                password=self.active_connection[4],
                client_machine_name="client_machine_name",
                server_name=self.active_connection[6],
                domain_name=self.active_connection[5],
                local_download_path=self.active_connection[9],
                password_file_path=self.active_connection[10],
                surname=surname,
                signal=self.signal
            ) as smb_connect:
                if self.type == 1:
                    return smb_connect.search_and_download()
                if self.type == 2:
                    smb_connect.install_all_certificates()
                if self.type == 5:
                    return smb_connect.open_password_file()
                return smb_connect.list_folders()
        except (ConnectionRefusedError, smb_structs.OperationFailure, AssertionError, base.NotConnectedError):
            gui.MessageWindows().show_warning_message_ui(
                "Не удалось подключиться к SMB-серверу.\nПроверьте интернет соединение или настройки подключения.")
            return None

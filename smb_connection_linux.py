import os
import io
import subprocess
from smb.SMBConnection import SMBConnection
import crypton_database_linux as db
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
                        self.setup_sertificate_linux(
                            local_file_path, local_file_name)

    def setup_sertificate_linux(self, local_file_path, local_file_name):
        # Установка сертификат
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

    def list_of_installed_certificates_linux(self):
        with os.popen(rf"/opt/cprocsp/bin/amd64/certmgr -list | grep -E 'Субъект|Истекает' | sed -n 's/.*CN=\(.*\)/\1/p; s/.*Истекает\s*:\s*/ | Истекает: /p' | paste -d '' - - ") as stream:  # noqa
            output = stream.read()

        list_of_installed_certificates = output.split('\n')
        list_of_installed_certificates_with_numbers = []
        number_of_lines = 1
        for line in list_of_installed_certificates:
            line = f"{number_of_lines}: {line}"
            number_of_lines += 1
            list_of_installed_certificates_with_numbers.append(line)
        return list_of_installed_certificates_with_numbers[:-1]

    def delete_certificate_method_linux(self, surname):
        user_name = surname.split(": ", 1)[1]
        user_name = user_name.split(" | ", 1)[0]
        with os.popen(f"/opt/cprocsp/bin/amd64/certmgr -list | awk -v user=\"{user_name}\" '$0 ~ user {{found=1}} found && /Идентификатор ключа/ {{print $NF; exit}}'") as stream:  # noqa
            key_identifier = stream.read()

        # Удаление файлов контейнера и сертификата
        with os.popen(f'/opt/cprocsp/bin/amd64/certmgr -list | awk -v user="{user_name}" \'$0 ~ user {{found=1}} found && /Контейнер/ {{print $NF; exit}}\'') as stream:  # noqa
            container_name = stream.read()
            if container_name:
                container_name = container_name.split('\n')[0]
                os.popen(
                    f"/opt/cprocsp/bin/amd64/certmgr -delete -container '{container_name}'")
                os.popen(
                    f'rm -rf "/var/opt/cprocsp/keys/user/{user_name}.cer"')

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
            return SMBConnectionManager.list_of_installed_certificates_linux(self)
        if self.type == 4:
            SMBConnectionManager.delete_certificate_method_linux(
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

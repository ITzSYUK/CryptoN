import sqlite3
import gui
import os
from getpass import getuser
import subprocess


class DatabaseApp():
    def __init__(self):
        super().__init__()
        USERNAME = getuser()
        db_path = f'C:/Users/{USERNAME}/crypton.db'
        local_download_path = 'V:\\'
        # Устанавливаем соединение с базой данных
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.notify_message = gui.MessageWindows()

        # Создаем таблицу, если она еще не существует
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS smbconnectconfig (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_of_connection TEXT NOT NULL,
                ipaddress TEXT NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                domainname TEXT NOT NULL,
                servername TEXT NOT NULL,
                sharename TEXT NOT NULL,
                remote_certs_path TEXT NOT NULL,
                local_download_path TEXT NOT NULL,
                password_path TEXT NOT NULL
            )
        ''')

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS active_connection (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        self.cursor.execute(
            "INSERT OR IGNORE INTO active_connection VALUES ('active_connection', '1')")

        # Данные по умолчанию
        self.cursor.execute(
            f'INSERT OR IGNORE INTO smbconnectconfig VALUES (1, "По умолчанию", "172.25.87.3", "cert_user", "cert2024", "SAMBA", "server-terminal", "обменник поликлиники", "/distr/certificates", "{local_download_path}", "/distr/certs_password.txt")')
        self.conn.commit()

    def save_to_db(self, name_of_connection, ipaddress, username, password, domainname, servername, sharename, remote_cert_path, local_download_path, password_path):
        # Обновляем данные в базе
        self.cursor.execute("SELECT COUNT(*) FROM smbconnectconfig WHERE name_of_connection=? AND ipaddress=? AND username=? AND password=? AND domainname=? AND servername=? AND sharename=? AND remote_certs_path=? AND local_download_path=? AND password_path=?",
                            (name_of_connection, ipaddress, username, password, domainname, servername, sharename, remote_cert_path, local_download_path, password_path))
        existing_entry = self.cursor.fetchone()
        # Проверяем, существует ли запись с таким именем
        self.cursor.execute(
            "SELECT name_of_connection FROM smbconnectconfig WHERE name_of_connection=?", (name_of_connection,))
        exist_name_of_connection = self.cursor.fetchone()
        if existing_entry[0] > 0:
            self.notify_message.show_warning_message_ui(
                "Ошибка. Такая запись уже существует!")
            return False

        elif exist_name_of_connection is None:
            if (name_of_connection and ipaddress and username and password and domainname and servername and sharename and remote_cert_path and local_download_path and password_path) == "":
                self.notify_message.show_warning_message_ui(
                    "Ошибка. Нельзя создать пустую запись")
                return False
            else:
                self.cursor.execute('INSERT INTO smbconnectconfig (name_of_connection, ipaddress, username, password, domainname, servername, sharename, remote_certs_path, local_download_path, password_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (
                    name_of_connection, ipaddress, username, password, domainname, servername, sharename, remote_cert_path, local_download_path, password_path))
            self.notify_message.show_success_message_ui(
                "Запись успешно добавлена!")
        else:
            self.notify_message.show_warning_message_ui(
                "Ошибка. Запись с таким именем уже существует!")
            return False

        self.conn.commit()
        return self.cursor.lastrowid

    def save_active_connection(self, connection_id):
        self.cursor.execute(
            "SELECT ipaddress, username, password, sharename FROM smbconnectconfig WHERE id=?", (connection_id,))
        connection_data = self.cursor.fetchall()
        try:
            result = subprocess.run(
                f'smbclient -L {connection_data[0][0]} -U {connection_data[0][1]}%{connection_data[0][2]} | grep "{connection_data[0][3]}"',
                shell=True,
                check=True,
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.cursor.execute("""
                    INSERT INTO active_connection (key, value) VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """, ("active_connection", connection_id))
                self.conn.commit()

        except subprocess.CalledProcessError:
            self.notify_message.show_warning_message_ui(
                "Нет соединения с удаленным сервером!")
            return False

    def load_active_connection(self):
        self.cursor.execute(
            "SELECT value FROM active_connection WHERE key = ?", ("active_connection",))
        return self.cursor.fetchone()

    def load_default_connection(self):
        self.cursor.execute(
            "SELECT * FROM smbconnectconfig WHERE id = ?", (1,))
        return self.cursor.fetchone()

    def delete_from_db(self, connection_id):
        # # Удаляем данные из базы
        self.cursor.execute(
            "DELETE FROM smbconnectconfig WHERE id=?", (connection_id,))

        self.conn.commit()

    def select_from_db(self, connection_id):
        # Выбираем данные из базы
        self.cursor.execute(
            'SELECT * FROM smbconnectconfig WHERE id=?', (connection_id,))
        return self.cursor.fetchone()

    def update_combobox(self):
        self.cursor.execute(
            'SELECT id, name_of_connection FROM smbconnectconfig')
        return self.cursor.fetchall()

    def close_connection(self):
        self.conn.close()
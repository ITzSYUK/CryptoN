import sqlite3


class DatabaseApp():
    def __init__(self):
        super().__init__()

        # Устанавливаем соединение с базой данных
        self.conn = sqlite3.connect(
            '/home/user/crypton.db')
        self.cursor = self.conn.cursor()

        # Создаем таблицу, если она еще не существует
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS smbconnectconfig (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ipaddress TEXT NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                domainname TEXT NOT NULL,
                servername TEXT NOT NULL,
                sharename TEXT NOT NULL,
                folderpath TEXT NOT NULL
            )
        ''')

        # Пример данных в базе
        self.cursor.execute(
            'INSERT OR IGNORE INTO smbconnectconfig VALUES (1, "1.1.1.1", "user", "password", "domain", "server", "share", "/home/user")')
        self.conn.commit()

    def save_to_db(self, ipaddress, username, password, domainname, servername, sharename, folderpath):
        # Сохраняем данные в базу
        self.cursor.execute(
            'INSERT OR IGNORE INTO smbconnectconfig VALUES (1, ?, ?, ?, ?, ?, ?, ?)', (ipaddress, username, password, domainname, servername, sharename, folderpath))
        # Обновляем данные в базе
        self.cursor.execute(
            'UPDATE smbconnectconfig SET ipaddress=?, username=?, password=?, domainname=?, servername=?, sharename=?, folderpath=? WHERE id=1', (ipaddress, username, password, domainname, servername, sharename, folderpath))
        self.conn.commit()

    def select_from_db(self):
        # Выбираем данные из базы
        self.cursor.execute('SELECT * FROM smbconnectconfig')
        return self.cursor.fetchall()

    def close_connection(self):
        self.conn.close()

import subprocess
import os

class VHDManager:
    def __init__(self, vhd_path, disk_size):
        self.vhd_path = vhd_path
        self.disk_size = disk_size
    
    def __enter__(self):
        # Создание временного файла PowerShell для создания VHD
        script_content = f'''
$vhdPath = "{self.vhd_path}"
$diskSize = {self.disk_size}  # Размер в MB

# Создание папки для виртуального диска (если она не существует)
New-Item -ItemType Directory -Path (Split-Path $vhdPath) -Force

# Создание команд для diskpart
$diskpartScript = @"
create vdisk file='$vhdPath' maximum=$diskSize
select vdisk file='$vhdPath'
attach vdisk
create partition primary
format fs=ntfs quick
assign letter=V
"@

# Выполнение команд diskpart
$diskpartScript | diskpart | Out-String
'''

        # Сохранение PowerShell скрипта во временный файл
        script_path = os.path.join(os.getenv('TEMP'), 'create_vhd.ps1')
        with open(script_path, 'w') as script_file:
            script_file.write(script_content)

        # Выполнение PowerShell скрипта
        result = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path], capture_output=True, text=True, shell=True)

        # Вывод результата выполнения
        print("Standard Output:")
        print(result.stdout)

        print("Standard Error:")
        print(result.stderr)

        # Удаление временного файла
        os.remove(script_path)

        # Возвращаем созданный путь для использования в программе
        return self.vhd_path

    def __exit__(self, exc_type, exc_value, traceback):
        # Форматирование и отключение диска при завершении программы
        print(f"Форматирование и отключение диска {self.vhd_path}")

        # Сначала форматируем диск
        script_content = f'''
$vhdPath = "{self.vhd_path}"

# Выбор виртуального диска, выбор тома и его форматирование
$diskpartScript = @"
select vdisk file='$vhdPath'
list volume
select volume V
format fs=ntfs quick
"@

# Выполнение команд diskpart
$diskpartScript | diskpart | Out-String
'''

        # Сохранение PowerShell скрипта во временный файл для форматирования
        script_path = os.path.join(os.getenv('TEMP'), 'format_vhd.ps1')
        with open(script_path, 'w') as script_file:
            script_file.write(script_content)

        # Выполнение PowerShell скрипта для форматирования
        result = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path], capture_output=True, text=True, shell=True)

        # Вывод результата форматирования
        print("Standard Output (format):")
        print(result.stdout)

        print("Standard Error (format):")
        print(result.stderr)

        # Удаление временного файла
        os.remove(script_path)

        # Отключаем диск
        script_content = f'''
$vhdPath = "{self.vhd_path}"

# Отключение виртуального диска
$diskpartScript = @"
select vdisk file='$vhdPath'
detach vdisk
"@

# Выполнение команд diskpart для отключения
$diskpartScript | diskpart | Out-String
'''

        # Сохранение PowerShell скрипта во временный файл для отключения диска
        script_path = os.path.join(os.getenv('TEMP'), 'detach_vhd.ps1')
        with open(script_path, 'w') as script_file:
            script_file.write(script_content)

        # Выполнение PowerShell скрипта для отключения
        result = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path], capture_output=True, text=True, shell=True)

        # Вывод результата отключения
        print("Standard Output (detach):")
        print(result.stdout)

        print("Standard Error (detach):")
        print(result.stderr)

        # Удаление временного файла
        os.remove(script_path)

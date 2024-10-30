# Crypton


## Copy repo

```
git clone https://gitlab.com/ITzSYUK/crypton.git -b dev_linux
```

## Creating Python virtual environment

```
python -m venv crypton
cd crypton
source ./bin/activate
```

## Dependency installation

```
python -m pip install pysmb pyqt6 pysqlite3 pyinstaller
```

## Program startup

```
python main.py
```

## Program compilation

```
python -m PyInstaller -F -w --name crypton main_linux.py
```
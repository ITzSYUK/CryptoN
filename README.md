# Crypton


## Copy repo

```
git clone https://gitlab.com/ITzSYUK/crypton.git -b dev_windows
```

## Creating Python virtual environment

```
pythom -m venv crypton
cd crypton
.\Scripts\activate
```

## Dependency installation

```
python -m pip install pysmb pyqt6 pysqlite3 pyinstaller
```

## Program startup

```
python main_win.py # (as administrator)
```

## Program compilation

```
python -m PyInstaller -F -w --name crypton main_win.py
```
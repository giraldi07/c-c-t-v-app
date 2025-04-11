@echo off
REM Build executable dengan PyInstaller
python setup.py

REM Kompilasi installer dengan Inno Setup
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup.iss

REM Buka folder output
explorer output
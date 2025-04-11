# setup.py
import PyInstaller.__main__
import os
import shutil

# Hapus build dan dist folder jika ada
shutil.rmtree('build', ignore_errors=True)
shutil.rmtree('dist', ignore_errors=True)

# Konfigurasi PyInstaller
PyInstaller.__main__.run([
    'main.py',               # File utama Anda
    '--onefile',             # Membuat single executable
    '--windowed',            # Untuk aplikasi GUI (tanpa console)
    '--icon=icon.ico',       # File icon (opsional)
    '--name=CCTVViewer',     # Nama aplikasi
    '--add-data=cctv_data.json;.',  # Include data JSON
    '--noconfirm',           # Tanpa konfirmasi overwrite
])
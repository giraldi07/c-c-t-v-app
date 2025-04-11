# CCTV Kota Bandung Viewer

Aplikasi desktop ringan untuk melihat ratusan CCTV di Kota Bandung.

## Fitur
- Pencarian lokasi CCTV
- Streaming langsung dengan `mpv`
- UI modern dan responsif dengan PySide6

## Instalasi

1. Pastikan Python 3.10+ sudah terinstall.
2. Install dependensi:

```bash
pip install -r requirements.txt
```

3. Jalankan program:

```bash
python main.py
```

## Build ke EXE (Opsional)
Install pyinstaller:

```bash
pip install pyinstaller
pyinstaller --onefile main.py
```

## Syarat
- Harus ada player `mpv` di PATH environment system (atau install [mpv.io](https://mpv.io/))

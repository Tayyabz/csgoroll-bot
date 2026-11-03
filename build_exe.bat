@echo off
REM Builds CSGORollArb.exe (run this on Windows, in this folder)
python -m pip install --upgrade requests pyinstaller
python -m PyInstaller --onefile --windowed --name CSGORollArb arb_bot.py
echo.
echo Done. Your exe is in the "dist" folder.
echo Put config.json and csgoroll_request.txt NEXT TO the exe (see README.md).
pause

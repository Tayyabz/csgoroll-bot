@echo off
REM Builds CSGORollArb.exe (run this on Windows, in this folder)
python -m pip install --upgrade requests playwright pyinstaller
python -m PyInstaller --onefile --windowed --name CSGORollArb --collect-all playwright arb_bot.py
echo.
echo Done. Your exe is in the "dist" folder.
pause

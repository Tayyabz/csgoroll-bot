@echo off
REM Builds RollTracker.exe (run this on Windows, in this folder)
python -m pip install --upgrade pyinstaller
python -m PyInstaller --onefile --windowed --name RollTracker roll_tracker.py
echo.
echo Done. Your exe is in the "dist" folder.
pause

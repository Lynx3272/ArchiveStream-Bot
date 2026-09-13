@echo off
title ArchiveStream Otonom Bot
cd /d "%~dp0"
call venv\Scripts\activate.bat
python -m bot.main
pause

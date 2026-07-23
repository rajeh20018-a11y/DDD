@echo off
cd /d "%~dp0"
set PORT=8772
echo AsirX database server: http://127.0.0.1:8772
echo Keep this window open while using Live Server.
python app.py
pause

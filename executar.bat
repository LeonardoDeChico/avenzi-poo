@echo off
cd /d "%~dp0"
pip install -r requirements.txt
echo.
echo Abra o navegador em http://localhost:5000
python app.py
pause

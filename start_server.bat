@echo off
REM Go to project folder
cd /d C:\Users\Shree\Desktop\MTC\ecommarce_website\ecommarce_website

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Optional: check python path
where python

REM Take DB backup BEFORE starting server
python backup_db.py

REM Start Django server
python manage.py runserver 0.0.0.0:8000

pause

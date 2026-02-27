@echo off
REM Go to project folder
cd /d C:\Users\Shree\Desktop\MTC\ecommarce_website\ecommarce_website

REM Activate virtual environment
call venv\Scripts\activate.bat

echo Checking for updates from Git...
git pull origin main

echo Taking DB backup...
python backup_db.py

echo Applying database changes...
python manage.py makemigrations
python manage.py migrate

echo.
echo ======================================================
echo    SYSTEM UPDATED SUCCESSFULLY!
echo    Now you can start the server again.
echo ======================================================
echo.

pause

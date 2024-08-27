@echo off
echo Activating virtual environment...
call venv\Scripts\activate
echo Starting the bot...
git pull
python main.py -a 2
pause

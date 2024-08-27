@echo off
echo Activating virtual environment...
title MuskEmpire
call venv\Scripts\activate
echo Starting git pull
git pull
echo Starting the bot...
python main.py -a 2
pause

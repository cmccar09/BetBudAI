@echo off
REM Simple batch script to run Racing Post scraper
REM Can be added to Task Scheduler manually

cd /d C:\Users\charl\OneDrive\futuregenAI\Betting
C:\Users\charl\OneDrive\futuregenAI\Betting\.venv\Scripts\python.exe scheduled_racingpost_scraper.py

REM Log completion
echo Scraper run completed at %date% %time% >> scraper_batch_log.txt

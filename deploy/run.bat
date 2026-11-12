@echo off
REM Windows: process every .xlsx in the input folder, then show run status and open tickets.
REM Schedule with Task Scheduler: schtasks /create /tn "InvoiceBot" /tr "C:\path\invoice-bot\deploy\run.bat" /sc daily /st 09:00
cd /d "%~dp0.."
if not exist input\*.xlsx (
  echo No input files found in input
  exit /b 0
)
for %%f in (input\*.xlsx) do (
  python main.py run "%%f" || echo Run failed for %%f - see logs\bot.log
)
python main.py status --limit 5
python main.py tickets --status OPEN

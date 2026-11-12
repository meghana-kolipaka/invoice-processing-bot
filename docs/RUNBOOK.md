# Support Runbook: Invoice Processing Bot

## 1. Daily check
1. `python main.py status`: confirm the latest run is `SUCCESS` or `COMPLETED_WITH_ERRORS`.
2. `python main.py tickets --status OPEN`: review open tickets.
3. Or use the API: `GET /runs`, `GET /tickets?status=open` (start it with `python main.py api`, docs at `/docs`).

## 2. Run statuses
| Status | Meaning | Action |
|---|---|---|
| SUCCESS | All rows loaded | None |
| COMPLETED_WITH_ERRORS | Some rows rejected; LOW ticket created | Open the error report in `reports/`, correct the source data, resend rejected rows |
| FAILED | Whole run failed and was rolled back; HIGH ticket created | Check `logs/bot.log` for the traceback; see section 3 |

## 3. Troubleshooting FAILED runs
| Symptom in log / ticket | Likely cause | Fix |
|---|---|---|
| `Input file is missing columns` | Wrong template | Use headers: invoice_id, vendor, email, amount, invoice_date |
| `BadZipFile` / cannot open file | Corrupt or non-xlsx file | Ask sender to resend as .xlsx |
| `database is locked` | Another process using bot.db | Wait or stop the other process, rerun |
| `already loaded in an earlier run` | Invoice was processed before | Expected; the bot never loads an invoice twice |

Linux: `tail -n 50 logs/bot.log` and `grep ERROR logs/bot.log`.
Windows: `Get-Content logs\bot.log -Tail 50` and `findstr ERROR logs\bot.log`.

## 4. Closing a ticket
`python main.py resolve <ticket_id> "what was wrong and what you did"` or `POST /tickets/<id>/resolve`.

## 5. Deployment
- Linux: `./deploy/deploy.sh` (creates venv, installs, runs tests). Schedule `deploy/run.sh` with cron.
- Windows: schedule `deploy\run.bat` with Task Scheduler.
- Docker: `docker build -t invoice-bot .`
- CI: GitHub Actions runs the tests on every push (`.github/workflows/ci.yml`). A deployment should only go ahead if CI is green.
- Rollback: redeploy the previous Git tag/commit and rerun the tests.

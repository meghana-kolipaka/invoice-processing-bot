"""Command line entry point.

  python main.py sample                      create a sample input file to try the bot
  python main.py run input/invoices.xlsx     process a file
  python main.py status                      show recent bot runs (monitoring view)
  python main.py tickets [--status OPEN]     list support tickets
  python main.py resolve 1 "note"            resolve a ticket with a resolution note
  python main.py api                         start the monitoring REST API on port 8000
"""
import argparse
import sys
from datetime import datetime

from bot import config, db
from bot.runner import process_file
from bot.sample import make_sample


def main(argv=None):
    p = argparse.ArgumentParser(description="Invoice Processing Bot")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run"); r.add_argument("file"); r.add_argument("--db", default=config.DB_PATH)
    s = sub.add_parser("status"); s.add_argument("--db", default=config.DB_PATH); s.add_argument("--limit", type=int, default=10)
    m = sub.add_parser("sample"); m.add_argument("--out", default=f"{config.INPUT_DIR}/invoices.xlsx")
    t = sub.add_parser("tickets"); t.add_argument("--db", default=config.DB_PATH); t.add_argument("--status")
    v = sub.add_parser("resolve"); v.add_argument("ticket_id", type=int); v.add_argument("note"); v.add_argument("--db", default=config.DB_PATH)
    a_ = sub.add_parser("api"); a_.add_argument("--port", type=int, default=8000)
    a = p.parse_args(argv)

    if a.cmd == "run":
        result = process_file(a.file, db_path=a.db)
        return 0 if result["status"] != "FAILED" else 1
    if a.cmd == "status":
        conn = db.connect(a.db)
        print(f"{'RUN':<5}{'STARTED':<21}{'FILE':<22}{'TOTAL':<7}{'LOADED':<8}{'FAILED':<8}STATUS")
        for r in db.recent_runs(conn, a.limit):
            print(f"{r['run_id']:<5}{r['started_at']:<21}{r['input_file']:<22}{r['total_rows']:<7}"
                  f"{r['loaded_rows']:<8}{r['failed_rows']:<8}{r['status']}")
        return 0
    if a.cmd == "tickets":
        conn = db.connect(a.db)
        print(f"{'ID':<5}{'RUN':<5}{'SEVERITY':<10}{'STATUS':<10}TITLE")
        for t in db.list_tickets(conn, a.status):
            print(f"{t['ticket_id']:<5}{t['run_id']:<5}{t['severity']:<10}{t['status']:<10}{t['title']}")
        return 0
    if a.cmd == "resolve":
        conn = db.connect(a.db)
        ok = db.resolve_ticket(conn, a.ticket_id, a.note, datetime.now().isoformat(timespec="seconds"))
        print("Resolved." if ok else "No open ticket with that id.")
        return 0 if ok else 1
    if a.cmd == "api":
        import uvicorn
        from bot.api import create_app
        uvicorn.run(create_app(), host="127.0.0.1", port=a.port)
        return 0
    if a.cmd == "sample":
        print("Sample file created:", make_sample(a.out))
        return 0


if __name__ == "__main__":
    sys.exit(main())

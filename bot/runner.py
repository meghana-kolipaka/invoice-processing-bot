"""Main bot logic: read Excel -> validate -> load to SQLite -> report errors."""
import logging
import shutil
import traceback
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook, load_workbook

from . import config, db
from .validators import validate_row

log = logging.getLogger("invoice_bot")


def setup_logging(log_dir):
    Path(log_dir).mkdir(exist_ok=True)
    handler = logging.FileHandler(Path(log_dir) / "bot.log")
    handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
    log.handlers.clear()
    log.addHandler(handler)
    log.addHandler(console)
    log.setLevel(logging.INFO)


def read_rows(xlsx_path):
    ws = load_workbook(xlsx_path, data_only=True).active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise ValueError("Input file is empty")
    headers = [str(h).strip().lower() if h else "" for h in rows[0]]
    missing = {"invoice_id", "vendor", "email", "amount", "invoice_date"} - set(headers)
    if missing:
        raise ValueError(f"Input file is missing columns: {sorted(missing)}")
    return [dict(zip(headers, r)) for r in rows[1:] if any(c not in (None, "") for c in r)]


def write_error_report(errors, report_dir, stamp):
    Path(report_dir).mkdir(exist_ok=True)
    path = Path(report_dir) / f"errors_{stamp}.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Rejected rows"
    ws.append(["excel_row", "invoice_id", "reason"])
    for e in errors:
        ws.append([e["excel_row"], e["invoice_id"], "; ".join(e["reasons"])])
    wb.save(path)
    return path


def process_file(xlsx_path, db_path=config.DB_PATH, report_dir=config.REPORT_DIR,
                 archive_dir=config.ARCHIVE_DIR, log_dir=config.LOG_DIR):
    """Run the bot on one file. Returns a summary dict. Never raises: failures are logged and recorded."""
    setup_logging(log_dir)
    xlsx_path = Path(xlsx_path)
    started = datetime.now()
    stamp = started.strftime("%Y%m%d_%H%M%S")
    conn = db.connect(db_path)
    run_id = db.start_run(conn, started.isoformat(timespec="seconds"), xlsx_path.name)
    log.info("Run %s started for %s", run_id, xlsx_path.name)

    total = loaded = 0
    errors = []
    try:
        rows = read_rows(xlsx_path)
        total = len(rows)
        seen = set()
        for i, raw in enumerate(rows, start=2):  # row 1 is the header
            clean, reasons = validate_row(raw, seen)
            if not reasons and db.invoice_exists(conn, str(raw["invoice_id"]).strip()):
                reasons = [f"Invoice {raw['invoice_id']} already loaded in an earlier run"]
            if reasons:
                errors.append({"excel_row": i, "invoice_id": raw.get("invoice_id"), "reasons": reasons})
                log.warning("Row %s rejected: %s", i, "; ".join(reasons))
                continue
            db.insert_invoice(conn, clean, datetime.now().isoformat(timespec="seconds"))
            seen.add(clean["invoice_id"])
            loaded += 1
        conn.commit()

        if errors:
            report = write_error_report(errors, report_dir, stamp)
            log.info("Error report written to %s", report)
        status = "SUCCESS" if not errors else "COMPLETED_WITH_ERRORS"
        message = f"{loaded} loaded, {len(errors)} rejected"

        Path(archive_dir).mkdir(exist_ok=True)
        shutil.move(str(xlsx_path), str(Path(archive_dir) / f"{stamp}_{xlsx_path.name}"))
    except Exception as exc:  # production-style handling: record, log, don't crash silently
        conn.rollback()
        status = "FAILED"
        message = f"{type(exc).__name__}: {exc}"
        loaded = 0
        log.error("Run %s FAILED: %s\n%s", run_id, message, traceback.format_exc())

    db.finish_run(conn, run_id, datetime.now().isoformat(timespec="seconds"),
                  total, loaded, len(errors), status, message)
    log.info("Run %s finished: %s (%s)", run_id, status, message)

    # Incident handling: raise a support ticket when a run fails or rejects rows.
    ticket_id = None
    if status == "FAILED":
        ticket_id = db.create_ticket(conn, run_id, "HIGH", f"Bot run {run_id} FAILED: {xlsx_path.name}",
                                     message, datetime.now().isoformat(timespec="seconds"))
    elif status == "COMPLETED_WITH_ERRORS":
        ticket_id = db.create_ticket(conn, run_id, "LOW", f"{len(errors)} rows rejected in run {run_id}: {xlsx_path.name}",
                                     "See the error report in reports/ for row-level reasons.",
                                     datetime.now().isoformat(timespec="seconds"))
    if ticket_id:
        log.info("Ticket %s created for run %s", ticket_id, run_id)
    conn.close()
    return {"run_id": run_id, "status": status, "total": total, "loaded": loaded,
            "failed": len(errors), "message": message, "ticket_id": ticket_id}

from datetime import date
from openpyxl import Workbook, load_workbook

from bot import db
from bot.runner import process_file
from bot.validators import validate_row

TODAY = date(2026, 11, 12)
GOOD = {"invoice_id": "A1", "vendor": "Acme", "email": "a@b.com", "amount": 10, "invoice_date": "2026-10-01"}


def make_xlsx(path, rows, headers=("invoice_id", "vendor", "email", "amount", "invoice_date")):
    wb = Workbook(); ws = wb.active
    ws.append(list(headers))
    for r in rows:
        ws.append(list(r))
    wb.save(path)


def run(tmp_path, rows, **kw):
    f = tmp_path / "in.xlsx"
    make_xlsx(f, rows, **kw)
    return process_file(f, db_path=tmp_path / "t.db", report_dir=tmp_path / "rep",
                        archive_dir=tmp_path / "arc", log_dir=tmp_path / "logs")


def test_valid_row_passes():
    clean, errs = validate_row(GOOD, set(), TODAY)
    assert errs == [] and clean["email"] == "a@b.com"


def test_missing_field():
    _, errs = validate_row({**GOOD, "vendor": ""}, set(), TODAY)
    assert "Missing vendor" in errs


def test_bad_email_amount_date():
    for patch, text in [({"email": "x"}, "Invalid email"), ({"amount": "abc"}, "not a number"),
                        ({"amount": -5}, "greater than 0"), ({"invoice_date": "2099-01-01"}, "future"),
                        ({"invoice_date": "nope"}, "Invalid date")]:
        _, errs = validate_row({**GOOD, **patch}, set(), TODAY)
        assert any(text in e for e in errs), patch


def test_duplicate_in_same_file():
    _, errs = validate_row(GOOD, {"A1"}, TODAY)
    assert any("Duplicate" in e for e in errs)


def test_successful_run_loads_and_archives(tmp_path):
    res = run(tmp_path, [("A1", "Acme", "a@b.com", 10, "2026-10-01")])
    assert res["status"] == "SUCCESS" and res["loaded"] == 1
    assert not (tmp_path / "in.xlsx").exists()          # moved to archive
    assert len(list((tmp_path / "arc").iterdir())) == 1


def test_mixed_run_writes_error_report(tmp_path):
    res = run(tmp_path, [("A1", "Acme", "a@b.com", 10, "2026-10-01"),
                         ("A2", "Bad", "oops", 10, "2026-10-01")])
    assert res["status"] == "COMPLETED_WITH_ERRORS" and res["loaded"] == 1 and res["failed"] == 1
    report = next((tmp_path / "rep").iterdir())
    ws = load_workbook(report).active
    assert ws.cell(2, 1).value == 3 and "Invalid email" in ws.cell(2, 3).value


def test_rerun_rejects_already_loaded_invoice(tmp_path):
    run(tmp_path, [("A1", "Acme", "a@b.com", 10, "2026-10-01")])
    res = run(tmp_path, [("A1", "Acme", "a@b.com", 10, "2026-10-01")])
    assert res["loaded"] == 0 and res["failed"] == 1


def test_missing_columns_marks_run_failed(tmp_path):
    res = run(tmp_path, [("A1", "x")], headers=("invoice_id", "vendor"))
    assert res["status"] == "FAILED" and "missing columns" in res["message"]
    conn = db.connect(tmp_path / "t.db")
    assert db.recent_runs(conn)[0]["status"] == "FAILED"


# ---- tickets (incident handling) ----
def test_failed_run_creates_high_ticket(tmp_path):
    res = run(tmp_path, [("A1", "x")], headers=("invoice_id", "vendor"))
    conn = db.connect(tmp_path / "t.db")
    t = db.list_tickets(conn, "open")[0]
    assert res["ticket_id"] == t["ticket_id"] and t["severity"] == "HIGH"


def test_rejected_rows_create_low_ticket(tmp_path):
    run(tmp_path, [("A1", "Acme", "a@b.com", 10, "2026-10-01"), ("A2", "Bad", "oops", 10, "2026-10-01")])
    t = db.list_tickets(db.connect(tmp_path / "t.db"))[0]
    assert t["severity"] == "LOW" and "1 rows rejected" in t["title"]


def test_clean_run_creates_no_ticket(tmp_path):
    res = run(tmp_path, [("A1", "Acme", "a@b.com", 10, "2026-10-01")])
    assert res["ticket_id"] is None


def test_resolve_ticket_once(tmp_path):
    run(tmp_path, [("A1", "x")], headers=("invoice_id", "vendor"))
    conn = db.connect(tmp_path / "t.db")
    assert db.resolve_ticket(conn, 1, "Fixed template", "2026-11-12T10:00:00") is True
    assert db.resolve_ticket(conn, 1, "again", "2026-11-12T10:01:00") is False

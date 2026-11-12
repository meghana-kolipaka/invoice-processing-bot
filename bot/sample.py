from pathlib import Path
from openpyxl import Workbook

ROWS = [
    ("INV-1001", "Acme Supplies", "billing@acme.com", 1250.50, "2026-10-01"),
    ("INV-1002", "Globex Traders", "accounts@globex.in", 980, "2026-10-03"),
    ("INV-1003", "Initech", "not-an-email", 450, "2026-10-04"),          # bad email
    ("INV-1004", "Umbrella Corp", "pay@umbrella.com", "abc", "2026-10-05"),  # bad amount
    ("INV-1005", "Stark Industries", "ap@stark.com", 7600, "2099-01-01"),    # future date
    ("INV-1001", "Acme Supplies", "billing@acme.com", 1250.50, "2026-10-01"),  # duplicate
    ("INV-1007", "", "ap@wayne.com", 300, "2026-10-08"),                # missing vendor
    ("INV-1008", "Wayne Enterprises", "ap@wayne.com", 2100, "08/10/2026"),
]


def make_sample(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook(); ws = wb.active
    ws.append(["invoice_id", "vendor", "email", "amount", "invoice_date"])
    for r in ROWS:
        ws.append(list(r))
    wb.save(path)
    return path

"""Row-level validation rules for the invoice bot."""
import re
from datetime import date, datetime

REQUIRED = ["invoice_id", "vendor", "email", "amount", "invoice_date"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def parse_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue
    return None


def validate_row(row, seen_ids, today=None):
    """Return (clean_row, errors). errors is a list of readable messages."""
    today = today or date.today()
    errors = []

    for field in REQUIRED:
        if row.get(field) in (None, ""):
            errors.append(f"Missing {field}")
    if errors:
        return None, errors

    invoice_id = str(row["invoice_id"]).strip()
    if invoice_id in seen_ids:
        errors.append(f"Duplicate invoice_id {invoice_id}")

    if not EMAIL_RE.match(str(row["email"]).strip()):
        errors.append(f"Invalid email '{row['email']}'")

    try:
        amount = round(float(row["amount"]), 2)
        if amount <= 0:
            errors.append("Amount must be greater than 0")
    except (TypeError, ValueError):
        amount = None
        errors.append(f"Amount is not a number '{row['amount']}'")

    inv_date = parse_date(row["invoice_date"])
    if inv_date is None:
        errors.append(f"Invalid date '{row['invoice_date']}'")
    elif inv_date > today:
        errors.append("Invoice date is in the future")

    if errors:
        return None, errors

    return {
        "invoice_id": invoice_id,
        "vendor": str(row["vendor"]).strip(),
        "email": str(row["email"]).strip().lower(),
        "amount": amount,
        "invoice_date": inv_date.isoformat(),
    }, []

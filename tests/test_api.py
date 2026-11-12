from fastapi.testclient import TestClient

from bot.api import create_app
from tests.test_bot import run


def make_client(tmp_path):
    run(tmp_path, [("A1", "Acme", "a@b.com", 10, "2026-10-01"), ("A2", "Bad", "oops", 10, "2026-10-01")])
    return TestClient(create_app(tmp_path / "t.db"))


def test_health(tmp_path):
    assert TestClient(create_app(tmp_path / "t.db")).get("/health").json() == {"status": "ok"}


def test_runs_and_single_run(tmp_path):
    c = make_client(tmp_path)
    runs = c.get("/runs").json()
    assert runs[0]["status"] == "COMPLETED_WITH_ERRORS"
    assert c.get("/runs/1").json()["loaded_rows"] == 1
    assert c.get("/runs/99").status_code == 404


def test_tickets_and_resolve(tmp_path):
    c = make_client(tmp_path)
    assert len(c.get("/tickets?status=open").json()) == 1
    assert c.post("/tickets/1/resolve", json={"note": "Reviewed report"}).status_code == 200
    assert c.get("/tickets?status=open").json() == []
    assert c.post("/tickets/1/resolve", json={"note": "again"}).status_code == 404


def test_invoices_endpoint(tmp_path):
    c = make_client(tmp_path)
    assert [i["invoice_id"] for i in c.get("/invoices").json()] == ["A1"]

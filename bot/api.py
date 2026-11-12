"""Monitoring REST API (FastAPI): check bot runs, tickets and loaded invoices."""
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from . import config, db


class Resolution(BaseModel):
    note: str


def create_app(db_path=None):
    app = FastAPI(title="Invoice Bot Monitoring API")
    path = db_path or config.DB_PATH

    def conn():
        return db.connect(path)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/runs")
    def runs(limit: int = 10):
        c = conn()
        try:
            return [dict(r) for r in db.recent_runs(c, limit)]
        finally:
            c.close()

    @app.get("/runs/{run_id}")
    def run(run_id: int):
        c = conn()
        try:
            r = db.get_run(c, run_id)
        finally:
            c.close()
        if r is None:
            raise HTTPException(404, f"Run {run_id} not found")
        return dict(r)

    @app.get("/tickets")
    def tickets(status: str | None = None):
        c = conn()
        try:
            return [dict(t) for t in db.list_tickets(c, status)]
        finally:
            c.close()

    @app.post("/tickets/{ticket_id}/resolve")
    def resolve(ticket_id: int, body: Resolution):
        c = conn()
        try:
            ok = db.resolve_ticket(c, ticket_id, body.note, datetime.now().isoformat(timespec="seconds"))
        finally:
            c.close()
        if not ok:
            raise HTTPException(404, f"Open ticket {ticket_id} not found")
        return {"ticket_id": ticket_id, "status": "RESOLVED"}

    @app.get("/invoices")
    def invoices(limit: int = 100):
        c = conn()
        try:
            return [dict(i) for i in db.list_invoices(c, limit)]
        finally:
            c.close()

    return app

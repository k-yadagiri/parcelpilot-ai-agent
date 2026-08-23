"""
Loads accounts / orders / tickets from the supplied Excel workbook into a
local SQLite database, and creates empty `escalations` and `follow_up_tasks`
tables that the agent's state-changing action tool writes to.

Run standalone: `python -m app.build_db`
"""
from __future__ import annotations

import sqlite3

import pandas as pd

from app.config import XLSX_PATH, DB_PATH, DB_DIR


def build_database(force: bool = True) -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists() and force:
        DB_PATH.unlink()

    xls = pd.ExcelFile(XLSX_PATH)
    accounts = pd.read_excel(xls, "accounts")
    orders = pd.read_excel(xls, "orders")
    tickets = pd.read_excel(xls, "tickets")

    conn = sqlite3.connect(DB_PATH)
    try:
        accounts.to_sql("accounts", conn, index=False, if_exists="replace")
        orders.to_sql("orders", conn, index=False, if_exists="replace")
        tickets.to_sql("tickets", conn, index=False, if_exists="replace")

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS escalations (
                escalation_id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                related_order_id TEXT,
                related_ticket_id TEXT,
                reason TEXT NOT NULL,
                severity TEXT,
                requested_by_role TEXT,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS follow_up_tasks (
                task_id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                related_order_id TEXT,
                related_ticket_id TEXT,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS service_credits (
                credit_id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                related_order_id TEXT,
                amount_inr REAL NOT NULL,
                reason TEXT NOT NULL,
                requires_manager_approval INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    build_database()
    print(f"Database built at {DB_PATH}")

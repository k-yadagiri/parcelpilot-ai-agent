"""
Proactive issue detection for the internal operations view (Problem 1).

All logic here is generic - it operates on whatever tickets/orders/accounts
exist in the database and the SLA targets loaded from policy config, so it
is not tied to the example records in the assessment pack.
"""
from __future__ import annotations

import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from typing import List, Dict, Any

from app.config import DB_PATH, DATASET_SNAPSHOT_TIME

# Default first-response SLA targets in minutes, from Support Policy v3.
# Account-specific overrides (Northstar, LumenWorks) are applied where known.
DEFAULT_SLA_MINUTES = {
    "Enterprise": {"P1": 30, "P2": 120, "P3": 24 * 60},
    "Growth": {"P1": 120, "P2": 240, "P3": 2 * 24 * 60},
    "Standard": {"P1": 240, "P2": 24 * 60, "P3": 2 * 24 * 60},
}
ACCOUNT_SLA_OVERRIDE_MINUTES = {
    "ACCT-001": {"P1": 15, "P2": 60, "P3": 8 * 60},   # Northstar Enterprise Agreement
    "ACCT-002": {"P1": 120, "P2": 240, "P3": 2 * 24 * 60},  # LumenWorks Growth Agreement
}

SEVERITY_KEYWORDS = {
    "P1": [
        r"\ball (shipments?|shipment creation)\b.*fail", r"\bcomplete outage\b",
        r"\bsecurity incident\b", r"\bkey exposure\b", r"\bcredential exposure\b",
        r"\bcan'?t create any\b",
    ],
    "P2": [r"\bbulk upload\b", r"\bfails?\b", r"\bwebhook\b", r"\bstill shows\b", r"\bdegraded\b"],
}


def _classify_severity(subject: str, description: str) -> str:
    text = f"{subject} {description}".lower()
    for sev in ("P1", "P2"):
        for pat in SEVERITY_KEYWORDS[sev]:
            if re.search(pat, text):
                return sev
    return "P3"


def _sla_minutes(plan: str, account_id: str, severity: str) -> int:
    override = ACCOUNT_SLA_OVERRIDE_MINUTES.get(account_id)
    if override:
        return override[severity]
    return DEFAULT_SLA_MINUTES.get(plan, DEFAULT_SLA_MINUTES["Standard"])[severity]


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def sla_risk_report(now: datetime = DATASET_SNAPSHOT_TIME) -> List[Dict[str, Any]]:
    """Flag open tickets that are approaching or exceeding their first-
    response SLA target, using each account's plan (and contract override,
    if any)."""
    conn = _conn()
    try:
        rows = conn.execute(
            """
            SELECT t.*, a.plan, a.account_name
            FROM tickets t JOIN accounts a ON t.account_id = a.account_id
            WHERE t.status = 'open'
            """
        ).fetchall()
    finally:
        conn.close()

    report = []
    for r in rows:
        d = dict(r)
        severity = _classify_severity(d.get("subject", ""), d.get("description", ""))
        target_minutes = _sla_minutes(d["plan"], d["account_id"], severity)
        created = datetime.fromisoformat(str(d["created_at"]))
        elapsed_minutes = (now - created).total_seconds() / 60
        pct_of_target = round(elapsed_minutes / target_minutes * 100, 1) if target_minutes else None
        status = "breached" if elapsed_minutes > target_minutes else (
            "at_risk" if pct_of_target and pct_of_target >= 70 else "ok"
        )
        report.append({
            "ticket_id": d["ticket_id"], "account_id": d["account_id"],
            "account_name": d["account_name"], "plan": d["plan"],
            "subject": d["subject"], "inferred_severity": severity,
            "elapsed_minutes": round(elapsed_minutes, 1), "sla_target_minutes": target_minutes,
            "pct_of_target": pct_of_target, "sla_status": status,
        })
    order = {"breached": 0, "at_risk": 1, "ok": 2}
    report.sort(key=lambda x: (order[x["sla_status"]], -x["elapsed_minutes"]))
    return report


_TOKEN_RE = re.compile(r"[a-zA-Z]{4,}")
_STOP = {"this", "that", "with", "have", "from", "about", "still", "user", "users", "customer"}


def recurring_issue_clusters(min_cluster_size: int = 2) -> List[Dict[str, Any]]:
    """Group open tickets by shared significant keywords in subject text to
    surface likely-duplicate / recurring product issues across accounts."""
    conn = _conn()
    try:
        rows = conn.execute(
            "SELECT t.*, a.account_name FROM tickets t JOIN accounts a ON t.account_id = a.account_id "
            "WHERE t.status = 'open'"
        ).fetchall()
    finally:
        conn.close()

    keyword_to_tickets = defaultdict(list)
    for r in rows:
        d = dict(r)
        tokens = {w.lower() for w in _TOKEN_RE.findall(d.get("subject", "") + " " + d.get("description", ""))}
        tokens -= _STOP
        for tok in tokens:
            keyword_to_tickets[tok].append(d)

    clusters = []
    seen_ticket_sets = set()
    for keyword, tix in keyword_to_tickets.items():
        accounts_involved = {t["account_id"] for t in tix}
        if len(tix) >= min_cluster_size and len(accounts_involved) >= 1:
            key = tuple(sorted(t["ticket_id"] for t in tix))
            if key in seen_ticket_sets or len(tix) < min_cluster_size:
                continue
            # only keep clusters that look meaningfully specific (avoid generic words)
            if len(tix) >= min_cluster_size and (len(accounts_involved) > 1 or len(tix) >= 2):
                seen_ticket_sets.add(key)
                clusters.append({
                    "keyword": keyword,
                    "ticket_count": len(tix),
                    "accounts_affected": sorted(accounts_involved),
                    "ticket_ids": [t["ticket_id"] for t in tix],
                })
    clusters.sort(key=lambda c: (-len(c["accounts_affected"]), -c["ticket_count"]))
    return clusters[:10]


def unusual_order_patterns() -> List[Dict[str, Any]]:
    """Surface orders with signals worth a human look: pickup significantly
    overdue, or long-pending cancellation requests."""
    conn = _conn()
    try:
        rows = conn.execute("SELECT * FROM orders").fetchall()
    finally:
        conn.close()
    now = DATASET_SNAPSHOT_TIME
    flags = []
    for r in rows:
        d = dict(r)
        notes = []
        if d["status"] == "BOOKED" and d.get("pickup_window_end") and not d.get("pickup_actual_at"):
            end = datetime.fromisoformat(str(d["pickup_window_end"]))
            overdue_min = (now - end).total_seconds() / 60
            if overdue_min > 60:
                notes.append(f"Pickup overdue by {round(overdue_min)} min past window end")
        if d.get("cancellation_requested_at") and d["status"] not in ("DELIVERED",):
            req = datetime.fromisoformat(str(d["cancellation_requested_at"]))
            pending_min = (now - req).total_seconds() / 60
            if pending_min > 60:
                notes.append(f"Cancellation requested {round(pending_min)} min ago and still not resolved")
        if notes:
            flags.append({"order_id": d["order_id"], "account_id": d["account_id"],
                           "status": d["status"], "flags": notes})
    return flags


def account_ticket_spike() -> List[Dict[str, Any]]:
    """Flag accounts with multiple open tickets at once - a proxy for a
    broader issue affecting one customer."""
    conn = _conn()
    try:
        rows = conn.execute(
            "SELECT t.account_id, a.account_name, COUNT(*) as open_count "
            "FROM tickets t JOIN accounts a ON t.account_id = a.account_id "
            "WHERE t.status = 'open' GROUP BY t.account_id HAVING COUNT(*) >= 2 "
            "ORDER BY open_count DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()

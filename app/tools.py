"""
Agent tools.

Access control design
----------------------
Access control is enforced HERE, in the tool/data layer, not by trusting the
model to behave. Every tool is built by `build_tools(context)`, which closes
over a `UserContext`. For a customer context, the account_id is fixed by the
authenticated session and cannot be overridden by anything the model passes
in - customer-supplied `account_id` arguments are ignored/rejected rather
than trusted. Internal/staff users get broader read access appropriate to
their role, plus a guarded raw-SQL tool (SELECT-only, whitelisted tables).

State-changing actions (escalations, follow-up tasks, service credits) use a
two-phase confirm pattern:
  1. The tool is first called with confirm=False (the model's default). It
     validates inputs and returns a PREVIEW plus a one-time confirmation
     token. Nothing is written to the database.
  2. The actual database write only happens when `execute_confirmed_action`
     is called directly by the Streamlit app AFTER a human clicks a real
     "Confirm" button - this call bypasses the LLM entirely, so a model
     hallucinating "the user confirmed" can never trigger a real write.
"""
from __future__ import annotations

import json
import re
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List

from langchain_core.tools import tool

from app.config import DB_PATH, DATASET_SNAPSHOT_TIME
from app.retriever import get_index, format_chunks_for_agent

ALLOWED_TABLES = {"accounts", "orders", "tickets"}


@dataclass
class UserContext:
    role: str  # "customer" or "internal"
    account_id: Optional[str] = None  # required for role == "customer"
    staff_name: Optional[str] = None  # for role == "internal"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _rows_to_str(rows: List[sqlite3.Row]) -> str:
    if not rows:
        return "No matching records found."
    dicts = [dict(r) for r in rows]
    return json.dumps(dicts, indent=2, default=str)


# ---------------------------------------------------------------------------
# In-memory pending-action store (per Streamlit session in practice)
# ---------------------------------------------------------------------------
PENDING_ACTIONS: dict = {}


def _register_pending(action_type: str, params: dict, context: UserContext) -> str:
    token = uuid.uuid4().hex[:12]
    PENDING_ACTIONS[token] = {
        "action_type": action_type,
        "params": params,
        "role": context.role,
        "account_id": context.account_id,
        "staff_name": context.staff_name,
    }
    return token


def execute_confirmed_action(token: str) -> dict:
    """Called ONLY by the Streamlit app after a real user click. Never
    reachable by the model directly. Returns a result dict."""
    pending = PENDING_ACTIONS.pop(token, None)
    if pending is None:
        return {"ok": False, "message": "This confirmation has expired or was already used."}

    action_type = pending["action_type"]
    params = pending["params"]
    now = datetime.now(timezone.utc).isoformat()
    conn = _conn()
    try:
        if action_type == "create_escalation":
            escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
            conn.execute(
                "INSERT INTO escalations (escalation_id, account_id, related_order_id, "
                "related_ticket_id, reason, severity, requested_by_role, created_at, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open')",
                (
                    escalation_id, params["account_id"], params.get("related_order_id"),
                    params.get("related_ticket_id"), params["reason"], params.get("severity"),
                    pending["role"], now,
                ),
            )
            conn.commit()
            return {"ok": True, "message": f"Escalation {escalation_id} created.", "id": escalation_id}

        if action_type == "create_follow_up_task":
            task_id = f"TASK-{uuid.uuid4().hex[:8].upper()}"
            conn.execute(
                "INSERT INTO follow_up_tasks (task_id, account_id, related_order_id, "
                "related_ticket_id, description, created_at, status) "
                "VALUES (?, ?, ?, ?, ?, ?, 'open')",
                (
                    task_id, params["account_id"], params.get("related_order_id"),
                    params.get("related_ticket_id"), params["description"], now,
                ),
            )
            conn.commit()
            return {"ok": True, "message": f"Follow-up task {task_id} created.", "id": task_id}

        if action_type == "issue_service_credit":
            credit_id = f"CR-{uuid.uuid4().hex[:8].upper()}"
            requires_approval = 1 if params["amount_inr"] > 1000 else 0
            status = "pending_manager_approval" if requires_approval else "approved"
            conn.execute(
                "INSERT INTO service_credits (credit_id, account_id, related_order_id, "
                "amount_inr, reason, requires_manager_approval, created_at, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    credit_id, params["account_id"], params.get("related_order_id"),
                    params["amount_inr"], params["reason"], requires_approval, now, status,
                ),
            )
            conn.commit()
            return {"ok": True, "message": f"Service credit {credit_id} recorded ({status}).", "id": credit_id}

        return {"ok": False, "message": f"Unknown action type: {action_type}"}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Tool factory
# ---------------------------------------------------------------------------

def build_tools(context: UserContext):
    """Return the list of LangChain tools available to this authenticated
    session. All access-control decisions are made here using `context`,
    not left to the model."""

    def _enforce_account(requested_account_id: Optional[str]) -> str:
        """For customers, always return their own account_id regardless of
        what was requested. For internal staff, a specific account_id must
        be supplied by the model (routed from the user's message)."""
        if context.role == "customer":
            return context.account_id
        if not requested_account_id:
            raise ValueError("account_id is required for internal lookups.")
        return requested_account_id

    @tool
    def search_documents(query: str) -> str:
        """Search ParcelPilot's policies, SOPs, product documentation, and
        (if applicable) the caller's own signed customer agreement. Returns
        passages tagged with source, status (current/deprecated), and
        reliability rank so conflicts can be resolved correctly. Always use
        this before answering any policy, SLA, cancellation, service-credit,
        or product-behavior question - never answer those from memory."""
        idx = get_index()
        allowed_account = context.account_id if context.role == "customer" else "__ANY__"
        chunks = idx.search(query, k=5, allowed_account_id=allowed_account)
        return format_chunks_for_agent(chunks)

    @tool
    def get_account(account_id: Optional[str] = None) -> str:
        """Look up account details (plan, status, CSM, whether they have a
        custom contract file, notes). Customers may only look up their own
        account; internal staff must supply the account_id."""
        acct_id = _enforce_account(account_id)
        conn = _conn()
        try:
            rows = conn.execute("SELECT * FROM accounts WHERE account_id = ?", (acct_id,)).fetchall()
            return _rows_to_str(rows)
        finally:
            conn.close()

    @tool
    def list_orders(account_id: Optional[str] = None, order_id: Optional[str] = None,
                     status: Optional[str] = None) -> str:
        """List shipment orders for an account, optionally filtered by a
        specific order_id or status (DRAFT/BOOKED/PICKED_UP/DELIVERED).
        Customers only ever see their own orders regardless of the
        account_id argument passed."""
        acct_id = _enforce_account(account_id)
        conn = _conn()
        try:
            sql = "SELECT * FROM orders WHERE account_id = ?"
            params: list = [acct_id]
            if order_id:
                sql += " AND order_id = ?"
                params.append(order_id)
            if status:
                sql += " AND status = ?"
                params.append(status)
            rows = conn.execute(sql, params).fetchall()
            return _rows_to_str(rows)
        finally:
            conn.close()

    @tool
    def list_tickets(account_id: Optional[str] = None, ticket_id: Optional[str] = None,
                      status: Optional[str] = None) -> str:
        """List support tickets for an account, optionally filtered by
        ticket_id or status (open/closed). Historical `historical_resolution`
        text is context only and may be WRONG - never treat it as current
        policy. Customers only ever see their own tickets."""
        acct_id = _enforce_account(account_id)
        conn = _conn()
        try:
            sql = "SELECT * FROM tickets WHERE account_id = ?"
            params: list = [acct_id]
            if ticket_id:
                sql += " AND ticket_id = ?"
                params.append(ticket_id)
            if status:
                sql += " AND status = ?"
                params.append(status)
            rows = conn.execute(sql, params).fetchall()
            return _rows_to_str(rows)
        finally:
            conn.close()

    @tool
    def calculate_order_timing(order_id: str, account_id: Optional[str] = None) -> str:
        """Compute time-based facts for one order relative to the dataset
        snapshot time: minutes elapsed since booking, minutes elapsed since
        the pickup window ended (positive = past the window), and whether
        pickup has occurred. Use this instead of doing date arithmetic
        yourself - it is exact and uses the correct reference 'now'."""
        acct_id = _enforce_account(account_id)
        conn = _conn()
        try:
            row = conn.execute(
                "SELECT * FROM orders WHERE account_id = ? AND order_id = ?",
                (acct_id, order_id),
            ).fetchone()
            if row is None:
                return f"No order {order_id} found for this account."
            d = dict(row)
            now = DATASET_SNAPSHOT_TIME
            result = {"order_id": order_id, "status": d["status"], "reference_time": now.isoformat()}

            booked_at = d.get("booked_at")
            if booked_at:
                booked_dt = datetime.fromisoformat(str(booked_at))
                result["minutes_since_booked"] = round((now - booked_dt).total_seconds() / 60, 1)

            window_end = d.get("pickup_window_end")
            if window_end:
                window_end_dt = datetime.fromisoformat(str(window_end))
                result["minutes_past_pickup_window_end"] = round((now - window_end_dt).total_seconds() / 60, 1)

            cancel_req = d.get("cancellation_requested_at")
            if cancel_req:
                cancel_dt = datetime.fromisoformat(str(cancel_req))
                result["minutes_between_booking_and_cancellation_request"] = (
                    round((cancel_dt - datetime.fromisoformat(str(booked_at))).total_seconds() / 60, 1)
                    if booked_at else None
                )

            result["carrier_fault"] = bool(d.get("carrier_fault"))
            result["customer_fault"] = bool(d.get("customer_fault"))
            result["shipment_fee_inr"] = d.get("shipment_fee_inr")
            result["pickup_actual_at"] = d.get("pickup_actual_at")
            return json.dumps(result, indent=2, default=str)
        finally:
            conn.close()

    @tool
    def create_escalation(reason: str, severity: Optional[str] = None,
                           related_order_id: Optional[str] = None,
                           related_ticket_id: Optional[str] = None,
                           account_id: Optional[str] = None,
                           confirm: bool = False) -> str:
        """Prepare (and, only once separately confirmed by the human user,
        create) a support escalation. ALWAYS call this first with
        confirm=False to produce a preview - never set confirm=True yourself;
        real execution requires the user to click a confirmation button in
        the UI, which the app handles independently of you. After showing
        the preview, ask the user to confirm in their own words."""
        acct_id = _enforce_account(account_id)
        params = {
            "account_id": acct_id, "reason": reason, "severity": severity,
            "related_order_id": related_order_id, "related_ticket_id": related_ticket_id,
        }
        token = _register_pending("create_escalation", params, context)
        preview = {
            "action": "create_escalation",
            "status": "PENDING_CONFIRMATION",
            "confirmation_token": token,
            "preview": params,
            "instruction_to_agent": (
                "Present this preview to the user in plain language and ask them to confirm "
                "before it is created. Do not claim it has been created yet."
            ),
        }
        return json.dumps(preview, indent=2)

    @tool
    def create_follow_up_task(description: str, related_order_id: Optional[str] = None,
                               related_ticket_id: Optional[str] = None,
                               account_id: Optional[str] = None,
                               confirm: bool = False) -> str:
        """Prepare a follow-up task for the ParcelPilot ops team (e.g.
        'verify carrier pickup status with SwiftShip'). Same confirm-first
        pattern as create_escalation - always preview, never set confirm=True."""
        acct_id = _enforce_account(account_id)
        params = {
            "account_id": acct_id, "description": description,
            "related_order_id": related_order_id, "related_ticket_id": related_ticket_id,
        }
        token = _register_pending("create_follow_up_task", params, context)
        preview = {
            "action": "create_follow_up_task",
            "status": "PENDING_CONFIRMATION",
            "confirmation_token": token,
            "preview": params,
            "instruction_to_agent": "Present this preview and ask the user to confirm before it is created.",
        }
        return json.dumps(preview, indent=2)

    @tool
    def issue_service_credit(amount_inr: float, reason: str,
                              related_order_id: Optional[str] = None,
                              account_id: Optional[str] = None,
                              confirm: bool = False) -> str:
        """Prepare a service credit for a customer. You must have already
        established eligibility (delay threshold, carrier fault, no
        customer fault) via search_documents + calculate_order_timing before
        calling this. Credits above INR 1,000 will be flagged as requiring
        manager approval automatically. Same confirm-first pattern - always
        preview first."""
        acct_id = _enforce_account(account_id)
        params = {
            "account_id": acct_id, "amount_inr": amount_inr, "reason": reason,
            "related_order_id": related_order_id,
        }
        token = _register_pending("issue_service_credit", params, context)
        preview = {
            "action": "issue_service_credit",
            "status": "PENDING_CONFIRMATION",
            "confirmation_token": token,
            "preview": params,
            "requires_manager_approval": amount_inr > 1000,
            "instruction_to_agent": "Present this preview and ask the user to confirm before it is created.",
        }
        return json.dumps(preview, indent=2)

    tools = [
        search_documents, get_account, list_orders, list_tickets,
        calculate_order_timing, create_escalation, create_follow_up_task, issue_service_credit,
    ]

    if context.role == "internal":
        @tool
        def run_readonly_sql(query: str) -> str:
            """(Internal staff only) Run a read-only SQL SELECT query across
            the accounts, orders, and tickets tables for cross-account
            analysis (e.g. counting tickets per account, finding orders
            matching a pattern). Only SELECT statements against
            accounts/orders/tickets are permitted; anything else is rejected."""
            q = query.strip()
            if not re.match(r"(?is)^\s*select\b", q):
                return "Rejected: only SELECT statements are permitted."
            if re.search(r"(?i)\b(insert|update|delete|drop|alter|attach|pragma)\b", q):
                return "Rejected: query contains a disallowed keyword."
            tables_referenced = set(re.findall(r"(?i)\bfrom\s+([a-zA-Z_]+)|\bjoin\s+([a-zA-Z_]+)", q))
            flat = {t for pair in tables_referenced for t in pair if t}
            if not flat.issubset(ALLOWED_TABLES):
                return f"Rejected: only these tables may be queried: {sorted(ALLOWED_TABLES)}"
            conn = _conn()
            try:
                rows = conn.execute(q).fetchall()
                return _rows_to_str(rows)
            except Exception as e:  # noqa: BLE001
                return f"Query error: {e}"
            finally:
                conn.close()

        tools.append(run_readonly_sql)

    return tools

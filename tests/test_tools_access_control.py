import json

import pytest

from app.tools import UserContext, build_tools


def _tool_map(ctx):
    return {t.name: t for t in build_tools(ctx)}


def test_customer_cannot_view_another_accounts_data_via_get_account():
    ctx = UserContext(role="customer", account_id="ACCT-001")
    tools = _tool_map(ctx)
    out = tools["get_account"].invoke({"account_id": "ACCT-002"})
    data = json.loads(out)
    assert len(data) == 1
    assert data[0]["account_id"] == "ACCT-001"


def test_customer_cannot_view_another_accounts_orders():
    ctx = UserContext(role="customer", account_id="ACCT-002")
    tools = _tool_map(ctx)
    out = tools["list_orders"].invoke({"account_id": "ACCT-001"})
    data = json.loads(out)
    assert all(o["account_id"] == "ACCT-002" for o in data)


def test_customer_cannot_view_another_accounts_tickets():
    ctx = UserContext(role="customer", account_id="ACCT-003")
    tools = _tool_map(ctx)
    out = tools["list_tickets"].invoke({"account_id": "ACCT-001"})
    data = json.loads(out)
    assert all(t["account_id"] == "ACCT-003" for t in data)


def test_customer_has_no_raw_sql_tool():
    ctx = UserContext(role="customer", account_id="ACCT-001")
    tools = _tool_map(ctx)
    assert "run_readonly_sql" not in tools


def test_internal_requires_explicit_account_id():
    ctx = UserContext(role="internal", staff_name="Rohit")
    tools = _tool_map(ctx)
    with pytest.raises(Exception):
        tools["get_account"].invoke({})


def test_internal_sql_tool_blocks_writes_and_other_tables():
    ctx = UserContext(role="internal", staff_name="Rohit")
    tools = _tool_map(ctx)
    assert "Rejected" in tools["run_readonly_sql"].invoke({"query": "DELETE FROM orders"})
    assert "Rejected" in tools["run_readonly_sql"].invoke({"query": "SELECT * FROM escalations"})
    ok = tools["run_readonly_sql"].invoke({"query": "SELECT account_id FROM accounts"})
    assert "Rejected" not in ok


def test_calculate_order_timing_uses_dataset_snapshot_time():
    ctx = UserContext(role="internal", staff_name="Rohit")
    tools = _tool_map(ctx)
    out = tools["list_orders"].invoke({"account_id": "ACCT-002"})
    orders = json.loads(out)
    assert orders, "expected seed orders for ACCT-002"
    order_id = orders[0]["order_id"]
    timing = json.loads(tools["calculate_order_timing"].invoke({"account_id": "ACCT-002", "order_id": order_id}))
    assert "minutes_since_booked" in timing
    assert timing["reference_time"].startswith("2026-08-16")

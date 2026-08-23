import json

from app.tools import UserContext, build_tools, execute_confirmed_action, PENDING_ACTIONS


def test_action_tool_never_writes_without_confirmation():
    ctx = UserContext(role="customer", account_id="ACCT-002")
    tools = {t.name: t for t in build_tools(ctx)}

    preview = json.loads(tools["create_follow_up_task"].invoke({"description": "check carrier status"}))
    assert preview["status"] == "PENDING_CONFIRMATION"
    token = preview["confirmation_token"]
    assert token in PENDING_ACTIONS

    # Calling the *tool* again does not itself execute anything, even if the
    # model were to (incorrectly) pass confirm=True - only the dedicated
    # execute_confirmed_action() entrypoint, called by the app after a real
    # button click, performs the write.
    preview2 = json.loads(tools["create_follow_up_task"].invoke(
        {"description": "check carrier status", "confirm": True}
    ))
    assert preview2["status"] == "PENDING_CONFIRMATION"


def test_confirmed_action_executes_exactly_once():
    ctx = UserContext(role="customer", account_id="ACCT-002")
    tools = {t.name: t for t in build_tools(ctx)}
    preview = json.loads(tools["create_escalation"].invoke({"reason": "test", "severity": "P3"}))
    token = preview["confirmation_token"]

    result = execute_confirmed_action(token)
    assert result["ok"] is True
    assert token not in PENDING_ACTIONS

    replay = execute_confirmed_action(token)
    assert replay["ok"] is False


def test_service_credit_over_1000_flagged_for_manager_approval():
    ctx = UserContext(role="internal", staff_name="Rohit")
    tools = {t.name: t for t in build_tools(ctx)}
    preview = json.loads(tools["issue_service_credit"].invoke(
        {"amount_inr": 1500, "reason": "goodwill", "account_id": "ACCT-002"}
    ))
    assert preview["requires_manager_approval"] is True

    token = preview["confirmation_token"]
    result = execute_confirmed_action(token)
    assert result["ok"] is True
    assert "pending_manager_approval" in result["message"]

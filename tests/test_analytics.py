from app import analytics


def test_sla_risk_report_returns_all_open_tickets():
    report = analytics.sla_risk_report()
    assert len(report) >= 1
    for row in report:
        assert row["sla_status"] in ("breached", "at_risk", "ok")
        assert row["sla_target_minutes"] > 0


def test_sla_report_sorted_worst_first():
    report = analytics.sla_risk_report()
    order = {"breached": 0, "at_risk": 1, "ok": 2}
    statuses = [order[r["sla_status"]] for r in report]
    assert statuses == sorted(statuses)


def test_unusual_order_patterns_returns_flag_reasons():
    flags = analytics.unusual_order_patterns()
    for f in flags:
        assert f["flags"], "every flagged order must have at least one reason"


def test_account_ticket_spike_only_returns_accounts_with_multiple_open_tickets():
    spikes = analytics.account_ticket_spike()
    for s in spikes:
        assert s["open_count"] >= 2

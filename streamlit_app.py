import json
import sqlite3
import uuid

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from app.config import DB_PATH
from app.build_db import build_database
from app import analytics
from app.tools import UserContext, execute_confirmed_action, PENDING_ACTIONS
from app.agent import build_agent

st.set_page_config(page_title="ParcelPilot AI Agent", page_icon="\U0001F4E6", layout="wide")

if not DB_PATH.exists():
    build_database()


# ---------------------------------------------------------------------------
# Mock auth
# ---------------------------------------------------------------------------
def get_accounts():
    conn = sqlite3.connect(DB_PATH)
    try:
        return pd.read_sql("SELECT account_id, account_name FROM accounts", conn)
    finally:
        conn.close()


with st.sidebar:
    st.title("\U0001F4E6 ParcelPilot AI Agent")
    st.caption("Mock authentication - choose a user context for this session.")

    mode = st.radio("I am a...", ["Customer", "ParcelPilot Internal Staff"])

    if mode == "Customer":
        accounts_df = get_accounts()
        label_map = {f"{r.account_name} ({r.account_id})": r.account_id for r in accounts_df.itertuples()}
        chosen = st.selectbox("Logged in as account:", list(label_map.keys()))
        account_id = label_map[chosen]
        role = "customer"
        staff_name = None
    else:
        role = "internal"
        account_id = None
        staff_name = st.text_input("Staff name", value="Rohit (Support)")
        st.info("Internal staff can look up any account and use cross-account analysis.")

    session_key = f"{role}:{account_id or staff_name}"
    if st.session_state.get("session_key") != session_key:
        st.session_state.clear()
        st.session_state["session_key"] = session_key
        st.session_state["thread_id"] = str(uuid.uuid4())
        st.session_state["history"] = []

    st.divider()
    if st.button("Reset conversation"):
        st.session_state["history"] = []
        st.session_state["thread_id"] = str(uuid.uuid4())
        st.rerun()

context = UserContext(role=role, account_id=account_id, staff_name=staff_name)

TOOL_ICONS = {
    "search_documents": "\U0001F4C4",
    "get_account": "\U0001F464",
    "list_orders": "\U0001F4E6",
    "list_tickets": "\U0001F3AB",
    "calculate_order_timing": "\U0001F9EE",
    "create_escalation": "\U0001F6A8",
    "create_follow_up_task": "\U0001F4DD",
    "issue_service_credit": "\U0001F4B0",
    "run_readonly_sql": "\U0001F5C4\uFE0F",
}

tabs = ["\U0001F4AC Chat"]
if role == "internal":
    tabs.append("\U0001F4CA Proactive Issue Detection")
tab_objs = st.tabs(tabs)

# ---------------------------------------------------------------------------
# Chat tab
# ---------------------------------------------------------------------------
with tab_objs[0]:
    if role == "customer":
        st.subheader(f"Support chat - {chosen}")
    else:
        st.subheader(f"Internal support/ops assistant - {staff_name}")

    for msg in st.session_state.get("history", []):
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant" and msg.get("tool_trace"):
                with st.expander("Tools used", expanded=False):
                    for t in msg["tool_trace"]:
                        icon = TOOL_ICONS.get(t["name"], "\U0001F527")
                        st.markdown(f"**{icon} `{t['name']}`**")
                        st.code(json.dumps(t["args"], indent=2), language="json")
                        st.text(t["output"][:1500])
            st.markdown(msg["content"])
            if msg.get("pending_token"):
                token = msg["pending_token"]
                still_pending = token in PENDING_ACTIONS
                if still_pending:
                    c1, c2 = st.columns(2)
                    if c1.button("\u2705 Confirm & execute", key=f"confirm_{token}"):
                        result = execute_confirmed_action(token)
                        status_icon = "\u2705" if result["ok"] else "\u26A0\uFE0F"
                        st.session_state["history"].append({
                            "role": "assistant",
                            "content": f"{status_icon} {result['message']}",
                        })
                        st.rerun()
                    if c2.button("\u274C Cancel", key=f"cancel_{token}"):
                        PENDING_ACTIONS.pop(token, None)
                        st.session_state["history"].append({
                            "role": "assistant", "content": "Action cancelled - nothing was created.",
                        })
                        st.rerun()

    user_input = st.chat_input("Ask about your account, an order, a policy, or report an issue...")
    if user_input:
        st.session_state["history"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        agent = build_agent(context)
        config = {"configurable": {"thread_id": st.session_state["thread_id"]}}

        with st.chat_message("assistant"):
            with st.spinner("Working..."):
                result = agent.invoke({"messages": [("user", user_input)]}, config=config)

            all_messages = result["messages"]
            tool_trace = []
            pending_token = None
            for m in all_messages:
                if getattr(m, "type", None) == "ai" and getattr(m, "tool_calls", None):
                    for tc in m.tool_calls:
                        tool_trace.append({"name": tc["name"], "args": tc["args"], "output": ""})
                if getattr(m, "type", None) == "tool":
                    if tool_trace:
                        for t in reversed(tool_trace):
                            if t["output"] == "":
                                t["output"] = str(m.content)
                                break
                    try:
                        payload = json.loads(m.content)
                        if isinstance(payload, dict) and payload.get("status") == "PENDING_CONFIRMATION":
                            pending_token = payload.get("confirmation_token")
                    except (json.JSONDecodeError, TypeError):
                        pass

            final_text = all_messages[-1].content if all_messages else ""
            if isinstance(final_text, list):
                final_text = "\n".join(
                    b.get("text", "") for b in final_text if isinstance(b, dict)
                )

            if tool_trace:
                with st.expander("Tools used", expanded=False):
                    for t in tool_trace:
                        icon = TOOL_ICONS.get(t["name"], "\U0001F527")
                        st.markdown(f"**{icon} `{t['name']}`**")
                        st.code(json.dumps(t["args"], indent=2), language="json")
                        st.text(t["output"][:1500])

            st.markdown(final_text)

            if pending_token:
                c1, c2 = st.columns(2)
                if c1.button("\u2705 Confirm & execute", key=f"confirm_{pending_token}"):
                    result2 = execute_confirmed_action(pending_token)
                    status_icon2 = "\u2705" if result2["ok"] else "\u26A0\uFE0F"
                    st.session_state["history"].append({
                        "role": "assistant",
                        "content": f"{status_icon2} {result2['message']}",
                    })
                    st.rerun()
                if c2.button("\u274C Cancel", key=f"cancel_{pending_token}"):
                    PENDING_ACTIONS.pop(pending_token, None)
                    st.session_state["history"].append({
                        "role": "assistant", "content": "Action cancelled - nothing was created.",
                    })
                    st.rerun()

        st.session_state["history"].append({
            "role": "assistant", "content": final_text,
            "tool_trace": tool_trace, "pending_token": pending_token,
        })

# ---------------------------------------------------------------------------
# Internal proactive-issue-detection tab
# ---------------------------------------------------------------------------
if role == "internal":
    with tab_objs[1]:
        st.subheader("Proactive issue detection")
        st.caption("Computed from current tickets/orders data as of the dataset snapshot time.")

        st.markdown("### \U0001F6A8 SLA risk")
        sla = analytics.sla_risk_report()
        if sla:
            df = pd.DataFrame(sla)
            breached = df[df.sla_status == "breached"]
            at_risk = df[df.sla_status == "at_risk"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Breached", len(breached))
            c2.metric("At risk (\u226570% of target)", len(at_risk))
            c3.metric("Open tickets tracked", len(df))
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No open tickets.")

        st.markdown("### \U0001F501 Recurring / clustered issues")
        clusters = analytics.recurring_issue_clusters()
        if clusters:
            st.dataframe(pd.DataFrame(clusters), use_container_width=True, hide_index=True)
        else:
            st.info("No recurring clusters detected among open tickets.")

        st.markdown("### \U0001F4E6 Unusual order patterns")
        flags = analytics.unusual_order_patterns()
        if flags:
            st.dataframe(pd.DataFrame(flags), use_container_width=True, hide_index=True)
        else:
            st.info("No unusual order patterns detected.")

        st.markdown("### \U0001F465 Accounts with multiple open tickets")
        spikes = analytics.account_ticket_spike()
        if spikes:
            st.dataframe(pd.DataFrame(spikes), use_container_width=True, hide_index=True)
        else:
            st.info("No account currently has multiple simultaneous open tickets.")

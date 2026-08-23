# Demo Script (~5 minutes)

## 1. Architecture (60s)
- One Streamlit app, two mocked login contexts (customer / internal staff).
- LangGraph ReAct agent over 3+ tools: document search (TF-IDF over the 6
  PDFs, tagged with reliability metadata), structured-data lookup/calc
  (SQLite built from the workbook), and state-changing actions
  (escalation / follow-up task / service credit).
- Access control lives in the tool layer (`build_tools(context)`), not in
  the prompt - show `app/tools.py` `_enforce_account()` briefly.
- Confirm-before-execute: tools only *preview* an action; the actual DB
  write is a separate function the UI calls after a real button click.

## 2. Customer chat - multi-step, correct source precedence (90s)
Log in as **Northstar Logistics (ACCT-001)**.
- Ask: *"Can I cancel my BOOKED order without a fee, and why?"*
  - Watch the tool trace: `list_orders` → `calculate_order_timing` →
    `search_documents`.
  - Answer should cite the Northstar Enterprise Agreement's no-fee
    cancellation clause, correctly overriding the default 30-minute SOP
    rule, and name the specific order.
- Ask: *"What's your P1 response time for my account?"*
  - Should answer 15 minutes / 24x7 from the Northstar agreement, not the
    30-minute default in Support Policy v3 - demonstrating precedence.

## 3. Cross-account leak check (30s)
Switch to **Beacon Retail (ACCT-003)**, which has no custom contract.
- Ask the same cancellation question - answer should fall back to the
  default SOP (₹250 fee after 30 minutes), and must not mention Northstar
  or LumenWorks at all.

## 4. Confirmation flow (60s)
As a customer with a legitimate case (e.g. a carrier-fault late pickup),
ask for a service credit.
- Agent should check eligibility via `calculate_order_timing` +
  `search_documents` before proposing anything.
- Show the tool returning a `PENDING_CONFIRMATION` preview, and that
  nothing is created until you click **Confirm & execute** in the UI.
- Click **Cancel** on a second example to show nothing is written either
  way without the click.

## 5. Internal staff view - proactive issue detection (60s)
Switch to **Internal Staff**.
- Chat: *"Any tickets close to breaching SLA right now?"* - agent should
  reason using `run_readonly_sql` / `list_tickets` and current policy
  targets.
- Open the **Proactive Issue Detection** tab: SLA risk table (breached/at
  risk), recurring issue clusters across accounts, unusual order patterns,
  and accounts with multiple open tickets - all computed live from the
  data, not hard-coded.

## 6. Trust and conflicting/incorrect sources (60s)
- Ask internal staff: *"A ticket says a customer was told the bulk upload
  limit is 3,000 rows - is that right?"*
  - Agent should flag that this matches a *historical* (possibly wrong)
    ticket resolution, and give the current product doc's real limit
    (5,000 rows, with a known-issue caveat around ~3,000 rows on some
    accounts).
- Point out the deprecated Support Policy v2 PDF is in the corpus but the
  agent never uses it as current guidance (shown as reliability metadata
  in the tool trace).

## Close (20s)
Recap: enforced access control, precedence-aware answers, hard confirmation
gate on writes, and a proactive dashboard - all generalizing beyond the
example IDs in the prompt, verified by the automated test suite (`pytest`,
20 tests, no live API key required).

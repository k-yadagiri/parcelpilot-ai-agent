# Architecture Note

## Overview

```
Streamlit UI  ──▶  UserContext (role, account_id)  ──▶  build_tools(context)
     │                                                        │
     │                                                        ▼
     │                                          [search_documents, get_account,
     │                                           list_orders, list_tickets,
     │                                           calculate_order_timing,
     │                                           create_escalation,
     │                                           create_follow_up_task,
     │                                           issue_service_credit,
     │                                           (internal only) run_readonly_sql]
     │                                                        │
     └──▶  LangGraph create_react_agent(ChatAnthropic, tools, system_prompt)
                    │
                    ├─▶ TF-IDF document index over the 6 PDFs (app/retriever.py)
                    └─▶ SQLite DB built from the Excel workbook (app/build_db.py)
```

Each chat turn is a LangGraph tool-calling loop: the model reads the
question, decides which tool(s) to call, observes the results, and either
calls another tool or produces a final answer. The full message/tool trace
is shown in the UI under "Tools used" per turn.

## Why these technical choices

**LangGraph's `create_react_agent`** gives a standard ReAct loop
(reason → act → observe → repeat) with message-history checkpointing per
session (`MemorySaver`, keyed by a per-session `thread_id`), so multi-turn
conversations keep context without any custom state machine code.

**TF-IDF retrieval instead of an embeddings API.** The corpus is six short
policy/contract PDFs. A full embeddings pipeline (external API calls, a
vector DB) would add latency, cost, and an extra dependency for no
accuracy benefit at this corpus size. `scikit-learn`'s TF-IDF +
cosine-similarity is deterministic, fast, and fully offline aside from the
Anthropic chat completions themselves, which makes local development and
testing (and grading) simpler. The retriever's `search()` interface is the
only thing tools/agent code depends on, so swapping in a real vector store
later is a drop-in change if the document corpus grows.

**SQLite over pandas-in-memory.** Loading the workbook into SQLite once
(`app/build_db.py`) lets the internal "structured-data lookup or
calculation" tool support both structured helper functions (`list_orders`,
`get_account`) *and* a constrained ad-hoc `run_readonly_sql` tool for
cross-account analysis, without writing a second query engine. It also
gives a natural home for the state-changing tables (`escalations`,
`follow_up_tasks`, `service_credits`) created in the same database.

## Access control: enforced in code, not in the prompt

`app/tools.py` builds the tool list via `build_tools(context: UserContext)`.
Every tool closes over `context`; for a **customer** context,
`_enforce_account()` *always* returns the session's own `account_id`,
ignoring or overriding whatever `account_id` argument the model supplies.
This means even if the model is convinced (by a prompt-injected document, or
simply by being wrong) to ask for another account's data, the SQL query
never runs with another account's ID - the leak is structurally impossible,
not just discouraged by instructions. This is verified directly in
`tests/test_tools_access_control.py` (e.g.
`test_customer_cannot_view_another_accounts_orders`). The same applies to
the document retriever: `search_documents` passes the session's
`account_id` (or `"__ANY__"` for internal) into `DocumentIndex.search()`,
which filters ineligible chunks *before* scoring, so another customer's
contract can never be retrieved for a different customer even if it would
otherwise be the best textual match (`test_customer_search_never_leaks_other_account_agreement`).

Internal staff additionally get a `run_readonly_sql` tool, gated to
`SELECT`-only statements against a table whitelist (`accounts`, `orders`,
`tickets`) via a regex guard rejecting `INSERT/UPDATE/DELETE/DROP/ALTER/
ATTACH/PRAGMA` and any table outside the whitelist - so escalations/credits
tables can't be read or written through it, and no destructive SQL can run
through it even if the model is convinced to try.

## Confirmation before state-changing actions

Every action tool (`create_escalation`, `create_follow_up_task`,
`issue_service_credit`) is called by the model with `confirm=False` by
default. On that call, the tool **only** validates inputs and registers a
pending action in an in-memory store keyed by a random token
(`_register_pending`); it never touches the database. The tool result tells
the model to show the preview and ask the user to confirm - it explicitly
instructs the model not to claim the action is done.

The actual write happens only inside `execute_confirmed_action(token)`,
which is called directly by the Streamlit app when a user clicks a real
"Confirm & execute" button rendered next to that specific pending action.
This function is never exposed to the model as a tool - there is no tool
call the model can make that results in a database write. Even a model
that "lies" and tells the user an action was completed cannot make it true;
the token is consumed exactly once (`test_confirmed_action_executes_exactly_once`),
so replay/double-submission is also not possible.

## Trust, precedence, and conflicting sources

`app/config.py` encodes explicit reliability metadata for every source
document: `doc_type`, `status` (current/deprecated), `reliability_rank`
(1 = highest authority), `effective_date`, and `account_id` (for
customer-specific agreements). `format_chunks_for_agent()` renders this
metadata alongside every retrieved passage, and the system prompt
(`app/agent.py`) states the precedence rule explicitly: signed customer
agreement > current policy/SOP > current product docs > deprecated
documents and historical ticket resolutions, which must never be treated as
authoritative. The workbook's `historical_resolution` field on closed
tickets is explicitly called out in the prompt as "may be WRONG" - two of
the seeded historical tickets in the pack in fact contain resolutions that
contradict the *current* policy (an old 30-minute-cancellation-fee answer,
and an old 3,000-row bulk-upload-limit answer), which is a deliberate test
of whether the agent repeats stale/incorrect guidance instead of checking
current sources.

## Proactive issue detection (Problem 1)

`app/analytics.py` computes, generically over whatever tickets/orders exist:
- **SLA risk**: infers ticket severity from subject/description keywords,
  looks up the applicable SLA target (contract override if one exists,
  otherwise the plan default from Support Policy v3), and flags tickets
  that are `breached` or `at_risk` (≥70% of target elapsed) relative to the
  dataset snapshot time.
- **Recurring issue clusters**: groups open tickets by shared significant
  keywords to surface likely duplicate/related product issues, especially
  ones spanning multiple accounts.
- **Unusual order patterns**: flags orders with pickups significantly
  overdue past their window, or cancellation requests pending unusually
  long.
- **Account ticket spikes**: accounts with multiple simultaneous open
  tickets, a proxy for a broader issue affecting one customer.

None of this logic references specific record IDs from the assessment pack
- it is derived from the data present at run time.

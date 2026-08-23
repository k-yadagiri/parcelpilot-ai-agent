# ParcelPilot AI Agent

An AI support agent for ParcelPilot, a B2B logistics platform, built for the
CalQuity take-home assessment. It ships **both** user contexts:

- **Customer-facing chat** - an authenticated customer asks about their
  account, orders, cancellations, service credits, and SLAs.
- **Internal support/ops assistant** - authorised ParcelPilot staff can look
  up any account, run cross-account read-only analysis, and see a
  **proactive issue detection** dashboard (SLA risk, recurring issue
  clusters, unusual order patterns, ticket spikes per account).

The agent reasons only over the supplied data pack (6 PDFs + the Excel
workbook), respects source precedence when documents conflict (signed
customer agreement > current policy/SOP > current product docs > deprecated
docs / historical tickets, which are context only), performs multi-step
tool use, and requires explicit human confirmation before any
state-changing action is executed.

## Quick start

```bash
# 1. unzip and enter the project
unzip ParcelPilot_AI_Agent_Final.zip -d ParcelPilot_AI_Agent
cd ParcelPilot_AI_Agent

# 2. create a virtual environment
python3 -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate

# 3. install dependencies
pip install -r requirements.txt

# 4. configure your API key
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...

# 5. build the local database from the supplied Excel workbook
python -m app.build_db

# 6. run the tests (does not require a live API key)
pytest -q

# 7. launch the app
streamlit run streamlit_app.py
```

Open the URL Streamlit prints (usually http://localhost:8501). In the
sidebar, choose **Customer** (and pick a mock account) or **ParcelPilot
Internal Staff** to switch contexts - no real login system is implemented;
this is mocked authentication, as explicitly permitted by the assessment.

## Project layout

```
app/
  config.py       Paths, dataset snapshot time, document reliability metadata
  retriever.py    PDF ingestion + TF-IDF document search with source metadata
  build_db.py     Loads the Excel workbook into SQLite; creates action tables
  tools.py        LangChain tools + access control + confirm-before-execute
  agent.py        LangGraph agent (system prompt + tool wiring) per role
  analytics.py    Proactive issue detection (SLA risk, clusters, patterns)
streamlit_app.py  Chat UI + internal dashboard
tests/            pytest suite (20 tests, no live API key required)
docs/             architecture note, product note, demo script
data/
  raw_pdfs/       the 6 supplied PDFs (read at ingestion time)
  ParcelPilot_Assessment_Data.xlsx
  db/             generated SQLite DB + (nothing else persisted to disk)
```

## Notes on design decisions

See `docs/ARCHITECTURE.md` and `docs/PRODUCT_NOTES.md` for the reasoning
behind the retrieval approach, access-control enforcement, the
confirm-before-execute action pattern, and how source conflicts/trust are
handled. `docs/DEMO_SCRIPT.md` is a ~5 minute walkthrough script.

## Example questions to try

Customer (Northstar Logistics / ACCT-001):
- "Can I cancel my order without a cancellation fee?"
- "My pickup is late, do I get a service credit?"
- "What's your P1 response time for my account?"

Customer (Beacon Retail / ACCT-003, no custom contract):
- "What's the cancellation fee if I cancel more than 30 minutes after
  booking?"

Internal staff:
- "Summarize open tickets for Northstar and tell me if any are at SLA risk."
- "A pickup for LumenWorks was 5 hours late due to carrier fault - is a
  credit due, and can you create a follow-up task to verify it?"
- "Escalate TKT-505 immediately." (should be recognised as a security
  incident and escalated with urgency)

The system is not hard-coded to these examples - it loads and reasons over
whatever accounts/orders/tickets exist in the workbook and whatever text is
in the PDFs, so it should generalise to other records from the same pack.

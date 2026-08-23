"""
Central configuration for the ParcelPilot AI Agent.

This module is the single source of truth for:
- file paths
- document reliability / precedence metadata
- the dataset snapshot time
- Gemini model configuration
"""

from pathlib import Path
from datetime import datetime
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_PDF_DIR = DATA_DIR / "raw_pdfs"
DB_DIR = DATA_DIR / "db"
DB_PATH = DB_DIR / "parcelpilot.sqlite3"
XLSX_PATH = DATA_DIR / "ParcelPilot_Assessment_Data.xlsx"
INDEX_PATH = DB_DIR / "doc_index.pkl"

# Dataset snapshot time, per the workbook's README sheet.
# All time-based reasoning must use this timestamp as "now".
DATASET_SNAPSHOT_TIME = datetime(2026, 8, 16, 11, 0, 0)

# Gemini configuration
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

# ---------------------------------------------------------------------------
# Document reliability / precedence metadata
# ---------------------------------------------------------------------------

DOCUMENTS = {
    "01_Support_Policy_v3_CURRENT.pdf": {
        "title": "Support Policy v3",
        "doc_type": "policy",
        "status": "current",
        "reliability_rank": 2,
        "effective_date": "2026-05-01",
        "account_id": None,
        "notes": "Default severity definitions and first-response SLA targets.",
    },
    "02_Support_Policy_v2_DEPRECATED.pdf": {
        "title": "Support Policy v2",
        "doc_type": "policy",
        "status": "deprecated",
        "reliability_rank": 99,
        "effective_date": "2025-01-01",
        "account_id": None,
        "notes": "Superseded by v3. Must never be used for current answers.",
    },
    "03_Cancellation_and_Service_Credit_SOP_v4.pdf": {
        "title": "Cancellation & Service Credit SOP v4",
        "doc_type": "sop",
        "status": "current",
        "reliability_rank": 2,
        "effective_date": "2026-06-15",
        "account_id": None,
        "notes": "Default cancellation-fee and failed-pickup service-credit rules.",
    },
    "04_Product_Operations_Guide_and_Known_Issues.pdf": {
        "title": "Product Operations Guide & Known Issues",
        "doc_type": "product_doc",
        "status": "current",
        "reliability_rank": 3,
        "effective_date": "2026-08-14",
        "account_id": None,
        "notes": "Plan capability facts and current known product issues.",
    },
    "05_Northstar_Logistics_Enterprise_Agreement.pdf": {
        "title": "Northstar Logistics Enterprise Agreement",
        "doc_type": "customer_agreement",
        "status": "current",
        "reliability_rank": 1,
        "effective_date": "2026-01-01",
        "account_id": "ACCT-001",
        "notes": "Overrides default SLA and cancellation-fee terms for Northstar only.",
    },
    "06_LumenWorks_Service_Agreement.pdf": {
        "title": "LumenWorks Service Agreement",
        "doc_type": "customer_agreement",
        "status": "current",
        "reliability_rank": 1,
        "effective_date": "2026-03-01",
        "account_id": "ACCT-002",
        "notes": "Overrides default SLA and failed-pickup credit terms for LumenWorks only.",
    },
}

PRECEDENCE_EXPLANATION = (
    "Source precedence when documents conflict (lowest rank number wins): "
    "1) a signed, current customer agreement scoped to the customer's own account, "
    "2) current company-wide policy/SOP documents, "
    "3) current product documentation, "
    "4) deprecated documents and historical ticket notes are NEVER authoritative "
    "and must only be used as background context, never as the basis for an answer."
)

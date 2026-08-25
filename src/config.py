"""Application configuration."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
INDEX_DIR = ROOT / "indexes"
DB_DIR = ROOT / "db"
DB_PATH = DB_DIR / "parcelpilot.db"
EXCEL_PATH = DATA_DIR / "ParcelPilot.xlsx"

FAISS_INDEX_PATH = INDEX_DIR / "faiss.index"
CHUNKS_PATH = INDEX_DIR / "chunks.pkl"

TZ = ZoneInfo("Asia/Kolkata")
SNAPSHOT_TIME = datetime(2026, 8, 16, 11, 0, tzinfo=TZ)

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Groq (OpenAI-compatible). Key format: gsk_...
GROQ_API_BASE = "https://api.groq.com/openai/v1"
GROQ_MODEL = "openai/gpt-oss-20b"

DOCUMENT_REGISTRY = {
    "01_Support_Policy_v3_CURRENT.pdf": {
        "title": "Support Policy v3",
        "doc_type": "policy",
        "version": "v3",
        "status": "current",
        "customer_scope": "global",
        "reliability_rank": 2,
    },
    "02_Support_Policy_v2_DEPRECATED.pdf": {
        "title": "Support Policy v2",
        "doc_type": "policy",
        "version": "v2",
        "status": "deprecated",
        "customer_scope": "global",
        "reliability_rank": 5,
    },
    "03_Cancellation_and_Service_Credit_SOP_v4.pdf": {
        "title": "Cancellation & Service Credit SOP v4",
        "doc_type": "sop",
        "version": "v4",
        "status": "current",
        "customer_scope": "global",
        "reliability_rank": 3,
    },
    "04_Product_Operations_Guide_and_Known_Issues.pdf": {
        "title": "Product Operations Guide & Known Issues",
        "doc_type": "product_guide",
        "version": "current",
        "status": "current",
        "customer_scope": "global",
        "reliability_rank": 4,
    },
    "05_Northstar_Logistics_Enterprise_Agreement.pdf": {
        "title": "Northstar Logistics Enterprise Agreement",
        "doc_type": "agreement",
        "version": "2026",
        "status": "current",
        "customer_scope": "ACCT-001",
        "reliability_rank": 1,
    },
    "06_LumenWorks_Service_Agreement.pdf": {
        "title": "LumenWorks Service Agreement",
        "doc_type": "agreement",
        "version": "2026",
        "status": "current",
        "customer_scope": "ACCT-002",
        "reliability_rank": 1,
    },
}

DEFAULT_SLA_TARGETS = {
    "Enterprise": {"P1": 30, "P2": 120, "P3": 1440},
    "Growth": {"P1": 120, "P2": 240, "P3": 2880},
    "Standard": {"P1": 240, "P2": 480, "P3": 2880},
}

NORTHSTAR_SLA_TARGETS = {"P1": 15, "P2": 60, "P3": 480}
LUMENWORKS_SLA_TARGETS = {"P1": 120, "P2": 240, "P3": 2880}

CUSTOMER_ACCOUNTS = {
    "ACCT-001": "Northstar Logistics",
    "ACCT-002": "LumenWorks",
    "ACCT-003": "Beacon Retail",
    "ACCT-004": "Axis Labs",
}

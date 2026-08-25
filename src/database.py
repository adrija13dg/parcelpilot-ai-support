"""SQLite database setup and ingestion."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from src.config import DB_DIR, DB_PATH, EXCEL_PATH


def get_connection() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database(force: bool = False) -> None:
    if DB_PATH.exists() and not force:
        return

    if not EXCEL_PATH.exists():
        raise FileNotFoundError(f"Excel file not found: {EXCEL_PATH}")

    accounts = pd.read_excel(EXCEL_PATH, sheet_name="accounts")
    orders = pd.read_excel(EXCEL_PATH, sheet_name="orders")
    tickets = pd.read_excel(EXCEL_PATH, sheet_name="tickets")

    conn = get_connection()
    try:
        accounts.to_sql("accounts", conn, if_exists="replace", index=False)
        orders.to_sql("orders", conn, if_exists="replace", index=False)
        tickets.to_sql("tickets", conn, if_exists="replace", index=False)

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS escalations (
                escalation_id TEXT PRIMARY KEY,
                ticket_id TEXT,
                account_id TEXT,
                severity TEXT,
                reason TEXT,
                created_at TEXT,
                created_by_role TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def fetch_one(query: str, params: tuple = ()) -> sqlite3.Row | None:
    conn = get_connection()
    try:
        row = conn.execute(query, params).fetchone()
        return row
    finally:
        conn.close()


def fetch_all(query: str, params: tuple = ()) -> list[sqlite3.Row]:
    conn = get_connection()
    try:
        rows = conn.execute(query, params).fetchall()
        return rows
    finally:
        conn.close()


def execute(query: str, params: tuple = ()) -> None:
    conn = get_connection()
    try:
        conn.execute(query, params)
        conn.commit()
    finally:
        conn.close()

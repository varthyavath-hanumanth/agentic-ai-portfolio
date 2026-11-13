"""Intent routing and read-only SQLite analysis."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DB = Path(__file__).resolve().parents[1] / "data" / "sales.db"

SCENARIOS = {
    "region": {
        "needles": ("by region", "per region", "region wise"),
        "title": "Total sales by region",
        "sql": "SELECT region, ROUND(SUM(revenue), 2) AS total_revenue FROM sales GROUP BY region ORDER BY total_revenue DESC",
    },
    "product": {
        "needles": ("by product", "per product", "product wise"),
        "title": "Total sales by product",
        "sql": "SELECT product, ROUND(SUM(revenue), 2) AS total_revenue FROM sales GROUP BY product ORDER BY total_revenue DESC",
    },
    "top_products": {
        "needles": ("top products", "top 3 products", "best selling products"),
        "title": "Top 3 products by revenue",
        "sql": "SELECT product, ROUND(SUM(revenue), 2) AS total_revenue FROM sales GROUP BY product ORDER BY total_revenue DESC LIMIT 3",
    },
    "monthly": {
        "needles": ("monthly sales", "by month", "per month"),
        "title": "Monthly sales",
        "sql": "SELECT substr(order_date, 1, 7) AS month, ROUND(SUM(revenue), 2) AS total_revenue FROM sales GROUP BY month ORDER BY month",
    },
}


def initialize_database(path: str | Path = DEFAULT_DB) -> None:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS sales (
            order_id TEXT PRIMARY KEY,
            order_date TEXT NOT NULL,
            region TEXT NOT NULL,
            product TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity > 0),
            unit_price REAL NOT NULL CHECK(unit_price >= 0),
            revenue REAL NOT NULL CHECK(revenue >= 0)
        )""")
        count = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
        if count == 0:
            rows = [
                ("O-1001", "2026-01-05", "South", "Laptop Stand", 4, 1200.0, 4800.0),
                ("O-1002", "2026-01-12", "North", "Keyboard", 8, 750.0, 6000.0),
                ("O-1003", "2026-02-02", "West", "Laptop Stand", 3, 1200.0, 3600.0),
                ("O-1004", "2026-02-18", "South", "Mouse", 15, 400.0, 6000.0),
                ("O-1005", "2026-03-04", "East", "Keyboard", 6, 750.0, 4500.0),
                ("O-1006", "2026-03-21", "North", "Mouse", 10, 400.0, 4000.0),
                ("O-1007", "2026-04-08", "West", "Monitor", 2, 8500.0, 17000.0),
                ("O-1008", "2026-04-19", "South", "Monitor", 1, 8500.0, 8500.0),
                ("O-1009", "2026-05-11", "East", "Laptop Stand", 5, 1200.0, 6000.0),
                ("O-1010", "2026-05-27", "North", "Monitor", 2, 8500.0, 17000.0),
            ]
            conn.executemany("INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
        conn.commit()


def classify_question(question: str) -> dict[str, str] | None:
    text = question.lower()
    # Check top-products before generic product intent.
    for key in ("top_products", "region", "monthly", "product"):
        scenario = SCENARIOS[key]
        if any(needle in text for needle in scenario["needles"]):
            return {"key": key, "title": scenario["title"], "sql": scenario["sql"]}
    return None


def run_read_only_query(path: str | Path, sql: str) -> tuple[list[str], list[tuple[Any, ...]]]:
    normalized = sql.lstrip().lower()
    if not normalized.startswith("select") or ";" in normalized:
        raise ValueError("Only a single read-only SELECT query is allowed.")
    db_uri = Path(path).resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(db_uri, uri=True)
    try:
        cursor = conn.execute(sql)
        columns = [item[0] for item in cursor.description or []]
        return columns, cursor.fetchall()
    finally:
        conn.close()


def analyze_question(question: str, db_path: str | Path = DEFAULT_DB) -> dict[str, Any]:
    initialize_database(db_path)
    scenario = classify_question(question)
    if scenario is None:
        return {
            "question": question,
            "status": "unsupported_question",
            "message": "I can analyze sales by region, by product, top products, or by month. Try one of those questions.",
            "columns": [],
            "rows": [],
        }
    columns, rows = run_read_only_query(db_path, scenario["sql"])
    return {
        "question": question,
        "status": "completed",
        "title": scenario["title"],
        "sql_template": scenario["sql"],
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "safety": "Executed an allowlisted SELECT query against the sample database in read-only mode.",
    }


def render_markdown_report(result: dict[str, Any]) -> str:
    if result["status"] != "completed":
        return f"# Analysis request\n\n**Question:** {result['question']}\n\n{result['message']}\n"
    lines = [f"# {result['title']}", "", f"**Question:** {result['question']}", "", "| " + " | ".join(result["columns"]) + " |", "| " + " | ".join("---" for _ in result["columns"]) + " |"]
    for row in result["rows"]:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    lines += ["", f"Rows: {result['row_count']}", "", f"Safety: {result['safety']}", ""]
    return "\n".join(lines)

"""Deterministic invoice extraction, validation, and JSON-ready output."""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


PATTERNS = {
    "invoice_number": r"(?im)^\s*invoice\s*(?:number|no\.?)\s*:\s*(.+?)\s*$",
    "invoice_date": r"(?im)^\s*date\s*:\s*(.+?)\s*$",
    "supplier": r"(?im)^\s*(?:supplier|vendor)\s*:\s*(.+?)\s*$",
    "subtotal": r"(?im)^\s*subtotal\s*:\s*[$₹]?\s*([\d,]+(?:\.\d{1,2})?)\s*$",
    "tax": r"(?im)^\s*tax\s*:\s*[$₹]?\s*([\d,]+(?:\.\d{1,2})?)\s*$",
    "total": r"(?im)^\s*total\s*:\s*[$₹]?\s*([\d,]+(?:\.\d{1,2})?)\s*$",
}


def _money(value: str | None) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(value.replace(",", "").strip()).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def extract_invoice(text: str) -> dict[str, Any]:
    """Extract labelled fields from invoice text; absent values remain None."""
    record: dict[str, Any] = {}
    for field, pattern in PATTERNS.items():
        match = re.search(pattern, text)
        value = match.group(1).strip() if match else None
        if field in {"subtotal", "tax", "total"}:
            amount = _money(value)
            record[field] = str(amount) if amount is not None else None
        else:
            record[field] = value
    return record


def validate_invoice(record: dict[str, Any]) -> list[str]:
    """Return human-readable validation issues."""
    issues: list[str] = []
    for field in ("invoice_number", "invoice_date", "supplier", "subtotal", "tax", "total"):
        if not record.get(field):
            issues.append(f"Missing or invalid required field: {field}")
    subtotal, tax, total = (_money(record.get(k)) for k in ("subtotal", "tax", "total"))
    if subtotal is not None and tax is not None and total is not None:
        expected = (subtotal + tax).quantize(Decimal("0.01"))
        if expected != total:
            issues.append(
                f"Total mismatch: subtotal + tax is {expected}, but invoice total is {total}"
            )
    for field in ("subtotal", "tax", "total"):
        amount = _money(record.get(field))
        if amount is not None and amount < 0:
            issues.append(f"Amount cannot be negative: {field}")
    return issues


def process_invoice_text(text: str, source: str = "text-input") -> dict[str, Any]:
    record = extract_invoice(text)
    issues = validate_invoice(record)
    return {
        "source": source,
        "document_type": "invoice",
        "status": "needs_review" if issues else "validated",
        "fields": record,
        "validation_issues": issues,
        "human_review_required": bool(issues),
    }


def process_invoice_file(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    return process_invoice_text(file_path.read_text(encoding="utf-8"), str(file_path))

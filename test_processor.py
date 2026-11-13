from document_agent.processor import process_invoice_text, validate_invoice

GOOD = """Invoice Number: INV-1
Date: 2026-11-10
Supplier: Sample Vendor
Subtotal: 100.00
Tax: 18.00
Total: 118.00
"""


def test_valid_invoice():
    result = process_invoice_text(GOOD)
    assert result["status"] == "validated"
    assert result["human_review_required"] is False


def test_total_mismatch_requires_review():
    result = process_invoice_text(GOOD.replace("Total: 118.00", "Total: 120.00"))
    assert result["status"] == "needs_review"
    assert any("Total mismatch" in issue for issue in result["validation_issues"])


def test_missing_field_is_flagged():
    issues = validate_invoice({"invoice_number": "INV-2"})
    assert any("supplier" in issue for issue in issues)

"""Command-line interface for the document processing agent."""
import argparse
import json
from pathlib import Path
from .processor import process_invoice_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract and validate a labelled text invoice.")
    parser.add_argument("input", help="Path to invoice .txt file")
    parser.add_argument("--output", default="invoice_result.json", help="Output JSON path")
    args = parser.parse_args()
    result = process_invoice_file(args.input)
    Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(f"\nSaved result to {args.output}")


if __name__ == "__main__":
    main()

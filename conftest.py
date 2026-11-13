from pathlib import Path
import sys

# Make this standalone project importable when tests run from the portfolio root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

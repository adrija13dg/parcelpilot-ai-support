"""One-time FAISS index builder. Re-run after adding new PDFs to data/."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.database import init_database
from src.rag import DocumentIndex


def main() -> None:
    print("Initializing SQLite database...")
    init_database(force=True)

    print("Building FAISS document index...")
    index = DocumentIndex()
    index.build()
    print(f"Indexed {len(index.chunks)} chunks.")
    print("Done. Commit indexes/ and db/ for fast Streamlit Cloud startup.")


if __name__ == "__main__":
    main()

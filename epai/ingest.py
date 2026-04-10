"""
EPAi — Dataingestion
PDF (inkl. OCR för inskannade) + Excel → ChromaDB + SQLite-metadata.

Kör:
  python epai/ingest.py --anlaggning all
  python epai/ingest.py --anlaggning 1
  python epai/ingest.py --anlaggning all --force-reindex
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterator

import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter

from config import (
    ANLAGGNINGAR, CHUNK_OVERLAP, CHUNK_SIZE, CHROMA_PATH,
    DOCTYPE_HINTS, EXCEL_CHUNK_ROWS, GLOBAL_COLLECTION,
    GLOBAL_DOCTYPE_KEYS, METADATA_DB_PATH, RAW_DATA_PATH,
)
from metadata_db import IngestedFile, MetadataDB
from ocr_utils import extract_text_with_ocr, needs_ocr

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("epai.ingest")

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    length_function=len,
)

# ── Hjälpfunktioner ────────────────────────────────────────────────────────────

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def _detect_doctype(filename: str) -> str:
    lower = filename.lower()
    for dtype, hints in DOCTYPE_HINTS.items():
        if any(h in lower for h in hints):
            return dtype
    return "okänd"


def _is_global_doc(doc_type: str) -> bool:
    return doc_type in GLOBAL_DOCTYPE_KEYS


def _iter_files(directory: Path) -> Iterator[Path]:
    for ext in ("*.pdf", "*.PDF", "*.xlsx", "*.xls", "*.XLSX", "*.XLS"):
        yield from directory.rglob(ext)


# ── PDF-extraktion ─────────────────────────────────────────────────────────────

def _extract_pdf(path: Path) -> tuple[str, bool]:
    """
    Returnerar (text, ocr_used).
    Försöker pdfplumber → OCR om text är för tunn.
    """
    text = ""
    num_pages = 1
    ocr_used = False

    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            num_pages = max(len(pdf.pages), 1)
            parts = [p.extract_text() or "" for p in pdf.pages]
            text = "\n".join(parts).strip()
    except Exception as e:
        log.warning("pdfplumber misslyckades för %s: %s", path.name, e)

    if needs_ocr(text, num_pages):
        log.info("  → OCR aktiveras för %s (text/sida < 100 tecken)", path.name)
        ocr_text = extract_text_with_ocr(path)
        if ocr_text:
            text = ocr_text
            ocr_used = True
        elif not text:
            # Fallback: pypdf
            try:
                from pypdf import PdfReader
                reader = PdfReader(str(path))
                text = "\n".join(p.extract_text() or "" for p in reader.pages).strip()
            except Exception as e:
                log.error("pypdf fallback misslyckades för %s: %s", path.name, e)

    return text, ocr_used


# ── Excel-extraktion ───────────────────────────────────────────────────────────

def _extract_excel(path: Path) -> list[str]:
    """Konvertera Excel-rader till text-chunks à EXCEL_CHUNK_ROWS rader."""
    import pandas as pd
    chunks: list[str] = []
    try:
        xl = pd.ExcelFile(path)
        for sheet in xl.sheet_names:
            df = xl.parse(sheet).fillna("").astype(str)
            headers = list(df.columns)
            rows_text: list[str] = []
            for _, row in df.iterrows():
                parts = [f"{h}: {v}" for h, v in zip(headers, row) if v.strip()]
                if parts:
                    rows_text.append(" | ".join(parts))

            # Gruppera i chunks om EXCEL_CHUNK_ROWS rader
            for start in range(0, len(rows_text), EXCEL_CHUNK_ROWS):
                group = rows_text[start:start + EXCEL_CHUNK_ROWS]
                chunk_text = (
                    f"[{path.stem} — {sheet} — rader {start + 1}–{start + len(group)}]\n"
                    + "\n".join(group)
                )
                chunks.append(chunk_text)
    except Exception as e:
        log.error("Excel-läsning misslyckades för %s: %s", path.name, e)
    return chunks


# ── ChromaDB ───────────────────────────────────────────────────────────────────

def _chroma_client() -> chromadb.ClientAPI:
    path = Path(CHROMA_PATH)
    path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(path),
        settings=Settings(anonymized_telemetry=False),
    )


def _upsert_chunks(
    client: chromadb.ClientAPI,
    collection_name: str,
    ids: list[str],
    documents: list[str],
    metadatas: list[dict],
    batch_size: int = 100,
) -> None:
    col = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )
    for i in range(0, len(ids), batch_size):
        col.upsert(
            ids=ids[i:i + batch_size],
            documents=documents[i:i + batch_size],
            metadatas=metadatas[i:i + batch_size],
        )


# ── Kärningest ─────────────────────────────────────────────────────────────────

def ingest_file(
    path: Path,
    customer_id: str,
    collection_name: str,
    chroma: chromadb.ClientAPI,
    db: MetadataDB,
    force: bool = False,
) -> int:
    """
    Ingestera en enskild fil. Returnerar antal tillagda chunks (0 = hoppad).
    """
    hash_val = _sha256(path)
    if not force and db.already_ingested(hash_val):
        log.debug("Hoppar över (redan indexerad): %s", path.name)
        return 0

    doc_type = _detect_doctype(path.name)
    is_excel = path.suffix.lower() in {".xlsx", ".xls"}
    ocr_used = False

    log.info("Bearbetar: %s [%s]", path.name, doc_type)

    # Extrahera text-chunks
    if is_excel:
        raw_chunks = _extract_excel(path)
        chunk_meta_extra = [
            {"rowRange": f"{i * EXCEL_CHUNK_ROWS + 1}–{(i + 1) * EXCEL_CHUNK_ROWS}"}
            for i in range(len(raw_chunks))
        ]
    else:
        raw_text, ocr_used = _extract_pdf(path)
        if not raw_text:
            log.warning("Ingen text extraherad från %s — hoppar", path.name)
            return 0
        raw_chunks = _splitter.split_text(raw_text)
        chunk_meta_extra = [{"pageNumber": ""}] * len(raw_chunks)

    if not raw_chunks:
        log.warning("Inga chunks genererade från %s", path.name)
        return 0

    ts = datetime.fromtimestamp(path.stat().st_mtime).isoformat()
    base_meta = {
        "customerId":    customer_id,
        "fileName":      path.name,
        "documentType":  doc_type,
        "dataSource":    "manuell_upload",
        "timeStamp":     ts,
        "hashValue":     hash_val,
        "collection":    collection_name,
    }

    ids = [f"{hash_val}_{i}" for i in range(len(raw_chunks))]
    metadatas = [{**base_meta, **extra} for extra in chunk_meta_extra]

    _upsert_chunks(chroma, collection_name, ids, raw_chunks, metadatas)

    # Logga i SQLite
    db.record(IngestedFile(
        customer_id=customer_id,
        file_name=path.name,
        document_type=doc_type,
        data_source="manuell_upload",
        time_stamp=datetime.now().isoformat(),
        hash_value=hash_val,
        chroma_ids=",".join(ids),
        ocr_used=int(ocr_used),
    ))

    log.info("  ✓ %d chunks → collection '%s'%s",
             len(raw_chunks), collection_name, " (OCR)" if ocr_used else "")
    return len(raw_chunks)


def ingest_directory(
    directory: Path,
    customer_id: str,
    chroma: chromadb.ClientAPI,
    db: MetadataDB,
    force: bool = False,
) -> int:
    """Ingestera alla filer i directory, routing till rätt collection."""
    total = 0
    for path in _iter_files(directory):
        doc_type = _detect_doctype(path.name)
        col = GLOBAL_COLLECTION if _is_global_doc(doc_type) else customer_id
        total += ingest_file(path, customer_id, col, chroma, db, force)
    return total


def run_full_ingest(
    targets: list[str],
    force: bool = False,
) -> dict[str, int]:
    """Kör ingestion för angivna anläggningar + global-katalogen."""
    chroma = _chroma_client()
    stats: dict[str, int] = {}

    with MetadataDB(METADATA_DB_PATH) as db:
        for anl_key in targets:
            anl_dir = Path(RAW_DATA_PATH) / anl_key
            if not anl_dir.exists():
                anl_dir.mkdir(parents=True, exist_ok=True)
                log.info("Katalog skapad (tom): %s", anl_dir)
                stats[anl_key] = 0
                continue
            n = ingest_directory(anl_dir, anl_key, chroma, db, force)
            stats[anl_key] = n

        # Global-katalog (vitböcker, lagar, manualer, kataloger)
        global_dir = Path(RAW_DATA_PATH) / "global"
        if global_dir.exists():
            n = ingest_directory(global_dir, "global", chroma, db, force)
            stats[GLOBAL_COLLECTION] = n
        else:
            global_dir.mkdir(parents=True, exist_ok=True)
            stats[GLOBAL_COLLECTION] = 0

    return stats


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="EPAi — Dataingestion")
    parser.add_argument(
        "--anlaggning",
        type=str,
        default="all",
        choices=["1", "2", "3", "all"],
        help="Vilken anläggning att ingestera (default: all)",
    )
    parser.add_argument(
        "--force-reindex",
        action="store_true",
        help="Tvinga omindexering av redan processade filer",
    )
    args = parser.parse_args()

    if args.anlaggning == "all":
        targets = list(ANLAGGNINGAR.keys())
    else:
        targets = [f"anlaggning_{args.anlaggning}"]

    print("\n🌊 EPAi Dataingestion")
    print("─" * 45)
    stats = run_full_ingest(targets, force=args.force_reindex)
    print("\nResultat:")
    for col, n in stats.items():
        print(f"  {col:25s}: {n} nya chunks")
    print("─" * 45)
    print("✓ Ingestion klar\n")


if __name__ == "__main__":
    main()

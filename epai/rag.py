"""
EPAi — RAG-pipeline
LangChain + Ollama (lokal) + ChromaDB. Hanterar följdfrågor via full konversationshistorik.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator, Optional

import chromadb
from chromadb.config import Settings
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_ollama import ChatOllama

from config import (
    ANLAGGNINGAR, CHROMA_PATH, EMBEDDING_MODEL, GLOBAL_COLLECTION,
    OLLAMA_BASE_URL, OLLAMA_MODEL, SYSTEM_PROMPT, TOP_K_RESULTS,
)

log = logging.getLogger("epai.rag")


# ── Dataklasser ────────────────────────────────────────────────────────────────

@dataclass
class Source:
    file_name:    str
    doc_type:     str
    customer_id:  str
    collection:   str
    page_or_row:  str
    excerpt:      str    # max 200 tecken


@dataclass
class RAGResult:
    answer:         str
    sources:        list[Source] = field(default_factory=list)
    model:          str = OLLAMA_MODEL
    anlaggning:     str = ""
    n_chunks_used:  int = 0
    error:          Optional[str] = None


# ── ChromaDB-helpers ───────────────────────────────────────────────────────────

def _chroma_client() -> chromadb.ClientAPI:
    path = Path(CHROMA_PATH)
    path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(path),
        settings=Settings(anonymized_telemetry=False),
    )


def _embeddings(model: str = EMBEDDING_MODEL) -> OllamaEmbeddings:
    return OllamaEmbeddings(base_url=OLLAMA_BASE_URL, model=model)


def _collections_for(anlaggning: str) -> list[str]:
    if anlaggning == "alla":
        return list(ANLAGGNINGAR.keys()) + [GLOBAL_COLLECTION]
    return [anlaggning, GLOBAL_COLLECTION]


def _fetch_docs(question: str, collections: list[str], k: int = TOP_K_RESULTS) -> list:
    """Hämta relevanta chunks från ChromaDB."""
    client = _chroma_client()
    emb    = _embeddings()
    docs   = []

    for col_name in collections:
        try:
            store = Chroma(
                client=client,
                collection_name=col_name,
                embedding_function=emb,
            )
            results = store.similarity_search(question, k=k)
            docs.extend(results)
        except Exception as e:
            log.warning("Collection '%s' ej tillgänglig: %s", col_name, e)

    return docs


def _format_context(docs: list) -> str:
    parts = []
    for doc in docs:
        m    = doc.metadata
        src  = f"[{m.get('fileName', '?')} — {m.get('documentType', '?')}]"
        parts.append(f"{src}\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def _docs_to_sources(docs: list) -> list[Source]:
    seen: set[str] = set()
    sources: list[Source] = []
    for doc in docs:
        m   = doc.metadata
        key = f"{m.get('fileName', '')}_{m.get('customerId', '')}"
        if key not in seen:
            seen.add(key)
            sources.append(Source(
                file_name=m.get("fileName", "okänd"),
                doc_type=m.get("documentType", "okänd"),
                customer_id=m.get("customerId", ""),
                collection=m.get("collection", ""),
                page_or_row=m.get("pageNumber", m.get("rowRange", "")),
                excerpt=doc.page_content[:200],
            ))
    return sources


# ── Konversationshistorik → LangChain-messages ────────────────────────────────

def _build_messages(
    context: str,
    question: str,
    history: list[dict],
) -> list:
    """Bygg messages-lista med full historik för följdfråge-stöd."""
    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    # Historik (tidigare frågor + svar)
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    # Aktuell fråga med kontext
    user_content = (
        f"Besvara frågan nedan baserat ENBART på följande kontext.\n"
        f"Om svaret inte finns i kontexten, säg tydligt att du saknar underlag.\n\n"
        f"KONTEXT:\n{context}\n\n"
        f"FRÅGA: {question}\n\n"
        f"Svara utförligt och hänvisa till källdokument (filnamn) i ditt svar."
    )
    messages.append(HumanMessage(content=user_content))
    return messages


# ── Publik API ────────────────────────────────────────────────────────────────

def ask(
    question: str,
    anlaggning: str = "anlaggning_1",
    history: Optional[list[dict]] = None,
    model: str = OLLAMA_MODEL,
    k: int = TOP_K_RESULTS,
) -> RAGResult:
    """
    Ställ en fråga till Ain (synkron).

    Args:
        question:    Användarens fråga.
        anlaggning:  "anlaggning_1" / "anlaggning_2" / "anlaggning_3" / "alla"
        history:     Konversationshistorik [{"role": "user"|"assistant", "content": str}]
        model:       Ollama-modellnamn.
        k:           Antal chunks per collection.

    Returns:
        RAGResult med answer, sources, n_chunks_used.
    """
    history = history or []
    collections = _collections_for(anlaggning)
    docs = _fetch_docs(question, collections, k=k)

    if not docs:
        return RAGResult(
            answer=(
                "Inga dokument har indexerats ännu för denna anläggning. "
                "Kör 'Uppdatera dokumentindex' eller python epai/ingest.py --anlaggning all."
            ),
            anlaggning=anlaggning,
            error="no_documents",
        )

    context  = _format_context(docs)
    messages = _build_messages(context, question, history)

    llm = ChatOllama(
        base_url=OLLAMA_BASE_URL,
        model=model,
        temperature=0.1,
    )

    try:
        response = llm.invoke(messages)
        answer   = response.content
    except Exception as e:
        log.error("LLM-anrop misslyckades: %s", e)
        return RAGResult(
            answer=f"Tekniskt fel vid LLM-anrop: {e}",
            anlaggning=anlaggning,
            model=model,
            error=str(e),
        )

    return RAGResult(
        answer=answer,
        sources=_docs_to_sources(docs),
        model=model,
        anlaggning=anlaggning,
        n_chunks_used=len(docs),
    )


def stream_ask(
    question: str,
    anlaggning: str = "anlaggning_1",
    history: Optional[list[dict]] = None,
    model: str = OLLAMA_MODEL,
    k: int = TOP_K_RESULTS,
) -> Generator[str | list[Source], None, None]:
    """
    Streama Ains svar token för token (används av Streamlit).

    Yields:
        str tokens under streaming.
        list[Source] som sista yield (källreferenserna).
    """
    history     = history or []
    collections = _collections_for(anlaggning)
    docs        = _fetch_docs(question, collections, k=k)

    if not docs:
        yield (
            "Inga dokument har indexerats ännu. "
            "Kör 'Uppdatera dokumentindex' i sidebaren."
        )
        yield []
        return

    context  = _format_context(docs)
    messages = _build_messages(context, question, history)

    llm = ChatOllama(
        base_url=OLLAMA_BASE_URL,
        model=model,
        temperature=0.1,
    )

    try:
        for chunk in llm.stream(messages):
            yield chunk.content
    except Exception as e:
        log.error("LLM-streaming misslyckades: %s", e)
        yield f"\n\n⚠️ Tekniskt fel: {e}"

    yield _docs_to_sources(docs)


def get_collection_counts() -> dict[str, int]:
    """Hämta antal indexerade chunks per collection."""
    try:
        client = _chroma_client()
        counts: dict[str, int] = {}
        for col_name in list(ANLAGGNINGAR.keys()) + [GLOBAL_COLLECTION]:
            try:
                col = client.get_collection(col_name)
                counts[col_name] = col.count()
            except Exception:
                counts[col_name] = 0
        return counts
    except Exception:
        return {}

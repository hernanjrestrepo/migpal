import argparse
import os
import re
from typing import List

import httpx
from sqlmodel import Session, select

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "backend") not in sys.path:
    sys.path.append(str(ROOT / "backend"))

from app.db.session import engine
from app.models.scraped_document import ScrapedDocument
from app.models.zillow_listing import ZillowListing
from app.models.business_listing import BusinessListing


def fetch_documents(limit: int = 50) -> List[ScrapedDocument]:
    with Session(engine) as session:
        docs = session.exec(
            select(ScrapedDocument).order_by(ScrapedDocument.created_at.desc()).limit(limit)
        ).all()
    return docs


def rank_documents(question: str, docs: List[ScrapedDocument], top_k: int = 3) -> List[ScrapedDocument]:
    tokens = re.findall(r"\w+", question.lower())
    scores = []
    for doc in docs:
        content = (doc.content or "").lower()
        score = sum(content.count(tok) for tok in tokens)
        scores.append((score, doc))
    scores.sort(key=lambda x: x[0], reverse=True)
    return [doc for score, doc in scores[:top_k] if score > 0]


def build_context(question: str) -> str:
    docs = fetch_documents()
    relevant = rank_documents(question, docs)

    context_parts = []
    for doc in relevant:
        snippet = doc.content[:1200]
        context_parts.append(f"Fuente: {doc.title}\n{snippet}\n")

    with Session(engine) as session:
        rental = session.exec(select(ZillowListing).order_by(ZillowListing.created_at.desc())).first()
        business = session.exec(select(BusinessListing).order_by(BusinessListing.created_at.desc())).first()
    if rental:
        context_parts.append(f"Última renta: {rental.address} en {rental.city}, {rental.state} por {rental.price_usd} USD\n")
    if business:
        context_parts.append(f"Último negocio: {business.title} en {business.city or ''} {business.state or ''}\n")

    if not context_parts:
        context_parts.append("No hay documentos relevantes, responde con conocimientos generales verificados.")

    return "\n".join(context_parts)


def ask_ollama(question: str, model: str, context: str, temperature: float = 0.2) -> str:
    ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
    system_prompt = (
        "Eres MigPAL Atlas, asistente experto en procesos migratorios. "
        "Usa únicamente el contexto proporcionado; si algo falta, dilo explícitamente."
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Contexto:\n{context}\n\nPregunta:\n{question}",
            },
        ],
        "options": {"temperature": temperature},
        "stream": False,
    }
    with httpx.Client(timeout=120.0) as client:
        response = client.post(f"{ollama_url}/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()
    return data.get("message", {}).get("content", "")


def run_simulation(question: str, model: str) -> str:
    context = build_context(question)
    answer = ask_ollama(question, model, context)
    return answer


def main():
    parser = argparse.ArgumentParser(description="Simulador del bot MigPAL con RAG + Ollama")
    parser.add_argument("question", help="Pregunta del usuario")
    parser.add_argument("--model", default=os.getenv("AI_MODEL", "llama3.1:70b"))
    args = parser.parse_args()

    result = run_simulation(args.question, args.model)
    print("=== Respuesta del bot ===")
    print(result)


if __name__ == "__main__":
    main()

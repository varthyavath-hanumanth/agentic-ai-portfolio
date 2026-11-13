"""Simple retrieval-and-draft support agent with source attribution."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DEFAULT_KB = Path(__file__).resolve().parents[1] / "knowledge_base.json"
STOP_WORDS = {"the", "a", "an", "is", "are", "i", "my", "me", "to", "for", "of", "and", "or", "how", "do", "can", "what", "where", "please"}


def tokenize(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP_WORDS}


def load_knowledge_base(path: str | Path = DEFAULT_KB) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def retrieve(question: str, articles: list[dict[str, Any]], top_k: int = 3) -> list[dict[str, Any]]:
    query_terms = tokenize(question)
    scored = []
    for article in articles:
        searchable = " ".join([article.get("title", ""), article.get("content", ""), *article.get("keywords", [])])
        terms = tokenize(searchable)
        overlap = query_terms & terms
        if overlap:
            score = len(overlap) / max(len(query_terms), 1)
            scored.append((score, article))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [dict(article, relevance=round(score, 3)) for score, article in scored[:top_k]]


def answer_question(question: str, articles: list[dict[str, Any]] | None = None, top_k: int = 3) -> dict[str, Any]:
    articles = articles if articles is not None else load_knowledge_base()
    matches = retrieve(question, articles, top_k)
    if not matches:
        draft = (
            "I couldn't find a reliable answer in the current help articles. "
            "Please route this question to a support specialist."
        )
    else:
        lines = [f"- {item['title']}: {item['content']}" for item in matches]
        draft = (
            "Thanks for reaching out. Based on our help information:\n"
            + "\n".join(lines)
            + "\n\nIf this does not resolve the issue, please let our support team know."
        )
    return {
        "question": question,
        "draft_reply": draft,
        "sources": [{"id": item["id"], "title": item["title"]} for item in matches],
        "status": "draft_for_human_review",
        "human_approval_required": True,
    }

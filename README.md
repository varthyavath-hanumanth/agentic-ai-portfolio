# 02 — Customer Support AI Agent

A grounded support workflow that searches a small knowledge base, selects relevant passages, and drafts a reply with source IDs. The output is explicitly a draft for human review.

## Workflow

1. Normalize the user's question.
2. Score knowledge-base articles using transparent keyword overlap.
3. Retrieve the best matching entries.
4. Draft a response only from retrieved material.
5. Show source IDs and a human-review reminder.

This starter version does not call an external LLM. That makes it free to run and easy to inspect. A future LLM can rewrite the retrieved facts, but should not invent policy.

## Run

```bash
python -m support_agent.cli "How do I reset my password?"
```

Use `--top-k 3` to change the number of retrieved articles.

## Tests

```bash
pytest 02-customer-support-agent/tests
```

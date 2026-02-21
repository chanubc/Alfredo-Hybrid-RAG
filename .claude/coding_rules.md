# 🛠 Coding Rules

## DI Strategy

Use FastAPI Depends.

Example:

```python
def get_agent_service(
    repo: LinkRepository = Depends(get_repository),
    llm: LLMClient = Depends(get_llm_client)
) -> AgentService:
    return AgentService(repo, llm)
```

---

## Domain Rules

- Pure functions only.
- No FastAPI imports.
- No SQLAlchemy imports.
- No HTTP calls.

---

## Repository Rules

- Only database logic.
- No business logic.
- No scoring logic.

---

## Service Rules

- Orchestration only.
- No raw SQL.
- Call domain for calculations.

---

## General

- Use type hints on all functions.
- Keep functions small.
- Follow Conventional Commits.
- Avoid premature abstraction.

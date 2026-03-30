# LinkdBot-RAG Project AGENTS.md

- Global OMX / runtime / skill behavior lives in `/home/chanu/AGENTS.md`
- This file is only for LinkdBot-RAG-specific rules
- Do not modify `CLAUDE.md` unless explicitly asked

## Project state

- This repo is effectively at **Phase 3 complete / Phase 4 preparation**
- Phase 4 means preparing for **LangGraph orchestration**
- Prefer incremental cleanup before broad framework rewrites

## Source of truth

- `CLAUDE.md` and `.claude/*` are reference docs for this repo
- `.claude/` is already indexed here
- Read them only when relevant to the task
- If docs and code differ, trust the current code structure first

## Architecture rules

- `app/api/` → presentation only
- `app/application/` → use cases, services, ports, agent orchestration
- `app/domain/` → pure domain logic and repository interfaces
- `app/infrastructure/` → repositories, adapters, external clients, RAG implementation

- keep domain logic pure
- use FastAPI `Depends` for DI only
- depend on interfaces / ports in application code
- create concrete implementations in DI factories
- avoid circular imports
- avoid collapsing layers for convenience

## Repo coding rules

- prefer small, reviewable, reversible diffs
- reuse existing utils and patterns before adding abstractions
- avoid thin pass-through wrappers
- keep responsibilities clear:
  - `TelegramWebhookHandler` → webhook/input branching
  - `MessageRouterService` → command/intent routing
  - use cases → business write flows
  - agent layer → answer generation/orchestration
- add or update tests when behavior changes
- verify before claiming completion

## Phase 4 guidance

- use LangGraph as an orchestration layer
- reuse existing RAG, repository, and domain logic where possible
- prefer nodes that compose existing code instead of reimplementing it
- prefer agent logic that can return structured results/state
- avoid broad LangChain abstractions unless they clearly simplify the codebase

## Workflow note

For feature/issue/branch startup workflow, use:

- `.claude/commands/start-feature.md`
- `.agents/skills/start-feature/SKILL.md`

## GitNexus workflow

- This repo is indexed in GitNexus as `LinkdBot-RAG`
- prefer `gitnexus_query` or `gitnexus_context` before broad grep when the task is "how does this work?", "where is this used?", or "what calls this?"
- run `gitnexus_impact` before changing shared functions, classes, repository methods, or routing logic
- run `gitnexus_context` plus `gitnexus_impact` before refactor, extract, move, or rename work
- run `gitnexus_detect_changes` before finishing larger code changes to confirm the expected scope
- use `rg` for raw text lookup, exact strings, and quick file discovery; use GitNexus for relationships, blast radius, and execution flow
- if GitNexus results look stale relative to the current branch, refresh the index with `npx gitnexus analyze` before relying on it

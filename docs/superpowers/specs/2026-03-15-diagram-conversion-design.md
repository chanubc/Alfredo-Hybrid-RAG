# Diagram Conversion Design — Mermaid Handdrawn Theme

**Date:** 2026-03-15
**Status:** Approved
**Scope:** Convert `system-flow.svg` and `clean-architecture.svg` to Mermaid format with handdrawn sketch theme

---

## Objective

Replace static SVG architecture diagrams with Mermaid diagrams using `look: "handDrawn"` + `theme: "base"` for a sketchy, informal visual style while maintaining clarity and reducing maintenance burden (Git diff-friendly text instead of binary SVG).

---

## Current State

| File | Type | Location | Diagram Type |
|------|------|----------|--------------|
| `system-flow.svg` | SVG | `docs/assets/` | Message processing pipeline (Telegram → Webhook → UseCase → DB) |
| `clean-architecture.svg` | SVG | `docs/assets/` | Concentric circles (Clean Architecture layers) |
| `archi-flow.xml` | SVG (mislabeled) | `docs/assets/` | Duplicate of system-flow.svg (to be deleted) |

---

## Design Decisions

### 1. **Format: draw.io with Sketch Theme**

**Choice:** draw.io (XML format) + SVG export + Sketch style

**Reasoning:**
- **Precise layout control** — SearchUseCase and PostgreSQL can be perfectly centered
- **Sketch theme** — draw.io sketch style matches handdrawn aesthetic
- **SVG export** — for embedding in README (vector, not raster)
- **Source control** — store `.drawio` XML files in git for version history
- **Editability** — easy to edit with draw.io app, VSCode extension, or web editor

**Files:**
- `docs/assets/system-flow.drawio` — source XML
- `docs/assets/system-flow.svg` — exported for README embedding

---

### 2. **Scope: Two Diagrams**

**Include:** `system-flow.svg` + `clean-architecture.svg`
**Delete:** `archi-flow.xml` (duplicate of updated system-flow)

---

### 3. **Storage Location: Separate .md Files**

**Format:**
- `docs/assets/system-flow.md` — Mermaid code + title + description
- `docs/assets/clean-architecture.md` — Mermaid code + title + description

**Rationale:**
- Text-based (Git-friendly)
- README links to .md files instead of embedding SVG images
- Easy to view/edit in any Markdown editor
- Source of truth for diagram logic

---

### 4. **system-flow.drawio — Pipeline with Layer Colors & Perfect Centering**

**Diagram Structure:**

```
        👤 Telegram User
              ↓
        📱 Telegram API
              ↓
        🔗 POST /webhook
              ↓
    WebhookHandler + TelegramWebhookHandler
              ↓
     MessageRouter + IntentClassifier
          ↙  ↓  ↘
   SaveLink Search  Knowledge
   UseCase UseCase  Agent
   (Left)  (Center) (Right)
          ↙  ↓  ↘
      🗄️ PostgreSQL (Center)
           ↓
    💬 Telegram Response
```

**Layers & Colors:**
| Layer | Color | Components |
|-------|-------|------------|
| **Input** (Blue) | `#dbeafe` | Telegram User, API, Webhook endpoint |
| **Process** (Green) | `#dcfce7` | Handler, Router, UseCases (SaveLink, Search, KnowledgeAgent) |
| **Storage** (Orange) | `#fed7aa` | PostgreSQL + pgvector |
| **External** (Purple) | `#f3e8ff` | Jina Reader, OpenAI API |

**Key Design Features:**
- **3-way branching from MessageRouter** → SaveLinkUseCase (left), SearchUseCase (center), KnowledgeAgent (right)
- **SearchUseCase centered** with HybridRetriever breakdown: "Dense · Sparse · Rerank"
- **PostgreSQL centered** — convergence point
- **Dashed edges** — external service calls (Jina Reader, OpenAI API)
- **Sketch style** — handdrawn aesthetic with rounded corners

**Implementation:**
1. Use draw.io app/VSCode extension to create `system-flow.drawio`
2. Manual layout ensures perfect centering (SearchUseCase and PostgreSQL aligned vertically)
3. Apply sketch style in draw.io settings
4. Export to `system-flow.svg` (File → Export As → SVG)

---

### 5. **clean-architecture.drawio — Concentric Layers (Original Design)**

**Diagram Structure:**

Restore the original concentric circles design using draw.io's shape grouping/nesting:

```
     ┌─────────────────────────────────┐
     │ 📱 Presentation (Red)           │
     │ ┌───────────────────────────┐   │
     │ │ ⚙️ Application (Green)    │   │
     │ │ ┌───────────────────────┐ │   │
     │ │ │ 🧩 Domain (Blue)      │ │   │
     │ │ │ Pure Logic · Entities │ │   │
     │ │ └───────────────────────┘ │   │
     │ │ Ports / Interfaces        │   │
     │ └───────────────────────────┘   │
     │ UseCases · Services             │
     └─────────────────────────────────┘
      FastAPI Routers · DI

     🔧 Infrastructure (Orange)
     SQLAlchemy · LLM Clients
     ↑ implements ↑
```

**Layers & Colors:**
| Layer | Color | Responsibility |
|-------|-------|-----------------|
| **Presentation** (Red) | `#fecaca` | FastAPI Routers, DI, HTTP endpoints |
| **Application** (Green) | `#bbf7d0` | UseCases, Services, Port interfaces (ABC) |
| **Domain** (Blue) | `#bfdbfe` | Pure logic, Entities, Repository interfaces |
| **Infrastructure** (Orange) | `#fed7aa` | SQLAlchemy repos, LLM clients, RAG, External adapters |

**Dependency Flow:**
```
Presentation → Application → Domain ← Infrastructure (implements)
```

**Implementation:**
1. Use draw.io app to create `clean-architecture.drawio`
2. Use concentric rectangles (nested shapes) to visualize layers
3. Add dependency arrows with labels ("depends", "implements")
4. Apply sketch style in draw.io settings
5. Export to `clean-architecture.svg` (File → Export As → SVG)

---

## Implementation Plan

### Phase 1: Create draw.io Diagrams

#### 1a. system-flow.drawio
1. Open [draw.io](https://draw.io) or VSCode draw.io extension
2. Create new diagram
3. Build structure:
   - **Input layer (Blue):** Telegram User → API → Webhook
   - **Process layer (Green):** WebhookHandler → MessageRouter → [SaveLink (left), Search (center), KnowledgeAgent (right)]
   - **Storage layer (Orange):** PostgreSQL + pgvector (centered below)
   - **External layer (Purple):** Jina Reader, OpenAI API (dashed edges)
4. **Critical:** Ensure SearchUseCase and PostgreSQL are **vertically centered**
5. Apply sketch style: Right-click canvas → Sketch style
6. Save as `docs/assets/system-flow.drawio`
7. Export: File → Export As → SVG → `docs/assets/system-flow.svg`

#### 1b. clean-architecture.drawio
1. Create new diagram in draw.io
2. Build concentric structure using nested rectangles:
   - Outermost: Presentation (Red) rectangle
   - Inside: Application (Green) rectangle
   - Inside: Domain (Blue) rectangle
   - Separate: Infrastructure (Orange) rectangle with arrow to Domain
3. Add layer labels and responsibilities
4. Add dependency arrows with labels ("depends", "implements")
5. Apply sketch style
6. Save as `docs/assets/clean-architecture.drawio`
7. Export: File → Export As → SVG → `docs/assets/clean-architecture.svg`

### Phase 2: Update README.md

- Keep SVG image references (draw.io exports to SVG)
  ```markdown
  ![System Flow Diagram](docs/assets/system-flow.svg)
  ![Architecture Diagram](docs/assets/clean-architecture.svg)
  ```

### Phase 3: Cleanup

- Delete `docs/assets/archi-flow.xml` (old duplicate)
- Keep `.drawio` and `.svg` files in repo

### Phase 4: Verification

- [ ] system-flow.svg renders in GitHub preview
- [ ] clean-architecture.svg renders in GitHub preview
- [ ] SearchUseCase and PostgreSQL are visually centered
- [ ] All colors match design specification
- [ ] Sketch style is applied (handdrawn aesthetic)
- [ ] All labels readable and positioned correctly

---

## Testing Strategy

- [ ] Mermaid code renders correctly in Mermaid Live Editor
- [ ] Diagrams render correctly in GitHub README preview
- [ ] Links in README navigate to `.md` files (file exists + accessible)
- [ ] No broken image references in README
- [ ] Git diff shows clean text-based changes (not binary)

---

## Risks & Mitigation

| Risk | Mitigation |
|------|-----------|
| Mermaid rendering differs from SVG | Test both before deletion; screenshot original for reference |
| GitHub Mermaid version outdated | Stick to core features (flowchart, subgraph, classDef); avoid bleeding-edge syntax |
| Links to .md files break | Verify file paths relative to README location |

---

## Success Criteria

✅ **Diagrams render correctly** with handdrawn sketch theme
✅ **Colors match design** (input/process/storage/external layers)
✅ **HybridRetriever** breakdown visible (Dense · Sparse · Rerank)
✅ **Architecture layers** clearly labeled and color-coded
✅ **README links** point to .md files and function
✅ **Git history** shows text-based diffs, not binary changes
✅ **No broken references** in documentation

---

## Files Affected

**Created:**
- `docs/assets/system-flow.drawio` — source (XML format)
- `docs/assets/system-flow.svg` — exported (vector format)
- `docs/assets/clean-architecture.drawio` — source (XML format)
- `docs/assets/clean-architecture.svg` — exported (vector format)

**Modified:**
- `README.md` — no changes needed (SVG references remain)

**Deleted:**
- `docs/assets/archi-flow.xml` (old duplicate)

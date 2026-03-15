# Diagram Conversion to Mermaid Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create two Mermaid diagrams (system-flow and clean-architecture) with handdrawn sketch theme, save as `.md` files, update README links, and clean up old SVG files.

**Architecture:** Mermaid flowcharts with `look: "handDrawn"` theme for sketchy aesthetic. system-flow uses 3-way branching with layer colors; clean-architecture uses subgraphs to represent layers. Both render natively in GitHub and are Git diff-friendly.

**Tech Stack:** Mermaid, Markdown, git

---

## Chunk 1: Create Mermaid Diagram Files

### Task 1: Create system-flow.md

**Files:**
- Create: `docs/assets/system-flow.md`
- Reference spec: `docs/superpowers/specs/2026-03-15-diagram-conversion-design.md`

- [ ] **Step 1: Create file**

```bash
touch docs/assets/system-flow.md
```

- [ ] **Step 2: Write file content**

```markdown
# System Flow (Message Processing Pipeline)

Processing flow: Telegram messages → Scraping → AI Analysis → Storage → Response

## Diagram

<diagram content from spec section 4>
```

Copy the **system-flow.md Mermaid Code** block from spec file (section 4).
Include the complete mermaid block with init directives.

- [ ] **Step 3: Verify markdown syntax**

Open file in editor.
Confirm:
- Title is `# System Flow`
- Mermaid code block is properly fenced with ````mermaid and ````
- No syntax errors

- [ ] **Step 4: Test rendering locally**

If using VSCode: Install "Markdown Preview Mermaid Support" extension
Open preview to verify diagram renders.

- [ ] **Step 5: Commit**

```bash
cd E:/VsCodeProjects/LinkdBot-RAG
git add docs/assets/system-flow.md
git commit -m "feat: add system-flow diagram (Mermaid, handdrawn theme)"
```

---

## Chunk 2: Create Clean Architecture Diagram

### Task 2: Create clean-architecture.md

**Files:**
- Create: `docs/assets/clean-architecture.md`

- [ ] **Step 1: Create file**

```bash
touch docs/assets/clean-architecture.md
```

- [ ] **Step 2: Write file content**

```markdown
# Clean Architecture (Layer Dependencies)

Four-layer architecture: Presentation depends on Application, which depends on Domain. Infrastructure implements Domain interfaces.

## Diagram

<diagram content from spec section 5>
```

Copy the **clean-architecture.md Mermaid Code** block from spec file (section 5).
Include the complete mermaid block with init directives.

- [ ] **Step 3: Verify markdown syntax**

Open file in editor.
Confirm:
- Title is `# Clean Architecture`
- Mermaid code block is properly fenced
- No syntax errors

- [ ] **Step 4: Test rendering locally**

VSCode preview or Markdown Preview Mermaid Support extension.
Verify diagram renders and shows 4 layers with colors.

- [ ] **Step 5: Commit**

```bash
cd E:/VsCodeProjects/LinkdBot-RAG
git add docs/assets/clean-architecture.md
git commit -m "feat: add clean-architecture diagram (Mermaid, subgraph layers)"
```

---

## Chunk 3: Update README and Cleanup

### Task 3: Update README.md links and delete old files

**Files:**
- Modify: `README.md`
- Delete: `docs/assets/system-flow.svg`, `docs/assets/clean-architecture.svg`, `docs/assets/archi-flow.xml`

- [ ] **Step 1: Update README.md**

Open `README.md` in editor.
Find lines around **System Flow** and **Architecture** sections (around line 61 and 84).

**Replace:**
```markdown
![System Flow Diagram](docs/assets/system-flow.svg)
```

**With:**
```markdown
[System Flow Diagram](docs/assets/system-flow.md)
```

**Replace:**
```markdown
![Architecture Diagram](docs/assets/clean-architecture.svg)
```

**With:**
```markdown
[Architecture Diagram](docs/assets/clean-architecture.md)
```

- [ ] **Step 2: Delete old SVG and XML files**

```bash
cd E:/VsCodeProjects/LinkdBot-RAG
rm docs/assets/system-flow.svg
rm docs/assets/clean-architecture.svg
rm docs/assets/archi-flow.xml
```

- [ ] **Step 3: Verify deletions**

```bash
ls docs/assets/
```

Expected output:
```
clean-architecture.md
system-flow.md
```

- [ ] **Step 4: Commit changes**

```bash
cd E:/VsCodeProjects/LinkdBot-RAG
git add README.md docs/assets/
git commit -m "chore: replace SVG diagrams with Mermaid markdown files"
```

---

## Chunk 4: Final Verification

### Task 4: Verify Mermaid diagrams render in GitHub

**Files:**
- Test: `README.md` rendering

- [ ] **Step 1: Check git log**

```bash
cd E:/VsCodeProjects/LinkdBot-RAG
git log --oneline -5
```

Expected: 3 commits visible
- system-flow.md
- clean-architecture.md
- README.md update + cleanup

- [ ] **Step 2: Open README.md locally**

```bash
code E:/VsCodeProjects/LinkdBot-RAG/README.md
```

- [ ] **Step 3: Verify diagram links render**

Open VSCode Markdown preview (or install "Markdown Preview Mermaid Support").
Look for:
- **System Flow Diagram** link → Click to open `system-flow.md`
- **Architecture Diagram** link → Click to open `clean-architecture.md`

- [ ] **Step 4: Verify Mermaid diagrams**

Open each `.md` file in preview.
Verify:
- **system-flow.md**: Shows vertical pipeline with layers, 3-way branching, sketch style
- **clean-architecture.md**: Shows 4 layers with colors, dependency arrows, sketch style

- [ ] **Step 5: Verify GitHub rendering (after push)**

```bash
git push origin feat/#94-phase-b-korean-morpheme-fts
```

Then visit GitHub branch:
`https://github.com/chanubc/LinkdBot-RAG/blob/feat/#94-phase-b-korean-morpheme-fts/README.md`

Verify:
- Both diagram links are clickable
- GitHub renders Mermaid diagrams natively (should auto-render in markdown)
- No broken images or error messages

---

## Summary

**Total commits:** 3
1. `system-flow.md` (Mermaid diagram)
2. `clean-architecture.md` (Mermaid diagram)
3. `README.md` update + cleanup (delete old SVG/XML files)

**Result:** Two Mermaid diagrams with handdrawn sketch theme, Git diff-friendly markdown files, native GitHub rendering. Links in README point to `.md` files instead of SVG images.

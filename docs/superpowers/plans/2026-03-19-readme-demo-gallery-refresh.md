# README Demo Gallery Refresh Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `README.md`의 Demo 섹션을 정리해 기존 Telegram 데모는 유지하고, Notion / Dashboard 갤러리를 추가하며, Hybrid RAG 설명을 더 정확한 가치 중심 문구로 교체한다.

**Architecture:** 구현 범위는 문서와 정적 자산에 한정한다. 먼저 외부 첨부 이미지를 `docs/assets/screenshots/` 아래 로컬 자산으로 정리한 뒤, `README.md`의 Demo 섹션에 기존 모바일 블록 → Notion block → Dashboard block 순서로 갤러리를 구성한다. Dashboard는 기본 2열을 완료 기준으로 하고, 3열은 GitHub README 가독성 검증을 통과할 때만 선택한다.

**Tech Stack:** Markdown, GitHub README HTML table markup, local image assets under `docs/assets/screenshots/`, shell verification commands, git

**Spec:** `docs/superpowers/specs/2026-03-19-readme-demo-gallery-design.md`

---

## File Map

| 파일 | 변경 종류 | 역할 |
|---|---|---|
| `README.md` | **수정** | Demo 섹션 재구성, 모바일 캡션 정리, Notion/Dashboard 갤러리 추가, Hybrid RAG 설명 문구 수정 |
| `docs/assets/screenshots/notion-db-overview.png` | **신규** | Notion knowledge archive overview 이미지 |
| `docs/assets/screenshots/dashboard-overview-1.png` | **신규** | Dashboard overview screen 1 |
| `docs/assets/screenshots/dashboard-overview-2.png` | **신규** | Dashboard overview screen 2 |
| `docs/assets/screenshots/dashboard-overview-3.png` | **신규** | Dashboard overview screen 3 |
| `docs/assets/screenshots/dashboard-overview-4.png` | **신규** | Dashboard overview screen 4 |
| `docs/assets/screenshots/dashboard-overview-5.png` | **신규** | Dashboard overview screen 5 |
| `docs/assets/screenshots/dashboard-overview-6.png` | **신규** | Dashboard overview screen 6 |

---

## Chunk 1: Asset Preparation

### Task 1: 확정된 외부 첨부 이미지를 로컬 screenshot 자산으로 저장

**Files:**
- Create: `docs/assets/screenshots/notion-db-overview.png`
- Create: `docs/assets/screenshots/dashboard-overview-1.png`
- Create: `docs/assets/screenshots/dashboard-overview-2.png`
- Create: `docs/assets/screenshots/dashboard-overview-3.png`
- Create: `docs/assets/screenshots/dashboard-overview-4.png`
- Create: `docs/assets/screenshots/dashboard-overview-5.png`
- Create: `docs/assets/screenshots/dashboard-overview-6.png`

- [ ] **Step 1: 대상 디렉터리 상태 확인**

```bash
find docs/assets/screenshots -maxdepth 1 -type f | sort
```
Expected: 기존 Telegram screenshot 파일들이 보이고, 아직 `notion-db-overview.png` 및 `dashboard-overview-*.png` 는 없거나 비어 있지 않은지 확인 가능.

- [ ] **Step 2: Notion screenshot 다운로드**

```bash
curl --fail --location "https://github.com/user-attachments/assets/5477af21-1368-43b8-b68a-12758125a396"   -o docs/assets/screenshots/notion-db-overview.png
```
Expected: exit code 0, `docs/assets/screenshots/notion-db-overview.png` 생성.

- [ ] **Step 3: Dashboard screenshots 6장 다운로드**

```bash
set -e
curl --fail --location "https://github.com/user-attachments/assets/ebe04969-ca68-4e8c-94db-1587bf71bd86" -o docs/assets/screenshots/dashboard-overview-1.png
curl --fail --location "https://github.com/user-attachments/assets/c83e52c3-5e79-4fc6-aab3-fc179adbef37" -o docs/assets/screenshots/dashboard-overview-2.png
curl --fail --location "https://github.com/user-attachments/assets/373a1fe0-0222-4435-8028-d3c77f55f3a3" -o docs/assets/screenshots/dashboard-overview-3.png
curl --fail --location "https://github.com/user-attachments/assets/b4dc261a-eb4e-486a-8138-605161ec8030" -o docs/assets/screenshots/dashboard-overview-4.png
curl --fail --location "https://github.com/user-attachments/assets/25a5d5c5-f759-441e-a1ae-86301f364332" -o docs/assets/screenshots/dashboard-overview-5.png
curl --fail --location "https://github.com/user-attachments/assets/1490c0d9-00c4-4cdb-8329-6bfc317c3764" -o docs/assets/screenshots/dashboard-overview-6.png
```
Expected: 모든 다운로드가 성공할 때만 exit code 0, 6개 파일 생성.

- [ ] **Step 4: 파일 존재 / 형식 / 개수 검증**

```bash
set -e
files=(
  docs/assets/screenshots/notion-db-overview.png
  docs/assets/screenshots/dashboard-overview-1.png
  docs/assets/screenshots/dashboard-overview-2.png
  docs/assets/screenshots/dashboard-overview-3.png
  docs/assets/screenshots/dashboard-overview-4.png
  docs/assets/screenshots/dashboard-overview-5.png
  docs/assets/screenshots/dashboard-overview-6.png
)
for f in "${files[@]}"; do
  test -s "$f"
  file "$f" | grep -qi 'PNG image data'
done
```
Expected: 출력은 file 결과만 보일 수 있고, 모든 파일이 비어 있지 않은 PNG로 확인되며 exit code 0.

- [ ] **Step 5: 자산 목록과 정확한 개수 재확인**

```bash
find docs/assets/screenshots -maxdepth 1 -type f | sort | grep -E 'notion-db-overview|dashboard-overview-[1-6]' | tee /tmp/readme-demo-assets.txt
wc -l /tmp/readme-demo-assets.txt
```
Expected: grep 결과에 7개 경로가 출력되고, `wc -l` 결과가 `7 /tmp/readme-demo-assets.txt`.

- [ ] **Step 6: 커밋**

```bash
git add docs/assets/screenshots/notion-db-overview.png docs/assets/screenshots/dashboard-overview-1.png docs/assets/screenshots/dashboard-overview-2.png docs/assets/screenshots/dashboard-overview-3.png docs/assets/screenshots/dashboard-overview-4.png docs/assets/screenshots/dashboard-overview-5.png docs/assets/screenshots/dashboard-overview-6.png
git commit -m "Prepare local README demo assets for Notion and Dashboard galleries

Bring the approved Notion and Dashboard screenshots into the repository so the README can reference stable local assets instead of external attachments.

Constraint: README image references should use repo-local paths rather than hotlinked user-attachment URLs
Constraint: Asset names must match the approved spec mapping so later README edits remain deterministic
Rejected: Keep GitHub user-attachment URLs directly in README | brittle external references and conflicts with the approved asset-handling rule
Confidence: high
Scope-risk: narrow
Reversibility: clean
Directive: Preserve these filenames unless the spec asset map is updated first
Tested: File existence, PNG file-type, and exact-count checks for all 7 new screenshot assets
Not-tested: Visual fidelity review of the downloaded images inside README layout
"
```
Expected: one new commit created for the 7 screenshot assets.

- [ ] **Step 7: 커밋 결과 확인**

```bash
git log --oneline -1
git status --short
```
Expected: latest commit message matches the asset-preparation intent, and working tree is clean.

---

## Chunk 2: README Demo Layout and Copy Refresh

> Prerequisite: Chunk 1의 screenshot 자산 다운로드와 검증이 완료되어 `docs/assets/screenshots/notion-db-overview.png` 및 `dashboard-overview-{1..6}.png` 가 존재해야 한다.

### Task 2: 기존 Telegram Demo 캡션을 기술 README 톤으로 정리

**Files:**
- Modify: `README.md:11-47`

- [ ] **Step 1: 현재 Demo 섹션 백업 확인용 diff 기준 확보**

```bash
grep -n "## Demo\|## Core Features" -A80 README.md
```
Expected: Demo 섹션 전체와 Core Features 시작 위치 확인.

- [ ] **Step 2: 기존 모바일 Demo 블록 유지 상태에서 캡션만 교체**

`README.md`의 기존 두 개 Telegram table 구조는 유지하고, **Hybrid RAG 캡션을 제외한 나머지 5개 모바일 caption만** 아래와 같이 명시적으로 교체한다.

```html
Link Save & Notion Sync → 본문 스크랩·요약 후 Notion DB까지 자동 동기화
Knowledge Q&A (`/ask`) → 저장된 링크와 메모를 바탕으로 근거 기반 답변 생성
Proactive Weekly Report → 관심사 변화와 reactivation 신호를 바탕으로 다시 볼 링크를 선제적으로 추천
Dashboard Entry → JWT magic link로 웹 dashboard에 안전하게 진입
Quick Menu → 검색·질문·리포트·대시보드 이동을 버튼으로 빠르게 실행
```

Expected: `Hybrid RAG (Dense + Sparse)` 캡션은 이 Task에서 건드리지 않고 그대로 유지된다.

- [ ] **Step 3: 캡션 변경 diff 확인**

```bash
git diff -- README.md | sed -n '1,160p'
```
Expected: Demo table 구조는 유지되고, Hybrid RAG 캡션을 제외한 5개 모바일 caption만 정리된 diff.

- [ ] **Step 4: 커밋**

```bash
git add README.md
git commit -m "Improve README mobile demo captions for clearer feature framing

Tighten the existing Telegram demo copy so five non-Hybrid mobile screenshots communicate their outcomes more clearly without changing the structure of the Demo section.

Constraint: The approved scope keeps the current Telegram demo tables intact
Constraint: README tone should remain technical and concise rather than portfolio-style
Rejected: Rebuild the mobile demo layout from scratch | unnecessary scope and conflicts with the approved design
Confidence: high
Scope-risk: narrow
Reversibility: clean
Directive: Keep captions outcome-focused and avoid marketing-heavy phrasing in future README edits
Tested: Manual diff review of 5 non-Hybrid Demo captions
Not-tested: Full README render after later gallery additions
"
```

---

### Task 3: Notion gallery block를 Demo 아래에 추가

**Files:**
- Modify: `README.md:47-60` (Demo 섹션 하단, Core Features 이전)
- Test: `docs/assets/screenshots/notion-db-overview.png`

- [ ] **Step 1: 단일 이미지 Notion block 추가**

`README.md`의 기존 Telegram Demo 블록 아래, 기존 `---` divider 바로 위에 아래 구조를 추가한다.

```md
### Notion Knowledge Archive

Telegram에서 저장한 링크와 요약이 Notion DB에서 어떻게 구조화되는지 보여주는 화면입니다.

<p align="center">
  <img src="docs/assets/screenshots/notion-db-overview.png" width="100%" alt="Notion knowledge archive overview" />
</p>

<p align="center"><sub>저장된 링크, 요약, 메타데이터가 구조화된 knowledge archive</sub></p>
```

- [ ] **Step 2: 자산 경로 참조 검증**

```bash
grep -n "Notion Knowledge Archive\|notion-db-overview.png\|저장된 링크, 요약, 메타데이터가 구조화된 knowledge archive\|Notion knowledge archive overview" README.md
```
Expected: 제목 1개, 이미지 경로 1개, caption 1개, alt text 1개 출력.

- [ ] **Step 3: Git diff로 삽입 위치 확인**

```bash
git diff -- README.md | sed -n '1,220p'
```
Expected: Notion block이 `## Demo` 안에 있고 `## Core Features` 이전에 위치.

- [ ] **Step 4: 커밋**

```bash
git add README.md
git commit -m "Show the Notion knowledge archive in README demos

Add the approved Notion DB screenshot below the existing Telegram demos so readers can see how saved links are structured after synchronization.

Constraint: This gallery is a single-image block in the approved spec
Constraint: The README should show the Notion result surface without expanding into a separate architecture section
Rejected: Fold the Notion screenshot into the existing mobile tables | weakens the distinction between Telegram input and Notion archive output
Confidence: high
Scope-risk: narrow
Reversibility: clean
Directive: Keep the Notion block directly below the Telegram demos unless the spec order changes
Tested: README grep check for title and asset path
Not-tested: Combined README render with Dashboard gallery still pending
"
```

---

### Task 4: Dashboard gallery block를 2열 기본으로 추가

**Files:**
- Modify: `README.md:60-82` (Notion block 아래, Core Features 이전)
- Test: `docs/assets/screenshots/dashboard-overview-1.png`
- Test: `docs/assets/screenshots/dashboard-overview-2.png`
- Test: `docs/assets/screenshots/dashboard-overview-3.png`
- Test: `docs/assets/screenshots/dashboard-overview-4.png`
- Test: `docs/assets/screenshots/dashboard-overview-5.png`
- Test: `docs/assets/screenshots/dashboard-overview-6.png`

- [ ] **Step 1: 2열 HTML table 기본안 작성**

`README.md`의 Notion block 아래이자 기존 `---` divider 바로 위에 아래와 같은 2열 grid를 추가한다. 6장을 3행 2열로 배치하고 각 캡션은 spec의 Caption 방향을 따른다.

```html
### Dashboard Views

텔레그램에서 저장한 지식을 탐색하고 회고할 수 있는 웹 dashboard 화면입니다.

<table width="100%">
  <tr>
    <td width="50%"><img src="docs/assets/screenshots/dashboard-overview-1.png" width="100%" alt="Dashboard overview screen 1" /></td>
    <td width="50%"><img src="docs/assets/screenshots/dashboard-overview-2.png" width="100%" alt="Dashboard overview screen 2" /></td>
  </tr>
  <tr>
    <td width="50%">저장된 링크와 핵심 지표를 한눈에 보는 dashboard overview</td>
    <td width="50%">탐색 또는 인사이트 흐름을 보여주는 dashboard view</td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/assets/screenshots/dashboard-overview-3.png" width="100%" alt="Dashboard overview screen 3" /></td>
    <td width="50%"><img src="docs/assets/screenshots/dashboard-overview-4.png" width="100%" alt="Dashboard overview screen 4" /></td>
  </tr>
  <tr>
    <td width="50%">검색·탐색·지표 확인을 지원하는 dashboard view</td>
    <td width="50%">관심사 변화나 분석 상세를 보여주는 dashboard view</td>
  </tr>
  <tr>
    <td width="50%"><img src="docs/assets/screenshots/dashboard-overview-5.png" width="100%" alt="Dashboard overview screen 5" /></td>
    <td width="50%"><img src="docs/assets/screenshots/dashboard-overview-6.png" width="100%" alt="Dashboard overview screen 6" /></td>
  </tr>
  <tr>
    <td width="50%">재발견과 분석을 보조하는 dashboard view</td>
    <td width="50%">라이브러리 탐색과 retrieval 보조 화면</td>
  </tr>
</table>
```

- [ ] **Step 2: 3열 승격 여부 판단 규칙 적용**

```text
기본 완료안은 2열이다.
3열로 바꾸려면 GitHub README 렌더 기준으로 각 이미지의 핵심 UI 텍스트와 카드 구분이 충분히 읽혀야 한다.
이 조건을 확실히 증명할 수 없으면 2열을 유지한다.
```
Expected: 별도 증거가 없으면 2열 유지.

- [ ] **Step 3: 이미지 경로와 alt text 확인**

```bash
grep -n "Dashboard Views\|dashboard-overview-1.png\|Dashboard overview screen 1\|저장된 링크와 핵심 지표를 한눈에 보는 dashboard overview\|dashboard-overview-2.png\|Dashboard overview screen 2\|탐색 또는 인사이트 흐름을 보여주는 dashboard view\|dashboard-overview-3.png\|Dashboard overview screen 3\|검색·탐색·지표 확인을 지원하는 dashboard view\|dashboard-overview-4.png\|Dashboard overview screen 4\|관심사 변화나 분석 상세를 보여주는 dashboard view\|dashboard-overview-5.png\|Dashboard overview screen 5\|재발견과 분석을 보조하는 dashboard view\|dashboard-overview-6.png\|Dashboard overview screen 6\|라이브러리 탐색과 retrieval 보조 화면" README.md
```
Expected: 제목 1개, dashboard 이미지 경로 6개, mapped alt text 6개, caption text 6개가 모두 출력.

- [ ] **Step 4: 커밋**

```bash
git add README.md
git commit -m "Add a dashboard gallery to the README demo section

Show the approved web dashboard screenshots as a separate gallery so the README distinguishes Telegram entry points from the actual dashboard browsing surface.

Constraint: The dashboard gallery defaults to a 2-column layout unless readability evidence supports 3 columns
Constraint: All 6 approved dashboard assets must appear with the mapped alt text and caption direction
Rejected: Omit some dashboard screens for a shorter gallery | conflicts with the approved asset scope
Confidence: high
Scope-risk: narrow
Reversibility: clean
Directive: Treat 2 columns as the default steady state unless a later render check proves 3 columns remain legible
Tested: README grep check for dashboard title and 6 asset references
Not-tested: Visual comparison of 2-column versus 3-column README render
"
```

---

### Task 5: Hybrid RAG 설명 범위 내 문구만 가치 중심으로 교체

**Files:**
- Modify: `README.md` (Demo 내 Hybrid RAG 카드 캡션)
- Modify: `README.md` (`### Hybrid RAG Architecture` 바로 아래 설명 문단)

- [ ] **Step 1: Demo 카드 캡션 수정**

`Hybrid RAG (Dense + Sparse)` 카드 아래 캡션을 아래 방향으로 교체한다.

```text
Dense+sparse retrieval과 reranking으로 관련 링크를 더 안정적으로 찾음
```

Expected: 정확히 `Dense+sparse retrieval과 reranking으로 관련 링크를 더 안정적으로 찾음` 문구를 사용.

- [ ] **Step 2: `### Hybrid RAG Architecture` 아래 설명 문단 교체**

아래 **2문장**으로 교체한다.

```text
Dense retrieval은 의미적으로 유사한 문서를 찾는 데 강하고, sparse retrieval은 키워드와 고유명사 같은 정확한 표현 매칭에 강하다. 둘을 함께 쓰면 한쪽만 사용할 때 놓치기 쉬운 결과를 더 안정적으로 회수할 수 있다.
Reranking은 이렇게 모은 후보의 최종 문맥 적합도를 다시 정리해 `/search`와 `/ask`의 신뢰도를 높인다.
```

- [ ] **Step 3: 수정 범위가 spec과 일치하는지 확인**

```bash
git diff -- README.md | sed -n "1,260p"
```
Expected: `Hybrid RAG (Dense + Sparse)` Demo 카드 캡션과 `### Hybrid RAG Architecture` 아래 설명 문단 diff만 보이고, `## Core Features` 나 `### Why These Matter Most` 의 Hybrid RAG 문구는 unchanged 상태.

- [ ] **Step 4: 커밋**

```bash
git add README.md
git commit -m "Explain Hybrid RAG in terms of retrieval quality

Replace the shallow component list with copy that explains why dense retrieval, sparse retrieval, and reranking together improve search and answer quality.

Constraint: The approved edit scope is limited to the Demo card caption and the Hybrid RAG Architecture intro text
Constraint: Core Features and later architecture sections stay untouched in this pass
Rejected: Rewrite every Hybrid RAG mention in the README | unnecessary scope and not approved in the spec
Confidence: high
Scope-risk: narrow
Reversibility: clean
Directive: Keep future Hybrid RAG copy focused on retrieval tradeoffs and user-facing quality, not just component names
Tested: Grep review of Hybrid RAG edit locations
Not-tested: Full README render after all Demo changes combined
"
```

---

## Chunk 3: Verification and Final Polish

### Task 6: README 렌더링/자산/가독성 검증 후 최종 정리

**Files:**
- Modify: `README.md` (필요 시 미세 조정)
- Test: `README.md`
- Test: `docs/assets/screenshots/notion-db-overview.png`
- Test: `docs/assets/screenshots/dashboard-overview-{1,2,3,4,5,6}.png`

- [ ] **Step 1: 이미지 경로 전체 검증**

```bash
set -e
patterns=(
  'docs/assets/screenshots/notion-db-overview.png'
  'docs/assets/screenshots/dashboard-overview-1.png'
  'docs/assets/screenshots/dashboard-overview-2.png'
  'docs/assets/screenshots/dashboard-overview-3.png'
  'docs/assets/screenshots/dashboard-overview-4.png'
  'docs/assets/screenshots/dashboard-overview-5.png'
  'docs/assets/screenshots/dashboard-overview-6.png'
)
for p in "${patterns[@]}"; do
  grep -n "$p" README.md
  test "$(grep -c "$p" README.md)" -eq 1
done
```
Expected: 7개 경로가 각각 정확히 1번씩 출력되고 exit code 0.

- [ ] **Step 2: 실제 자산 존재 재검증**

```bash
set -e
for f in   docs/assets/screenshots/notion-db-overview.png   docs/assets/screenshots/dashboard-overview-1.png   docs/assets/screenshots/dashboard-overview-2.png   docs/assets/screenshots/dashboard-overview-3.png   docs/assets/screenshots/dashboard-overview-4.png   docs/assets/screenshots/dashboard-overview-5.png   docs/assets/screenshots/dashboard-overview-6.png; do
  test -s "$f"
  file "$f" | grep -qi 'PNG image data'
done
```
Expected: 7개 자산이 모두 비어 있지 않은 PNG 파일로 확인되고 exit code 0.

- [ ] **Step 3: Demo 섹션 최종 구조 검증**

```bash
grep -n "## Demo\|### Notion Knowledge Archive\|### Dashboard Views\|## Core Features" README.md
```
Expected: `## Demo` 아래에 `### Notion Knowledge Archive`, `### Dashboard Views` 가 있고, 그 다음에 `## Core Features` 가 시작됨.

- [ ] **Step 4: 소스 차원의 table/markup 징후 확인**

```bash
sed -n '1,140p' README.md
```
Expected: opening/closing `<table>`, `<tr>`, `<td>`, `<img>` 구조가 Demo 영역에서 짝이 맞고 Markdown heading이 끊기지 않음.

- [ ] **Step 5: GitHub PR preview 기준 렌더 검증**

```text
- 브랜치를 push하고 GitHub에서 PR 또는 브랜치 페이지를 열어 rendered `README.md`를 확인한다.
- 확인한 PR URL을 **PR description 또는 PR comment**에 남긴다.
- 렌더 결과 스크린샷 1~2장 또는 아래 체크리스트 통과 결과도 **같은 PR description/comment**에 남긴다.
- Demo 안에서 기존 Telegram block → Notion block → Dashboard block 순서가 유지되는지 확인한다.
- Notion 이미지는 단일 블록으로 보이는지 확인한다.
- Dashboard는 2열을 기본 완료안으로 보고, 3열은 실제 GitHub render에서 이미지 핵심 UI 텍스트와 카드 경계가 충분히 읽힐 때만 허용한다.
- HTML table 깨짐, broken image, alt/caption 누락이 없는지 확인한다.
```
Expected: GitHub README render 증거(PR URL + checklist or screenshots)가 PR description/comment에 남고, 2열 기본안 또는 증거가 있는 3열안만 승인된다.

- [ ] **Step 6: 누적 변경 범위 검토**

```bash
BASE=$(git merge-base HEAD main)
ALLOWED=$(mktemp)
printf '%s
'   README.md   docs/assets/screenshots/notion-db-overview.png   docs/assets/screenshots/dashboard-overview-1.png   docs/assets/screenshots/dashboard-overview-2.png   docs/assets/screenshots/dashboard-overview-3.png   docs/assets/screenshots/dashboard-overview-4.png   docs/assets/screenshots/dashboard-overview-5.png   docs/assets/screenshots/dashboard-overview-6.png | sort > "$ALLOWED"
git diff --name-only "$BASE"..HEAD | sort | tee /tmp/readme-demo-changed-files.txt
comm -23 /tmp/readme-demo-changed-files.txt "$ALLOWED"
```
Expected: changed-files 목록은 허용된 8개 파일 범위 안에만 있고, `comm -23` 결과는 비어 있어야 한다.

- [ ] **Step 7: Hybrid RAG 수정 범위 재검증**

```bash
grep -n "Hybrid RAG (Dense + Sparse)" -A2 README.md
grep -n "^### Hybrid RAG Architecture$" -A4 README.md
! git diff "$(git merge-base HEAD main)"..HEAD -- README.md | grep -q "## Core Features\|### Why These Matter Most"
```
Expected: Demo 카드 캡션과 `### Hybrid RAG Architecture` 아래 설명 문단은 승인된 문구로 보이고, diff에는 `## Core Features` 와 `### Why These Matter Most` 섹션 변경이 없어야 한다.

- [ ] **Step 8: 최종 미세 조정이 있을 때만 커밋**

```bash
if ! git diff --quiet -- README.md docs/assets/screenshots/notion-db-overview.png docs/assets/screenshots/dashboard-overview-1.png docs/assets/screenshots/dashboard-overview-2.png docs/assets/screenshots/dashboard-overview-3.png docs/assets/screenshots/dashboard-overview-4.png docs/assets/screenshots/dashboard-overview-5.png docs/assets/screenshots/dashboard-overview-6.png; then
  git add README.md docs/assets/screenshots/notion-db-overview.png docs/assets/screenshots/dashboard-overview-1.png docs/assets/screenshots/dashboard-overview-2.png docs/assets/screenshots/dashboard-overview-3.png docs/assets/screenshots/dashboard-overview-4.png docs/assets/screenshots/dashboard-overview-5.png docs/assets/screenshots/dashboard-overview-6.png
  git commit -m "Make the README demo reflect the full product surfaces

Reorganize the Demo section so it keeps the Telegram flow, adds the approved Notion and Dashboard galleries, and explains Hybrid RAG in terms of why retrieval quality improves.

Constraint: The approved implementation is documentation-only and must stay within README plus local screenshot assets
Constraint: Dashboard layout should prefer legibility, making 2 columns the default completion path
Rejected: Expand into broader README restructuring beyond the Demo and Hybrid RAG intro areas | outside the approved scope
Confidence: high
Scope-risk: narrow
Reversibility: clean
Directive: When future demo assets change, update the spec asset map and keep README verification focused on render integrity and readability
Tested: Asset existence checks, README structure grep checks, rendered preview review, manual Demo markup review
Not-tested: GitHub-hosted remote render beyond available preview surfaces
"
else
  echo "No additional polish changes to commit"
fi
```
Expected: Step 5~7 결과로 추가 수정이 생긴 경우에만 1개의 최종 polish commit이 생성된다. 추가 수정이 없다면 이 Step은 skip 가능하다.

- [ ] **Step 9: 최종 상태 확인**

```bash
git log --oneline -3
git status --short
```
Expected: 최신 커밋들이 README demo refresh 관련 lore-format commit들이고, working tree 는 clean 상태다.


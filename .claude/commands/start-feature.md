다음 순서대로 실행하세요. 각 단계는 반드시 순서를 지킬 것.

## 1. 기능 설명 확인
사용자가 기능 설명을 제공하지 않았다면 먼저 물어보세요.
이미 제공했다면 그대로 사용하세요.

## 2. GitHub 이슈 생성
`.github/ISSUE_TEMPLATE/issue_template.md` 형식에 맞춰 이슈를 생성하세요.

```bash
gh issue create --title "[FEAT] {기능 설명}" --body "$(cat <<'EOF'
## 📌 𝗧𝗮𝘀𝗸
- [ ] {기능 설명}

## 💡 𝗥𝗲𝗳𝗲𝗿𝗲𝗻𝗰𝗲

EOF
)"
```

출력에서 이슈 번호 N을 추출하세요.

## 3. main 최신화
작업 시작 전에 반드시 main 브랜치를 최신 상태로 만드세요.

```bash
git checkout main
git pull origin main
```

## 4. 브랜치 생성 및 체크아웃
브랜치 이름 규칙: `prefix/#N-{영어 kebab-case 설명}`

```bash
git checkout -b prefix/#N-{설명}
```

예시: `prefix/#34-add-ask-command`

## 5. 완료 메시지 출력
```
✅ 준비 완료!
📌 이슈: #{N}
🌿 브랜치: prefix/#N-{설명}

이제 작업을 시작하세요.
```

## 6. 작업 완료 후 커밋하기
하나의 기능 작업이 완료되면 다음 형식으로 커밋하세요.

```bash
git add {변경된 파일}
git commit -m "#N [prefix]: 커밋 메시지"
```

**커밋 메시지 형식:**
- `#N [feat]: 새로운 기능 설명` (새 기능)
- `#N [fix]: 버그 수정 설명` (버그 수정)
- `#N [refactor]: 코드 개선 설명` (리팩토링)
- `#N [add]: 파일 추가 설명` (파일 추가)

**주의:** Co-Authored-By 라인은 추가하지 마세요.

## 7. 작업 완료 후 PR 생성 (작업 완료 시 별도 실행)
`.github/PULL_REQUEST_TEMPLATE.md` 형식에 맞춰 PR을 생성하세요.

## 8. PR 머지
GitHub UI에서 "Create a merge commit" 선택 후 병합. 또는 CLI:

```bash
gh pr merge {PR_NUMBER} --merge
```

# Prompt: Review Draft Post

## Task

Review a draft post for quality, accuracy, and completeness before publishing.

## Input

- **Post slug or file path**: 검토할 포스트

## Checklist

### 1. Front Matter 검증

- [ ] `title`: 명확하고 흥미로운가?
- [ ] `slug`: URL에 적합한 영문인가?
- [ ] `tags`: 적절한 태그가 있는가?
- [ ] `categories`: 올바른 카테고리인가?
- [ ] `tldr`: 핵심을 잘 요약했는가?
- [ ] `translationKey`: 모든 번역본에서 동일한가?
- [ ] `cover.image`: 이미지가 존재하고 경로가 맞는가?
- [ ] `cover.alt`: 이미지 설명이 있는가?

### 2. 내용 검증

- [ ] 서론이 주제를 명확히 소개하는가?
- [ ] 논리적 흐름이 있는가?
- [ ] 코드 예시가 정확하고 실행 가능한가?
- [ ] 오타나 문법 오류가 없는가?
- [ ] 외부 링크가 유효한가?
- [ ] 결론이 명확한가?

### 3. 번역 검증

- [ ] 모든 언어 버전이 존재하는가? (ko, en, ja)
- [ ] 번역이 자연스러운가?
- [ ] 기술 용어가 일관되게 사용되었는가?
- [ ] 코드 블록이 번역되지 않았는가?

### 4. SEO/메타데이터

- [ ] 제목이 검색에 적합한가?
- [ ] 설명(tldr)이 검색 결과에 매력적으로 보이는가?

## Validation Command

**Windows**: `.\scripts\validate-translations.ps1`
**macOS/Linux**: `python3 scripts/validate_translations.py`

## Output

검토 결과를 다음 형식으로 제공:

```
## 검토 결과: {slug}

### ✅ 통과 항목
- ...

### ⚠️ 수정 권장
- ...

### ❌ 필수 수정
- ...

### 최종 판정
[ ] 발행 가능
[ ] 수정 후 재검토 필요
```

## After Review

검토가 완료되면:
- 문제가 없으면 `/publish-draft` 프롬프트로 발행
- 수정이 필요하면 수정 후 다시 `/review-draft` 실행

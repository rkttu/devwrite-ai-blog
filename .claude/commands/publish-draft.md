---
description: draft 포스트를 모든 언어 버전 일괄 발행 (draft true → false)
argument-hint: <slug>
---

# Publish Draft

## Task

Change a draft post's status from `draft: true` to `draft: false` to publish it.

## Input

발행할 포스트 슬러그:

```
$ARGUMENTS
```

## Pre-publish Checklist

발행 전 다음을 확인하세요:

1. `/review-draft` 로 검토 완료
2. 모든 번역본 존재 (ko, en, ja)
3. Hero 이미지 존재 (WebP 변환 완료)
4. TL;DR 작성 완료
5. `description` 필드 존재 (50~160자, 각 언어별)
6. `static/llms.txt` 에 포스트 추가 완료

## Actions

### 1. Update All Language Versions

모든 언어 버전의 `draft` 값을 변경:

```yaml
# Before
draft: true

# After
draft: false
```

### Files to Update (Page Bundle 구조)

- `content/ko/posts/{YYYY-MM-DD}-{slug}/index.md`
- `content/en/posts/{YYYY-MM-DD}-{slug}/index.md`
- `content/ja/posts/{YYYY-MM-DD}-{slug}/index.md`

### 2. Verify Publication

Hugo 서버가 실행 중이면 자동으로 반영됩니다.
확인: `http://localhost:1313/ko/posts/{slug}/`

## Output

```
## 발행 완료: {slug}

### 변경된 파일
- ✅ content/ko/posts/{YYYY-MM-DD}-{slug}/index.md (draft: false)
- ✅ content/en/posts/{YYYY-MM-DD}-{slug}/index.md (draft: false)
- ✅ content/ja/posts/{YYYY-MM-DD}-{slug}/index.md (draft: false)

### 접속 URL
- KO /ko/posts/{slug}/
- EN /en/posts/{slug}/
- JA /ja/posts/{slug}/
```

## Rollback

발행을 취소하려면 `/unpublish-post` 슬래시 커맨드를 사용하세요.

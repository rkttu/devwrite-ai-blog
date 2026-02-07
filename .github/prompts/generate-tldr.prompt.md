# Prompt: Generate TL;DR and Description

> **스타일 가이드**: 작성 시 `/writing-style-guide.md` 파일의 언어별 어투 규칙을 따르세요.

## Task
Generate a concise TL;DR summary and an SEO-friendly description for a blog post.

## Input
- Post file path or content

## Instructions

1. Read the full post content
2. Identify the main topic and key takeaways
3. Generate two separate summaries:

### `description` (SEO 메타 태그용)
- **용도**: `<meta name="description">`, OpenGraph, Twitter Cards, JSON-LD `"description"`
- **길이**: 50~160자 (한국어 기준, 검색 결과 스니펫 최적)
- **톤**: 클릭을 유도하는 매력적이고 간결한 표현
- **내용**: 글의 주제와 가치를 한 문장으로 요약
- 각 언어로 자연스럽게 작성

### `tldr` (독자용 핵심 요약)
- **용도**: 글 본문 상단에 표시, JSON-LD `"abstract"` 필드
- **길이**: 1-2문장 (description보다 길고 상세)
- **톤**: 핵심 내용을 정확하게 전달
- **내용**: 구체적 수치/방법/결과 포함, 독자가 글을 읽지 않아도 핵심을 파악 가능
- 각 언어로 자연스럽게 작성

## Guidelines

### Good Description
- "Hugo 정적 사이트 생성기로 다국어 블로그를 구축하고 GitHub Pages에 배포하는 방법을 단계별로 설명합니다."
- "Docker의 기본 개념을 이해하고, 설치부터 첫 번째 컨테이너 실행까지 단계별로 알아봅니다."

### Bad Description
- "이 글에서는 블로그에 대해 알아봅니다." (너무 모호)
- "Hugo를 다룹니다." (너무 짧음)

### Good TL;DR
- "Hugo와 PaperMod 테마로 다국어 블로그를 구축하고 GitHub Pages에 배포하는 방법을 다룹니다. i18n 설정, hreflang 태그, 번역 워크플로우까지 포함합니다."
- "React 18의 Concurrent Features를 활용해 사용자 경험을 개선하는 세 가지 패턴을 소개합니다."

### Bad TL;DR
- "이 글에서는 블로그에 대해 알아봅니다." (너무 모호, description과 동일)
- "Hugo 설치, 설정, 테마 적용, 다국어 설정, 배포까지 전부 다룹니다." (목차 나열)

## Example

### Post Content
```markdown
## Hugo란?
Hugo는 Go로 작성된 정적 사이트 생성기입니다...

## 설치하기
먼저 Hugo를 설치합니다...

## 테마 적용
PaperMod 테마를 적용해보겠습니다...
```

### Generated Output
```yaml
description: "Hugo 정적 사이트 생성기와 PaperMod 테마로 블로그를 만드는 방법을 단계별로 설명합니다."
tldr: "Hugo를 설치하고 PaperMod 테마를 적용하여 정적 블로그를 구축하는 과정을 다룹니다. 기본 설정부터 커스터마이징까지 실습할 수 있습니다."
```

## Output
Return both `description` and `tldr` values to be inserted into front matter.

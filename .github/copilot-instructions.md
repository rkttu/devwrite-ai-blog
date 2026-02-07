# DevWrite Blog - Copilot Instructions

이 문서는 GitHub Copilot 및 AI 에이전트가 이 블로그 리포지토리에서 작업할 때 따라야 할 규칙입니다.

## 프로젝트 개요

- **프레임워크**: Hugo (정적 사이트 생성기)
- **테마**: PaperMod
- **지원 언어**: 한국어(ko), English(en), 日本語(ja)
- **기본 언어**: 한국어 (ko)

## 디렉터리 구조

```
content/
├── ko/           # 한국어 (원본)
│   ├── posts/    # Page Bundle 구조
│   │   └── {YYYY-MM-DD}-{slug}/
│   │       ├── index.md      # 포스트 본문
│   │       └── (이미지 등 리소스 파일)
│   └── archives.md
├── en/           # English (번역)
│   ├── posts/    # Page Bundle 구조
│   │   └── {YYYY-MM-DD}-{slug}/
│   │       ├── index.md
│   │       └── (이미지 등 리소스 파일)
│   └── archives.md
└── ja/           # 日本語 (번역)
    ├── posts/    # Page Bundle 구조
    │   └── {YYYY-MM-DD}-{slug}/
    │       ├── index.md
    │       └── (이미지 등 리소스 파일)
    └── archives.md

static/
└── images/
    └── posts/    # Hero 이미지 저장 위치 (공용)
```

## 파일 명명 규칙

- **포스트 디렉터리명**: `{YYYY-MM-DD}-{slug}/` (예: `2025-12-04-docker-basics/`)
- **포스트 파일명**: 각 디렉터리 안에 `index.md` (예: `2025-12-04-docker-basics/index.md`)
- **포스트 내 이미지**: 같은 디렉터리에 저장 (예: `2025-12-04-docker-basics/diagram.png`)
- **URL**: `slug` 필드가 결정 (예: `/ko/posts/docker-basics/`)
- **Hero 이미지**: `static/images/posts/{slug}.jpg` (예: `docker-basics.jpg`)
- **모든 언어에서 동일한 디렉터리명 사용**

## Front Matter 필수 필드

모든 포스트는 다음 필드를 포함해야 합니다:

```yaml
---
title: "포스트 제목"
date: 2025-01-01T00:00:00+09:00
draft: false
slug: "url-friendly-slug"
tags:
  - tag1
  - tag2
categories:
  - category
translationKey: "unique-key-for-linking-translations"
cover:
  image: "images/posts/slug-name.jpg"
  alt: "이미지 설명"
tldr: "이 글의 핵심 요약 (1-2문장)"
license: "CC BY-NC 4.0"  # 선택사항, 기본값: CC BY-NC 4.0
---
```

### 필드 설명

| 필드 | 필수 | 설명 |
|------|------|------|
| `title` | ✅ | 사람이 읽기 좋은 제목 (각 언어로) |
| `date` | ✅ | ISO 8601 형식, 타임존 포함 |
| `draft` | ✅ | 발행 여부 |
| `slug` | ✅ | URL에 사용될 영문 슬러그 (모든 언어에서 동일) |
| `translationKey` | ✅ | 번역본 연결 키 (모든 언어에서 동일) |
| `tags` | ⚪ | 태그 목록 (각 언어로 번역) |
| `categories` | ⚪ | 카테고리 (각 언어로 번역) |
| `cover.image` | ⚪ | Hero 이미지 경로 |
| `tldr` | ⚪ | 요약 (각 언어로) |
| `license` | ⚪ | 개별 라이선스 (기본값: CC BY-NC 4.0) |

## 라이선스 설정

### 기본 라이선스
- 모든 포스트는 기본적으로 **CC BY-NC 4.0** 라이선스가 적용됩니다
- 개별 포스트에서 `license` 필드로 재정의할 수 있습니다

### 지원되는 라이선스
| 라이선스 | 설명 |
|----------|------|
| `CC BY-NC 4.0` | 저작자표시-비영리 (기본값) |
| `CC BY 4.0` | 저작자표시 |
| `CC BY-SA 4.0` | 저작자표시-동일조건변경허락 |
| `CC BY-NC-SA 4.0` | 저작자표시-비영리-동일조건변경허락 |
| `CC BY-NC-ND 4.0` | 저작자표시-비영리-변경금지 |
| `CC0` | 퍼블릭 도메인 |
| `MIT` | MIT 라이선스 |
| `All Rights Reserved` | 모든 권리 보유 |

### 개별 라이선스 지정 예시
```yaml
---
title: "오픈소스 프로젝트 소개"
license: "MIT"  # 이 글만 MIT 라이선스 적용
---
```

## 번역 워크플로우

### 규칙

1. **원본은 항상 한국어** (`content/ko/`)
2. **slug와 translationKey는 모든 언어에서 동일**
3. **디렉터리명도 모든 언어에서 동일** (예: `2025-12-04-hello-world/index.md`)
4. **태그/카테고리는 각 언어로 번역**
5. **license 필드는 모든 언어에서 동일** (번역하지 않음)

### 번역 시 주의사항

- 코드 블록은 번역하지 않음
- 기술 용어는 원어 유지 가능 (예: Hugo, Git)
- 링크가 내부 링크인 경우 해당 언어 경로로 변경
- 문화적 맥락이 필요한 경우 의역 허용

### 예시

**원본 (ko)**:
```yaml
tags:
  - 블로그
  - 시작하기
```

**영어 (en)**:
```yaml
tags:
  - blog
  - getting-started
```

**일본어 (ja)**:
```yaml
tags:
  - ブログ
  - はじめに
```

## Hero 이미지 규칙

### 저장 위치
```
static/images/posts/{slug}.jpg
```

### Unsplash 사용 시

1. 검색어는 포스트 주제와 관련된 영어 키워드 사용
2. 가로형 이미지 선택 (16:9 또는 비슷한 비율)
3. 최소 1200px 너비
4. 저작자 표시가 필요한 경우 front matter에 추가:
   ```yaml
   cover:
     image: "images/posts/my-post.jpg"
     caption: "Photo by [Name](url) on Unsplash"
   ```

## TL;DR 작성 규칙

- 1-2문장으로 핵심 내용 요약
- 각 언어로 자연스럽게 작성
- 기술적 내용은 구체적으로

## 커밋 메시지 규칙

```
feat(content): Add new post "포스트 제목"
feat(i18n): Add English translation for "slug-name"
feat(i18n): Add Japanese translation for "slug-name"
fix(content): Fix typo in "slug-name"
chore(images): Add hero image for "slug-name"
```

## 스크립트 사용

`scripts/` 디렉터리에 유틸리티 스크립트가 있습니다. **OS에 따라 적절한 스크립트를 선택**하세요:

| 기능 | Windows (PowerShell) | macOS/Linux (Python 3) |
|------|---------------------|------------------------|
| 새 포스트 생성 | `scripts/new-post.ps1` | `scripts/new_post.py` |
| 번역 검증 | `scripts/validate-translations.ps1` | `scripts/validate_translations.py` |
| Hero 이미지 다운로드 | `scripts/fetch-hero-image.ps1` | `scripts/fetch_hero_image.py` |
| 이미지 WebP 변환 | `scripts/optimize-images.ps1` | `scripts/optimize_images.py` |

### 스크립트 선택 규칙

1. **Windows 환경**: `.ps1` 파일 사용 (PowerShell 기본 제공)
2. **macOS/Linux 환경**: 
   - `python3 --version`으로 Python 3 설치 확인
   - 설치되어 있으면 `.py` 파일 사용
   - Python 3가 없으면 설치 안내 또는 PowerShell Core(`pwsh`) 사용

### 사용 예시

**Windows (PowerShell)**:
```powershell
.\scripts\new-post.ps1 -Slug "my-post" -Title "새 포스트"
.\scripts\validate-translations.ps1
.\scripts\fetch-hero-image.ps1 -Slug "my-post" -Keywords "coding,tech"
.\scripts\optimize-images.ps1
.\scripts\optimize-images.ps1 -Slug "my-post" -DeleteOriginals -UpdateFrontmatter
```

**macOS/Linux (Python)**:
```bash
python3 scripts/new_post.py --slug "my-post" --title "새 포스트"
python3 scripts/validate_translations.py
python3 scripts/fetch_hero_image.py --slug "my-post" --keywords "coding,tech"
python3 scripts/optimize_images.py
python3 scripts/optimize_images.py --slug "my-post" --delete-originals --update-frontmatter
```

## 검증 체크리스트

새 포스트 또는 번역 추가 시:

- [ ] Front matter 필수 필드 확인
- [ ] `translationKey`가 모든 번역본에서 동일
- [ ] `slug`가 모든 번역본에서 동일
- [ ] 디렉터리명이 모든 언어에서 동일
- [ ] Hero 이미지가 존재하면 경로 확인
- [ ] Hero 이미지 WebP 변환 완료 (`scripts/optimize_images.py`)
- [ ] 내부 링크가 올바른 언어 경로 사용

## 마크다운 작성 규칙

markdownlint 호환성을 위해 다음 규칙을 준수합니다:

### 테이블 작성 (MD060)

- 파이프(`|`) 좌우에 반드시 **공백 1개 이상**을 포함합니다.
- 구분선(`---`)도 파이프 좌우에 공백을 포함합니다.

**올바른 예시:**
```markdown
| Feature | Container | Virtual Machine |
| ------- | --------- | --------------- |
| Startup | Seconds   | Minutes         |
```

**잘못된 예시:**
```markdown
|Feature|Container|Virtual Machine|
|-------|---------|---------------|
|Startup|Seconds  |Minutes        |
```

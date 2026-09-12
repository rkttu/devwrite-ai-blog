# CLAUDE.md

<!-- 이 파일은 AGENTS.md에서 자동 생성됩니다. 수정하려면 AGENTS.md를 고친 뒤 `python3 scripts/sync_agent_docs.py`를 실행하세요. -->

이 파일은 Claude Code가 이 저장소에서 작업할 때 자동으로 컨텍스트에 로드됩니다.
원본은 [AGENTS.md](./AGENTS.md)입니다.

한국어 글쓰기 스타일 가이드는 다음 파일에서 불러옵니다.

@./writing-style-guide.md

## 프로젝트 개요

- **프레임워크**: Hugo (정적 사이트 생성기)
- **테마**: PaperMod
- **지원 언어**: 한국어(ko), English(en), 日本語(ja)
- **기본 언어**: 한국어 (ko)

## 공용 Agent Skills

블로그 작업 스킬의 원본은 `.agents/skills/`에 있습니다. GitHub Copilot과 Codex는 이 경로의 원본을 사용합니다.
Claude Code는 `.claude/skills/`의 심볼릭 링크를 통해 같은 원본을 불러옵니다. Windows에서 Developer Mode를 활성화하고
Git이 심볼릭 링크를 보존하도록 설정하면 이 구조를 사용할 수 있습니다.
`.claude/skills/<스킬 이름>/SKILL.md`를 열면 원본 파일의 내용을 확인할 수 있습니다.
스킬을 수정할 때에는 `.agents/skills/<스킬 이름>/SKILL.md`와 해당 디렉터리의 리소스만 갱신합니다.

에이전트가 요청에 맞는 스킬을 자동으로 선택하도록 작업 내용을 설명하거나 `/스킬 이름`으로 직접 호출할 수 있습니다.
전체 발행에는 `/publish-blog-post`를 사용합니다. 특정 단계만 수행할 때에는 `/prepare-blog-post`, `/deploy-blog-post`,
`/publish-blog-to-dotnetdev`, `/share-blog-on-linkedin` 또는 해당 하위 스킬을 사용합니다.

한국어 문안을 작성, 번역, 윤문 또는 리뷰하는 작업에서는 먼저 저장소 루트의 `writing-style-guide.md` 전체를 읽고
산출물의 종류에 맞는 적용 등급을 사용합니다. 사용자가 별도 문체를 지정했다면 사용자 지시를 우선합니다.

| 스킬 | 용도 | 인자 |
| --- | --- | --- |
| `/create-draft` | 새 포스트 생성 | `<slug> <주제>` |
| `/complete-manual-post` | 수동으로 쓴 글에 front matter, 요약, 번역 보강 | `<ko-post-path>` |
| `/generate-tldr` | 포스트의 `description`과 `tldr` 생성 | `<post-path>` |
| `/select-hero-image` | 히어로 이미지 후보 검색 또는 생성 | `<post-path>` |
| `/translate-post` | 한국어 포스트를 영어/일본어로 번역 | `<slug> <en\|ja>` |
| `/review-draft` | 발행 전 체크리스트 검토 | `<slug-or-path>` |
| `/publish-draft` | `draft: true`에서 `false`로 일괄 변경 | `<slug>` |
| `/unpublish-post` | `draft: false`에서 `true`로 일괄 변경 | `<slug>` |
| `/prepare-blog-post` | 글 작성, 보완, 번역, 리뷰와 발행 전 검증 | `<slug 또는 경로>` |
| `/deploy-blog-post` | 커밋, 푸시, GitHub Pages 배포 검증 | `<slug>` |
| `/publish-blog-to-dotnetdev` | 닷넷데브 게시 초안 생성과 브라우저 인계 | `<slug>` |
| `/share-blog-on-linkedin` | LinkedIn 문안 생성과 공유 화면 인계 | `<slug>` |
| `/publish-blog-post` | 글 준비부터 배포와 외부 채널 공유까지 전체 발행 | `<slug 또는 주제>` |

## 공용 MCP 설정

프로젝트 MCP 서버 설정의 원본은 `.codex/config.toml`입니다. `.mcp.json`은 GitHub Copilot과 Claude Code가 함께 읽는
파생 파일이므로 직접 수정하지 않습니다. 원본을 변경한 뒤 `python3 scripts/sync_mcp_config.py`를 실행하고
`python3 scripts/sync_mcp_config.py --check`로 두 파일이 일치하는지 확인합니다. 공용 형식으로 안전하게 변환할 수 없는
Codex 전용 필드가 있으면 변환 스크립트가 실패합니다.

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

assets/
└── images/
    └── posts/    # Hero 이미지 저장 위치 (공용)
```

## 파일 명명 규칙

- **포스트 디렉터리명**: `{YYYY-MM-DD}-{slug}/` (예: `2025-12-04-docker-basics/`)
- **포스트 파일명**: 각 디렉터리 안에 `index.md` (예: `2025-12-04-docker-basics/index.md`)
- **포스트 내 이미지**: 같은 디렉터리에 저장 (예: `2025-12-04-docker-basics/diagram.png`)
- **URL**: `slug` 필드가 결정 (예: `/ko/posts/docker-basics/`)
- **Hero 이미지**: `assets/images/posts/{slug}.jpg` (예: `docker-basics.jpg`)
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
description: "SEO용 1문장 요약, 50~160자 (각 언어로)"
cover:
  image: "images/posts/slug-name.jpg"
  alt: "이미지 설명"
tldr: "이 글의 핵심 요약 (1-2문장, description보다 상세)"
license: "CC BY-NC 4.0"  # 선택사항, 기본값: CC BY-NC 4.0
---
```

### 필드 설명

| 필드 | 필수 | 설명 |
| --- | --- | --- |
| `title` | ✅ | 사람이 읽기 좋은 제목 (각 언어로) |
| `date` | ✅ | ISO 8601 형식, 타임존 포함 |
| `draft` | ✅ | 발행 여부 |
| `slug` | ✅ | URL에 사용될 영문 슬러그 (모든 언어에서 동일) |
| `translationKey` | ✅ | 번역본 연결 키 (모든 언어에서 동일) |
| `description` | ✅ | SEO 메타 태그용 요약, 50~160자 (각 언어로) |
| `tags` | ⚪ | 태그 목록 (각 언어로 번역) |
| `categories` | ⚪ | 카테고리 (각 언어로 번역) |
| `cover.image` | ⚪ | Hero 이미지 경로 |
| `cover.alt` | ⚪ | 이미지 대체 텍스트 (각 언어로) |
| `tldr` | ⚪ | 독자용 핵심 요약 (각 언어로, description보다 상세) |
| `license` | ⚪ | 개별 라이선스 (기본값: CC BY-NC 4.0) |

### `description`과 `tldr`의 차이

| 항목 | `description` | `tldr` |
| --- | --- | --- |
| **용도** | SEO 메타 태그 (`<meta name="description">`, OG, Twitter) | 본문 상단 표시, JSON-LD `"abstract"` |
| **길이** | 50~160자 (검색 스니펫 최적) | 1~2문장 (description보다 상세) |
| **톤** | 클릭을 유도하는 매력적 표현 | 핵심 내용을 정확히 전달 |

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
5. **description과 tldr은 각 언어로 번역** (SEO에 중요)
6. **license 필드는 모든 언어에서 동일** (번역하지 않음)

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

## 예약 발행

사용자가 예약 발행을 요청하면 세 언어의 `date`에 같은 공개 시각과 시간대를 지정하고 `draft: false`로 전환합니다. 별도 `publishDate`를 사용하는 경우 세 언어에서 같은 값을 유지합니다. 디렉터리 날짜도 공개일에 맞춥니다.

프로덕션 빌드는 `buildDrafts=false`와 `buildFuture=false`로 실행합니다. `deploy.yml`은 매일 오전 9시(한국 시각, UTC cron `0 0 * * *`)에 기본 브랜치를 다시 빌드하며 푸시와 수동 실행도 지원합니다. GitHub 실행 지연이나 빌드 실패에 따라 실제 공개 시각은 늦어질 수 있습니다.

미래 회차를 참조하는 링크는 `series-link` shortcode로 작성합니다. 공개 전에는 제목과 공개 예정 문구를 표시하고 해당 언어의 페이지가 빌드에 포함되면 링크를 생성합니다. 공개 일정 전후의 빌드에서 페이지와 목록, 피드, 검색, 사이트맵, 내부 링크를 검증합니다.

예약 설정 완료와 실제 공개 완료를 구분해 보고합니다. 예약 시각 전에는 운영 URL이 공개되지 않았음을 확인하고, 공개 시각이 지난 글은 HTTP 상태와 제목, canonical을 확인합니다. 실행 실패 시 `main`의 배포 워크플로를 수동 실행하면 그 시점까지 기한이 지난 글을 반영합니다. 상세 운영 조건은 `docs/decisions/0004-daily-scheduled-publishing.md`에 있습니다.

## Hero 이미지 규칙

### 저장 위치

```
assets/images/posts/{slug}.jpg   ← 원본 (다운로드 시)
assets/images/posts/{slug}.webp  ← 최적화 후 (권장)
```

### WebP 변환 (권장)

다운로드 후 `scripts/optimize-images.ps1` 또는 `scripts/optimize_images.py`로 WebP 변환:

```powershell
.\scripts\optimize-images.ps1 -Slug "{slug}" -DeleteOriginals -UpdateFrontmatter
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
.\scripts\optimize-images.ps1
.\scripts\optimize-images.ps1 -Slug "my-post" -DeleteOriginals -UpdateFrontmatter
```

**macOS/Linux (Python)**:

```bash
python3 scripts/new_post.py --slug "my-post" --title "새 포스트"
python3 scripts/validate_translations.py
python3 scripts/optimize_images.py
python3 scripts/optimize_images.py --slug "my-post" --delete-originals --update-frontmatter
```

## 검증 체크리스트

새 포스트 또는 번역 추가 시:

- [ ] Front matter 필수 필드 확인 (`title`, `date`, `draft`, `slug`, `translationKey`, `description`)
- [ ] `description`이 50~160자이고 SEO에 적합한지 확인
- [ ] `description`과 `tldr`이 서로 다른 문장인지 확인
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

## 환경 메모

- 주 작업 환경은 Windows 11 + PowerShell. macOS/Linux의 동등한 Python 스크립트는 `scripts/*.py`.
- 커밋과 푸시처럼 외부 영향이 있는 작업은 사용자가 명시적으로 요청했을 때만 수행합니다.

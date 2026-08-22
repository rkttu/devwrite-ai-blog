# /dev/write

[운영 사이트](https://devwrite.ai/ko/) | [배포 상태](https://github.com/rkttu/devwrite-ai-blog/actions/workflows/deploy.yml)

[![Deploy Hugo site to GitHub Pages](https://github.com/rkttu/devwrite-ai-blog/actions/workflows/deploy.yml/badge.svg)](https://github.com/rkttu/devwrite-ai-blog/actions/workflows/deploy.yml)

이 저장소는 Hugo Extended와 PaperMod를 기반으로 운영하는 다국어 소프트웨어 개발 블로그입니다. 한국어 글을 원본으로 관리하고 영어와 일본어 번역, 검색 메타데이터, GitHub Pages 배포 산출물을 함께 생성합니다.

콘텐츠 준비부터 번역, 리뷰, 배포, 닷넷데브와 LinkedIn 공유까지 에이전트 스킬로 구성했습니다. OpenAI Codex, GitHub Copilot, Claude Code는 같은 글쓰기 규칙과 발행 절차를 사용합니다.

아래에서는 로컬 실행, 콘텐츠 구조, 에이전트 워크플로, MCP 설정, 배포와 운영 정책 순서로 저장소 사용법을 정리하겠습니다.

## 주요 기능

- 한국어, 영어, 일본어 Page Bundle과 언어 전환 링크
- 언어별 RSS 피드, 검색 페이지, 아카이브, 관련 글과 다국어 404 페이지
- `description`, Open Graph, Twitter Card, `BlogPosting`과 `Person` JSON-LD
- 언어별 `llms.txt`, `robots.txt`, 사이트맵과 AI 크롤러 정책
- Hugo 이미지 처리, WebP 변환 도구와 1MB 자산 제한 검사
- 포스트별 라이선스와 기본 `CC BY-NC 4.0` 정책
- GitHub Actions 품질 검사와 GitHub Pages 배포
- `.agents/skills/`를 원본으로 사용하는 다중 에이전트 글 작성 및 발행 절차
- 광고, 댓글, 예약 발행, 외부 뉴스레터 연동을 포함하지 않는 정적 운영 구조

## 로컬 환경과 검증

### 요구 사항

- Git
- [Hugo Extended](https://gohugo.io/installation/) 0.165.0 이상
- Python 3.12, GitHub Actions와 같은 버전으로 검증할 때 사용
- Pillow 12.3.0, 이미지 변환 도구를 사용할 때만 설치

### 개발 서버

저장소를 받은 다음 개발 환경으로 Hugo를 실행합니다. PaperMod 기준 리비전 복사본은 저장소에 포함되어 있습니다. 개발 설정은 `draft: true`인 글도 표시합니다.

```bash
git clone https://github.com/rkttu/devwrite-ai-blog.git
cd devwrite-ai-blog
hugo server --environment development
```

기본 접속 주소는 `http://localhost:1313/ko/`입니다. Hugo는 콘텐츠와 템플릿 변경을 감지해 브라우저를 새로고침합니다.

### 이미지 도구

Hero 이미지를 WebP로 변환하거나 크기를 조정할 때 Python 가상 환경에 도구 의존성을 설치합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-tools.txt
python scripts/optimize_images.py --slug "my-post" --delete-originals --update-frontmatter
```

Windows에서는 `scripts/optimize-images.ps1`이 같은 Python 스크립트를 호출합니다.

### 소스 품질 검사

Pull Request와 수동 실행에서는 [품질 검사 워크플로](.github/workflows/quality.yml)가 다음 검사를 실행합니다. MCP 설정 동기화 검사는 단위 테스트에 포함됩니다.

```bash
python3 scripts/sync_mcp_config.py --check
python3 -m unittest discover -s tests -v
python3 scripts/validate_translations.py
python3 scripts/check_asset_sizes.py
```

### 프로덕션 산출물

GitHub Pages 배포와 같은 조건으로 정적 파일을 생성하고 내부 링크, JSON-LD, 이미지 대체 텍스트, 필수 파일을 검사합니다.

```bash
hugo --environment production --cleanDestinationDir --gc --minify --panicOnWarning --buildDrafts=false
cp public/ko/404.html public/404.html
cp public/ko/llms.txt public/llms.txt
python3 scripts/validate_site.py public
```

루트 `404.html`과 `llms.txt`는 한국어 산출물을 복사합니다. 각 언어 디렉터리의 파일은 그대로 유지됩니다.

## 콘텐츠 구조와 작성 규칙

### 다국어 Page Bundle

세 언어는 같은 디렉터리명, `slug`, `translationKey`, 날짜와 공개 상태를 공유합니다. 제목, 본문, `description`, `tldr`, 태그, 카테고리와 이미지 대체 텍스트는 언어별로 작성합니다.

```text
content/
├── ko/posts/2026-08-23-my-post/index.md
├── en/posts/2026-08-23-my-post/index.md
└── ja/posts/2026-08-23-my-post/index.md
```

### 새 한국어 초안

수동 작성용 스크립트는 한국어 Page Bundle 하나를 `draft: true` 상태로 생성합니다. PowerShell 래퍼도 같은 Python 구현을 사용합니다.

```bash
python3 scripts/new_post.py --slug "my-post" --title "새 포스트"
pwsh -File scripts/new-post.ps1 -Slug "my-post" -Title "새 포스트"
```

세 언어 초안과 메타데이터를 함께 준비하려면 `create-draft` 또는 `prepare-blog-post` 스킬을 사용합니다.

### Front Matter

새 글은 다음 구조를 기준으로 작성합니다. `date`에는 시간대를 포함하며 미래 시각을 입력하지 않습니다.

```yaml
---
title: "포스트 제목"
date: 2026-08-23T10:00:00+09:00
draft: true
slug: "my-post"
description: "검색 결과와 공유 카드에 사용할 한 문장 요약"
tags:
  - Hugo
categories:
  - 개발 도구
translationKey: "my-post"
cover:
  image: "images/posts/my-post.webp"
  alt: "대표 이미지의 내용을 설명하는 대체 텍스트"
tldr: "본문 상단과 JSON-LD abstract에 사용할 핵심 요약"
license: "CC BY-NC 4.0"
---
```

작성 정책은 다음 필드를 기준으로 검사합니다.

| 필드 | 작성 기준 | 언어 간 일치 여부 |
| --- | --- | --- |
| `title` | 언어별 제목 | 다르게 작성 |
| `date` | 시간대를 포함한 현재 또는 과거 시각 | 동일 |
| `draft` | 초안은 `true`, 배포 대상은 `false` | 동일 |
| `slug` | 영문 소문자, 숫자와 단일 하이픈 | 동일 |
| `translationKey` | 번역본 연결 식별자 | 동일 |
| `description` | 검색용 50자에서 160자 사이 요약 | 다르게 작성 |
| `tldr` | 독자와 JSON-LD용 한두 문장 요약 | 다르게 작성 |
| `cover.image` | `assets/images/` 아래의 공용 이미지 | 동일 |
| `cover.alt` | 이미지 의미를 전달하는 대체 텍스트 | 다르게 작성 |
| `license` | 생략하면 `CC BY-NC 4.0` 적용 | 동일 |

한국어 글과 작업 보고는 [한국어 글쓰기 스타일 가이드](writing-style-guide.md)를 따릅니다. 콘텐츠와 메타데이터의 세부 규칙은 [GitHub Copilot 작업 지침](.github/copilot-instructions.md)에 정리했습니다.

## 에이전트 글 작성과 발행 워크플로

블로그 스킬의 원본은 [`.agents/skills/`](.agents/skills/)에 있습니다. GitHub Copilot과 OpenAI Codex는 이 경로를 사용합니다. Claude Code는 `.claude/skills/`의 심볼릭 링크를 통해 같은 원본을 읽으며 [CLAUDE.md](CLAUDE.md)가 공용 작업 지침과 글쓰기 가이드를 불러옵니다.

작업 범위에 따라 다음 스킬을 선택할 수 있습니다.

- 새 글 생성: `create-draft`
- 수동 작성 글 보완: `complete-manual-post`
- 요약 작성: `generate-tldr`
- Hero 이미지 선정: `select-hero-image`
- 영어와 일본어 번역: `translate-post`
- 사실성, 문장, SEO와 번역 검토: `review-draft`
- 작성부터 발행 직전 검증까지 통합: `prepare-blog-post`
- 세 언어의 공개 상태 전환: `publish-draft`, `unpublish-post`
- 커밋, 푸시, Actions와 운영 URL 검증: `deploy-blog-post`
- 닷넷데브 게시 초안과 브라우저 인계: `publish-blog-to-dotnetdev`
- LinkedIn 문안과 공유 화면 인계: `share-blog-on-linkedin`
- 준비부터 외부 채널 공유까지 조정: `publish-blog-post`

글 준비와 검토만 요청하면 스킬은 커밋이나 푸시를 수행하지 않습니다. 배포 스킬도 사용자가 커밋 또는 푸시 범위를 명시한 경우에만 Git 상태를 변경합니다.

## 공용 MCP 설정

OpenAI Codex는 [`.codex/config.toml`](.codex/config.toml)을 프로젝트 MCP 설정 원본으로 읽습니다. GitHub Copilot Agent Host와 CLI, Claude Code는 Codex TOML 형식을 직접 읽지 못하므로 변환한 [`.mcp.json`](.mcp.json)을 함께 사용합니다.

MCP 서버를 추가하거나 수정한 뒤 다음 명령으로 공용 설정을 생성하고 일치 여부를 검사합니다.

```bash
python3 scripts/sync_mcp_config.py
python3 scripts/sync_mcp_config.py --check
```

변환 스크립트는 세 도구에서 의미가 같은 HTTP와 표준 입출력 설정만 처리합니다. 지원하지 않는 Codex 전용 필드를 발견하면 해당 필드를 누락하지 않고 오류를 반환합니다. 기존 `.vscode/mcp.json`은 같은 서버의 중복 등록을 피하기 위해 제거했습니다.

현재 공용 설정은 Microsoft Learn MCP 서버를 Streamable HTTP로 연결합니다. 각 도구는 프로젝트 또는 MCP 서버를 처음 사용할 때 신뢰 여부를 확인할 수 있습니다. API 키와 토큰은 저장소에 기록하지 않습니다.

## GitHub Pages 배포와 외부 채널

### 배포 흐름

`main` 브랜치에 푸시하면 [배포 워크플로](.github/workflows/deploy.yml)가 다음 순서로 사이트를 반영합니다.

1. Hugo Extended 패키지의 체크섬을 검증하고 설치합니다.
2. 단위 테스트, 번역 일관성 검사와 이미지 크기 검사를 실행합니다.
3. 프로덕션 사이트를 빌드하고 산출물 구조를 검사합니다.
4. GitHub Pages 아티팩트를 업로드하고 배포합니다.
5. `deploy-blog-post` 스킬이 해당 커밋의 Actions 결과와 세 언어 URL을 확인합니다.

`draft: false`는 다음 프로덕션 빌드에 글을 포함한다는 뜻이며 커밋이나 배포를 대신하지 않습니다. 예약 발행은 지원하지 않으며 미래 날짜가 있으면 번역 검증 단계가 실패합니다. 철회 배경은 [예약 발행 결정 기록](docs/decisions/0001-retire-scheduled-publishing.md)에 정리했습니다.

### 닷넷데브와 LinkedIn

운영 블로그 URL을 외부 게시의 원본으로 유지합니다. `publish-blog-to-dotnetdev`는 `disc` CLI로 포럼 작성 화면을 열고 초안을 전달합니다. `share-blog-on-linkedin`은 일반 포스트 문안과 해시태그를 만든 뒤 클립보드와 공유 화면으로 넘깁니다.

두 스킬은 게시 버튼을 누르지 않습니다. 사용자가 브라우저에서 문안을 검토하고 발행을 완료합니다. LinkedIn 뉴스레터 API나 웹 자동 입력 기능도 사용하지 않습니다.

### 제외한 통합

Kit 뉴스레터 연동은 현재 사용하지 않습니다. 제거 배경은 [Kit 연동 결정 기록](docs/decisions/0002-remove-kit-newsletter.md)에 남겼습니다. 카카오 애드핏과 댓글 시스템도 제거했으며 페이지 로드 시 실행하는 외부 코드는 [외부 서비스 로딩 정책](docs/external-services.md)에 기록한 항목으로 제한합니다.

## 저장소 구조와 운영 문서

주요 디렉터리와 설정 파일은 다음과 같이 구성했습니다.

```text
content/                 # 한국어, 영어, 일본어 콘텐츠
assets/                  # Hugo 파이프라인이 처리하는 CSS와 이미지
layouts/                 # PaperMod 재정의 템플릿
config/                  # 기본, 개발, 프로덕션 Hugo 설정
scripts/                 # 생성, 이미지 처리, 검증, MCP 동기화 도구
tests/                   # Python 단위 테스트
.agents/skills/          # 블로그 작업 스킬 원본
.claude/skills/          # Claude Code용 심볼릭 링크
.codex/config.toml       # MCP 설정 원본
.mcp.json                # Copilot과 Claude Code용 MCP 파생 설정
.github/workflows/       # 품질 검사와 GitHub Pages 배포
docs/decisions/          # 운영 결정 기록
themes/PaperMod/         # 저장소에 포함한 PaperMod 기준 리비전 복사본
```

운영 상태와 설계 근거는 다음 문서에서 확인할 수 있습니다.

- [SEO 및 트래픽 개선 완료 기록](seo-improvements.md)
- [외부 서비스 로딩 정책](docs/external-services.md)
- [PaperMod 기준 리비전과 갱신 절차](themes/PaperMod/UPSTREAM.md)
- [예약 발행 철회 기록](docs/decisions/0001-retire-scheduled-publishing.md)
- [Kit 뉴스레터 연동 제거 기록](docs/decisions/0002-remove-kit-newsletter.md)
- [HTTP 보안 헤더 적용 경로](docs/decisions/0003-plan-http-security-headers.md)

GitHub Pages는 저장소 템플릿에서 응답 헤더를 지정할 수 없습니다. 보안 헤더는 CDN이나 프록시를 도입할 때 적용하며 현재 HTML에서 제공할 수 있는 Referrer Policy와 링크 보안 속성은 템플릿이 처리합니다.

저장소의 코드와 도구는 [MIT 라이선스](LICENSE)로 배포합니다. 블로그 포스트는 별도 값을 지정하지 않으면 `CC BY-NC 4.0`을 적용합니다. PaperMod는 원본 프로젝트의 MIT 라이선스를 따릅니다.

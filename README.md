# /dev/write

> *코드와 글이 만나는 곳, 개발자의 생각을 담는 블로그*

Hugo 정적 사이트 생성기와 PaperMod 테마를 기반으로 구축된 다국어 개발 블로그입니다. GitHub Copilot과의 협업을 통해 콘텐츠 작성부터 번역까지 AI 기반 워크플로우를 지원합니다.

[![Deploy Hugo site to GitHub Pages](https://github.com/rkttu/devwrite-ai-blog/actions/workflows/deploy.yml/badge.svg)](https://github.com/rkttu/devwrite-ai-blog/actions/workflows/deploy.yml)

## 🌐 지원 언어

이 블로그는 세 가지 언어로 콘텐츠를 제공합니다. 모든 포스트는 한국어로 먼저 작성되며, 영어와 일본어로 번역됩니다.

- 🇰🇷 **한국어** — 기본 언어, 모든 원본 콘텐츠의 출발점
- 🇺🇸 **English** — 글로벌 독자를 위한 영어 번역
- 🇯🇵 **日本語** — 일본어권 독자를 위한 번역

## 🚀 시작하기

### 필수 요구사항

로컬에서 블로그를 실행하려면 다음이 필요합니다:

- [Hugo Extended](https://gohugo.io/installation/) v0.139.0 이상 (SCSS 처리를 위해 Extended 버전 필수)
- Git

### 로컬 개발 환경 설정

저장소를 클론하고 개발 서버를 실행합니다. Hugo의 라이브 리로드 기능 덕분에 파일을 수정하면 브라우저가 자동으로 새로고침됩니다.

```bash
# 저장소 클론
git clone https://github.com/rkttu/devwrite-ai-blog.git
cd devwrite-ai-blog

# 개발 서버 실행 (-D 플래그로 드래프트 포스트도 표시)
hugo server -D

# 브라우저에서 http://localhost:1313 접속
```

### 프로덕션 빌드

배포용 정적 파일을 생성합니다. `--gc` 플래그로 사용하지 않는 캐시를 정리하고, `--minify`로 파일 크기를 최적화합니다.

```bash
hugo --gc --minify --buildDrafts=false --buildFuture=false
```

## 📁 프로젝트 구조

```text
content/
├── ko/           # 한국어 콘텐츠 (원본)
├── en/           # English 콘텐츠 (번역)
└── ja/           # 日本語 콘텐츠 (번역)

static/
└── images/
    └── posts/    # 포스트 Hero 이미지 (1200x630px 권장)

scripts/          # 포스트 생성, 번역 검증 등 유틸리티 스크립트

.github/
├── workflows/    # GitHub Actions CI/CD 파이프라인
└── copilot-instructions.md  # GitHub Copilot 작업 가이드
```

## 🤖 GitHub Copilot으로 글 작성하기

이 블로그는 GitHub Copilot(또는 AI 에이전트)과의 협업을 염두에 두고 설계되었습니다. `.github/copilot-instructions.md` 파일에 정의된 규칙을 통해 Copilot이 프로젝트 구조와 컨벤션을 이해하고 일관된 결과물을 생성합니다.

### 새 포스트 작성 요청

VS Code에서 GitHub Copilot Chat을 열고 다음과 같이 요청할 수 있습니다:

```
"Docker 기초 사용법"이라는 제목으로 새 블로그 포스트를 만들어줘.
slug는 "docker-basics"로 하고, 태그는 Docker, 컨테이너, DevOps로 해줘.
```

Copilot은 `copilot-instructions.md`의 규칙에 따라:
- 올바른 파일명 형식(`2025-12-04-docker-basics.md`)으로 생성
- 필수 Front Matter 필드 자동 포함
- 세 언어 디렉터리에 각각 파일 생성

### 번역 요청

기존 한국어 포스트를 영어나 일본어로 번역해달라고 요청할 수 있습니다:

```
content/ko/posts/2025-12-04-docker-basics.md 파일을 영어와 일본어로 번역해줘.
```

Copilot은 다음 규칙을 자동으로 준수합니다:
- `slug`와 `translationKey`는 원본과 동일하게 유지
- 코드 블록은 번역하지 않음
- 태그와 카테고리는 각 언어로 자연스럽게 번역
- 기술 용어(Hugo, Git 등)는 원어 유지

### Hero 이미지 추가

포스트에 어울리는 커버 이미지도 요청할 수 있습니다:

```
docker-basics 포스트에 어울리는 Hero 이미지를 Unsplash에서 찾아서 추가해줘.
```

### 번역 상태 검증

모든 언어에 번역이 완료되었는지 확인하려면:

```
번역이 누락된 포스트가 있는지 확인해줘.
```

## ✍️ 수동으로 포스트 작성하기

Copilot 없이 직접 포스트를 작성하려면 스크립트를 사용하거나 수동으로 파일을 생성할 수 있습니다.

### 스크립트 사용

#### Windows (PowerShell)

```powershell
.\scripts\new-post.ps1 -Slug "my-post" -Title "새 포스트"
```

#### macOS/Linux (Python)

```bash
python3 scripts/new_post.py --slug "my-post" --title "새 포스트"
```

### 포스트 Front Matter 형식

모든 포스트는 다음 Front Matter 구조를 따라야 합니다:

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
---
```

| 필드 | 필수 | 설명 |
|------|:----:|------|
| `title` | ✅ | 각 언어로 작성된 포스트 제목 |
| `date` | ✅ | ISO 8601 형식의 날짜 (타임존 포함) |
| `draft` | ✅ | `true`면 개발 환경에서만 표시 |
| `slug` | ✅ | URL 경로에 사용될 영문 식별자 |
| `translationKey` | ✅ | 번역본을 연결하는 고유 키 |
| `tags` | ⚪ | 관련 태그 목록 |
| `cover.image` | ⚪ | Hero 이미지 경로 |
| `tldr` | ⚪ | 한두 문장으로 요약 |

## 🔧 주요 기능

- **🌍 다국어 지원** — 한국어, 영어, 일본어 세 언어로 콘텐츠 제공
- **📡 RSS 피드** — 언어별 `/feed.xml` 자동 생성으로 구독 지원
- **🔗 OpenGraph/Twitter Cards** — Facebook, X(Twitter) 등 SNS 공유 시 풍부한 미리보기
- **🌓 다크/라이트 테마** — 시스템 설정에 따라 자동 전환, 수동 토글 가능
- **📋 코드 하이라이팅** — 구문 강조와 원클릭 복사 버튼
- **⏱️ 읽기 시간 표시** — 포스트별 예상 읽기 시간 자동 계산

## 📡 RSS 피드

구독자들이 새 글을 받아볼 수 있도록 언어별 RSS 피드를 제공합니다:

| 언어 | 피드 URL |
|------|----------|
| 한국어 | `https://devwrite.ai/ko/feed.xml` |
| English | `https://devwrite.ai/en/feed.xml` |
| 日本語 | `https://devwrite.ai/ja/feed.xml` |

## 🚀 배포

이 블로그는 **GitHub Pages**로 호스팅되며, `main` 브랜치에 푸시하면 **GitHub Actions**가 자동으로 빌드하고 배포합니다.

배포 과정:
1. `main` 브랜치에 커밋 푸시
2. GitHub Actions가 Hugo로 정적 파일 빌드
3. 빌드된 파일이 GitHub Pages에 자동 배포
4. 수 분 내로 변경사항이 라이브 사이트에 반영

수동 배포가 필요한 경우 GitHub Actions 탭에서 "Run workflow" 버튼을 클릭할 수 있습니다.

## 📜 라이선스

이 프로젝트는 [MIT 라이선스](LICENSE)로 배포됩니다. 자유롭게 사용, 수정, 배포할 수 있습니다.

### 테마 저작권 안내

이 블로그는 [PaperMod](https://github.com/adityatelange/hugo-PaperMod) 테마를 기반으로 커스터마이징되었습니다. PaperMod는 빠르고 깔끔한 디자인으로 사랑받는 Hugo 테마입니다.

**원본 테마 저작권:**

- Copyright (c) 2020 nanxiaobei and adityatelange
- Copyright (c) 2021-2025 adityatelange

PaperMod 테마는 MIT 라이선스로 배포됩니다. 자세한 내용은 [원본 저장소](https://github.com/adityatelange/hugo-PaperMod)에서 확인할 수 있습니다.

## 🙏 감사의 말

이 프로젝트는 훌륭한 오픈소스 도구들 덕분에 가능했습니다:

- **[Hugo](https://gohugo.io/)** — 세계에서 가장 빠른 정적 사이트 생성기
- **[PaperMod](https://github.com/adityatelange/hugo-PaperMod)** — 미니멀하면서도 기능이 풍부한 Hugo 테마
- **[GitHub Copilot](https://github.com/features/copilot)** — AI 기반 코딩 및 콘텐츠 작성 보조

# Prompt: Create New Blog Post (Full Workflow)

> **스타일 가이드**: 글 작성 시 반드시 `/writing-style-guide.md` 파일을 참조하여 언어별 작성 규칙을 따르세요.

## Task

Create a complete blog post with all translations, TL;DR, and hero image.

## Input

- **Topic**: 글의 주제 또는 제목
- **Slug**: URL에 사용할 영문 슬러그
- **Content outline or full content**: 작성할 내용 (개요 또는 전체)

## Workflow

### Step 1: Create Korean (Original) Post

1. Create directory: `content/ko/posts/{YYYY-MM-DD}-{slug}/`
2. Create file: `content/ko/posts/{YYYY-MM-DD}-{slug}/index.md`
3. Generate front matter with all required fields
4. Write the full content in Korean

**디렉터리 구조**: Page Bundle — `{date}-{slug}/index.md` (예: `2025-12-04-docker-basics/index.md`)

### Step 2: Generate TL;DR and Description

1. Analyze the post content
2. Write `description`: SEO용 1문장 요약, 50~160자 (검색 결과 스니펫)
3. Write `tldr`: 독자용 핵심 요약, 1-2문장 (description보다 상세하고 구체적)

**`description` vs `tldr` 차이**:

| 항목 | `description` | `tldr` |
| --- | --- | --- |
| **용도** | SEO 메타 태그 (`<meta name="description">`, OG, Twitter) | 본문 상단 표시 (독자용 요약) |
| **길이** | 50~160자 (검색 스니펫 최적) | 1~2문장 (더 상세하고 기술적) |
| **JSON-LD** | `"description"` 필드 | `"abstract"` 필드 |
| **톤** | 클릭을 유도하는 매력적인 표현 | 핵심 내용을 정확히 전달 |

### Step 3: Select Hero Image

1. Analyze post topic
2. Find appropriate image from Unsplash (https://unsplash.com)
3. Get direct image URL: `https://images.unsplash.com/photo-XXXXX?w=1200&h=630&fit=crop`
4. Download to `static/images/posts/{slug}.jpg`

**Windows (PowerShell)**:
```powershell
$url = "https://images.unsplash.com/photo-XXXXX?w=1200&h=630&fit=crop"
Invoke-WebRequest -Uri $url -OutFile "static/images/posts/{slug}.jpg"
```

**macOS/Linux**:
```bash
curl -L "https://images.unsplash.com/photo-XXXXX?w=1200&h=630&fit=crop" -o static/images/posts/{slug}.jpg
```

### Step 4: Create Translations

Create translated versions for all configured languages (Page Bundle 구조):

| Language | Path | Notes |
| --- | --- | --- |
| English (en) | `content/en/posts/{YYYY-MM-DD}-{slug}/index.md` | Translate content, tags, categories, description, tldr, cover.alt |
| Japanese (ja) | `content/ja/posts/{YYYY-MM-DD}-{slug}/index.md` | Translate content, tags, categories, description, tldr, cover.alt |

**Important**: Use the same date and directory name across all languages.

### Step 5: Optimize Hero Image

이미지를 WebP로 변환하여 최적화:

**Windows**: `.\scripts\optimize-images.ps1 -Slug "{slug}" -DeleteOriginals -UpdateFrontmatter`
**macOS/Linux**: `python3 scripts/optimize_images.py --slug "{slug}" --delete-originals --update-frontmatter`

### Step 6: Update llms.txt

새 포스트를 `static/llms.txt`의 포스트 목록에 추가:
```
- [포스트 제목](/ko/posts/{slug}/) — description 내용
```

### Step 7: Validate

Run validation script:

**Windows**: `.\scripts\validate-translations.ps1`
**macOS/Linux**: `python3 scripts/validate_translations.py`

## Front Matter Template

```yaml
---
title: "제목 (각 언어로)"
date: YYYY-MM-DDTHH:MM:SS+09:00
draft: true
slug: "{slug}"
tags:
  - tag1 (각 언어로)
  - tag2
categories:
  - category (각 언어로)
translationKey: "{slug}"
description: "SEO용 1문장 요약, 50~160자 (각 언어로)"
tldr: "핵심 요약, 1-2문장 (각 언어로, description보다 상세)"
cover:
  image: "images/posts/{slug}.jpg"
  alt: "이미지 설명 (각 언어로)"
---
```

**Note**: 새 글은 항상 `draft: true`로 생성됩니다. 검토 후 `draft: false`로 변경하여 발행하세요.

## Fields That Must Be Identical Across Languages

- `date`
- `draft`
- `slug`
- `translationKey`
- `cover.image`
- `license` (사용 시)

## Fields That Must Be Translated

- `title`
- `tags`
- `categories`
- `description`
- `tldr`
- `cover.alt`
- All body content (except code blocks)

## Example Output Structure

```
content/
├── ko/posts/{YYYY-MM-DD}-{slug}/
│   └── index.md                       ✅ Created (original)
├── en/posts/{YYYY-MM-DD}-{slug}/
│   └── index.md                       ✅ Created (translation)
└── ja/posts/{YYYY-MM-DD}-{slug}/
    └── index.md                       ✅ Created (translation)

static/images/posts/
└── {slug}.webp                        ✅ Downloaded & optimized
```

**Example**: For a post with slug `docker-basics` created on 2025-12-04:
- `content/ko/posts/2025-12-04-docker-basics/index.md`
- `content/en/posts/2025-12-04-docker-basics/index.md`
- `content/ja/posts/2025-12-04-docker-basics/index.md`
- URL: `/ko/posts/docker-basics/` (slug determines URL, not directory name)

## Translation Guidelines

### English

- Use American English spelling
- Technical terms can remain in English
- Professional but accessible tone

### Japanese

- Use です/ます form (polite)
- Technical terms: katakana or English with explanation
- Follow Japanese technical writing conventions

## Do Not Translate

- Code blocks
- Command examples
- URLs
- File paths
- Technical identifiers

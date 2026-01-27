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

1. Create file: `content/ko/posts/{YYYY-MM-DD}-{slug}.md`
2. Generate front matter with all required fields
3. Write the full content in Korean

**File naming**: `{date}-{slug}.md` (e.g., `2025-12-04-docker-basics.md`)

### Step 2: Generate TL;DR

1. Analyze the post content
2. Write 1-2 sentence summary
3. Must be specific, not generic

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

Create translated versions for all configured languages:

| Language | Path | Notes |
|----------|------|-------|
| English (en) | `content/en/posts/{YYYY-MM-DD}-{slug}.md` | Translate content, tags, categories, tldr, cover.alt |
| Japanese (ja) | `content/ja/posts/{YYYY-MM-DD}-{slug}.md` | Translate content, tags, categories, tldr, cover.alt |

**Important**: Use the same date and filename across all languages.

### Step 5: Validate

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
tldr: "핵심 요약 (각 언어로)"
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

## Fields That Must Be Translated

- `title`
- `tags`
- `categories`
- `tldr`
- `cover.alt`
- All body content (except code blocks)

## Example Output Structure

```
content/
├── ko/posts/{YYYY-MM-DD}-{slug}.md    ✅ Created (original)
├── en/posts/{YYYY-MM-DD}-{slug}.md    ✅ Created (translation)
└── ja/posts/{YYYY-MM-DD}-{slug}.md    ✅ Created (translation)

static/images/posts/
└── {slug}.jpg                         ✅ Downloaded
```

**Example**: For a post with slug `docker-basics` created on 2025-12-04:
- `content/ko/posts/2025-12-04-docker-basics.md`
- `content/en/posts/2025-12-04-docker-basics.md`
- `content/ja/posts/2025-12-04-docker-basics.md`
- URL: `/ko/posts/docker-basics/` (slug determines URL, not filename)

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

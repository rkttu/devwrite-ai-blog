# Prompt: Translate Blog Post

> **스타일 가이드**: 번역 시 반드시 `/writing-style-guide.md` 파일을 참조하여 언어별 작성 규칙을 따르세요.

## Task
Translate a blog post from Korean to the target language while maintaining the original meaning and technical accuracy.

## Input
- Source file: `content/ko/posts/{YYYY-MM-DD}-{slug}/index.md`
- Target language: `en` or `ja`

## Instructions

1. **Read the source file** from `content/ko/posts/`

2. **Preserve these fields exactly** (do not translate):
   - `date`
   - `draft`
   - `slug`
   - `translationKey`
   - `cover.image`
   - `license` (사용 시)
   - Code blocks
   - URLs

3. **Translate these fields**:
   - `title`
   - `tags` (use common terms in target language)
   - `categories`
   - `description` (SEO 메타 태그용, 50~160자)
   - `tldr` (독자용 핵심 요약)
   - `cover.alt`
   - All body content (except code blocks)

4. **Create the translated file** at (Page Bundle 구조):
   - English: `content/en/posts/{YYYY-MM-DD}-{slug}/index.md`
   - Japanese: `content/ja/posts/{YYYY-MM-DD}-{slug}/index.md`

## Translation Guidelines

### For English (en)
- Use American English spelling
- Technical terms can remain in English
- Keep tone professional but accessible

### For Japanese (ja)
- Use です/ます form (polite)
- Technical terms: use katakana or keep English with explanation
- Respect Japanese technical writing conventions

## Example

### Source (ko)
```yaml
---
title: "Hugo로 블로그 만들기"
slug: "create-blog-with-hugo"
tags:
  - 블로그
  - Hugo
translationKey: "create-blog-with-hugo"
description: "Hugo 정적 사이트 생성기로 다국어 블로그를 구축하는 방법을 단계별로 설명합니다."
tldr: "Hugo와 PaperMod 테마로 다국어 블로그를 구축하고 GitHub Pages에 배포하는 방법을 다룹니다."
---
```

### English (en)
```yaml
---
title: "Creating a Blog with Hugo"
slug: "create-blog-with-hugo"
tags:
  - blog
  - Hugo
translationKey: "create-blog-with-hugo"
description: "A step-by-step guide to building a multilingual blog with the Hugo static site generator."
tldr: "Learn how to create a multilingual blog using Hugo and PaperMod theme, then deploy it to GitHub Pages."
---
```

### Japanese (ja)
```yaml
---
title: "Hugoでブログを作成する"
slug: "create-blog-with-hugo"
tags:
  - ブログ
  - Hugo
translationKey: "create-blog-with-hugo"
description: "Hugo静的サイトジェネレーターで多言語ブログを構築する方法をステップごとに説明します。"
tldr: "HugoとPaperModテーマで多言語ブログを構築し、GitHub Pagesにデプロイする方法を学びます。"
---
```

## Output
Create the translated markdown file as `index.md` inside the same-named Page Bundle directory in the target language.

**Example**:
- Source: `content/ko/posts/2025-12-04-docker-basics/index.md`
- English: `content/en/posts/2025-12-04-docker-basics/index.md`
- Japanese: `content/ja/posts/2025-12-04-docker-basics/index.md`

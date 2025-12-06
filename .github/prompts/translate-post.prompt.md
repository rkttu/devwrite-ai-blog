# Prompt: Translate Blog Post

> **스타일 가이드**: 번역 시 반드시 `/writing-style-guide.md` 파일을 참조하여 언어별 작성 규칙을 따르세요.

## Task
Translate a blog post from Korean to the target language while maintaining the original meaning and technical accuracy.

## Input
- Source file: `content/ko/posts/{filename}.md`
- Target language: `en` or `ja`

## Instructions

1. **Read the source file** from `content/ko/posts/`

2. **Preserve these fields exactly** (do not translate):
   - `date`
   - `draft`
   - `slug`
   - `translationKey`
   - `cover.image`
   - Code blocks
   - URLs

3. **Translate these fields**:
   - `title`
   - `tags` (use common terms in target language)
   - `categories`
   - `tldr`
   - `cover.alt`
   - All body content (except code blocks)

4. **Create the translated file** at:
   - English: `content/en/posts/{filename}.md`
   - Japanese: `content/ja/posts/{filename}.md`

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
tldr: "Hugo를 사용해서 정적 블로그를 만드는 방법을 알아봅니다."
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
tldr: "Learn how to create a static blog using Hugo."
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
tldr: "Hugoを使って静的ブログを作成する方法を学びます。"
---
```

## Output
Create the translated markdown file with the same filename in the target language directory.

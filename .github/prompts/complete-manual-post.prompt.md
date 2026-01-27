# Prompt: Complete Manual Post

> **스타일 가이드**: 글 작성 시 반드시 `/writing-style-guide.md` 파일을 참조하여 언어별 작성 규칙을 따르세요.

## Task

Complete a manually written blog post by adding proper front matter, TL;DR, hero image, and translations. This prompt is for posts that were written directly without using the blog's standard creation workflow.

## Input

- Path to the manually created Korean post in `content/ko/posts/`

## Instructions

### Step 1: Analyze the Post

1. Read the entire post content
2. Identify:
   - Main topic and key message
   - Appropriate tags and categories
   - Suitable slug (from filename or content)

### Step 2: Generate Front Matter

If the post lacks proper front matter, generate it:

```yaml
---
title: "[Extract from content or filename]"
date: [Use file date or current date in ISO 8601 format with +09:00 timezone]
draft: false
slug: "[Generate from filename, e.g., 2025-10-23-using-ubuntu-with-hyperv-gen2.md → using-ubuntu-with-hyperv-gen2]"
tags:
  - [Relevant tags in Korean]
categories:
  - [Appropriate category in Korean]
translationKey: "[Same as slug]"
cover:
  image: "images/posts/[slug].jpg"
  alt: "[Descriptive alt text in Korean]"
tldr: "[1-2 sentence summary in Korean]"
---
```

### Step 3: Generate TL;DR

Write a concise TL;DR that:
- Captures the core message in 1-2 sentences
- Is specific to the content (not generic)
- Highlights the key takeaway or solution

### Step 4: Select Hero Image

1. Search Unsplash for an appropriate image based on post topic
2. Download and save to `static/images/posts/[slug].jpg`
3. Use dimensions: 1200x630px (or similar 16:9 ratio)
4. Update `cover.alt` with descriptive text

### Step 5: Create Translations

Create translated versions in:
- `content/en/posts/[same-filename].md`
- `content/ja/posts/[same-filename].md`

Follow translation guidelines from `translate-post.prompt.md`:
- Preserve: `date`, `draft`, `slug`, `translationKey`, `cover.image`, code blocks, URLs
- Translate: `title`, `tags`, `categories`, `tldr`, `cover.alt`, body content

## Example

### Input File
`content/ko/posts/2025-10-23-using-ubuntu-with-hyperv-gen2.md`

### Generated Front Matter
```yaml
---
title: "Hyper-V 2세대 가상 머신에서 Ubuntu 부팅하기"
date: 2025-10-23T00:00:00+09:00
draft: false
slug: "using-ubuntu-with-hyperv-gen2"
tags:
  - Hyper-V
  - Ubuntu
  - 가상화
  - Windows
categories:
  - 개발 환경
translationKey: "using-ubuntu-with-hyperv-gen2"
cover:
  image: "images/posts/using-ubuntu-with-hyperv-gen2.jpg"
  alt: "서버 가상화 개념 이미지"
tldr: "Hyper-V 2세대 VM에서 Ubuntu 부팅 실패 시, 보안 부팅 템플릿을 'Microsoft UEFI 인증 기관'으로 변경하면 해결됩니다."
---
```

### Translation (English)
```yaml
---
title: "Booting Ubuntu on Hyper-V Generation 2 Virtual Machine"
date: 2025-10-23T00:00:00+09:00
draft: false
slug: "using-ubuntu-with-hyperv-gen2"
tags:
  - Hyper-V
  - Ubuntu
  - Virtualization
  - Windows
categories:
  - Development Environment
translationKey: "using-ubuntu-with-hyperv-gen2"
cover:
  image: "images/posts/using-ubuntu-with-hyperv-gen2.jpg"
  alt: "Server virtualization concept image"
tldr: "If Ubuntu fails to boot on Hyper-V Gen 2 VM, change the Secure Boot template to 'Microsoft UEFI Certificate Authority' to fix it."
---
```

## Checklist

After completion, verify:

- [ ] Front matter has all required fields
- [ ] `slug` and `translationKey` match across all languages
- [ ] Filename is consistent: `{YYYY-MM-DD}-{slug}.md`
- [ ] Hero image exists at `static/images/posts/[slug].jpg`
- [ ] TL;DR is specific and informative
- [ ] Translations exist in `content/en/posts/` and `content/ja/posts/`
- [ ] Code blocks are not translated
- [ ] Internal links use correct language paths

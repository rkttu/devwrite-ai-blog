# Prompt: Complete Manual Post

> **스타일 가이드**: 글 작성 시 반드시 `/writing-style-guide.md` 파일을 참조하여 언어별 작성 규칙을 따르세요.

## Task

Complete a manually written blog post by adding proper front matter, TL;DR, description, hero image, and translations. This prompt is for posts that were written directly without using the blog's standard creation workflow.

## Input

- Path to the manually created Korean post in `content/ko/posts/`

## Instructions

### Step 1: Analyze the Post

1. Read the entire post content
2. Identify:
   - Main topic and key message
   - Appropriate tags and categories
   - Suitable slug (from directory name or content)
   - SEO-friendly description (50~160자)

### Step 2: Generate Front Matter

If the post lacks proper front matter, generate it.

> **참고**: 포스트는 Page Bundle 구조입니다.
> 디렉터리명: `{YYYY-MM-DD}-{slug}/`, 파일명: `index.md`

```yaml
---
title: "[Extract from content or directory name]"
date: [Use file date or current date in ISO 8601 format with +09:00 timezone]
draft: false
slug: "[Generate from directory name, e.g., 2025-10-23-using-ubuntu-with-hyperv-gen2/ → using-ubuntu-with-hyperv-gen2]"
tags:
  - [Relevant tags in Korean]
categories:
  - [Appropriate category in Korean]
translationKey: "[Same as slug]"
description: "[SEO용 1문장 요약, 50~160자. 검색 결과 스니펫에 표시됨]"
cover:
  image: "images/posts/[slug].jpg"
  alt: "[Descriptive alt text in Korean]"
tldr: "[독자용 핵심 요약, 1-2문장. description보다 상세하고 구체적]"
---
```

### `description`과 `tldr`의 차이

| 항목 | `description` | `tldr` |
| --- | --- | --- |
| **용도** | SEO 메타 태그 (`<meta name="description">`, OG, Twitter) | 본문 상단 표시 (독자용 요약) |
| **길이** | 50~160자 (검색 스니펫 최적) | 1~2문장 (더 상세하고 기술적) |
| **JSON-LD** | `"description"` 필드 | `"abstract"` 필드 |
| **톤** | 클릭을 유도하는 매력적인 표현 | 핵심 내용을 정확히 전달 |

**예시**:
- `description`: "Java hwplib을 .NET으로 포팅하면서 AI 활용과 'Living Port' 방식의 오픈소스 기여 경험을 공유합니다."
- `tldr`: "C# 파일 첫 줄에 원본 Java 파일 힌트를 삽입하고 AI가 diff를 분석하게 하면, upstream 동기화 시간을 80% 이상 줄일 수 있습니다."

### Step 3: Generate TL;DR and Description

**TL;DR** 작성:
- 핵심 메시지를 1-2문장으로 포착
- 구체적 수치/방법/결과 포함
- 독자가 글을 읽지 않아도 핵심을 파악할 수 있어야 함

**Description** 작성:
- 검색 결과에 스니펫으로 표시되는 텍스트
- 50~160자 범위 (한국어 기준)
- 주제와 가치를 매력적으로 전달
- 글의 전체 흐름을 한 문장으로 요약

### Step 4: Select Hero Image

1. Search Unsplash for an appropriate image based on post topic
2. Download and save to `static/images/posts/[slug].jpg`
3. Use dimensions: 1200x630px (or similar 16:9 ratio)
4. Update `cover.alt` with descriptive text

### Step 5: Optimize Hero Image

이미지를 WebP로 변환하여 최적화:

**Windows (PowerShell)**:
```powershell
.\scripts\optimize-images.ps1 -Slug "[slug]" -DeleteOriginals -UpdateFrontmatter
```

**macOS/Linux**:
```bash
python3 scripts/optimize_images.py --slug "[slug]" --delete-originals --update-frontmatter
```

### Step 6: Create Translations

Create translated versions in (Page Bundle 구조):
- `content/en/posts/{YYYY-MM-DD}-{slug}/index.md`
- `content/ja/posts/{YYYY-MM-DD}-{slug}/index.md`

Follow translation guidelines from `translate-post.prompt.md`:
- Preserve: `date`, `draft`, `slug`, `translationKey`, `cover.image`, `license`, code blocks, URLs
- Translate: `title`, `tags`, `categories`, `description`, `tldr`, `cover.alt`, body content

### Step 7: Update llms.txt

새 포스트를 `static/llms.txt`의 포스트 목록에 추가:
```
- [포스트 제목](/ko/posts/{slug}/) — description 내용
```

## Example

### Input Directory
`content/ko/posts/2025-10-23-using-ubuntu-with-hyperv-gen2/index.md`

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
description: "Hyper-V 2세대 VM에서 Ubuntu UEFI 부팅 실패를 해결하는 방법을 알려드립니다."
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
description: "Learn how to fix Ubuntu UEFI boot failure on Hyper-V Generation 2 VMs."
cover:
  image: "images/posts/using-ubuntu-with-hyperv-gen2.jpg"
  alt: "Server virtualization concept image"
tldr: "If Ubuntu fails to boot on Hyper-V Gen 2 VM, change the Secure Boot template to 'Microsoft UEFI Certificate Authority' to fix it."
---
```

## Checklist

After completion, verify:

- [ ] Front matter has all required fields (`title`, `date`, `draft`, `slug`, `translationKey`, `description`)
- [ ] `description` is 50~160자 and SEO-friendly
- [ ] `tldr` is specific and informative (description과 다른 내용)
- [ ] `slug` and `translationKey` match across all languages
- [ ] Directory name is consistent: `{YYYY-MM-DD}-{slug}/index.md` (Page Bundle)
- [ ] Hero image exists at `static/images/posts/[slug].webp` (WebP 변환 완료)
- [ ] Cover image path in front matter uses `.webp` extension
- [ ] Translations exist in `content/en/posts/` and `content/ja/posts/` (동일 디렉터리 구조)
- [ ] `description` is translated for each language version
- [ ] Code blocks are not translated
- [ ] Internal links use correct language paths
- [ ] `static/llms.txt` updated with new post entry

# Prompt: Select Hero Image from Unsplash

## Task

Suggest an appropriate Unsplash image URL for a blog post's hero image.

## Input

- Post title and content
- Post tags/categories

## Instructions

1. Analyze the post topic
2. Search Unsplash (https://unsplash.com) for a suitable image
3. Select an image that:
   - Is horizontal (landscape orientation)
   - Has minimal text
   - Is professional-looking
   - Relates to the topic abstractly

## Guidelines

### Good Keywords for Search

| Topic | Keywords |
|-------|----------|
| 프로그래밍 일반 | `coding`, `computer`, `developer` |
| 웹 개발 | `web`, `design`, `technology` |
| DevOps/CI | `automation`, `pipeline`, `server` |
| 데이터베이스 | `data`, `network`, `abstract` |
| AI/ML | `artificial intelligence`, `neural`, `futuristic` |
| 생산성 | `workspace`, `productivity`, `minimal` |

### Avoid

- Too specific terms (won't find images)
- Brand names
- Text-heavy images

## Example

### Input

```yaml
title: "Docker 컨테이너 최적화하기"
tags:
  - Docker
  - DevOps
  - 성능
```

### Output

```
image_url: "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=1200&h=630&fit=crop"
keywords_used: ["server", "technology"]
alt: "Server room with blue lights"
```

## Download Command

**Windows (PowerShell)**:
```powershell
$url = "https://images.unsplash.com/photo-XXXXXXXXXX?w=1200&h=630&fit=crop"
$output = "static/images/posts/{slug}.jpg"
Invoke-WebRequest -Uri $url -OutFile $output
```

**macOS/Linux**:
```bash
curl -L "https://images.unsplash.com/photo-XXXXXXXXXX?w=1200&h=630&fit=crop" -o static/images/posts/{slug}.jpg
```

## Optimize Image (WebP 변환)

다운로드 후 WebP로 변환하여 최적화:

**Windows (PowerShell)**:
```powershell
.\scripts\optimize-images.ps1 -Slug "{slug}" -DeleteOriginals -UpdateFrontmatter
```

**macOS/Linux**:
```bash
python3 scripts/optimize_images.py --slug "{slug}" --delete-originals --update-frontmatter
```

이 스크립트는 이미지를 WebP로 변환하고, 모든 언어 버전의 front matter에서 `.jpg` → `.webp`로 경로를 자동 업데이트합니다.

## Update Front Matter

스크립트를 사용하지 않는 경우, 수동으로 모든 언어 버전에 추가:

```yaml
cover:
  image: "images/posts/{slug}.webp"
  alt: "Brief description of the image"
```

## Important Notes

- Use `images.unsplash.com` direct URLs (not `source.unsplash.com` which is deprecated)
- Always include `?w=1200&h=630&fit=crop` for consistent sizing
- The same image is shared across all language versions of a post
- WebP 변환 후 원본 `.jpg` 파일은 삭제 권장

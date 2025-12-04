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

## Update Front Matter

After downloading, add to all language versions:

```yaml
cover:
  image: "images/posts/{slug}.jpg"
  alt: "Brief description of the image"
```

## Important Notes

- Use `images.unsplash.com` direct URLs (not `source.unsplash.com` which is deprecated)
- Always include `?w=1200&h=630&fit=crop` for consistent sizing
- The same image is shared across all language versions of a post

# Prompt: Select Hero Image from Unsplash

## Task
Suggest appropriate Unsplash search keywords for a blog post's hero image.

## Input
- Post title and content
- Post tags/categories

## Instructions

1. Analyze the post topic
2. Suggest 2-3 English keywords for Unsplash search
3. Keywords should be:
   - Abstract enough to find good images
   - Related to the topic
   - Likely to return professional-looking photos

## Guidelines

### Good Keywords
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
keywords: ["container", "server", "technology"]
unsplash_url: "https://unsplash.com/s/photos/container-server-technology"
```

## Usage

After selecting an image:
1. Download the image
2. Save to `static/images/posts/{slug}.jpg`
3. Update front matter:
   ```yaml
   cover:
     image: "images/posts/{slug}.jpg"
     alt: "Brief description of the image"
     caption: "Photo by [Author](author_url) on Unsplash"  # if attribution needed
   ```

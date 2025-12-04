# Prompt: Generate TL;DR Summary

## Task
Generate a concise TL;DR summary for a blog post.

## Input
- Post file path or content

## Instructions

1. Read the full post content
2. Identify the main topic and key takeaways
3. Write a 1-2 sentence summary that:
   - Captures the core message
   - Is specific (not generic)
   - Uses active voice
   - Matches the language of the post

## Guidelines

### Good TL;DR
- "Hugo와 PaperMod 테마로 다국어 블로그를 구축하고 GitHub Pages에 배포하는 방법을 다룹니다."
- "React 18의 Concurrent Features를 활용해 사용자 경험을 개선하는 세 가지 패턴을 소개합니다."

### Bad TL;DR
- "이 글에서는 블로그에 대해 알아봅니다." (너무 모호)
- "Hugo 설치, 설정, 테마 적용, 다국어 설정, 배포까지 전부 다룹니다." (목차 나열)

## Example

### Post Content
```markdown
## Hugo란?
Hugo는 Go로 작성된 정적 사이트 생성기입니다...

## 설치하기
먼저 Hugo를 설치합니다...

## 테마 적용
PaperMod 테마를 적용해보겠습니다...
```

### Generated TL;DR
```yaml
tldr: "Hugo 정적 사이트 생성기와 PaperMod 테마로 블로그를 만드는 과정을 단계별로 설명합니다."
```

## Output
Return only the tldr value to be inserted into front matter.

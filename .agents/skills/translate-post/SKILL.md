---
name: translate-post
description: 한국어 Hugo 블로그 글을 영어 또는 일본어로 번역하고 Page Bundle과 front matter 일관성을 유지합니다. 원문 작성이나 외부 게시에는 사용하지 않습니다.
---

# 블로그 글 번역

## 원문과 대상

한국어 파일 `content/ko/posts/<날짜>-<slug>/index.md`를 원문으로 사용합니다. 대상 언어는 영어, 일본어 또는 둘 다입니다. 원문 전체와 `writing-style-guide.md`의 대상 언어 규칙을 읽습니다.

다음 값은 원문과 동일하게 유지합니다.

- `date`
- `draft`
- `slug`
- `translationKey`
- `cover.image`
- `license`
- 코드, 명령, URL, 파일 경로, 기술 식별자

제목, 태그, 카테고리, `description`, `tldr`, `cover.alt`, 본문은 대상 언어에 맞게 번역합니다. 코드 블록 안의 주석은 사용자가 별도로 요청하지 않는 한 원문을 유지합니다. 내부 링크는 해당 언어 경로가 실제로 존재할 때만 바꿉니다.

영어는 자연스러운 미국 영어 기술 문체를 사용합니다. 일본어는 です/ます調를 사용하고 기술 용어를 일관되게 표기합니다. 번역문에 원문에 없는 주장이나 예시를 추가하지 않습니다.

번역 후 다음 검증을 실행하고 오류가 있으면 수정합니다.

```bash
python3 scripts/validate_translations.py
```

번역 작업은 `draft` 상태 변경, 커밋, 푸시를 포함하지 않습니다.

---
name: complete-manual-post
description: 직접 작성한 한국어 Hugo 글에 누락된 front matter, 요약, 번역, 선택적 히어로 이미지를 보강합니다. 새 주제로 글을 만드는 작업에는 사용하지 않습니다.
---

# 수동 작성 글 보완

## 원문 보존

대상은 `content/ko/posts/<날짜>-<slug>/index.md`의 한국어 원고입니다. 전체 본문과 `CLAUDE.md`, `.github/copilot-instructions.md`, `writing-style-guide.md`를 읽습니다.

필자의 주장과 문체를 유지합니다. 확인할 수 없는 수치, 경험, 의도, 결론을 추가하지 않습니다. 원고의 논지를 크게 바꾸는 편집은 먼저 제안하고 사용자 승인을 받습니다.

## 보완 범위

다음 항목을 점검하고 실제로 빠진 내용만 보완합니다.

- Page Bundle 디렉터리명과 slug
- 필수 front matter와 시간대가 포함된 현재 또는 과거 날짜
- 글의 사실을 반영한 `description`과 `tldr`
- 태그, 카테고리, `translationKey`
- 선택적 `license`
- 필요한 경우의 히어로 이미지와 언어별 대체 텍스트
- 영어와 일본어 번역본

요약은 `$generate-tldr`, 번역은 `$translate-post`, 이미지는 `$select-hero-image`의 규칙을 적용합니다. 기존 값이 적절하면 덮어쓰지 않습니다.

## 검증과 경계

세 언어에서 `date`, `draft`, `slug`, `translationKey`, `cover.image`, `license`가 일치하는지 확인하고 다음 검증을 실행합니다.

```bash
python3 scripts/validate_translations.py
python3 scripts/check_asset_sizes.py
```

이 스킬은 `draft` 상태 변경, 커밋, 푸시, 배포를 수행하지 않습니다.

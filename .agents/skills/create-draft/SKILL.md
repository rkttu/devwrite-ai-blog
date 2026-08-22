---
name: create-draft
description: 새 Hugo 블로그 글을 한국어 원문과 영어 및 일본어 번역을 갖춘 draft 상태의 Page Bundle로 생성합니다. 기존 글 보완이나 발행에는 사용하지 않습니다.
---

# 블로그 초안 생성

## 입력과 사전 확인

사용자가 지정한 slug와 주제, 개요, 참고 자료를 사용합니다. 입력이 불충분해도 글의 방향을 바꿀 정도가 아니라면 합리적으로 가정하고 그 내용을 알립니다.

먼저 `CLAUDE.md`, `.github/copilot-instructions.md`, `writing-style-guide.md` 전체를 읽습니다. 한국어 원문에는 완결된 배포 문서에 해당하는 규칙을 적용합니다. 같은 slug나 디렉터리가 이미 있으면 새 글을 만들지 않고 기존 글 보완 요청인지 확인합니다.

## 초안 작성

`scripts/new_post.py` 또는 현재 운영체제에 맞는 동등한 스크립트로 세 언어의 Page Bundle 뼈대를 만듭니다. 날짜는 Asia/Seoul 기준 현재 시각을 사용하며 미래 날짜를 만들지 않습니다.

한국어 원문부터 작성합니다. 다음 원칙을 지킵니다.

- `draft: true`
- 모든 필수 front matter
- 글에서 확인한 사실만 반영한 `description`과 `tldr`
- 실행 가능하거나 공식 문서와 일치하는 코드 및 명령
- 본문 가까이에 배치한 1차 출처 링크
- 개인 경험이나 성과를 추정하지 않는 서술

영어와 일본어 번역에는 `$translate-post`의 규칙을 적용합니다. `date`, `draft`, `slug`, `translationKey`, `cover.image`, `license`는 세 언어에서 일치시킵니다.

히어로 이미지가 요청되었거나 글에 필요하다고 합의한 경우에만 `$select-hero-image`를 사용합니다. 이미지 없이도 완성할 수 있는 글에 임의의 이미지를 추가하지 않습니다.

## 완료 기준

다음 명령을 실행해 초안 구조를 검증합니다.

```bash
python3 scripts/validate_translations.py
python3 scripts/check_asset_sizes.py
```

초안 생성은 `draft: false` 변경, 커밋, 푸시, 외부 게시를 포함하지 않습니다. 생성한 파일과 남은 검토 항목을 보고합니다.

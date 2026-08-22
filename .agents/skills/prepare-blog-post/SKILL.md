---
name: prepare-blog-post
description: Hugo 블로그 글을 작성, 보완, 번역, 리뷰, 탈고하고 운영 배포 직전 상태까지 준비합니다. 커밋, 푸시, 외부 채널 게시에는 사용하지 않습니다.
---

# 블로그 글 발행 준비

## 실행 범위 선택

사용자가 요청한 작업만 수행합니다. 전체 준비를 요청받았을 때에는 다음 하위 스킬을 필요한 순서로 사용합니다.

- 새 글 작성: `$create-draft`
- 수동 원고 보완: `$complete-manual-post`
- description과 tldr만 작성: `$generate-tldr`
- 영어 또는 일본어 번역: `$translate-post`
- 히어로 이미지: `$select-hero-image`
- 리뷰 또는 리뷰 후 탈고: `$review-draft`
- 검토를 마친 글의 배포 대상 전환: `$publish-draft`

특정 작업만 요청받았다면 다른 하위 스킬로 범위를 넓히지 않습니다. 리뷰 요청에는 파일을 수정하지 않으며 리뷰와 수정을 함께 요청받았을 때만 탈고를 반영합니다.

## 전체 준비 흐름

전체 글 준비 요청에서는 `writing-style-guide.md` 전체를 읽고 한국어 원문을 먼저 완성합니다. 완결된 배포 문서에 해당하는 규칙과 탈고 체크리스트를 적용합니다. 변경 가능성이 있는 제품 버전, API, 일정, 가격, 정책은 공식 1차 출처로 확인하고 본문 가까이에 링크를 배치합니다. 원문에 없는 개인 경험과 결과를 만들지 않습니다.

한국어 원문이 확정되면 영어와 일본어를 번역합니다. 세 언어에서 날짜, draft, slug, `translationKey`, 이미지 경로, 라이선스를 일치시킵니다. 각 번역의 제목, description, tldr, 대체 텍스트, 본문은 대상 언어에 맞게 작성합니다.

리뷰와 탈고를 마친 뒤 사용자에게 다음 항목을 보여 줍니다.

- 세 언어 제목과 파일 경로
- slug와 예상 운영 URL
- description과 tldr
- 출처 및 확인하지 못한 항목
- 이미지 출처와 사용 조건
- 남은 리뷰 항목

사용자가 발행 준비 완료를 승인하면 `$publish-draft`를 사용해 세 언어의 `draft`를 `false`로 바꿉니다.

## 최종 검증

다음 명령을 실행합니다.

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_translations.py
python3 scripts/check_asset_sizes.py
hugo --environment production --cleanDestinationDir --gc --minify --panicOnWarning --buildDrafts=false
cp public/ko/404.html public/404.html
cp public/ko/llms.txt public/llms.txt
python3 scripts/validate_site.py public
```

생성된 `public/<언어>/posts/<slug>/index.html`과 원본 파일의 제목, canonical URL, Open Graph 메타데이터를 대조합니다.

완료 시 글이 `커밋 가능` 상태라고 보고합니다. 이 스킬은 Git 커밋, 푸시, GitHub Actions 감시, Discourse 또는 LinkedIn 게시를 수행하지 않습니다.

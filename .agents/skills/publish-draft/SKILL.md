---
name: publish-draft
description: 검토를 마친 Hugo 글의 세 언어 front matter를 draft true에서 false로 바꿔 배포 대상으로 전환합니다. Git 커밋과 실제 배포에는 사용하지 않습니다.
---

# Draft 발행 상태 전환

대상 slug에 대응하는 한국어, 영어, 일본어 Page Bundle을 찾습니다. 누락된 언어가 있거나 날짜, slug, `translationKey`가 일치하지 않으면 상태를 바꾸지 않습니다.

`$review-draft` 결과에서 발행을 막는 항목이 없고 사용자가 상태 전환을 요청했을 때만 세 파일의 `draft` 값을 `false`로 바꿉니다. 미래 날짜는 허용하지 않습니다.

변경 후 다음 명령으로 로컬 산출물을 확인합니다.

```bash
python3 scripts/validate_translations.py
hugo --environment production --cleanDestinationDir --gc --minify --panicOnWarning --buildDrafts=false
cp public/ko/404.html public/404.html
cp public/ko/llms.txt public/llms.txt
python3 scripts/validate_site.py public
```

`draft: false`는 다음 빌드에 글을 포함한다는 의미입니다. 이 작업만으로 운영 사이트에 발행되지 않습니다. 커밋과 푸시, GitHub Pages 배포는 `$deploy-blog-post`의 별도 범위입니다.

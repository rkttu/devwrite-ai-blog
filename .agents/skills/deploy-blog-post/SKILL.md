---
name: deploy-blog-post
description: 준비된 Hugo 블로그 글을 커밋하거나 main에 푸시하고 해당 GitHub Actions 실행과 실제 slug URL을 검증합니다. 글 작성이나 외부 채널 공유에는 사용하지 않습니다.
---

# 블로그 글 배포

## 실행 모드

사용자의 요청 범위에 맞춰 다음 중 하나만 수행할 수 있습니다.

- 커밋만 생성
- 커밋과 푸시 후 배포 확인
- 이미 푸시한 커밋의 GitHub Actions 감시 재개
- 이미 배포한 slug URL 검증

`푸시하지 말아줘`라는 지시가 있거나 푸시 권한이 명확하지 않으면 커밋 이후 중단합니다. 이전 요청에서 허용한 푸시를 다른 글에 대한 권한으로 확장하지 않습니다.

## 배포 전 점검

대상 slug와 세 언어 Page Bundle을 확인합니다. `draft: false`, 현재 또는 과거 날짜, 번역 일관성, 이미지 존재 여부를 점검합니다. 작업 트리의 사용자 변경을 모두 확인하고 대상 글과 무관한 변경을 커밋에 포함하지 않습니다.

커밋 전에 `$prepare-blog-post`의 최종 검증 명령을 실행합니다. 현재 브랜치, 실제 기본 브랜치, 원격 저장소를 확인합니다. 이 저장소의 Pages 워크플로는 `main` 푸시에서 실행되므로 다른 브랜치라면 임의로 병합하거나 푸시하지 않습니다.

글, 번역, 해당 글의 이미지는 하나의 콘텐츠 커밋으로 묶을 수 있습니다. 도구, 워크플로, 테마 변경은 별도 커밋으로 분리합니다. 커밋 후 SHA와 포함 파일을 사용자에게 보여 줍니다.

## 푸시와 실행 감시

사용자가 푸시를 승인한 경우에만 GitHub 인증 상태를 확인하고 정확한 기본 브랜치로 푸시합니다. 푸시한 SHA를 기록하고 그 SHA에 연결된 `deploy.yml` 실행만 찾습니다.

```bash
commit_sha=$(git rev-parse HEAD)
gh run list --workflow deploy.yml --commit "$commit_sha" --limit 10 \
  --json databaseId,headSha,status,conclusion,url
gh run watch <run-id> --exit-status
```

Actions 등록이 늦으면 제한된 횟수로 다시 조회합니다. 진행 중에는 60초 안에 상태를 알립니다. 실패하면 `gh run view <run-id> --log-failed`로 원인을 확인하고 배포 단계에서 중단합니다. 수정 권한이 요청 범위에 포함된 경우에만 원인을 고치고 새 커밋과 새 실행을 추적합니다.

## 운영 URL 검증

워크플로 성공 후 다음 URL을 확인합니다.

- `https://devwrite.ai/ko/posts/<slug>/`
- `https://devwrite.ai/en/posts/<slug>/`
- `https://devwrite.ai/ja/posts/<slug>/`

각 URL에서 HTTP 200, 최종 URL, 예상 제목, canonical URL을 확인합니다. 한국어 페이지에서는 `og:title`, `og:description`, `og:image`, `og:url`도 확인하고 대표 이미지 URL이 HTTP 200을 반환하는지 검사합니다.

CDN 반영이 늦으면 몇 분 동안 제한적으로 재시도합니다. Actions 성공만으로 운영 발행을 완료 처리하지 않습니다. 운영 HTML이 예상 커밋의 내용을 보여 줄 때 배포 완료로 기록합니다.

완료 보고에는 커밋 SHA, Actions 실행 URL, 세 언어 운영 URL과 검증 결과를 포함합니다. Discourse와 LinkedIn 게시는 별도 스킬의 범위입니다.

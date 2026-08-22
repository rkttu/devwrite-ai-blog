# HTTP 보안 헤더 적용 경로

## 상태

2026년 8월 22일 결정

## 배경

Hugo는 HTML과 정적 자산을 생성하지만 HTTP 응답 헤더를 전송하지 않습니다. 현재 운영 사이트는 GitHub Pages가 Hugo 빌드 산출물을 직접 제공합니다. GitHub는 [사용자 정의 워크플로가 정적 산출물을 Pages에 배포하는 구조](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)를 안내하며 [저장소별 MIME 형식도 지정할 수 없다고 설명합니다](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site#mime-types-on-github-pages).

GitHub Enterprise Server 관리자는 [인스턴스 전체의 Pages 응답 헤더를 설정](https://docs.github.com/en/enterprise-server@3.21/admin/configuring-settings/configuring-user-applications-for-your-enterprise/configuring-github-pages-for-your-enterprise#configuring-github-pages-response-headers-for-your-enterprise)할 수 있습니다. 반면 GitHub.com Pages는 저장소나 배포 산출물에서 응답 헤더를 설정하는 경로를 제공하지 않습니다.

2026년 8월 22일 `https://devwrite.ai/`의 실제 응답도 `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options`, `Permissions-Policy`를 포함하지 않았습니다.

## 결정

GitHub Pages가 해석하지 않는 `_headers` 파일을 저장소에 추가하지 않습니다. `Referrer-Policy`는 동등한 HTML `meta` 요소로 유지합니다. 나머지 HTTP 전용 정책은 응답 헤더를 제어할 수 있는 CDN이나 리버스 프록시를 도입할 때 적용합니다.

호스팅 계층을 변경하면 다음 헤더부터 구성합니다.

- `Content-Security-Policy-Report-Only`: 현재 외부 서비스와 인라인 스크립트의 위반 보고 수집
- `Content-Security-Policy`: 보고 결과를 반영한 허용 출처와 `frame-ancestors` 제한
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), geolocation=(), microphone=()`

Content Security Policy는 외부 서비스 목록과 인라인 스크립트를 함께 반영해야 합니다. 외부 서비스 변경 시 정책도 같은 커밋에서 갱신합니다.

## 완료 조건

CDN이나 프록시를 도입한 뒤 운영 URL의 응답 헤더를 자동 검사하면 이 제약을 해소한 것으로 봅니다. 적용 전에는 README와 이 결정 기록에서 호스팅 제약을 계속 알립니다.

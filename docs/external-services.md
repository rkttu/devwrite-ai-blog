# 외부 서비스 로딩 정책

## 적용 원칙

사이트가 실행하는 외부 JavaScript는 운영 환경에서 명시적으로 활성화한 서비스로 제한합니다. `config/_default/hugo.toml`은 실행 코드 통합을 비활성화하며 `config/production/hugo.toml`이 운영에 사용할 항목만 활성화합니다.

새 서비스를 추가할 때는 다음 조건을 같은 변경 단위에서 반영합니다.

1. `params.integrations`에 기본값이 `false`인 스위치를 추가합니다.
2. 운영 환경에서 사용할 스위치만 `true`로 덮어씁니다.
3. HTTPS 주소와 비동기 로딩을 사용합니다.
4. 이 문서의 서비스 목록과 보안 헤더 계획을 갱신합니다.
5. 개발 및 운영 빌드 산출물에서 로딩 여부를 검사합니다.

## 서비스별 설정 경계

| 서비스 | 리소스와 용도 | 출력 범위 | 설정 |
| --- | --- | --- | --- |
| Google Analytics | [Google tag](https://developers.google.com/tag-platform/gtagjs/reference) 방문 분석 스크립트 | 운영 환경의 전체 페이지 | `params.integrations.googleanalytics`, `googleAnalytics` |
| Google Fonts | 언어별 본문 폰트와 코드 폰트 스타일시트 | 모든 환경의 전체 페이지 | `params.integrations.googlefonts` |
| Creative Commons 배지 | 라이선스 이미지 | 공개 포스트 | `params.license` |

공유 버튼은 사용자가 누를 때 외부 사이트로 이동하는 링크이며 페이지 로드 시 외부 JavaScript를 실행하지 않습니다.

## 운영 시 점검 항목

1. 개발 빌드에서 Google Analytics 스크립트가 출력되지 않는지 검사합니다.
2. 운영 빌드에서 활성화한 서비스의 HTTPS 주소가 출력되는지 검사합니다.
3. 서비스를 비활성화한 뒤 해당 도메인의 요청이 사라지는지 브라우저 네트워크 기록으로 확인합니다.
4. CDN이나 프록시를 도입하면 [HTTP 보안 헤더 적용 경로](decisions/0003-plan-http-security-headers.md)의 Content Security Policy 허용 출처를 이 목록과 맞춥니다.

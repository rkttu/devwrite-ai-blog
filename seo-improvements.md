# SEO 및 트래픽 개선 완료 기록

2026년 8월 23일 저장소와 운영 사이트를 기준으로 기존 SEO 개선 항목 19개를 다시 점검했습니다. 저장소 설정, Hugo 템플릿, 콘텐츠 메타데이터, 검증 스크립트와 운영 응답이 완료 상태와 일치합니다.

검색 결과 메타데이터, 사이트 탐색, 구조화 데이터, AI 검색 노출, 이미지와 보안 정책까지 구현했습니다. Google과 Bing의 사이트 소유권 확인용 DNS 레코드도 운영 도메인에서 응답합니다.

아래에서는 검색 메타데이터, 탐색 구조, 구조화 데이터, AI 검색, 성능과 운영 정책 순서로 구현 결과와 확인 근거를 정리하겠습니다.

## 검색 결과를 구성하는 메타데이터

- **운영 환경 판별**: [배포 워크플로](.github/workflows/deploy.yml)는 `--environment production`으로 Hugo를 실행합니다. PaperMod는 `hugo.IsProduction`으로 Open Graph, Twitter Card와 JSON-LD를 활성화합니다.
- **검색엔진 소유권 확인**: 운영 도메인의 DNS TXT 레코드에서 Google과 Bing 확인 값을 점검했습니다. Naver 확인 값은 [Hugo 기본 설정](config/_default/hugo.toml)의 `params.analytics.naver.SiteVerificationTag`로 관리합니다.
- **포스트 설명**: 한국어, 영어, 일본어 포스트 42개가 `description`을 포함합니다. 각 언어에는 14개 포스트가 있으며 이 중 13개를 발행 상태로 관리합니다.
- **사이트 설명**: [언어별 설정](config/_default/hugo.toml)은 세 언어의 독자와 주제를 반영한 사이트 설명을 제공합니다.
- **기본 언어 대체 링크**: [head 확장 템플릿](layouts/_partials/extend_head.html)은 한국어 URL을 `hreflang="x-default"`로 출력합니다.
- **Twitter Card 계정**: 기본 설정은 `site`와 `creator`에 `@rkttu`를 사용합니다.
- **홈페이지 키워드**: 언어별 `params.keywords`가 .NET, C#, Azure, AI와 블로그의 주요 주제를 제공합니다.

## 검색과 내부 탐색 경로

- **언어별 검색 페이지**: [한국어](content/ko/search.md), [영어](content/en/search.md), [일본어](content/ja/search.md) 검색 페이지와 JSON 홈 출력을 활성화했습니다.
- **다국어 404 페이지**: [404 템플릿](layouts/404.html)은 요청 경로와 브라우저 언어에 맞춰 홈, 검색, 최근 글 링크를 제공합니다.
- **언어 이름 표시**: 언어 선택기는 `한국어`, `English`, `日本語`를 전체 이름으로 표시합니다.
- **관련 글 연결**: [관련 글 설정](config/_default/hugo.toml)과 [관련 글 템플릿](layouts/_partials/related_posts.html)은 태그, 카테고리, 날짜를 기준으로 내부 링크를 생성합니다.

## 구조화 데이터와 저자 신호

- **저자 구조**: [JSON-LD 템플릿](layouts/_partials/templates/schema_json.html)은 저자를 `Person`으로 표현하고 동일한 식별자를 글의 `author`와 `publisher`에서 참조합니다.
- **외부 프로필 연결**: `sameAs`는 GitHub, LinkedIn, X, Microsoft MVP 프로필과 닷넷데브 커뮤니티를 연결합니다.
- **저자 정보**: 세 언어의 소개 페이지는 경력, 자격, 전문 분야, 오픈소스 활동과 발행 주제를 제공합니다.
- **글 요약 구조**: 포스트의 `tldr`은 본문 상단에 표시되며 `BlogPosting.abstract`에도 반영됩니다.

## AI 검색을 위한 공개 정보

- **AI 크롤러 정책**: [robots.txt 템플릿](layouts/robots.txt)은 GPTBot, Google-Extended, CCBot, anthropic-ai를 포함한 주요 크롤러에 `Allow: /`를 명시합니다.
- **언어별 llms.txt**: [llms.txt 템플릿](layouts/llms.txt)은 사이트 정보, RSS, 저자 페이지와 발행 글 목록을 언어별로 생성합니다.
- **llms.txt 탐색 링크**: 모든 HTML 문서의 head에서 `rel="help"`로 해당 언어의 `llms.txt`를 안내합니다.
- **콘텐츠 요약 구분**: 검색 스니펫용 `description`과 독자 및 AI 검색용 `tldr`을 별도 필드로 관리합니다.

## 성능과 운영 정책

- **언어별 폰트**: head 확장 템플릿은 현재 언어에 맞는 Noto Sans 계열 하나와 공통 코드 폰트만 불러옵니다.
- **히어로 이미지 최적화**: [이미지 최적화 스크립트](scripts/optimize_images.py)는 크기 조정, WebP 변환과 front matter 갱신을 지원합니다.
- **HTTP 보안 헤더**: GitHub.com Pages에서는 저장소가 응답 헤더를 지정할 수 없습니다. [결정 기록](docs/decisions/0003-plan-http-security-headers.md)은 현재 제약과 CDN 또는 프록시 도입 이후 적용할 정책을 정의합니다.
- **Referrer Policy**: HTTP 헤더와 동등하게 적용할 수 있는 `strict-origin-when-cross-origin` 값을 HTML meta 요소로 제공합니다.

## 저장소와 운영 사이트 검증

저장소에서는 다음 명령으로 콘텐츠, 자산, Hugo 산출물을 검사합니다.

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate_translations.py
python3 scripts/check_asset_sizes.py
hugo --environment production --cleanDestinationDir --gc --minify --panicOnWarning --buildDrafts=false
cp public/ko/404.html public/404.html
cp public/ko/llms.txt public/llms.txt
python3 scripts/validate_site.py public
```

2026년 8월 23일 점검에서 운영 사이트의 `/robots.txt`, `/llms.txt`, `/ko/llms.txt`, `/ko/search/`가 HTTP 200을 반환했습니다. 존재하지 않는 경로는 커스텀 본문과 함께 HTTP 404를 반환했습니다. 운영 홈페이지에서는 description, Naver 확인 태그, Open Graph와 Twitter Card 메타데이터를 확인했습니다.

## 유지 관리 기준

여기까지 정리하면 저장소는 일반 검색엔진과 AI 검색엔진이 사용할 메타데이터와 탐색 파일을 함께 제공합니다. GitHub Pages의 응답 헤더 제약은 현재 호스팅 계층에서 남아 있으며 나머지 항목은 저장소와 운영 사이트에 반영했습니다.

새 포스트를 추가하면 세 언어의 `description`, `tldr`, `translationKey` 일관성을 기존 검증 스크립트로 확인합니다. 호스팅 계층을 변경하는 경우에는 보안 헤더 결정 기록을 다시 검토하고 운영 응답 검사를 자동화할 수 있습니다.

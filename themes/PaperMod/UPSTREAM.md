# PaperMod 기준 리비전과 갱신 절차

이 디렉터리는 PaperMod를 저장소에 포함한 복사본입니다. Git submodule로 관리하지 않습니다.

## 기준 리비전

- 원본 저장소: <https://github.com/adityatelange/hugo-PaperMod>
- 기준 커밋: [`d3768854d00ad003b0a8dbdba254ce9224377a01`](https://github.com/adityatelange/hugo-PaperMod/commit/d3768854d00ad003b0a8dbdba254ce9224377a01)
- 기준 확인일: 2026년 8월 22일
- 저장소 갱신 커밋: `f4d95796cb80c4b4d646a0f894f08b870bafc312`

기준 커밋 이후 `themes/PaperMod` 안에서 바꾼 코드는 이 블로그의 로컬 변경입니다. 루트의 `layouts`와 `assets/css/extended`도 PaperMod 템플릿과 스타일을 덮어씁니다.

## 로컬 호환 수정

PaperMod의 기준 커밋은 Hugo 0.165.0에서 폐기 경고가 발생하며 `--panicOnWarning` 빌드가 중단됩니다. 포함한 복사본은 다음 수정만 테마 내부에 유지합니다.

- `.Language.Direction`, `.Language.Locale`, `.Language.Label` API 사용
- 404 검색 제외 정책과 선택형 파비콘 출력
- 운영 환경의 Google Analytics 통합 스위치
- 공통 바닥글의 AI 어시스트 안내
- Hugo 최소 버전 0.165.0 지정

사이트 전용 템플릿은 Hugo의 새 경로 규칙에 맞춰 루트 `layouts/_partials`, `layouts/single.html`, `layouts/llms.txt`에 둡니다. 사이트 전용 CSS도 루트 `assets/css/extended`에 둡니다.

## 갱신 순서

1. 원본 저장소에서 적용할 커밋과 릴리스 노트를 확인합니다.
2. 기준 커밋과 새 커밋 사이의 변경 사항을 별도 작업 디렉터리에서 비교합니다.
3. `themes/PaperMod`의 로컬 호환 수정과 루트 오버라이드를 함께 검토합니다.
4. 새 원본 파일을 반영하고 로컬 호환 수정을 다시 적용합니다.
5. 루트 오버라이드가 upstream의 레이아웃 경로 규칙과 일치하는지 확인합니다.
6. `hugo --environment production --cleanDestinationDir --minify --gc --panicOnWarning --buildDrafts=false`로 빌드합니다.
7. `public/ko/404.html`과 `public/ko/llms.txt`를 `public` 루트에 복사합니다.
8. `python3 scripts/validate_site.py public`으로 링크와 구조화 데이터를 검사합니다.

테마 갱신과 블로그 기능 변경은 서로 다른 커밋으로 나누면 원본 변경과 로컬 변경을 추적하기 쉽습니다.

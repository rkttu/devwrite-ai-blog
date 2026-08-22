# PaperMod 기준 리비전과 갱신 절차

이 디렉터리는 PaperMod를 저장소에 포함한 복사본입니다. Git submodule로 관리하지 않습니다.

## 기준 리비전

- 원본 저장소: <https://github.com/adityatelange/hugo-PaperMod>
- 기준 커밋: [`1cf53273c3ba58f0593ecb7c2befe11274f51a4e`](https://github.com/adityatelange/hugo-PaperMod/commit/1cf53273c3ba58f0593ecb7c2befe11274f51a4e)
- 저장소 포함 커밋: `405cfe068e8a9f270b7fe9daf0e3ff3a410beee3`

기준 커밋 이후 `themes/PaperMod` 안에서 바꾼 코드는 이 블로그의 로컬 변경입니다. 루트의 `layouts`와 `assets/css/extended`도 PaperMod 템플릿과 스타일을 덮어씁니다.

## 갱신 순서

1. 원본 저장소에서 적용할 커밋과 릴리스 노트를 확인합니다.
2. 기준 커밋과 새 커밋 사이의 변경 사항을 별도 작업 디렉터리에서 비교합니다.
3. `themes/PaperMod`의 로컬 변경과 루트의 오버라이드를 함께 검토합니다.
4. 새 원본 파일을 반영한 뒤 이 문서의 기준 커밋을 갱신합니다.
5. `hugo --environment production --minify --gc --panicOnWarning`으로 빌드합니다.
6. `public/ko/404.html`과 `public/ko/llms.txt`를 `public` 루트에 복사합니다.
7. `python3 scripts/validate_site.py public`으로 링크와 구조화 데이터를 검사합니다.

테마 갱신과 블로그 기능 변경은 서로 다른 커밋으로 나누면 원본 변경과 로컬 변경을 추적하기 쉽습니다.

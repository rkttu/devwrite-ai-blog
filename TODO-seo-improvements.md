# SEO & 트래픽 개선 TODO

## 높은 우선순위 (High Impact)

- [x] **1. `params.env = "production"` 추가** — OG/Twitter/JSON-LD 활성화 보장
- [x] **2. 검색엔진 등록 태그 설정** — Google(DNS), Bing(DNS), Naver(meta tag) 완료
- [x] **3. 포스트 `description` 필드 추가** — 14개 포스트의 세 언어 문서 42개에 description 반영 완료
- [x] **4. 사이트 description 확장** — 각 언어별 50~160자 설명 작성 완료
- [x] **5. `x-default` hreflang 추가** — extend_head.html에 추가 완료

## 중간 우선순위 (Medium Impact)

- [x] **6. 검색 페이지 활성화** — 각 언어별 search.md 생성 + 메뉴 추가 + JSON 출력 포맷 활성화 완료
- [x] **7. 커스텀 404 페이지** — 홈 링크, 최근 포스트, 검색 포함 + 3개 언어 i18n 완료
- [x] **8. JSON-LD author 구조 수정** — schema_json.html 오버라이드 + sameAs 소셜 프로필 추가 완료
- [x] **9. 언어별 조건부 폰트 로딩** — 현재 언어의 Noto Sans 계열과 공통 코드 폰트만 로드
- [x] **10. Twitter/X site/creator 설정** — @rkttu 계정 설정 완료

## AI 검색엔진 최적화 (AI Search)

- [x] **11. robots.txt AI 크롤러 전면 허용** — 모든 AI 크롤러(GPTBot, Google-Extended, CCBot, anthropic-ai 등) Allow로 변경, enableRobotsTXT 활성화, 메타 태그 차단도 제거
- [x] **12. `llms.txt` 파일 생성** — Hugo 템플릿으로 언어별 발행 글 목록 생성, HTML head에 link[rel=help] 태그 추가
- [x] **13. E-E-A-T 신호 강화** — 3개 언어 저자 페이지에 경력 연차·자격·전문 분야 테이블·발행 이력 섹션 추가, sameAs에 DotNetDev 커뮤니티 추가
- [x] **14. 콘텐츠 구조 AI 친화적 개선** — TL;DR을 별도 영역으로 표시, JSON-LD BlogPosting에 abstract 필드 추가

## 낮은 우선순위 (Low Impact)

- [x] **15. 언어 레이블 가독성 개선** — '가'→'한국어', 'A'→'English', 'あ'→'日本語' 변경 완료
- [x] **16. 홈페이지 `keywords` 설정** — 각 언어별 params.keywords 추가 완료
- [x] **17. 관련 포스트(Related Content) 섹션** — Hugo related 설정 + related_posts.html partial + CSS 스타일 추가 완료
- [x] **18. 이미지 최적화** — scripts/optimize_images.py (Pillow 기반 WebP 변환 + 리사이즈 + front matter 업데이트) 구현 완료
- [ ] **19. HTTP 보안 헤더 설정** — Hugo의 meta 요소로 대체할 수 없는 X-Content-Type-Options, X-Frame-Options, Permissions-Policy는 CDN 또는 호스팅 계층에서 설정

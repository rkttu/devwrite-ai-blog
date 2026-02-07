# SEO & 트래픽 개선 TODO

## 높은 우선순위 (High Impact)

- [ ] **1. `params.env = "production"` 추가** — OG/Twitter/JSON-LD 활성화 보장
- [ ] **2. 검색엔진 등록 태그 설정** — Google Search Console, Naver, Bing verification tag
- [ ] **3. 포스트 `description` 필드 추가** — tldr 값을 description으로 매핑 또는 복사
- [ ] **4. 사이트 description 확장** — 각 언어별 50~160자 설명 작성
- [ ] **5. `x-default` hreflang 추가** — extend_head.html에 추가

## 중간 우선순위 (Medium Impact)

- [ ] **6. 검색 페이지 활성화** — 각 언어별 search.md 생성 + 메뉴 추가
- [ ] **7. 커스텀 404 페이지** — 홈 링크, 인기 포스트, 검색 포함
- [ ] **8. JSON-LD author 구조 수정** — schema_json.html 오버라이드
- [ ] **9. 언어별 조건부 폰트 로딩** — 불필요한 CJK 폰트 제거
- [ ] **10. Twitter/X site/creator 설정** — 계정 정보 추가

## AI 검색엔진 최적화 (AI Search)

- [ ] **11. robots.txt AI 크롤러 차단 정책 재검토** — 선택적 허용 또는 전면 허용 결정
- [ ] **12. `llms.txt` 파일 생성** — AI에게 사이트 콘텐츠를 설명하는 표준 파일
- [ ] **13. E-E-A-T 신호 강화** — 저자 페이지 상세화, sameAs JSON-LD에 소셜 프로필 연결
- [ ] **14. 콘텐츠 구조 AI 친화적 개선** — 질문-답변 소제목, 자기완결적 단락, 리스트/테이블 활용

## 낮은 우선순위 (Low Impact)

- [ ] **15. `languageName` 가독성 개선** — '가'→'한국어', 'A'→'English', 'あ'→'日本語'
- [ ] **16. 홈페이지 `keywords` 설정** — params.keywords 추가
- [ ] **17. 관련 포스트(Related Content) 섹션** — 내부 링크 강화
- [ ] **18. 이미지 최적화** — Hero 이미지 WebP 변환, 리사이즈
- [ ] **19. 보안 헤더 설정** — 호스팅 레벨 HSTS, CSP 등

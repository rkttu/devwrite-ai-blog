# SEO & 트래픽 개선 TODO

## 높은 우선순위 (High Impact)

- [x] **1. `params.env = "production"` 추가** — OG/Twitter/JSON-LD 활성화 보장
- [x] **2. 검색엔진 등록 태그 설정** — Google(DNS), Bing(DNS), Naver(meta tag) 완료
- [x] **3. 포스트 `description` 필드 추가** — tldr 값을 description으로 복사 (24개 전체 완료)
- [x] **4. 사이트 description 확장** — 각 언어별 50~160자 설명 작성 완료
- [x] **5. `x-default` hreflang 추가** — extend_head.html에 추가 완료

## 중간 우선순위 (Medium Impact)

- [x] **6. 검색 페이지 활성화** — 각 언어별 search.md 생성 + 메뉴 추가 + JSON 출력 포맷 활성화 완료
- [x] **7. 커스텀 404 페이지** — 홈 링크, 최근 포스트, 검색 포함 + 3개 언어 i18n 완료
- [x] **8. JSON-LD author 구조 수정** — schema_json.html 오버라이드 + sameAs 소셜 프로필 추가 완료
- [ ] **9. 언어별 조건부 폰트 로딩** — 테마 head.html 전체 오버라이드 필요 (위험도 높아 보류)
- [x] **10. Twitter/X site/creator 설정** — @rkttu 계정 설정 완료

## AI 검색엔진 최적화 (AI Search)

- [x] **11. robots.txt AI 크롤러 전면 허용** — 모든 AI 크롤러(GPTBot, Google-Extended, CCBot, anthropic-ai 등) Allow로 변경, enableRobotsTXT 활성화, 메타 태그 차단도 제거
- [x] **12. `llms.txt` 파일 생성** — static/llms.txt에 사이트·저자·포스트 목록 포함, HTML head에 link[rel=help] 태그 추가
- [x] **13. E-E-A-T 신호 강화** — 3개 언어 저자 페이지에 경력 연차·자격·전문 분야 테이블·발행 이력 섹션 추가, sameAs에 DotNetDev 커뮤니티 추가
- [x] **14. 콘텐츠 구조 AI 친화적 개선** — TL;DR을 details/summary로 구조화 표시, JSON-LD BlogPosting에 abstract 필드 추가

## 낮은 우선순위 (Low Impact)

- [ ] **15. `languageName` 가독성 개선** — '가'→'한국어', 'A'→'English', 'あ'→'日本語'
- [ ] **16. 홈페이지 `keywords` 설정** — params.keywords 추가
- [ ] **17. 관련 포스트(Related Content) 섹션** — 내부 링크 강화
- [ ] **18. 이미지 최적화** — Hero 이미지 WebP 변환, 리사이즈
- [ ] **19. 보안 헤더 설정** — 호스팅 레벨 HSTS, CSP 등

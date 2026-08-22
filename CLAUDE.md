# CLAUDE.md

이 파일은 Claude Code 가 이 저장소에서 작업할 때 자동으로 컨텍스트에 로드됩니다.
프로젝트 규칙, 디렉터리 구조, front matter 스키마, 작성 스타일 가이드는 두 개의 외부 파일에서 가져옵니다.
GitHub Copilot 과 동일한 원본 (`.github/copilot-instructions.md`, `writing-style-guide.md`) 을 그대로 공유하므로,
한쪽이 갱신되면 양쪽 도구 모두 같은 규칙을 따릅니다.

@./.github/copilot-instructions.md

@./writing-style-guide.md

---

## 프로젝트 스킬

블로그 작업 스킬의 원본은 여러 에이전트가 공유할 수 있도록 `.agents/skills/` 에 있습니다.
GitHub Copilot은 이 경로를 직접 탐색합니다.
Claude Code는 `.agents/skills/` 를 직접 탐색하지 않으므로 `.claude/skills/` 의 심볼릭 링크를 통해 같은 원본을 불러옵니다.
Windows에서는 Developer Mode를 활성화하고 Git이 심볼릭 링크를 보존하도록 설정해야 합니다. `.claude/skills/<스킬 이름>/SKILL.md`가 일반 텍스트 링크가 아닌 실제 파일로 열리는지 확인합니다.

| 스킬 | 용도 | 인자 |
| --- | --- | --- |
| `/create-draft` | 새 포스트 생성 | `<slug> <주제>` |
| `/complete-manual-post` | 수동으로 쓴 글에 front matter, 요약, 번역 보강 | `<ko-post-path>` |
| `/generate-tldr` | 포스트의 `description` 과 `tldr` 생성 | `<post-path>` |
| `/select-hero-image` | 히어로 이미지 후보 검색 또는 생성 | `<post-path>` |
| `/translate-post` | 한국어 포스트를 영어/일본어로 번역 | `<slug> <en\|ja>` |
| `/review-draft` | 발행 전 체크리스트 검토 | `<slug-or-path>` |
| `/publish-draft` | `draft: true`에서 `false`로 일괄 변경 | `<slug>` |
| `/unpublish-post` | `draft: false`에서 `true`로 일괄 변경 | `<slug>` |
| `/prepare-blog-post` | 글 작성, 보완, 번역, 리뷰와 발행 전 검증 | `<slug 또는 경로>` |
| `/deploy-blog-post` | 커밋, 푸시, GitHub Pages 배포 검증 | `<slug>` |
| `/publish-blog-to-dotnetdev` | 닷넷데브 게시 초안 생성과 브라우저 인계 | `<slug>` |
| `/share-blog-on-linkedin` | LinkedIn 문안 생성과 공유 화면 인계 | `<slug>` |
| `/publish-blog-post` | 글 준비부터 배포와 외부 채널 공유까지 전체 발행 | `<slug 또는 주제>` |

## 환경 메모

- 주 작업 환경은 Windows 11 + PowerShell. macOS/Linux 의 동등한 Python 스크립트는 `scripts/*.py`.
- 커밋과 푸시처럼 외부 영향이 있는 작업은 사용자가 명시적으로 요청했을 때만 수행합니다.

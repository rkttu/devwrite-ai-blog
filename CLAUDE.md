# CLAUDE.md

이 파일은 Claude Code 가 이 저장소에서 작업할 때 자동으로 컨텍스트에 로드됩니다.
프로젝트 규칙·디렉터리 구조·프론트매터 스키마·작성 스타일 가이드는 두 개의 외부 파일에서 가져옵니다.
GitHub Copilot 과 동일한 원본 (`.github/copilot-instructions.md`, `writing-style-guide.md`) 을 그대로 공유하므로,
한쪽이 갱신되면 양쪽 도구 모두 같은 규칙을 따릅니다.

@./.github/copilot-instructions.md

@./writing-style-guide.md

---

## 슬래시 커맨드

블로그 작업용 슬래시 커맨드는 `.claude/commands/` 에 있습니다.
모두 `.github/prompts/` 의 GitHub Copilot 프롬프트와 1:1 대응됩니다.

| 커맨드 | 용도 | 인자 |
| --- | --- | --- |
| `/create-draft` | 새 포스트 생성 (한국어 원본 + 번역 + 히어로 이미지까지 일괄) | `<slug> <주제>` |
| `/complete-manual-post` | 수동으로 쓴 글에 프론트매터·TL;DR·번역 보강 | `<ko-post-path>` |
| `/generate-tldr` | 포스트의 `description` 과 `tldr` 생성 | `<post-path>` |
| `/select-hero-image` | Unsplash 에서 히어로 이미지 후보 추천 | `<post-path>` |
| `/translate-post` | 한국어 포스트를 영어/일본어로 번역 | `<slug> <en\|ja>` |
| `/review-draft` | 발행 전 체크리스트 검토 | `<slug-or-path>` |
| `/publish-draft` | `draft: true` → `false` 일괄 변경 | `<slug>` |
| `/unpublish-post` | `draft: false` → `true` 일괄 변경 | `<slug>` |

## 환경 메모

- 주 작업 환경은 Windows 11 + PowerShell. macOS/Linux 의 동등한 Python 스크립트는 `scripts/*.py`.
- 커밋·푸시 같은 외부 영향이 있는 작업은 사용자의 명시적 요청이 있을 때만 수행합니다.

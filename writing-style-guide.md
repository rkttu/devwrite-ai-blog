# 블로그 글 작성 스타일 가이드

이 문서는 블로그 아티클 자동 생성 시 참고할 언어별 작성 스타일을 정의합니다.

---

## AI 어시스트 안내

이 블로그의 글들은 AI의 도움을 받아 작성됩니다. 이 사실은 시스템 레벨에서 자동으로 글 상단에 표시됩니다.

### 자동 표시 (시스템 레벨)

- 모든 글 상단에 AI 어시스트 안내 문구가 자동으로 표시됨
- 각 언어별 번역은 `i18n/` 디렉터리의 `aiAttribution` 키로 관리
  - 한국어: "AI의 도움을 받아 작성되었습니다"
  - English: "Content assisted by AI"
  - 日本語: "AIの支援により作成されました"

### 표시 비활성화

특정 글에서 AI 안내를 숨기려면 front matter에 다음을 추가:

```yaml
hideAiAttribution: true
```

---

## 공통 스타일

### 헤더 작성 규칙

- 헤더 제목에 숫자 번호를 붙이지 않음 (예: `## 1. 소개` ❌ → `## 소개` ✅)
- 헤더는 간결하고 명확하게 작성
- `##` (H2)를 본문의 주요 섹션으로 사용
- `###` (H3) 이하는 하위 섹션으로 사용

### 코드 블록

- 코드 블록에는 반드시 언어 지정 (예: ` ```csharp `)
- 코드 내 주석은 해당 언어로 작성
- 긴 코드는 핵심 부분만 발췌하고 `// ...` 로 생략 표시

### 링크

- 외부 링크는 설명과 함께 제공
- 내부 링크는 해당 언어 경로 사용 (예: `/ko/posts/...`)

### 이미지

- Hero 이미지는 `cover.image` 필드에 경로 지정
- 본문 내 이미지는 상대 경로 또는 절대 경로 사용

---

## 한국어 (ko) 스타일

### 어투

- **격식체(합쇼체)** 사용: ~입니다, ~됩니다, ~합니다
- 친근하지만 전문적인 톤 유지
- 독자를 직접 지칭할 때는 "여러분" 또는 생략

### 용어

- 기술 용어는 원어 유지 가능 (예: File-Based App, Graceful Shutdown)
- 처음 등장 시 괄호로 원어 병기 가능 (예: 파일 기반 앱(File-Based App))
- 일반적으로 통용되는 외래어는 한글로 표기 (예: 리포지토리, 업그레이드)

### 문장 구조

- 한 문장은 가능한 짧게 유지
- 나열할 때는 불릿 포인트 활용
- 강조할 때는 **굵은 글씨** 사용

### 예시

```markdown
## 소개

이번 업데이트에서는 프로젝트 구조가 대폭 단순화되었습니다.

주요 특징:

- **프로젝트 파일 불필요**: `.csproj` 없이 실행 가능
- **패키지 참조 인라인 선언**: `#:package` 지시문 사용
```

---

## English (en) Style

### Tone

- Professional but approachable
- Use active voice when possible
- Address readers as "you" when appropriate

### Terminology

- Use standard technical terms
- Avoid unnecessary jargon
- Define acronyms on first use (e.g., FBA (File-Based App))

### Sentence Structure

- Keep sentences concise and clear
- Use bullet points for lists
- Use **bold** for emphasis

### Example

```markdown
## Introduction

This update significantly simplifies the project structure.

Key features:

- **No project file required**: Run without `.csproj`
- **Inline package references**: Use `#:package` directive
```

---

## 日本語 (ja) スタイル

### 文体

- **です・ます調** を使用
- 丁寧だが堅すぎない文体を維持
- 読者への呼びかけは「皆さん」または省略

### 文末表現の注意点

- **ですよ / ですよね の多用を避ける**: 読者に押し付けがましい印象を与える可能性があるため、基本的に **です / ます** で終える
- 日本語の技術ブログでは、独り言のように淡々と書き、読者が自然に読み取るスタイルが好まれる
- 強調が必要な場合は文末表現ではなく、**太字**や文構造で表現する

**良い例:**

- `このアップデートでは構造が簡素化されました。`
- `FBA方式を使用することで、ビルド手順が不要になります。`

**避けるべき例:**

- `このアップデートでは構造が簡素化されましたよ。` ❌
- `便利ですよね。` ❌

### 用語

- 技術用語は原語のまま使用可能（例：File-Based App、Graceful Shutdown）
- 初出時は括弧で原語を併記可能（例：ファイルベースアプリ（File-Based App））
- 一般的に使われる外来語はカタカナ表記（例：リポジトリ、アップグレード）

### 文構造

- 一文は短く簡潔に
- 列挙する場合は箇条書きを活用
- 強調には**太字**を使用

### 例

```markdown
## はじめに

今回のアップデートでは、プロジェクト構造が大幅に簡素化されました。

主な特徴：

- **プロジェクトファイル不要**: `.csproj`なしで実行可能
- **インラインパッケージ参照**: `#:package`ディレクティブを使用
```

---

## 참고사항

- 이 스타일 가이드는 AI 에이전트가 블로그 글을 자동 생성할 때 참조합니다.
- 새로운 스타일 규칙이 필요하면 이 파일에 추가하세요.
- 각 프롬프트 파일에서 이 가이드를 참조할 수 있습니다.

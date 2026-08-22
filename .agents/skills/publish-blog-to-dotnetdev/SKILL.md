---
name: publish-blog-to-dotnetdev
description: 특정 Hugo 블로그 글을 닷넷데브 포럼에 소개하거나 교차 게시할 때 disc CLI로 게시 초안을 만들고 브라우저 검토 단계로 넘깁니다. 일반적인 블로그 작성이나 다른 포럼 작업에는 사용하지 않습니다.
---

# 닷넷데브 블로그 글 게시 초안

## 실행 범위

이 스킬은 블로그 글 선택, 포럼용 본문 작성, 중복 검색, 카테고리 조회, Discourse 초안 적재를 자동화합니다. disc는 직접 발행 기능을 제공하지 않습니다. `disc draft`가 브라우저 작성기를 열면 사용자가 내용을 검토하고 발행 버튼을 직접 누릅니다.

사용자가 "자동 발행"을 요청해도 브라우저 인계까지 자동화된다고 먼저 알립니다. 사용자가 브라우저에서 발행을 확인하기 전에는 게시가 완료되었다고 보고하지 않습니다. disc의 설계 배경과 설치 명령은 [닷넷데브 소개 글](https://forum.dotnetdev.kr/t/discourse-net-disc/14722)과 [disc 저장소](https://github.com/rkttu/disc)를 기준으로 확인합니다.

## 환경 진단

읽기 전용 진단 명령은 바로 실행할 수 있습니다. 다음 순서로 CLI, 컨텍스트, 자격 증명, 권한 범위를 확인합니다.

```bash
command -v disc
disc --version
disc context list --json
disc status --json
disc whoami --json
```

현재 컨텍스트의 호스트가 `forum.dotnetdev.kr`인지 확인합니다. 다른 컨텍스트가 현재값이지만 `dotnetdev` 컨텍스트가 존재한다면 현재값을 바꾸지 않고 `disc --context dotnetdev ...` 형식으로 실행합니다.

## 설치와 로그인 복구

disc가 없으면 전역 도구 설치가 로컬 시스템을 변경한다고 알리고 실행 전에 승인을 받습니다. .NET SDK가 설치되어 있을 때 다음 명령을 사용합니다.

```bash
dotnet tool install --global Discourse.Cli
```

설치 후에도 명령을 찾지 못하면 `~/.dotnet/tools`가 `PATH`에 포함되어 있는지 확인합니다. .NET SDK도 없다면 작업을 중단하고 [공식 .NET 다운로드 페이지](https://dotnet.microsoft.com/download)에서 SDK를 설치하는 절차를 안내합니다. 설치된 도구를 갱신하라는 요청을 받은 경우에만 `dotnet tool update --global Discourse.Cli`를 실행합니다.

닷넷데브 컨텍스트가 없으면 다음 설정 명령을 안내합니다. 사용자가 승인하면 추가하고 이후 명령에는 컨텍스트를 명시합니다.

```bash
disc context add dotnetdev --host forum.dotnetdev.kr
disc context use dotnetdev
```

로그인이 풀렸거나 권한 범위가 `read`뿐이면 브라우저 인증이 필요하다고 알리고 다음 명령을 실행합니다.

```bash
disc --context dotnetdev login --enable-drafts
```

인증 후 `disc --context dotnetdev whoami --json`과 `disc --context dotnetdev status --json`을 다시 실행합니다. `valid`가 `true`이고 쓰기 범위가 포함되어야 초안을 만들 수 있습니다. 닷넷데브의 User API Key 발급에는 신뢰 레벨 2 이상이 필요합니다. 인증이나 권한 확인이 실패하면 반복 로그인하지 않고 원인과 다음 명령을 안내한 뒤 중단합니다.

자격 증명 값과 운영체제 보안 저장소의 내용은 출력하거나 파일로 저장하지 않습니다.

## 블로그 원문 선택

한국어 글을 원문으로 사용합니다. 사용자가 경로를 지정하면 `content/ko/posts/<날짜>-<슬러그>/index.md` 내부인지 확인합니다. 슬러그만 지정하면 front matter의 `slug`가 정확히 일치하는 파일을 찾아 결과가 한 개인지 확인합니다.

front matter와 본문에서 다음 정보를 읽습니다.

- `title`
- `description` 또는 `tldr`
- `slug`
- `date`
- `draft`
- 포럼 소개문에 사용할 핵심 내용

`draft: true`인 글은 사용자가 미공개 글의 포럼 초안 작성을 별도로 승인하지 않는 한 중단합니다. 기본 원문 URL은 front matter의 슬러그를 사용한 `https://devwrite.ai/ko/posts/<slug>/`입니다. 영어와 일본어 번역본을 별도 토픽으로 만들지 않습니다.

## 포럼용 본문

제목과 본문을 작성하기 전에 `writing-style-guide.md` 전체를 읽습니다. 사용자가 별도 문체를 지정하지 않았다면 커뮤니티 글에 해당하는 존댓말 구어체를 사용하고 산출물의 길이와 구조에 맞는 적용 등급을 선택합니다.

기본 형식은 블로그 원문으로 독자를 안내하는 소개 글입니다. 전체 본문을 복제하지 않고 확인한 `description`이나 `tldr`, 핵심 항목, 원문 링크를 사용합니다. 사용자가 전문 교차 게시를 명시한 경우에만 Markdown 본문 전체를 바탕으로 작성하며 원문 URL을 앞부분에 표시합니다.

제목과 본문에서 확인하지 못한 경험, 성과, 수치, 의견을 새로 만들지 않습니다. 임시 본문 파일은 Git 추적 대상 밖에 만들고 커밋하지 않습니다.

## 중복과 카테고리 확인

초안을 적재하기 전에 원문 URL과 제목을 각각 검색합니다.

```bash
disc --context dotnetdev search --query "https://devwrite.ai/ko/posts/<slug>/" --json
disc --context dotnetdev search --query "<제목>" --json
disc --context dotnetdev categories --json
```

같은 글을 소개하는 기존 토픽을 발견하면 새 토픽을 만들지 않고 검색 결과를 보여 줍니다. 새 토픽과 기존 토픽 답글 중 어떤 형태를 원하는지 사용자에게 확인합니다. 게시 가능 카테고리는 매번 조회하며 슬러그나 ID를 하드코딩하지 않습니다.

## 최종 승인과 초안 적재

외부 상태를 바꾸기 직전에 제목, 카테고리, 추가 태그, 본문 전체, 원문 URL을 보여 주고 사용자의 최종 승인을 받습니다. disc가 `disc` 태그와 도구 출처 문구를 자동으로 추가한다는 점도 알립니다.

승인을 받은 뒤 한 번만 실행합니다. 추가 태그가 없다면 `--tag`를 생략합니다.

```bash
disc --context dotnetdev draft \
  --title "<제목>" \
  --category <카테고리> \
  --body-file <임시-본문-파일> \
  --tag <쉼표로-구분한-추가-태그> \
  --yes
```

명령이 성공하면 브라우저 작성기가 열렸으며 최종 발행은 사용자가 수행한다고 안내합니다. 명령이 실패하면 같은 초안을 자동 재시도하지 않습니다. 종료 코드와 오류를 보고하고 인증, 카테고리 권한, 네트워크 상태 중 확인 가능한 원인을 구분합니다.

## 중단 조건

다음 상태에서는 `disc draft`를 실행하지 않습니다.

- disc 또는 .NET SDK 설치 안내가 완료되지 않은 상태
- 닷넷데브 컨텍스트를 확인하지 못한 상태
- 인증 만료 또는 초안 쓰기 범위 부족
- 게시 가능 카테고리 미확정
- 중복 토픽 처리 방식 미확정
- 사용자에게 보여 주지 않은 본문
- 외부 초안 적재에 대한 최종 승인 부재

disc는 대화형 데스크톱 도구입니다. CI, 예약 작업, 무인 반복 실행으로 우회하지 않습니다.

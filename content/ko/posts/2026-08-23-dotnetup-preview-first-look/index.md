---
title: "dotnetup 프리뷰: global.json에서 SDK와 런타임 관리까지"
date: 2026-08-23T01:35:51+09:00
draft: false
slug: "dotnetup-preview-first-look"
description: "dotnetup 프리뷰가 운영체제 패키지와 개발용 SDK를 분리하고 global.json, 런타임, 업데이트 상태를 관리하는 방식을 정리합니다."
tags:
  - .NET
  - dotnetup
  - .NET SDK
  - global.json
  - 개발 환경
categories:
  - .NET 개발
translationKey: "dotnetup-preview-first-look"
cover:
  image: "images/posts/dotnetup-preview-first-look.webp"
  alt: "구성 파일이 상태 관리자를 거쳐 사용자 범위의 SDK와 런타임 구성 요소로 연결되는 일러스트레이션"
tldr: "dotnetup은 rustup과 비슷하게 시스템 패키지는 유지하면서 개발용 .NET SDK와 런타임을 사용자 계정에서 따로 관리합니다. 저장소의 global.json을 추적 가능한 설치 요구 사항으로 연결하고 채널 업데이트와 공유 구성 요소 정리도 지원합니다."
license: "CC BY-NC 4.0"
---

Microsoft는 Microsoft Build 2026 사전 녹화 세션 OD804 [「Simplifying .NET installs with .NET Up」](https://www.youtube.com/watch?v=ZMnyohA5yrw)에서 사용자 단위 .NET 설치를 관리하는 새 도구 `dotnetup`을 소개했습니다. 2026년 8월 22일 현재 `dotnet/sdk` 저장소의 `release/dnup` 브랜치는 Windows, macOS, Linux용 프리뷰 설치 방법과 명령 참조 문서를 제공합니다. 이 글은 세션이 제시한 문제와 설계 의도를 토대로 현재 프리뷰에서 확인할 수 있는 동작을 정리합니다.

`dotnetup`은 관리자 권한 없이 사용자 프로필 아래에 .NET SDK와 런타임을 설치합니다. 저장소의 `global.json`을 읽어 필요한 SDK 채널을 추적하고 여러 요구 사항이 공유하는 설치 파일을 업데이트하거나 정리합니다. 셸과 애플리케이션이 관리 대상 `dotnet`을 찾는 방식도 선택할 수 있습니다. 이 글에서는 설치 방식, `global.json` 해석, SDK와 런타임의 분리, 설치 상태 관리, 자동화 활용을 다룹니다.

먼저 기존 설치 방식에서 남아 있던 관리 공백을 살펴봅니다. 이후 프리뷰 설치와 저장소 단위 SDK 준비 과정을 따라갑니다. 런타임과 업데이트 모델을 설명하고 현재 구현과 OD804 로드맵 사이의 차이로 글을 마무리합니다.

> 기준일: 2026년 8월 22일. `dotnetup`은 프리뷰 단계이며 명령 이름과 동작이 달라질 수 있습니다. 이 글은 [`release/dnup` 브랜치의 공식 문서](https://github.com/dotnet/sdk/tree/release/dnup/documentation/general/dotnetup)와 이날 내려받은 `0.2.0-preview.1.26410.1`을 기준으로 작성했습니다.

## 설치 스크립트보다 rustup에 가까운 상태 관리자

.NET 설치 경로가 왜 하나의 관리 도구로 모이는지 살펴보겠습니다. OD804 세션은 Windows에서 Visual Studio가 도구 체인을 관리하는 경우와 그 밖의 경우를 대비합니다. 후자에는 운영체제 패키지 관리자, 웹 설치 프로그램, `dotnet-install` 스크립트, DNVM과 mise 같은 버전 관리 도구가 섞여 있습니다. 설치 주체와 업데이트 주기가 서로 달라지면 저장소마다 필요한 SDK를 준비하고 오래된 설치를 제거하는 절차도 달라집니다. [세션의 문제 정의 구간](https://www.youtube.com/watch?v=ZMnyohA5yrw&t=69s)은 이 차이를 도구가 해결하려는 출발점으로 제시합니다.

기존 `dotnet-install` 스크립트도 관리자 권한 없는 설치를 지원합니다. 다만 Microsoft는 이 스크립트를 SDK가 실행마다 사라져도 되는 CI 환경에 주로 사용한다고 설명합니다. 개발 환경에는 설치 프로그램을 안내해 왔습니다. [`dotnet-install` 공식 문서](https://learn.microsoft.com/dotnet/core/tools/dotnet-install-script)는 이 사용 범위를 명시합니다.

이 지점에서 `dotnetup`은 설치 스크립트보다 Rust의 `rustup`과 가까운 도구 체인 관리자입니다. Ubuntu처럼 [배포판 패키지의 SDK 기능 밴드와 더 최신 SDK 배포 사이에 차이가 생길 수 있는 환경](https://learn.microsoft.com/dotnet/core/install/linux-ubuntu-install)에서는 시스템 패키지를 유지한 채 개발용 최신 SDK만 사용자 계정에 분리할 수 있습니다. 패키지 관리자를 교체하거나 관리자 권한을 얻지 않고도 프로젝트마다 다른 채널을 추적할 수 있다는 점을 [닷넷데브의 초기 소개 글](https://forum.dotnetdev.kr/t/dotnetup-rustup-net-toolchain-manager/14805)에서도 강조했습니다.

`dotnetup`은 원하는 구성 요소와 채널을 기록한 뒤 실제 설치 버전과 연결합니다. 그래서 `latest`, `lts`, `10.0.1xx`처럼 계속 이동하는 요구 사항을 나중에 다시 해석할 수 있습니다. 정확한 버전을 지정하면 해당 요구 사항을 고정합니다. 설치 파일을 받는 작업과 설치 상태를 관리하는 작업을 한 명령 체계에 넣었다는 점에서 기존 스크립트와 역할이 갈립니다. [공식 개요 문서](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/index.md)는 설치, 업데이트, 제거, 환경 구성을 현재 범위로 설명합니다.

## 관리자 권한 없는 사용자 단위 설치

프리뷰 설치와 접근 모드를 정리하겠습니다. macOS와 Linux에서는 공식 스크립트로 시작할 수 있습니다.

```bash
curl -fsSL https://aka.ms/dotnet/dotnetup/preview/get-dotnetup.sh | bash
export PATH="$HOME/.dotnetup:$PATH"
dotnetup init
dotnetup --version
```

스크립트는 운영체제와 CPU에 맞는 실행 파일을 내려받고 SHA-512 체크섬을 검증한 뒤 기본적으로 `~/.dotnetup`에 `dotnetup` 실행 파일을 둡니다. Windows용 PowerShell 절차와 `daily` 빌드 설치법은 [시작 문서](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/README.md)에서 함께 확인할 수 있습니다. 보안 정책상 파이프 실행을 허용하지 않는 환경이라면 스크립트를 파일로 저장해 검토한 뒤 실행할 수 있습니다.

`dotnetup init`은 SDK 채널과 접근 모드를 묻습니다. 접근 모드는 기존 `dotnet` 설치와의 우선순위를 결정합니다.

| 표시 이름 | 설정값 | 관리 대상 `dotnet`을 찾는 범위 |
| --- | --- | --- |
| Isolation Mode | `none` | `PATH`를 바꾸지 않고 `dotnetup dotnet <command>`로 실행 |
| Terminal Mode | `shell` | 선택한 셸 프로필을 갱신하고 해당 셸에서 시작한 프로세스에 적용 |
| Everywhere Mode | `everywhere` | Windows 사용자 환경과 셸 프로필에 적용 |

macOS와 Linux에서는 지원하는 셸을 감지하면 Terminal Mode를 기본 후보로 표시합니다. Windows에서는 Everywhere Mode를 기본 후보로 제시합니다. `dotnetup`이 관리하는 SDK와 런타임의 기본 설치 루트는 운영체제별 사용자 데이터 디렉터리 아래에 두며 시스템 관리 경로에는 쓰지 않습니다. [환경 구성 문서](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/concepts/environment.md)가 경로와 환경 변수의 실제 동작을 설명합니다.

이번 확인에서는 공식 프리뷰 스크립트가 macOS arm64용 `0.2.0-preview.1.26410.1` 실행 파일을 선택하고 체크섬 검증을 마쳤습니다. OD804는 빠른 시작과 작은 런타임 의존성을 위해 Native AOT를 설계 방향으로 설명합니다. 내려받은 파일도 .NET SDK를 먼저 설치하지 않은 상태에서 바로 실행할 수 있는 플랫폼별 실행 파일이었습니다. 이 결과는 2026년 8월 22일의 macOS arm64 확인에 한정됩니다.

첫 실행에서는 사용량 텔레메트리 수집을 고지합니다. 기존 .NET CLI와 같은 `DOTNET_CLI_TELEMETRY_OPTOUT=1` 환경 변수로 전송을 중단할 수 있습니다. 프리뷰를 자동화 환경에 넣을 때에는 [공식 텔레메트리 안내](https://aka.ms/dotnetup-telemetry)와 조직 정책을 함께 적용할 수 있습니다.

## global.json을 설치 요청으로 해석하는 채널 모델

저장소 요구 사항을 설치 상태로 바꾸는 과정을 짚어보겠습니다. 다음 `global.json`은 10.0.1xx 기능 밴드 안에서 최신 패치를 허용합니다.

```json
{
  "sdk": {
    "version": "10.0.100",
    "rollForward": "latestPatch"
  }
}
```

저장소 루트에서 `dotnetup sdk install`을 실행하면 도구가 현재 디렉터리부터 상위 디렉터리 방향으로 가장 가까운 `global.json`을 찾습니다. 채널을 명령줄에 적지 않았고 사용할 수 있는 파일도 없다면 `latest`를 선택합니다. 파일을 찾으면 `sdk.version`과 `rollForward`를 다음 규칙으로 설치 요청에 대응시킵니다.

| `rollForward` | `10.0.103`에서 추적하는 요청 |
| --- | --- |
| 생략 또는 `latestPatch` | `10.0.1xx` |
| `latestFeature` | `10.0` |
| `latestMinor` | `10` |
| `latestMajor` | `latest` |
| `disable`, `patch`, `feature`, `minor`, `major` | 정확한 버전 `10.0.103` |

이 대응은 .NET 호스트가 설치된 SDK 중 하나를 고르는 규칙과 목적이 다릅니다. `dotnetup`은 어떤 버전을 설치하고 계속 추적할지 결정하고 .NET 호스트는 설치를 마친 SDK 중 실행에 사용할 버전을 고릅니다. [`global.json` 공식 문서](https://learn.microsoft.com/dotnet/core/tools/global-json)는 SDK 선택과 런타임 대상 지정을 서로 독립된 항목으로 설명합니다. `dotnetup`의 변환 규칙은 [저장소 연동 문서](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/usecases/install-with-global-json.md)에서 확인할 수 있습니다.

이번 확인에서는 위 파일을 읽은 `dotnetup`이 요청을 `10.0.1xx`로 기록하고 `10.0.111`을 별도 설치 루트에 배치했습니다. `dotnetup list`도 설치 출처로 해당 `global.json`의 전체 경로를 표시했으며 설치한 `dotnet --version`은 `10.0.111`을 반환했습니다. 같은 명령을 다른 날 실행하면 채널이 가리키는 버전이 달라질 수 있습니다.

`--update-global-json`을 추가하면 설치한 구체 버전을 `sdk.version`에 반영합니다. 다른 속성과 서식, 감지한 텍스트 인코딩은 유지합니다. `sdk.paths`가 있는 저장소에서는 첫 번째 경로를 설치 루트로 사용할 수도 있습니다. 명령줄의 `--install-path`가 `sdk.paths`보다 먼저 적용됩니다.

## 최신 SDK와 과거 런타임의 분리

SDK와 런타임을 따로 설치하는 이유를 다루겠습니다. SDK는 컴파일러, MSBuild, CLI 같은 개발 도구를 제공합니다. 런타임은 빌드한 애플리케이션과 테스트를 실제로 실행합니다. 최신 SDK로 여러 대상 프레임워크를 빌드하더라도 해당 버전의 테스트를 실행할 런타임은 별도로 필요할 수 있습니다.

OD804 데모는 .NET 10 SDK로 `net8.0`, `net9.0`, `net10.0` 테스트를 빌드한 뒤 .NET 8과 .NET 9 런타임이 없어 두 테스트가 시작되지 않는 상황을 보여 줍니다. 이전 SDK 전체를 나란히 설치하는 대신 필요한 런타임만 추가하는 해법을 다음과 같이 시연합니다.

```console
dotnetup runtime install 8.0 9.0 10.0
dotnetup runtime install aspnetcore@8.0 aspnetcore@10.0
dotnet --list-runtimes
```

버전만 쓰면 `Microsoft.NETCore.App` 런타임을 선택합니다. `aspnetcore@10.0`은 ASP.NET Core 런타임을 선택하고 Windows에서는 `windowsdesktop@10.0`도 사용할 수 있습니다. 정확한 런타임 버전을 적으면 고정 요청으로 저장합니다. [구성 요소 설치 문서](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/usecases/install-components.md)는 현재 지원하는 명령 형식을 설명합니다.

세션에서 보여 준 `global.json`의 런타임 선언은 미래 구상을 설명하기 위한 가상 문법이었습니다. 현재 프리뷰 문서는 `global.json`에서 SDK 요구 사항만 읽습니다. 런타임은 `dotnetup runtime install`에 직접 지정합니다. [세션의 런타임 데모 구간](https://www.youtube.com/watch?v=ZMnyohA5yrw&t=1505s)도 이 문법이 확정되지 않았다고 밝힙니다.

## 요구 상태와 실제 설치를 나누는 매니페스트

설치 이후의 업데이트와 정리 방식을 검토하겠습니다. `dotnetup`은 사용자가 요청한 채널과 디스크에 배치한 구체 버전을 별도로 기록합니다.

| 상태 요소 | 기록하는 내용 | 쓰임새 |
| --- | --- | --- |
| 설치 사양 | 구성 요소, 채널 또는 정확한 버전, 요청 출처 | 업데이트할 범위와 고정 여부 판단 |
| 설치 항목 | 구체 버전, 아키텍처, 설치 루트, 공유 하위 구성 요소 | 파일 검증과 제거 범위 계산 |
| 환경 설정 | `dotnet` 접근 모드와 `dotnetup`의 `PATH` 포함 여부 | 셸 프로필과 현재 설정의 차이 탐지 |

상태를 조회하고 갱신하는 기본 흐름은 다음과 같습니다.

```console
dotnetup list
dotnetup update
dotnetup list --format json
```

`dotnetup update`는 각 이동 채널을 다시 해석해 새 버전을 설치합니다. 정확한 버전 요청은 건너뜁니다. 업데이트가 끝나면 남아 있는 설치 사양이 더 이상 요구하지 않는 버전과 다른 설치 항목이 공유하지 않는 하위 구성 요소를 정리합니다. 여러 요청이 같은 설치를 가리키면 파일을 한 번만 유지합니다. [업데이트 문서](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/usecases/update-installations.md)와 [상태 모델 문서](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/concepts/how-dotnetup-works.md)가 이 동작을 나누어 설명합니다.

OD804는 사용자 데이터 디렉터리의 매니페스트를 선언한 시스템 상태에 대한 잠금 파일에 비유합니다. 이 비유는 저장소에 커밋하는 계약까지 뜻하지 않습니다. 저장소 계약은 `global.json`이 담당하며 매니페스트는 각 컴퓨터에서 설치 사양과 실제 파일을 연결하는 장부에 가깝습니다. 도구는 매니페스트 내용이 자신이 기록한 상태에서 달라졌는지 검사하는 해시 파일도 유지하므로 해당 파일을 직접 편집하지 않습니다.

## 사람과 자동화가 함께 쓰는 개발용 경계

사람과 에이전트가 같은 설치 절차를 사용하는 범위를 확인하겠습니다. OD804는 `dotnetup`의 주요 사용자를 개발자와 자동화된 실행 주체로 나눕니다. 자동화에는 LLM 기반 코딩 에이전트뿐 아니라 CI도 포함합니다. 관리자 권한을 주지 않은 샌드박스에서도 저장소에 맞는 SDK를 준비할 수 있고 명시적인 명령과 JSON 출력으로 상태를 읽을 수 있기 때문입니다.

자동화에서는 대화형 초기 설정에 의존하지 않는 다음 형태를 사용할 수 있습니다.

```console
dotnetup sdk install 10.0.1xx --no-progress --interactive false
dotnetup dotnet test -- --logger trx
dotnetup list --format json --no-verify
```

`dotnetup`은 CI 또는 리디렉션된 출력을 감지하면 첫 실행 안내를 비활성화합니다. `--no-progress`는 터미널 진행 표시가 로그에 섞이는 문제를 피하고 `--interactive false`는 입력 대기를 막습니다. 검증이 필요한 자동화에서는 `--no-verify`를 빼면 기록된 파일이 실제로 존재하고 유효한지 검사합니다. 세부 옵션은 [자동화 문서](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/usecases/automation.md)에서 확인할 수 있습니다.

`dotnetup dotnet`은 관리 대상 기본 설치 루트의 환경을 자식 프로세스에만 적용합니다. 임의의 `--install-path`로 만든 설치를 자동으로 고르지 않으므로 사용자 지정 루트에서는 그 안의 `dotnet` 실행 파일을 직접 호출하거나 환경 스크립트로 활성화합니다. 이 제약은 [명령 참조](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/reference/dotnetup-dotnet.md)에 적혀 있습니다.

`dotnetup dotnet`은 File-based App의 실행 경로로도 연결할 수 있습니다. `env -S`를 지원하는 Unix 환경에서 `sample.cs`의 첫 줄을 `#!/usr/bin/env -S dotnetup dotnet`으로 지정하고 실행 권한을 부여하면 관리 대상 SDK로 파일을 직접 실행할 수 있습니다. 시스템에 `dotnetup` CLI만 준비하면 관리자 권한이 없는 환경에서도 같은 실행 경로를 구성할 수 있습니다. [닷넷데브 글의 추가 예시](https://forum.dotnetdev.kr/t/dotnetup-rustup-net-toolchain-manager/14805/2)가 이 구성을 보여 줍니다.

도구의 범위는 개발 환경에 머뭅니다. [세션의 사용 대상 설명](https://www.youtube.com/watch?v=ZMnyohA5yrw&t=2055s)은 프로덕션의 프레임워크 종속 배포에는 운영체제 패키지 관리자를 사용하고 다른 경우에는 자체 포함 배포를 선택하는 기존 방식을 유지한다고 설명합니다. 실제 배포 형태에 따른 런타임 포함 여부는 [.NET 애플리케이션 게시 개요](https://learn.microsoft.com/dotnet/core/deploying/)에서 구분할 수 있습니다.

## 현재 프리뷰와 OD804 로드맵의 간격

OD804에서 예고한 기능 가운데 일부가 현재 명령 표면에 들어왔고 나머지는 공개 문서에서 아직 확인되지 않습니다. 세션은 내부 프리뷰, 공개 프리뷰, GA 이후를 나눠 일일 빌드, 한 번의 명령에 특정 SDK를 고르는 실행 방식, 자체 업데이트, 서명 검증, 에이전트 스킬, CI 공급자 통합을 제시했습니다.

| 항목 | 2026년 8월 22일 확인 결과 |
| --- | --- |
| 안정판, LTS, 프리뷰, 일일 빌드, 숫자 채널 | SDK와 런타임 채널로 제공 |
| `global.json` 연동 | SDK 버전과 `rollForward`, `sdk.paths`, 선택적 파일 갱신 지원 |
| SDK와 런타임 구성 요소 | 설치, 업데이트, 제거, 목록 조회 지원 |
| 한 번의 명령으로 실행 | `dotnetup dotnet` 전달 명령 제공. 특정 SDK 버전을 명령 옵션으로 고르는 기능은 이번 프리뷰 도움말에서 확인되지 않음 |
| `dotnetup` 자체 업데이트 | 이번 프리뷰의 공개 명령 목록에서 확인되지 않음 |
| `global.json`의 런타임 선언 | 세션의 가상 문법에 머물며 현재 문서는 SDK 요구 사항만 설명 |
| 에이전트 스킬과 CI 공급자 통합 | 세션의 장기 방향이며 현재 공개 사용 문서에서 확인되지 않음 |
| 다운로드 검증 | 프리뷰 설치 스크립트는 SHA-512 체크섬을 검증. 일일 빌드는 코드 서명을 거치지 않았다고 공식 문서가 고지 |

SHA-512 체크섬 검증과 코드 서명 검증은 같은 보장을 뜻하지 않습니다. 현재 [시작 문서](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/README.md)는 프리뷰 설치 스크립트의 체크섬 검증을 안내합니다. OD804의 [로드맵 구간](https://www.youtube.com/watch?v=ZMnyohA5yrw&t=2539s)은 .NET SDK와 런타임, `dotnetup` 자체의 서명 검증을 공개 프리뷰 목표로 설명했습니다.

일일 빌드 채널은 `11.0.1xx-daily`처럼 메이저 버전과 기능 밴드, 프리뷰 단계를 좁혀 지정할 수 있습니다. [일일 채널 문서](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/channels/daily.md)는 지원 릴리스가 아니며 코드 서명을 거치지 않았다고 경고합니다. 장기간 유지할 개발 환경보다 짧은 시험에 맞는 선택입니다.

현재 문서는 [.NET SDK 저장소 안의 구현 문서](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/index.md)로 제공됩니다. 공식 개요도 배포 방식이 내부 릴리스마다 달라질 수 있다고 고지합니다. 블로그의 설치 예시를 나중에 다시 사용할 때에는 `dotnetup --version`과 `dotnetup --help`를 함께 기록하면 당시 명령 표면을 남길 수 있습니다.

## 프리뷰 적용 전 점검 항목

프리뷰 적용 전에는 [공식 시작 문서](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/README.md)와 현재 환경의 요구 사항을 기준으로 다음 순서를 사용할 수 있습니다.

1. 공식 시작 문서의 설치 URL과 지원 운영체제를 다시 확인합니다.
2. 기존 `dotnet`을 유지하려면 Isolation Mode를 선택하고 `dotnetup dotnet`으로 실행합니다.
3. 저장소의 `global.json`과 `rollForward`가 어떤 채널로 바뀌는지 기록합니다.
4. 이동 채널이 필요한 환경과 정확한 버전 고정이 필요한 빌드를 분리합니다.
5. 일일 빌드는 별도 설치 루트에서 짧게 시험하고 결과에 버전을 남깁니다.
6. CI에서는 진행 표시와 대화형 입력을 끄고 종료 코드를 검사합니다.
7. 텔레메트리를 보내지 않는 환경에서는 `DOTNET_CLI_TELEMETRY_OPTOUT=1`을 설정합니다.

## 개발 환경의 선언과 설치를 잇는 dotnetup

여기까지 정리하면 `dotnetup`은 개발 환경에서 .NET SDK와 런타임의 요구 상태를 설치 파일과 연결합니다. `global.json`을 새 형식으로 대체하지 않고 저장소가 이미 가진 선언을 설치와 업데이트의 입력으로 활용합니다. SDK와 런타임을 구성 요소로 나눈 명령 체계는 다중 대상 테스트와 여러 저장소를 오가는 작업에서 특히 쓸모가 드러납니다.

장기적으로는 OD804가 제시한 자체 업데이트, 서명 검증 확대, 에이전트 스킬, CI 통합이 도구의 관리 범위를 넓힐 수 있습니다. 지금 바로 영향을 주는 부분은 사용자 권한 설치, `global.json` 기반 SDK 준비, 런타임 분리 설치, 추적한 채널의 일괄 업데이트입니다. 프리뷰와 일일 빌드의 검증 수준은 서로 다르므로 같은 신뢰 수준으로 다루지 않습니다.

여러 .NET 저장소를 로컬에서 다루거나 격리된 에이전트가 빌드 환경을 준비한다면 현재 프리뷰를 별도 설치 루트에서 시험할 만합니다. 운영체제 패키지 정책이 중요한 프로덕션 서버에는 기존 배포 방식을 유지할 수 있습니다. 팀이 SDK 버전을 정확히 고정하는 경우에는 정확한 버전 채널을 사용하고 기능 밴드 안에서 패치를 따라가려는 경우에는 `global.json`의 `rollForward`와 `dotnetup`의 채널 대응을 기준으로 판단할 수 있습니다.

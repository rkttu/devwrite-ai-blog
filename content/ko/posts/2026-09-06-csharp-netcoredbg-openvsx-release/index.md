---
title: "netcoredbg 기반 C# 확장의 8개 플랫폼 자동 릴리스 구축기"
date: 2026-09-06T22:25:17+09:00
draft: false
slug: "csharp-netcoredbg-openvsx-release"
description: "AI를 활용해 netcoredbg 통합 C# 확장을 Open VSX에 출시한 과정을 기록합니다. 기존 커뮤니티의 기여와 8개 플랫폼 자동 검증, 배포 복구, VS Code OSS 기반 .NET 개발 도구 구상을 다룹니다."
tags:
  - C#
  - .NET
  - netcoredbg
  - Open VSX
  - GitHub Actions
categories:
  - .NET 개발
translationKey: "csharp-netcoredbg-openvsx-release"
cover:
  image: "images/posts/csharp-netcoredbg-openvsx-release.webp"
  alt: "밝은 갈색 악보 위의 C#과 여러 경로로 연결한 노드로 표현한 플랫폼별 자동 배포"
tldr: "muhammadsammy와 기여자들이 마련한 대안에 감사를 전하며, AI를 활용해 최신 .NET 개발 환경을 더 넓게 전달하려는 프로젝트의 첫 결과를 공유합니다. C# (with netcoredbg)의 8개 플랫폼 자동 배포를 구현했고, 후속 오픈 소스 개발 도구는 아직 착수 전 구상으로 구분합니다."
license: "CC BY-NC 4.0"
---

2026년 9월 6일 제가 운영하는 [vscode-csharp-autobuild](https://github.com/rkttu/vscode-csharp-autobuild) 저장소에서 **C# (with netcoredbg) 2.148.23001**의 첫 릴리스를 완료했습니다. Windows, Linux, Alpine Linux, macOS의 x64와 ARM64용 패키지를 모두 Open VSX에 게시했고, 공개한 파일의 해시가 검증에 사용한 VSIX와 일치하는지 확인했습니다. [첫 릴리스](https://github.com/rkttu/vscode-csharp-autobuild/releases/tag/csharp-v2.148.23-netcoredbg-v3.2.0-1092-g9744e1f05186-r1)는 C# 확장과 netcoredbg의 소스 버전, 플랫폼별 패키지, 검증 기록을 함께 제공합니다.

이번 글에서는 기존 커뮤니티의 기여와 AI를 활용한 프로젝트의 출발 취지, 8개 플랫폼의 호환성 검증, 게시 중단 후 복구를 다룹니다. 정기 작업이 새 버전을 발견하면 소스 빌드부터 공개 파일 확인까지 처리하고, 문제가 생기면 해당 후보의 게시를 멈추도록 구성했습니다. 이번 릴리스를 바탕으로 생각하고 있는 후속 개발 도구의 방향도 덧붙입니다.

아래에서는 별도 확장을 만든 이유에서 시작해 플랫폼 호환 문제와 테스트 범위를 설명합니다. 이어서 버전 연결 방식, 첫 게시에서 발견한 운영 문제, 실험용 워크플로를 정리한 결과를 살펴보겠습니다. 끝으로 VS Code OSS 기반 .NET 개발 도구 구상을 소개합니다. 글에서 다루는 지원 범위와 실행 결과는 2026년 9월 6일의 첫 릴리스를 기준으로 합니다.

## 기존 C# 배포를 유지하는 별도 확장 ID

배포를 둘로 나눈 이유부터 정리하겠습니다. 기존 저장소는 Microsoft의 C# 확장 소스를 자동으로 빌드해 Open VSX에 게시해 왔습니다. 여기서 다루는 대상은 C# 확장이며 C# Dev Kit를 포함하지 않습니다. 기존 배포는 게시용 메타데이터와 빌드 환경을 조정하면서 상류 확장의 동작과 디버거 구현을 유지합니다.

C# 확장의 소스를 공개한다는 사실과 함께 제공하는 디버거의 사용 범위는 구분할 수 있습니다. Microsoft는 [`vsdbg` 관련 문서](https://github.com/dotnet/vscode-csharp/blob/main/docs/debugger/Microsoft-.NET-Core-Debugger-licensing-and-Microsoft-Visual-Studio-Code.md)에서 디버거를 독점 구성 요소로 설명하고 Microsoft IDE에서의 사용으로 제한합니다. 그래서 확장을 Open VSX에 옮기는 작업만으로 VS Code 파생 편집기의 디버거 제약까지 해결할 수는 없습니다.

기존 배포에는 상류 동작을 가능한 한 유지한다는 가치가 있었습니다. 디버거 교체를 기존 사용자에게 일괄 적용하는 대신 별도 확장 ID를 만들었습니다. 두 배포의 선택 기준은 다음과 같습니다.

| 배포 | 확장 ID | 유지하거나 변경하는 범위 |
| --- | --- | --- |
| 기존 C# 배포 | `dotnetdev-kr-custom.csharp` | 상류 확장의 동작과 디버거 구현 유지 |
| C# (with netcoredbg) | `dotnetdev-kr-custom.csharp-with-netcoredbg` | `coreclr` 디버그 어댑터를 자체 빌드한 netcoredbg로 교체 |

커뮤니티에서는 [muhammadsammy/free-vscode-csharp](https://github.com/muhammadsammy/free-vscode-csharp)가 이미 netcoredbg를 통합해 VS Code 파생 편집기에서 사용할 수 있는 C# 개발 환경을 제공해 왔습니다. 저는 이 프로젝트가 마련해 온 선택지와 그 과정에서 축적한 기여를 역사적으로 매우 값지게 생각합니다. 대안을 실제 확장으로 배포하고 유지해 온 muhammadsammy와 기여자들의 노력에 경의와 감사를 전합니다.

저는 빠르게 변화하는 .NET 생태계의 성과를 더 많은 사람에게 알리고 각자의 편집기에서 직접 접할 수 있도록 돕고 싶어 이 프로젝트를 시작했습니다. AI를 조사와 구현, 실패 원인 분석에 활용하면서 관리자의 반복 개입을 줄이는 배포 체계를 만들고자 했습니다. 이번 첫 릴리스에서는 그 취지를 8개 플랫폼의 패키지와 자동 검증 절차로 구체화할 수 있었습니다.

이번 배포는 상류 동작을 보존하는 기존 배포를 함께 유지하면서 태그별 소스 빌드, 플랫폼 전체 검증, 별도 확장 게시를 하나의 운영 흐름으로 연결하는 데 초점을 맞췄습니다. 기존 커뮤니티 확장과의 차이도 이러한 배포 목적과 운영 구조에서 설명할 수 있습니다. AI를 활용해 마련한 스크립트와 테스트가 정기 배포를 수행하고, 검증에 실패한 회차는 관리자가 로그를 살펴 대응하도록 구성했습니다.

이름도 처음 검토했던 Samsung 표기 대신 `C# (with netcoredbg)`로 정했습니다. 아이콘은 밝은 갈색 악보 위에 C와 #을 놓는 형태로 구분했습니다. 프로젝트 출처는 설명과 고지에 남기고 공식 배포나 후원 관계를 암시하는 브랜드 표현은 넣지 않았습니다. [배포 구분과 패키지 정책](https://github.com/rkttu/vscode-csharp-autobuild/blob/main/README.md)에 두 확장의 역할을 기록했습니다.

## 원본 소스 보존과 외부 호환 코드의 경계

Samsung 원본을 보존하면서 어디까지 수정했는지 짚어보겠습니다. 출발점은 netcoredbg의 새 태그를 가져와 플랫폼별로 빌드한 뒤 C# 확장에 연결하는 방식이었습니다. [netcoredbg의 MIT 라이선스](https://github.com/Samsung/netcoredbg/blob/9744e1f051866215611b8440c638042aa2aa2f72/LICENSE)는 저작권과 허가 고지를 포함하는 조건으로 복제, 수정, 배포를 허용합니다. 실제 패키지에는 함께 넣는 라이브러리의 고지도 별도로 보존했습니다.

원본 보존 여부는 파일 해시로 판단했습니다. 빌드 전후에 Samsung 입력 파일 498개의 SHA-256을 비교했고, 첫 릴리스의 모든 네이티브 대상에서 변경이 없음을 확인했습니다. 중간 산출물과 테스트용 프로젝트, 호환 코드는 원본 소스 트리 밖에서 관리했습니다.

컴파일러와 런타임 환경의 차이는 빌드 자동화만 추가한다고 사라지지 않았습니다. Windows에서는 네이티브 빌드와 관리 코드 빌드가 중간 출력 경로를 공유하면서 NuGet 자산 파일이 충돌했습니다. 네이티브 부분과 ManagedPart의 빌드를 분리하고 출력 경로를 나누어 해결했습니다.

Alpine에서는 디버거를 빌드한 뒤에도 .NET 런타임을 초기화하는 과정에서 충돌했습니다. 호출 스택과 재현 결과를 토대로 외부 호환 코드를 추가했고, CoreCLR 초기화를 자체적으로 확보한 8 MiB 스레드 스택에서 실행하도록 구성했습니다. 이 변경은 원본 파일을 수정하지 않으면서도 런타임 동작에 관여합니다. 따라서 원본 파일을 보존했다는 사실과 저장소가 호환 코드의 유지보수를 맡았다는 사실을 함께 설명했습니다. [빌드 문제와 해결 기록](https://github.com/rkttu/vscode-csharp-autobuild/blob/main/docs/research/2026-09-06-build-troubleshooting.md)에 재현 조건과 근거를 남겼습니다.

C# 확장 쪽에도 코드 변경이 들어갔습니다. 임시 체크아웃에 적용하는 오버레이가 확장 ID와 표시 이름, 디버거 다운로드 경로, 어댑터 선택, SDK 환경 전달과 패키징을 조정합니다. 상류 코드가 예상과 달라지면 오버레이가 실패하도록 검사합니다. [통합 코드](https://github.com/rkttu/vscode-csharp-autobuild/blob/main/scripts/variant/overlay.py)에 이러한 변경을 모았습니다. 디버거를 교체해도 C# 확장의 다른 구성 요소에 적용되는 라이선스와 사용 조건은 각각 유지합니다.

## 빌드 성공 이후에 드러난 디버거 동작 오류

기본적인 중단점 검증을 통과한 macOS 디버거에서도 종료 코드 오류가 드러났습니다. 처음 만든 검증용 프로그램은 정상 종료 코드 0을 반환했습니다. Samsung의 `VSCodeTestExitCode`는 macOS에서 종료 코드 3을 기대했는데, 당시 자체 빌드한 디버거는 DAP 응답으로 0을 전달했습니다. 정상 종료만 확인하는 테스트로는 발견할 수 없는 문제였습니다.

DAP(Debug Adapter Protocol)는 편집기와 디버거가 중단점, 스택, 변수, 프로세스 종료 같은 정보를 주고받는 규약입니다. 종료 코드가 달라지면 프로세스는 끝났더라도 편집기가 전달받는 실행 결과는 틀릴 수 있습니다.

macOS의 프로세스 종료 상태를 관찰하는 외부 라이브러리를 연결해 문제를 수정했습니다. .NET 8에서 동작한 뒤에도 .NET 10에서는 추가 조정이 필요했습니다. .NET 10의 런타임 구성 요소가 `waitpid$NOCANCEL` 진입점을 사용한다는 점을 확인하고 그 경로까지 처리했습니다. 이후 같은 테스트가 두 런타임에서 모두 종료 코드 3을 반환했습니다. 실패한 테스트는 검증 목록에 그대로 유지했으며 [Darwin 호환 코드 조사 기록](https://github.com/rkttu/vscode-csharp-autobuild/blob/main/docs/research/2026-09-06-functional-gate-and-darwin-exit.md)에 수정 전후의 결과를 구분했습니다.

기능 검증은 자체 프로그램의 8개 검사 항목에 Samsung의 자동 DAP 시나리오 30개를 더하는 방식으로 확장했습니다. 상류 테스트의 C# 소스와 단언문은 유지하고 외부 프로젝트에서 .NET 8과 .NET 10을 대상으로 빌드했습니다. 수동 실행용으로 분류된 별도 시나리오는 자동 검사 수에 포함하지 않았습니다.

첫 릴리스에서 실행한 플랫폼 범위는 다음과 같습니다.

| 운영체제 계열 | CPU 대상 | 실행한 런타임 | 검증 단계 |
| --- | --- | --- | --- |
| Windows | x64, ARM64 | .NET 8.0.24, .NET 10.0.11 | 소스 빌드 후, VSIX 추출 후 |
| Linux glibc | x64, ARM64 | .NET 8.0.24, .NET 10.0.11 | 소스 빌드 후, VSIX 추출 후 |
| Alpine Linux | x64, ARM64 | .NET 8.0.24, .NET 10.0.11 | 소스 빌드 후, VSIX 추출 후 |
| macOS | x64, ARM64 | .NET 8.0.24, .NET 10.0.11 | 소스 빌드 후, VSIX 추출 후 |

8개 플랫폼과 2개 런타임을 두 단계에서 검증하므로 총 32개 조합을 실행했습니다. 같은 시나리오를 빌드 직후와 VSIX에서 꺼낸 디버거에 각각 적용해 패키징 이후의 동작도 확인했습니다. [첫 릴리스 실행](https://github.com/rkttu/vscode-csharp-autobuild/actions/runs/34031151621)은 모든 네이티브 빌드, VSIX 패키징, 추출 후 기능 검증을 첫 시도에 통과했습니다. 게시 단계의 실패는 뒤에서 따로 다룹니다.

다만 전체 플랫폼의 DAP 검증과 실제 편집기 UI 검증은 범위가 다릅니다. 별도의 설치 검증은 macOS ARM64의 VS Code 1.135.0에서 수행했습니다. VSCodium을 포함한 모든 파생 편집기나 원격 디버깅, 통합 터미널, Hot Reload, C# Dev Kit의 전체 기능까지 확인한 결과로 확대하지 않았습니다.

아래 실행 화면에서는 `Program.cs`의 7번째 줄에 설정한 중단점에서 실행을 멈추고 지역 변수와 호출 스택을 확인할 수 있습니다.

{{< figure src="debugging-breakpoint.png" link="debugging-breakpoint.png" alt="C# 디버깅 화면에서 Program.cs의 7번째 줄에 멈춘 실행과 지역 변수 x=7, y=1 및 호출 스택을 표시한 모습" caption="중단점에서 지역 변수 x=7과 y=1을 확인한 실제 실행 화면" >}}

조사 중에는 macOS 시작 지연과 예외 스택 관련 테스트가 간헐적으로 실패했습니다. 같은 후보의 재실행이 통과한 기록도 있지만 근본 원인은 확정하지 못했습니다. 실패 기록을 보존했고, 이후 후보에서도 같은 문제가 발생하면 게시를 차단하도록 유지했습니다.

## C# 버전과 디버거 버전을 연결하는 배포 기록

두 프로젝트의 버전을 하나의 확장 버전에 연결하는 방식을 다루겠습니다. 사용자가 설치하는 버전은 C# 확장의 버전 흐름을 따라가되, 디버거만 바뀌거나 패키징 코드를 수정했을 때도 새 패키지를 구분할 수 있도록 배포 차수를 추가했습니다.

첫 릴리스의 입력과 출력은 다음과 같습니다.

| 항목 | 값 | 기록하는 의미 |
| --- | --- | --- |
| 상류 C# 태그 | `v2.148.23-prerelease` | 언어 서비스와 확장 소스의 기준 |
| netcoredbg 태그 | `3.2.0-1092` | 디버거 소스의 기준 |
| 패키징 차수 | `1` | 같은 C# 버전 안에서의 배포 구분 |
| 공개 VSIX 버전 | `2.148.23001` | 편집기가 설치와 업데이트에 사용하는 버전 |

숫자 패치 부분은 `상류 C# 패치 × 1000 + 배포 차수`로 계산합니다. 이번에는 `23 × 1000 + 1 = 23001`이므로 `2.148.23001`을 사용했습니다. 다음 차수는 `2.148.23002`로 구분하고 C# 패치가 24로 바뀌면 `2.148.24001`부터 시작합니다. 배포 차수는 1부터 999까지 허용하며 범위를 넘으면 자동 작업을 실패 처리합니다.

GitHub 릴리스 태그에는 C# 버전, netcoredbg 태그, 디버거 커밋의 축약값과 배포 차수를 함께 넣습니다. 전체 커밋 ID와 빌드 설정 지문, 검증 실행 ID, 파일 해시는 매니페스트와 패키지 메타데이터에 보존합니다. 숫자 버전만으로 세부 입력을 모두 표현하려고 하지 않고, 설치 버전에서 정확한 소스와 검증 파일을 찾아갈 수 있도록 연결했습니다. [버전 계산 코드](https://github.com/rkttu/vscode-csharp-autobuild/blob/main/scripts/variant/versioning.py)와 [첫 릴리스 매니페스트](https://github.com/rkttu/vscode-csharp-autobuild/blob/main/docs/research/cross-platform-2026-09-06/first-release-34031151621/release-manifest.json)에서 실제 대응 관계를 확인할 수 있습니다.

상류 태그의 `-prerelease` 표기도 기록에 남겼습니다. VSIX에 숫자 버전을 부여했다고 해서 상류 프리릴리스 소스의 성격까지 바뀌지는 않습니다. 게시 전 초안 릴리스와 완료한 릴리스는 사용한 차수를 예약하고, 게시 없는 검증 실행은 차수를 소비하지 않습니다.

## 첫 게시에서 발견한 공개 지연과 초안 조회 권한

첫 Open VSX 업로드는 모든 기능 검증을 통과한 뒤에 실패했습니다. 게시 도구가 Windows x64 패키지를 접수했다는 응답을 반환했지만, 직후 공개 메타데이터 조회는 HTTP 404를 반환했습니다. 당시 게시 코드는 공개 파일을 즉시 확인할 수 있다고 가정했기 때문에 작업을 중단했습니다.

약 4분 뒤에는 같은 버전의 Windows x64 패키지를 공개 주소에서 조회할 수 있었습니다. [Open VSX의 게시 처리 코드](https://github.com/eclipse-openvsx/openvsx/blob/v1.1.2/server/src/main/java/org/eclipse/openvsx/publish/PublishExtensionVersionHandler.java)는 파일 저장과 검사 등 일부 처리를 비동기로 수행하고, 활성화가 끝나기 전에는 버전을 공개하지 않습니다. CLI의 접수 성공과 공개 다운로드 가능 시점을 각각 확인하는 방식으로 게시 절차를 수정했습니다.

수정한 게시기는 아직 없는 플랫폼을 한 번씩 업로드한 뒤 공개 상태를 기다립니다. 모든 업로드를 제출한 뒤부터 공통 15분 한도를 적용하고, 공개한 파일을 내려받아 검증한 VSIX의 SHA-256과 비교합니다. 이 한도를 넘거나 공개 파일의 내용이 다르면 해당 실행을 실패 처리합니다. 공개를 기다리는 동안 같은 파일을 반복해서 업로드하지는 않습니다.

복구에 사용할 파일은 첫 업로드 전에 GitHub 초안 릴리스에 보관합니다. 8개 디버거 압축 파일, 8개 VSIX, 검증 매니페스트, 릴리스 매니페스트, 압축한 검증 기록까지 총 19개 자산을 보존했습니다. 일부 플랫폼만 게시한 상태에서 작업이 멈추면 다음 실행이 초안의 파일을 복원하고 이미 공개한 파일의 해시를 비교합니다. 내용이 일치하는 플랫폼은 건너뛰고 나머지 게시를 이어갑니다.

초안을 복구하는 첫 실행에서는 또 다른 문제가 드러났습니다. 탐지 작업에 부여한 `contents: read` 권한으로는 공개 릴리스 목록을 읽을 수 있었지만 비공개 초안은 목록에 나타나지 않았습니다. [GitHub 릴리스 API 문서](https://docs.github.com/en/rest/releases/releases#list-releases)는 푸시 권한이 있는 호출자에게만 초안 목록을 제공한다고 설명합니다. 탐지 작업에 `contents: write`를 부여한 뒤에는 보존한 첫 릴리스를 찾을 수 있었습니다. 빌드와 패키징 작업의 저장소 권한은 읽기로 유지했습니다.

이로써 [복구 실행](https://github.com/rkttu/vscode-csharp-autobuild/actions/runs/34034255861)은 첫 릴리스의 버전과 파일을 유지한 채 남은 7개 플랫폼을 게시했습니다. 한국 시각 2026년 9월 6일 21시 57분 19초에 GitHub 릴리스 확정까지 완료했습니다. 이미 공개했던 Windows x64 패키지는 다시 빌드하거나 업로드하지 않았으며, 별도로 수행한 다운로드 검사에서도 8개 플랫폼 모두 원래 검증 해시와 일치했습니다. [첫 게시와 복구 기록](https://github.com/rkttu/vscode-csharp-autobuild/blob/main/docs/research/2026-09-06-first-release.md)에 실패 당시 상태와 복구 결과를 함께 남겼습니다.

## 세션 없이 실행하는 배포와 유지보수 범위

정기 배포는 기본 브랜치 `main`에서 6시간마다 실행합니다. C#과 netcoredbg의 태그를 확인하고 새로운 소스 또는 빌드 설정 조합을 발견하면 전체 검증을 시작합니다. 완료한 조합은 건너뛰며 게시 중단으로 남은 초안이 있으면 그 파일의 복구를 먼저 처리합니다. 모든 단계는 GitHub 호스팅 러너에서 실행하므로 로컬 터미널이나 이번 작업 세션을 계속 열어둘 이유가 없습니다. [정기 배포 워크플로](https://github.com/rkttu/vscode-csharp-autobuild/blob/main/.github/workflows/release-netcoredbg.yml)에 이 진입점을 모았습니다.

운영 정책은 실패한 Actions 실행과 그 증거를 중심으로 구성했습니다. 기능 검사, 파일 해시, 플랫폼 결과 중 하나라도 맞지 않으면 그 후보의 게시를 멈춥니다. 실패한 입력은 다음 주기에도 다시 검토할 수 있고, 관리자는 로그를 토대로 원인을 조사합니다. 알림 수신은 관리자의 GitHub 설정을 따르며 별도 알림 서버나 격리 큐는 추가하지 않았습니다. 토큰 유효성이나 서비스 장애, GitHub의 [예약 실행 지연과 비활동 저장소 처리](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)는 계속 운영 조건에 포함됩니다.

여러 플랫폼을 Open VSX에 게시하는 과정은 한 번에 전부 성공하거나 전부 취소하는 트랜잭션으로 묶이지 않습니다. 일부 플랫폼이 먼저 공개될 수 있으므로 원래 검증 파일을 보존해 이어서 게시하는 쪽을 선택했습니다. 자동 롤백은 넣지 않았고, 게시 후 기능 문제를 수정할 때는 높은 배포 차수로 새 패키지를 제공하는 경로를 사용합니다. 배포를 철회하더라도 사용자가 이미 설치한 파일까지 자동으로 되돌아가지는 않습니다. [복구와 롤백 검토 기록](https://github.com/rkttu/vscode-csharp-autobuild/blob/main/docs/research/2026-09-06-publication-recovery-and-rollback.md)에 이 범위를 구분했습니다.

릴리스 뒤에는 실험 과정에서 만든 Windows 전용 검증과 Alpine 진단 워크플로를 정리했습니다. 기존 C# 게시, 새 확장의 배포 진입점과 내부 검증 워크플로, GitHub 관리 Copilot 작업을 유지했습니다. 수동 검증도 새 배포 진입점에서 게시 옵션을 끄는 방식으로 통일했습니다. 임시 브랜치와 승인한 진단 실행 기록을 삭제한 뒤에도 조사 문서와 정식 릴리스 자산은 보존했습니다. [정리 기록](https://github.com/rkttu/vscode-csharp-autobuild/blob/main/docs/research/2026-09-06-workflow-cleanup.md)을 남기고 [이슈 #2](https://github.com/rkttu/vscode-csharp-autobuild/issues/2#issuecomment-5559474828)를 해결 완료 상태로 닫았습니다.

## VS Code OSS 기반 .NET 개발 도구로 이어지는 구상

이번 릴리스의 경험을 바탕으로 다음에 기회가 닿으면 VS Code OSS 기반의 오픈 소스 .NET 개발 도구에도 착수해 보고자 합니다. C# Dev Kit이 제공하는 개발 경험을 참고해 솔루션과 프로젝트 탐색, 빌드, 테스트, 디버깅을 편집기 안에서 연결하는 방향을 생각하고 있습니다. Microsoft의 [C# 개발 문서](https://code.visualstudio.com/docs/languages/csharp)는 C# Dev Kit을 통한 솔루션 관리와 통합 테스트 등을 소개합니다. 이러한 작업 흐름 가운데 오픈 소스 도구로 구성할 수 있는 범위부터 검토할 계획입니다.

후속 개발 도구의 진행 상태를 기준일과 함께 남깁니다.

> 2026년 9월 6일 현재 후속 개발 도구에는 아직 착수하지 않았습니다. 착수 시점과 세부 기능은 향후 검토를 거쳐 구체화할 예정입니다.

이번 확장에서 마련한 디버거 통합과 플랫폼별 검증 경험은 후속 작업의 출발점으로 삼을 수 있습니다. 솔루션 관리와 테스트 실행까지 연결하려면 기존 오픈 소스 구성 요소의 역할과 라이선스를 따로 조사하고 실제 편집기에서의 동작도 검증할 예정입니다. 후속 작업에서도 AI를 조사와 구현에 활용하고 실행 결과를 근거로 공개할 기능과 지원 범위를 정해 나가고자 합니다.

## 검증한 범위에서 시작하는 별도 C# 배포

여기까지 정리하면 이번 프로젝트에서는 커뮤니티가 마련해 온 대안에 감사를 표하며, AI를 활용해 최신 .NET 개발 환경을 더 넓게 전달하려는 취지를 실제 배포로 연결했습니다. 상류 C# 확장과 netcoredbg의 소스를 조합하고 검증한 플랫폼별 파일을 반복해서 출시하는 운영 경로를 마련했습니다. [첫 릴리스 기록](https://github.com/rkttu/vscode-csharp-autobuild/blob/main/docs/research/2026-09-06-first-release.md)은 기능 검사와 공개 파일 확인 결과, 남은 한계를 함께 보존합니다.

현재 설치할 패키지는 [Open VSX의 C# (with netcoredbg)](https://open-vsx.org/extension/dotnetdev-kr-custom/csharp-with-netcoredbg)에서 선택할 수 있습니다. 기존 상류 동작의 유지를 우선한다면 원래 배포를 계속 사용할 수 있고, netcoredbg 통합판을 선택한다면 기록한 플랫폼과 기능 범위를 기준으로 판단할 수 있습니다. 당장의 운영에서는 새 태그와 런타임, 컴파일러 변화에 같은 검증을 반복하고 실패 원인을 조사합니다. VS Code OSS 기반 개발 도구는 다음 기회에 착수를 검토할 장기 구상으로 두고, 이번 확장은 공개한 지원 범위 안에서 유지해 나가겠습니다.

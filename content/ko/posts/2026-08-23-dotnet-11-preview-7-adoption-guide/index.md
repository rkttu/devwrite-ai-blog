---
title: "출시를 앞둔 .NET 11의 변경 사항과 도입 판단"
date: 2026-08-23T00:52:15+09:00
draft: false
slug: "dotnet-11-preview-7-adoption-guide"
tags:
  - .NET
  - .NET 11
  - C# 15
  - ASP.NET Core
  - Entity Framework Core
categories:
  - .NET 개발
translationKey: "dotnet-11-preview-7-adoption-guide"
description: ".NET 11 Preview 7의 지원 주기, 하드웨어 기준선, Runtime Async, C# 15와 프레임워크 변화를 바탕으로 도입 판단 기준을 정리합니다."
cover:
  image: "images/posts/dotnet-11-preview-7-adoption-guide.webp"
  alt: "닷넷봇이 반투명한 숫자 11을 향해 날아가는 밝은 보라색 일러스트레이션"
tldr: ".NET 11은 STS 지원 기간보다 x86-64-v2 기준선, Runtime Async, SDK 기본 동작과 C# 15의 변화가 도입 판단에 더 큰 영향을 줍니다. .NET 10을 운영 중이라면 지원 기간보다 기능과 검증 비용을 기준으로 비교할 수 있습니다."
license: "CC BY-NC 4.0"
---

Microsoft는 .NET 11 정식 버전을 2026년 11월 10일에 출시할 예정입니다. 2026년 8월 23일 현재 Microsoft는 8월 11일에 공개한 .NET 11 Preview 7을 최신 빌드로 제공합니다. Microsoft는 런타임과 SDK, C# 15, ASP.NET Core, .NET MAUI, Entity Framework Core를 포함한 제품군 전반을 계속 다듬고 있습니다. 정식 출시 전까지 기능과 동작이 달라질 가능성도 남아 있습니다. [Microsoft의 .NET 11 Preview 7 발표](https://devblogs.microsoft.com/dotnet/dotnet-11-preview-7/)

이 글에서는 .NET 11의 변화를 지원 주기, 하드웨어 기준선, 런타임과 개발 도구, C# 15, 응용 프레임워크라는 다섯 가지 축으로 정리합니다. 기능의 수보다 기존 서비스를 옮길 때 영향을 받는 지점을 중심에 두었습니다.

먼저 지원 주기와 실행 환경을 다룬 뒤 Runtime Async와 SDK로 범위를 옮깁니다. 이어서 C# 15의 타입 모델과 ASP.NET Core, EF Core의 주요 기능을 검토합니다. 마지막에는 정식 출시 전에 적용할 수 있는 점검 절차를 제시합니다.

이 글은 아래 기준일에 공개된 미리 보기 자료를 토대로 작성했습니다.

> 기준일: 2026년 8월 23일
>
> 대상 버전: .NET 11 Preview 7, SDK 11.0.100-preview.7
>
> 상태: 미리 보기 기능과 호환성 변경 목록은 정식 출시 전까지 달라질 수 있습니다. 미리 보기 빌드는 일반적으로 프로덕션 사용을 지원하지 않습니다.

## 지원 기간을 늘리지 않는 STS 릴리스

.NET 11의 지원 주기부터 정리하겠습니다. Microsoft는 .NET 11을 STS로 분류하고 2026년 11월 10일부터 2028년 11월 9일까지 2년간 지원할 계획입니다. LTS와 STS는 품질 수준이 같고 지원 기간만 다릅니다. LTS는 3년, STS는 2년간 패치와 기술 지원을 제공합니다. 이 일정은 [.NET 11 릴리스 계획](https://github.com/dotnet/core/blob/main/release-notes/11.0/README.md)과 [.NET 지원 정책](https://dotnet.microsoft.com/en-us/platform/support/policy)에서 확인할 수 있습니다.

현재 버전별 일정을 함께 놓으면 업그레이드 판단 기준이 드러납니다.

| 버전 | 릴리스 유형 | 정식 출시일 | 지원 종료일 |
| --- | --- | --- | --- |
| .NET 8 | LTS | 2023년 11월 14일 | 2026년 11월 10일 |
| .NET 9 | STS | 2024년 11월 12일 | 2026년 11월 10일 |
| .NET 10 | LTS | 2025년 11월 11일 | 2028년 11월 14일 |
| .NET 11 | STS | 2026년 11월 10일 예정 | 2028년 11월 9일 예정 |

.NET 10 LTS에서 .NET 11로 옮겨도 지원 종료일이 늘어나지 않습니다. 오히려 현재 계획으로는 .NET 11의 지원이 닷새 먼저 끝납니다. .NET 10을 운영 중인 팀이라면 새 기능과 성능, 개발 경험이 마이그레이션 비용을 상쇄하는지를 기준으로 판단할 수 있습니다. .NET 8이나 .NET 9를 운영 중이라면 두 버전의 지원이 .NET 11 출시 예정일에 끝나므로 .NET 10과 .NET 11을 함께 후보로 놓고 검토할 수 있습니다.

## 기존 장비에 영향을 주는 하드웨어 기준선

.NET 11은 x86/x64의 JIT 및 AOT 최소 기준을 모든 운영체제에서 `x86-64-v1`에서 `x86-64-v2`로 상향합니다. `SSE3`, `SSSE3`, `SSE4.1`, `SSE4.2`, `POPCNT` 같은 명령어를 지원하지 않는 CPU에서는 .NET 11 애플리케이션이 실행되지 않습니다. [.NET 11 런타임의 최소 하드웨어 요구 사항](https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-11/runtime#updated-minimum-hardware-requirements)

ReadyToRun 대상도 운영체제에 따라 달라집니다.

| 운영체제 | x86/x64 JIT 및 AOT 최소 기준 | ReadyToRun 대상 |
| --- | --- | --- |
| macOS | `x86-64-v2` | `x86-64-v2` |
| Linux | `x86-64-v2` | `x86-64-v3` |
| Windows | `x86-64-v2` | `x86-64-v3` |

Linux와 Windows의 ReadyToRun 대상이 `x86-64-v3`로 올라가지만 실행 최소 기준은 `v2`를 유지합니다. `v2`를 지원하는 장비에서도 실행할 수 있습니다. 다만 미리 컴파일된 코드를 사용할 수 없는 구간에서 JIT 컴파일이 늘어 시작 시간이 길어질 수 있습니다.

Arm64에서는 Apple과 Linux의 실행 최소 기준이 유지됩니다. Windows Arm64는 `LSE` 명령어를 요구하고 ReadyToRun 대상을 `armv8.2-a + RCPC`로 상향합니다. 최근 클라우드 인스턴스에서는 영향이 제한적일 가능성이 크지만 오래된 사내 서버, 엣지 장비, 고객사 설치형 제품은 별도 확인 대상으로 남습니다.

## 비동기 실행과 개발 도구의 기본 동작 변화

런타임과 SDK의 실행 경로를 살펴보겠습니다. Runtime Async는 비동기 메서드의 중단과 재개를 런타임으로 옮기고, SDK는 NativeAOT CLI와 MSBuild 서버를 기본 경로에 배치합니다. 두 변화 모두 애플리케이션 코드를 크게 바꾸지 않아도 실행과 빌드 과정에 영향을 줄 수 있습니다.

### 비동기 실행을 런타임으로 옮기는 Runtime Async

기존 C# 컴파일러는 `async` 메서드마다 상태 머신을 생성합니다. Runtime Async V2는 중단과 재개 상태를 런타임에서 관리합니다. Microsoft는 이 구조를 통해 라이브 호출 스택을 간결하게 만들고 디버깅 경험과 실행 오버헤드를 개선하려고 합니다. [.NET 11 Runtime Async 설명](https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-11/runtime#runtime-async)

현재 애플리케이션 코드에서 Runtime Async를 시험하려면 프로젝트 파일에 다음 설정을 추가합니다.

```xml
<PropertyGroup>
  <Features>runtime-async=on</Features>
</PropertyGroup>
```

`net11.0` 프로젝트에서는 `EnablePreviewFeatures`를 별도로 켜지 않아도 이 기능을 사용할 수 있습니다. .NET 11 런타임 라이브러리 자체도 Runtime Async를 적용해 빌드합니다. 애플리케이션 코드에서는 여전히 기능을 명시적으로 켭니다.

공개된 예시에서는 라이브 호출 스택에서 컴파일러 상태 머신 프레임이 줄고 실제 메서드 호출 관계가 더 잘 드러납니다. 예외 객체에 기록되는 스택 추적은 기존 방식에서도 정리되므로 차이가 없습니다. NativeAOT와 ReadyToRun도 Runtime Async를 지원합니다. 처리량과 할당량 개선 폭은 애플리케이션의 비동기 호출 패턴에 따라 달라집니다. 대상 서비스의 부하 시험 결과를 기준으로 정식 도입을 판단할 수 있습니다.

### 반복 작업을 줄이는 SDK와 테스트 도구

Preview 7은 NativeAOT 기반 `dotnet` CLI 경로와 MSBuild 서버를 기본으로 켰습니다. 또한 Microsoft.Testing.Platform을 사용하는 `dotnet test`에 실행 전체를 제어하는 옵션을 추가했습니다. [.NET 11 SDK와 도구 변경 사항](https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-11/sdk)

- **NativeAOT CLI 경로**: `dotnet --info`, 도움말, 일부 `dotnet sln` 명령, 도구 검색과 실행은 NativeAOT 경로를 사용합니다. `build`, `run`, `test`, `pack`, `publish`처럼 MSBuild나 NuGet을 프로세스 안에서 사용하는 명령은 관리형 CLI로 돌아갑니다.

- **기본 MSBuild 서버**: SDK는 준비된 MSBuild 작업자 프로세스를 명령 사이에 유지합니다. 연속해서 실행하는 `dotnet build`, `dotnet test`, `dotnet run`은 MSBuild 시작 비용을 줄일 수 있습니다. 커스텀 빌드 태스크가 프로세스 격리를 전제로 한다면 `DOTNET_CLI_USE_MSBUILD_SERVER=false`로 기존 동작과 비교할 수 있습니다.

- **테스트 실행 정책**: Microsoft.Testing.Platform 모드에서는 `dotnet test --timeout 90s`와 `dotnet test --maximum-failed-tests 5`처럼 전체 실행의 시간과 실패 수를 제한할 수 있습니다. `Microsoft.Build.Traversal` 프로젝트도 테스트 대상을 모아 실행할 수 있습니다.

- **로컬 컨테이너 선택**: SDK의 컨테이너 게시 기능은 Windows에서 `wslc`, macOS에서 `container`를 먼저 찾습니다. Docker와 Podman은 그다음 후보로 이동합니다. 빌드 환경에서 특정 엔진 동작에 의존한다면 `LocalRegistry` 속성으로 대상을 고정할 수 있습니다.

이 변화들은 SDK만 교체한 비교 시험에서도 빌드 시간과 프로세스 수, 커스텀 태스크의 상태 유지 여부를 함께 기록해야 원인을 구분할 수 있음을 보여 줍니다.

## 닫힌 타입 집합을 표현하는 C# 15

C# 15의 타입 모델 변화를 짚어보겠습니다. 이번 버전은 컬렉션 식 인수, 유니언 타입, 닫힌 계층, 확장 인덱서, 레이블을 지정한 `break`와 `continue`, 메모리 안전성 작업을 포함합니다. 이 가운데 유니언 타입과 닫힌 계층은 컴파일러가 가능한 타입의 집합을 파악하고 `switch`의 완전성을 검사할 수 있게 합니다. [C# 15의 새로운 기능](https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-15)

유니언 타입으로 결제 결과를 표현하면 다음과 같이 모든 경우를 나눌 수 있습니다.

```csharp
public record Paid(string TransactionId);
public record Declined(string Reason);
public record Pending(DateTimeOffset RetryAt);

public union PaymentResult(Paid, Declined, Pending);

static string Describe(PaymentResult result) => result switch
{
    Paid paid => $"승인: {paid.TransactionId}",
    Declined declined => $"거절: {declined.Reason}",
    Pending pending => $"재시도: {pending.RetryAt:O}",
};
```

`closed` 한정자는 같은 어셈블리 안에서만 직접 파생 타입을 선언할 수 있게 합니다. 컴파일러가 직접 파생 타입을 모두 알 수 있으므로 기본 처리 항목이 없는 `switch`도 완전성을 검사합니다. 닫힘은 자동으로 하위 계층 전체에 전파되지 않습니다. 중간 타입 아래까지 제한하려면 해당 타입에도 `closed`를 지정합니다.

유니언 타입 명세의 일부 기능은 Preview 7에도 아직 구현되지 않았습니다. 메모리 안전성 개선도 여러 릴리스에 걸쳐 진행할 계획입니다. C# 15 기능을 제품 코드에 반영할 때에는 현재 구문을 최종 사양으로 간주하지 않고 정식 컴파일러와 호환성 문서를 다시 대조할 여지가 있습니다.

## 응용 계층에서 체감하는 라이브러리와 프레임워크 변화

응용 계층의 개선은 작업 부하별로 나누어 보겠습니다. .NET 11 기본 라이브러리는 프로세스 실행, 압축, 직렬화, 진단, 수치 연산을 넓힙니다. ASP.NET Core와 EF Core도 서버 자원 관리와 쿼리 변환을 보완합니다. [.NET 11 전체 변경 사항](https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-11/overview)

- **기본 라이브러리**: `Process`에 실행과 출력 수집을 다루는 API가 추가됩니다. `System.IO.Compression`은 Zstandard 압축과 ZIP 암호, CRC32 검증을 지원합니다. `System.Text.Json`은 C# 유니언 타입 직렬화와 닫힌 타입 계층의 다형성 추론을 지원합니다. IEEE 754 10진 부동소수점 타입과 제네릭 `Complex<T>`도 수치 처리 범위를 넓힙니다. [.NET 11 Preview 7 라이브러리 릴리스 노트](https://github.com/dotnet/core/blob/main/release-notes/11.0/preview/preview7/libraries.md)

- **ASP.NET Core**: Blazor Interactive Server는 숨겨진 브라우저 탭의 회로를 일정 시간이 지난 뒤 멈추고 사용자가 돌아오면 재개할 수 있습니다. 이 기능은 별도 패키지와 설정으로 활성화합니다. Blazor SSR 출력 캐시, 검증 메시지 현지화, OpenAPI 3.2의 Server-Sent Events 표현도 Preview 7에 들어왔습니다. [ASP.NET Core Preview 7 릴리스 노트](https://github.com/dotnet/core/blob/main/release-notes/11.0/preview/preview7/aspnetcore.md)

- **Entity Framework Core**: SQL Server 공급자는 `int.Parse`와 여러 숫자 파싱 메서드를 서버의 `CAST`로 변환합니다. 참조 탐색을 거치는 `GroupBy` 집계는 상관 서브쿼리 대신 하나의 조인과 그룹화로 변환할 수 있습니다. 기존 쿼리의 SQL 형태가 달라질 수 있으므로 실제 데이터 분포에서 실행 계획과 수행 시간을 비교할 만합니다. [EF Core Preview 7 릴리스 노트](https://github.com/dotnet/core/blob/main/release-notes/11.0/preview/preview7/efcore.md)

모든 애플리케이션이 이 기능을 같은 비중으로 활용하지는 않습니다. 압축 파일을 교환하는 서비스는 ZIP 검증 동작을 먼저 볼 수 있고 Blazor Server 서비스는 회로 중단이 메모리 사용량에 미치는 영향을 측정할 수 있습니다. 데이터 접근 비중이 큰 서비스는 EF Core가 생성한 SQL을 기존 버전과 비교하는 방식으로 범위를 좁힐 수 있습니다.

## 정식 출시 전 점검 항목

정식 출시 전 검증 절차를 확인하겠습니다. Microsoft가 공개한 [.NET 11 호환성 변경 목록](https://learn.microsoft.com/en-us/dotnet/core/compatibility/11)은 아직 작성 중이며 완전한 목록이 아닙니다. 따라서 Preview 7 시험 결과와 정식 버전의 결과가 같다고 전제하지 않습니다.

1. 운영 서버와 빌드 에이전트, 고객사 장비의 CPU 명령어 지원 범위를 수집합니다.
2. 격리한 시험 환경에서 SDK `11.0.100-preview.7`을 고정하고 기존 소스의 빌드 경고와 테스트 결과를 기록합니다.
3. MSBuild 서버를 켠 상태와 끈 상태에서 연속 빌드 시간과 커스텀 태스크 동작을 비교합니다.
4. 비동기 호출이 많은 서비스에 한해 Runtime Async를 적용하고 처리량, 지연 시간, 할당량, 라이브 호출 스택을 기존 방식과 비교합니다.
5. ASP.NET Core와 EF Core 애플리케이션은 생성한 OpenAPI 문서, 인증 흐름, 주요 LINQ 쿼리의 SQL과 실행 계획을 대조합니다.
6. 압축, 인증서, 파일과 파이프, 호스팅 종료 동작과 관련된 호환성 변경을 서비스 사용 범위와 연결합니다.
7. RC와 정식 버전이 나오면 미리 보기에서 사용한 기능의 상태와 호환성 목록을 다시 확인합니다.

## 지원 기간보다 실행 조건이 먼저 보이는 업그레이드

여기까지 정리하면 .NET 11은 비동기 실행 구조와 하드웨어 기준선, 타입 모델, 개발 도구의 기본 동작을 함께 손봅니다. API 추가만 보고 넘어가기에는 실행 환경과 빌드 경로의 변화가 큽니다.

장기 과제로는 Runtime Async와 C# 15가 향후 .NET 애플리케이션의 코드 생성과 타입 설계에 미칠 영향을 살펴볼 수 있습니다. 당장 영향을 주는 사안으로는 x86/x64 최소 기준 상향, MSBuild 서버와 NativeAOT CLI의 기본 활성화, 일부 라이브러리의 동작 변경이 앞에 놓입니다.

.NET 8이나 .NET 9를 운영하는 팀은 2026년 11월 10일의 지원 종료에 맞춰 .NET 10 LTS와 .NET 11 STS 중 어느 쪽으로 옮길지 정할 수 있습니다. .NET 10을 이미 운영한다면 지원 기간 때문에 서두를 이유는 적습니다. 오래된 장비나 설치형 제품을 다룬다면 CPU 기준선부터 조사하고 최신 클라우드 환경과 자동화된 시험 체계를 갖췄다면 Preview 7로 호환성 자료를 모으는 순서가 적합합니다.

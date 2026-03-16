---
title: ".NET의 새로운 장르: NuGet-Free Single File C# 코딩의 시대"
date: 2026-03-16T00:00:00+09:00
draft: false
slug: "nuget-free-single-file-csharp"
tags:
  - .NET
  - C#
  - File-Based App
  - Runtime Async
  - 성능 최적화
categories:
  - .NET 개발
translationKey: "nuget-free-single-file-csharp"
description: ".NET 10의 file-based app과 Runtime Async가 만나면, NuGet 없이 BCL만으로 빠르고 타입 안전한 단일 파일 C# 코딩이 가능해집니다."
cover:
  image: "images/posts/nuget-free-single-file-csharp.webp"
  alt: "단일 C# 파일로 실행되는 코드 개념 이미지"
tldr: "dotnet run file.cs의 BuildLevel.Csc 최적화와 Runtime Async의 결합으로, NuGet 패키지 없이 BCL만 사용하는 단일 파일 C# 프로그램이 반복 실행 200ms~630ms의 성능을 달성하며, Python의 편의성과 Go의 배포 단순성, C#의 타입 안전성을 결합한 새로운 코딩 장르가 열립니다."
---

> C#이 스크립트 언어처럼 가벼워지는 것이 아니라, 스크립트 언어가 부러워할 만큼 빨라지는 것이다.

## 들어가며

.NET 10에서 도입된 `dotnet run file.cs` — 이른바 **file-based app** — 은 `.csproj` 파일 없이 단일 `.cs` 파일만으로 C# 코드를 실행할 수 있게 해주는 기능입니다. 하지만 현재 이 기능의 실행 속도는 첫 실행 기준 Windows에서 약 1.5초, WSL2에서 약 0.8초 수준입니다. Python의 `python script.py`가 50ms 내외인 것과 비교하면 아직 "스크립팅"이라 부르기 민망한 수준이죠.

그런데 지금 .NET 생태계에서 동시에 진행 중인 두 가지 큰 변화가 이 그림을 근본적으로 바꿀 수 있습니다:

1. **`dotnet run file.cs`의 빌드 최적화** — MSBuild를 우회하여 Roslyn을 직접 호출하는 전략
2. **Runtime Async (async2)** — async/await를 런타임 수준에서 처리하여 상태 머신 오버헤드를 제거

이 두 가지가 만나면, **NuGet 패키지 없이 BCL만으로 작성하는 단일 파일 C# 프로그램** 이 하나의 독립적인 코딩 장르로 자리잡을 수 있습니다. 이 글에서는 그 기술적 기반과 미래상을 그려봅니다.

---

## File-Based App의 현재: MSBuild라는 병목

### 본질: `.csproj` + `.cs` = 하나의 `.cs`

File-based app은 C# 스크립트(`.csx`)와 근본적으로 다릅니다. `.csx`는 별도의 스크립트 호스트가 런타임에 해석하지만, file-based app은 **컴파일 타임에 가상 `.csproj`로 변환** 되어 정규 빌드 파이프라인을 거칩니다. 결과물은 일반 프로젝트와 동일한 managed DLL입니다.

```cs
// 이 디렉티브들이 곧 .csproj의 내용
#:package System.CommandLine@2.0.0

// 여기서부터가 실제 코드
Console.WriteLine("Hello, file-based app!");
```

### 문제: MSBuild의 무게

`dotnet run hello.cs`를 실행하면 내부적으로 벌어지는 일:

| 단계 | 소요 시간(대략) | 설명 |
| ------ | --------------- | ------ |
| CLI 로드 | ~200ms | .NET 런타임 JIT, CLI 명령 디스패치 |
| MSBuild 엔진 로드 | ~200ms | 빌드 엔진 초기화 |
| SDK targets 평가 | ~300ms | 수백 개의 `.props`/`.targets` 파일 순차 평가 |
| NuGet restore | ~100ms+ | 패키지 의존성 해결 (캐시된 경우) |
| Roslyn 컴파일 | ~200ms | 실제 C# → IL 변환 |
| 실행 | ~50ms | 결과 DLL 실행 |

**총 ~1.5초** 중 실제 "컴파일 + 실행"은 ~250ms에 불과합니다. 나머지는 전부 MSBuild 관련 오버헤드입니다.

---

## MSBuild를 우회하는 전략: `BuildLevel.Csc`

dotnet/sdk 팀은 이 병목을 인식하고, **MSBuild를 아예 건너뛸 수 있는 경우를 식별하여 Roslyn 컴파일러를 직접 호출** 하는 최적화 경로를 구현했습니다.

### 세 단계의 빌드 레벨

```text
dotnet run hello.cs
       │
       ▼
  입력 변경 감지
       │
  ┌────┼────────────┐
  ▼    ▼            ▼
None  Csc          All
  │    │            │
  ▼    ▼            ▼
스킵  csc만 호출   MSBuild 풀 빌드
~200ms ~400-630ms  ~1.5s
```

- **`BuildLevel.None`**: 아무것도 변하지 않았으므로 이전 빌드 결과를 그대로 실행
- **`BuildLevel.Csc`**: `.cs` 코드만 바뀌었으므로 Roslyn 컴파일러 서버에 직접 요청 — **MSBuild 완전 우회**
- **`BuildLevel.All`**: 패키지나 SDK 설정이 바뀌었으므로 MSBuild 풀 빌드 실행

### `BuildLevel.Csc`의 조건

이 빠른 경로를 타려면:

- ✅ `#:package` 디렉티브가 없거나 변경 없음
- ✅ `#:sdk` 디렉티브가 없거나 변경 없음
- ✅ `Directory.Build.props` 등 implicit build file 없음
- ✅ `-c Release` 같은 글로벌 프로퍼티 커스터마이징 없음
- ✅ 이전 빌드의 캐시된 컴파일러 인자(`.rsp`)가 존재

이 모든 조건을 충족하면, SDK는 가상 프로젝트 파일을 만들지도, MSBuild를 로드하지도 않고, 캐시된 `.rsp` 파일을 들고 **Roslyn 컴파일러 서버에 직접 named pipe로 요청** 을 보냅니다.

```cs
// CSharpCompilerCommand.cs에서 실제로 일어나는 일
var buildRequest = BuildServerConnection.CreateBuildRequest(
    requestId: EntryPointFileFullPath,
    language: RequestLanguage.CSharpCompile,
    arguments: ["/noconfig", "/nologo", $"@{rspPath}"],
    workingDirectory: BaseDirectory,
    tempDirectory: Path.GetTempPath(),
    ...);

var pipeName = BuildServerConnection.GetPipeName(clientDirectory: ClientDirectory);
var responseTask = BuildServerConnection.RunServerBuildRequestAsync(buildRequest, pipeName, ...);
```

### 이것은 미니 빌드 시스템이다

`CSharpCompilerCommand`는 이미 MSBuild가 하던 일의 일부를 C# 하드코딩으로 재구현합니다:

- AssemblyAttributes.cs 생성
- GlobalUsings.g.cs 생성
- AssemblyInfo.cs 생성
- EditorConfig 생성
- AppHost 바이너리 패치
- RuntimeConfig.json 생성
- 컴파일러 응답 파일(.rsp) 생성

이것은 "MSBuild가 한 번 해준 결과를 캐시해서 재사용한다"는 전략이지, MSBuild를 대체하는 것이 아닙니다. 첫 실행은 반드시 MSBuild를 거치고, 구조적 변경이 있으면 다시 MSBuild로 돌아갑니다.

### 설계의 핵심 긴장

SDK 팀은 이 우회 범위를 의도적으로 좁게 유지하고 있습니다:

```cs
// Release 빌드만 붙여도 MSBuild로 돌아감
// Note that Release builds won't go through this optimized code path because
// `-c Release` translates to global property `Configuration=Release`
// and customizing global properties triggers a full MSBuild run.
```

왜? 우회 범위를 넓히면 넓힐수록 **file-based app만을 위한 별도 빌드 시스템** 을 만드는 격이 되고, MSBuild와 행동이 달라질 가능성이 커지기 때문입니다. File-based app의 핵심 원칙 — "프로젝트로 전환(grow-up)했을 때 동일하게 동작해야 한다" — 이 깨질 수 있습니다.

---

## Runtime Async: async/await의 근본적 재설계

### 현재의 async/await: 컴파일러가 만드는 상태 머신

현재 C#의 `async/await`는 **컴파일러(Roslyn)** 가 처리합니다. `async` 메서드를 작성하면 컴파일러가 이것을 상태 머신 구조체로 변환하고, `IAsyncStateMachine.MoveNext()`를 생성합니다.

```cs
// 여러분이 작성하는 코드
async Task<int> FetchDataAsync()
{
    var data = await httpClient.GetStringAsync(url);
    return data.Length;
}

// 컴파일러가 실제로 만드는 코드 (단순화)
struct <FetchDataAsync>d__0 : IAsyncStateMachine
{
    public int <>1__state;
    public AsyncTaskMethodBuilder<int> <>t__builder;
    public TaskAwaiter<string> <>u__1;

    public void MoveNext()
    {
        switch (<>1__state)
        {
            case 0: goto Label_Await;
            // ...
        }
        // 실제 로직...
    }
}
```

이 방식의 비용:

- **상태 머신 구조체 할당** (hot path에서도)
- **`MoveNext()` 호출 오버헤드**
- **ExecutionContext 캡처/복원**
- **IL 코드 크기 증가** (상태 머신 보일러플레이트)

### Runtime Async: 런타임이 직접 처리

.NET 10에서 실험적으로 도입되고 .NET 11에서 본격 활성화될 **Runtime Async** 는 이 전체 구조를 뒤집습니다. 컴파일러가 상태 머신을 만드는 대신, **JIT 컴파일러와 VM이 직접 async 메서드의 중단/재개를 처리** 합니다.

ECMA-335 명세에 새로운 메서드 속성이 추가됩니다:

```text
MethodImplOptions.Async = 0x2000
```

그리고 `await`는 더 이상 컴파일러 마법이 아니라, 런타임이 인식하는 **suspension point** 가 됩니다:

```cs
// 런타임이 인식하는 await 패턴
namespace System.Runtime.CompilerServices
{
    public static class AsyncHelpers
    {
        [MethodImpl(MethodImplOptions.Async)]
        public static T Await<T>(Task<T> task);

        [MethodImpl(MethodImplOptions.Async)]
        public static void Await(ValueTask task);
        // ...
    }
}
```

### 핵심 메커니즘: Method Variant Pairs

Runtime Async의 구현에서 가장 중요한 개념은 **variant pairs** 입니다. `Task`를 반환하는 모든 메서드에 대해 런타임이 자동으로 두 개의 진입점을 생성합니다:

- **Task-returning variant**: 기존과 동일한 `Task<T>` 반환 시그니처
- **Async variant**: `T`를 직접 반환하되, 중단이 필요한 경우 Continuation 객체를 통해 처리하는 새로운 호출 규약

async → async 호출 체인에서 중단이 발생하지 않으면(hot path), **Task 객체를 아예 할당하지 않고 값을 직접 반환** 합니다. 이것이 극적인 성능 개선의 핵심입니다.

### 실측 벤치마크에서의 의미

```text
현재 (async1): async 메서드 호출 → 상태 머신 할당 → Task 할당 → await
Runtime Async:  async 메서드 호출 → (동기 완료 시) 값 직접 반환, Task 할당 없음
```

.NET 팀의 실험 결과에 따르면, Runtime Async는 **기존 compiler-async와 최소 동등하거나 더 나은 성능** 을 보여주었습니다. 특히:

- **동기 완료(suspension 없음) 경로**: 상태 머신과 Task 할당이 완전히 제거되어 일반 메서드 호출과 거의 동일한 비용
- **IL 코드 크기**: 상태 머신 보일러플레이트가 사라져 크게 감소
- **완전한 호환성**: 기존 async1과 drop-in replacement 가능

---

## 두 변화의 합류: NuGet-Free Single File App의 부상

### 성능 스펙트럼

두 최적화가 모두 적용된 후의 예상 성능:

| 시나리오 | 현재 | BuildLevel.Csc | + Runtime Async |
| --------- | ------ | ---------------- | ----------------- |
| 첫 실행 (`dotnet run hello.cs`) | ~1.5s | ~1.5s (첫 실행은 동일) | ~1.5s |
| 반복 실행 (코드 변경) | ~1.5s | **~400-630ms** | **~400-630ms** |
| 반복 실행 (변경 없음) | ~1.5s | **~200ms** | **~200ms** |
| async 호출 체인 성능 | 기준 | 기준 | **대폭 개선** |

`BuildLevel.Csc`는 빌드 시간을, Runtime Async는 실행 시간 중 async 관련 오버헤드를 줄입니다. 두 개선은 **직교(orthogonal)** 하여, 합산 효과를 냅니다.

### NuGet-Free의 조건이 곧 최적 경로의 조건

`BuildLevel.Csc`의 혜택을 최대한 받으려면:

- `#:package` 없음 → NuGet restore 불필요
- `#:sdk` 변경 없음 → SDK targets 재평가 불필요
- implicit build file 없음 → MSBuild 프로퍼티 재평가 불필요

이 조건을 만족하는 코드는 정확히 **NuGet 패키지에 의존하지 않는 코드** 입니다. 그리고 .NET BCL이 이미 제공하는 것만으로도 놀랍도록 많은 일을 할 수 있습니다:

```cs
// ✅ 전부 BCL만으로 가능한 것들

using System.Net.Http;                      // HTTP 클라이언트
using System.Text.Json;                     // JSON 직렬화/역직렬화
using System.Text.RegularExpressions;       // 정규식
using System.IO.Compression;                // ZIP, GZip
using System.Security.Cryptography;         // 해시, 암호화
using System.Threading.Channels;            // 생산자-소비자 패턴
using System.Collections.Concurrent;        // 동시성 컬렉션
using System.Xml.Linq;                      // XML 처리
using System.Diagnostics;                   // 프로세스 관리
using System.Net;                           // DNS, IP, 소켓
```

### 실용적인 사용 시나리오

#### **1. CLI 유틸리티**

```cs
#!/usr/bin/env dotnet run
// file: cleanup.cs

var targetDir = args.Length > 0 ? args[0] : ".";
var cutoff = DateTime.Now.AddDays(-30);

foreach (var file in Directory.EnumerateFiles(targetDir, "*.log", SearchOption.AllDirectories))
{
    if (File.GetLastWriteTime(file) < cutoff)
    {
        File.Delete(file);
        Console.WriteLine($"Deleted: {file}");
    }
}
```

#### **2. 간이 HTTP 서버 / API 테스트**

```cs
// file: api-check.cs

using var client = new HttpClient();
var endpoints = new[] {
    "https://api.example.com/health",
    "https://api.example.com/status",
};

await Parallel.ForEachAsync(endpoints, async (url, ct) =>
{
    try
    {
        var sw = Stopwatch.StartNew();
        var response = await client.GetAsync(url, ct);
        Console.WriteLine($"{url} → {response.StatusCode} ({sw.ElapsedMilliseconds}ms)");
    }
    catch (Exception ex)
    {
        Console.WriteLine($"{url} → FAILED: {ex.Message}");
    }
});
```

Runtime Async가 적용되면, 이 `Parallel.ForEachAsync` + `await` 체인에서 동기 완료되는 호출은 상태 머신 할당 없이 처리됩니다.

#### **3. JSON 데이터 변환 파이프라인**

```cs
// file: transform.cs

using System.Text.Json;

var input = args.Length > 0 ? File.ReadAllText(args[0]) : Console.In.ReadToEnd();
var doc = JsonDocument.Parse(input);

var result = doc.RootElement.EnumerateArray()
    .Where(e => e.GetProperty("status").GetString() == "active")
    .Select(e => new {
        Id = e.GetProperty("id").GetInt32(),
        Name = e.GetProperty("name").GetString(),
    });

Console.WriteLine(JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true }));
```

#### **4. 시스템 관리 자동화**

```cs
// file: sysinfo.cs

using System.Runtime.InteropServices;

Console.WriteLine($"OS: {RuntimeInformation.OSDescription}");
Console.WriteLine($"Architecture: {RuntimeInformation.OSArchitecture}");
Console.WriteLine($"Framework: {RuntimeInformation.FrameworkDescription}");
Console.WriteLine($"Processors: {Environment.ProcessorCount}");
Console.WriteLine($"Memory: {GC.GetGCMemoryInfo().TotalAvailableMemoryBytes / 1024 / 1024:N0} MB");
Console.WriteLine($"Host: {Environment.MachineName}");
Console.WriteLine($"User: {Environment.UserName}");
```

### NuGet을 넘는 순간

NuGet 없이 BCL만으로는 커버되지 않는 영역이 있습니다:

| 필요한 기능 | 상태 |
| ----------- | ------ |
| 데이터베이스 (Npgsql, Dapper) | ❌ `#:package` 필요 → `BuildLevel.All` |
| 클라우드 SDK (Azure, AWS) | ❌ `#:package` 필요 |
| 웹 프레임워크 (ASP.NET Core) | ❌ `#:sdk Microsoft.NET.Sdk.Web` 필요 |
| 고급 CLI 파싱 | ❌ `#:package System.CommandLine` 필요 |
| 테스트 프레임워크 | ❌ `#:package` 필요 |

이 경계를 넘으면 `BuildLevel.Csc`의 혜택이 사라지고, ~1.5초의 MSBuild 풀 빌드로 돌아갑니다. 이것이 자연스럽게 **"NuGet-free single file"과 "프로젝트 기반 앱" 사이의 경계선** 을 그어줍니다.

---

## Runtime Async가 File-Based App에 가져올 미래

### 코드 크기 감소

현재 `async` 메서드는 컴파일러가 상태 머신으로 변환하면서 IL 크기가 크게 증가합니다. Runtime Async는 이 변환을 JIT가 담당하므로, **IL 수준의 코드 크기가 줄어듭니다**. File-based app에서 이것은:

- 더 빠른 컴파일 (처리할 IL이 줄어듦)
- 더 작은 출력 바이너리
- `dotnet publish file.cs`로 만드는 Native AOT 바이너리 크기 감소

### Hot Path 최적화

Runtime Async의 variant pair 메커니즘은 async 메서드 체인에서 **동기 완료 경로를 극적으로 최적화** 합니다. NuGet-free single file app에서 흔한 패턴:

```cs
// 대부분의 HTTP 요청은 "이미 완료된" 결과를 반환
async Task<string> GetCachedDataAsync(string key)
{
    if (cache.TryGetValue(key, out var value))
        return value;  // ← 동기 경로: Task 할당 없음!

    var data = await FetchFromSourceAsync(key);
    cache[key] = data;
    return data;
}
```

현재는 이 메서드가 호출될 때마다 상태 머신 구조체가 생성됩니다. Runtime Async에서는 캐시 히트 시 **일반 메서드 호출과 동일한 비용** 으로 처리됩니다.

### `dotnet publish file.cs` + Native AOT

File-based app을 `dotnet publish`하면 Native AOT로 컴파일하여 **의존성 없는 단일 네이티브 바이너리** 를 생성할 수 있습니다. Runtime Async와 결합하면:

```bash
$ dotnet publish hello.cs
# → hello (Linux) / hello.exe (Windows)
# 단일 네이티브 바이너리, Go의 go build와 동일한 경험
```

이것은 Go나 Rust가 제공하는 "컴파일 → 단일 바이너리" 경험과 사실상 동일합니다. 하지만 C#의 풍부한 BCL과 async/await의 인체공학적 우위가 더해집니다.

---

## 비교: 다른 언어 생태계와의 위치

| | Python | Go | C# (NuGet-free file-based) |
| --- | -------- | ----- | --------------------------- |
| 단일 파일 실행 | ✅ `python script.py` | ❌ (패키지 필요) | ✅ `dotnet run script.cs` |
| 반복 실행 속도 | ~50ms | N/A (컴파일 필요) | ~200-600ms |
| 타입 안전성 | ❌ 동적 타입 | ✅ 정적 타입 | ✅ 정적 타입 |
| 비동기 지원 | `asyncio` (제한적) | goroutine | `async/await` (runtime-native) |
| 단일 바이너리 배포 | ❌ (PyInstaller 등 필요) | ✅ `go build` | ✅ `dotnet publish` + AOT |
| 표준 라이브러리 풍부함 | ★★★★☆ | ★★★★★ | ★★★★★ |
| 생태계 패키지 접근 | pip | go mod | #:package (NuGet) |

Python보다 첫 실행이 느리지만, 타입 안전성과 성능(특히 async 시나리오)에서 압도적 우위. Go와 유사한 단일 바이너리 배포가 가능하면서, 더 풍부한 async/await 지원.

---

## 남은 과제와 한계

### MSBuild라는 천장

모든 최적화에도 불구하고, file-based app은 근본적으로 MSBuild(SDK) 환경 위에 세워져 있습니다. MSBuild는 .NET 생태계의 정체성이나 다름없어서:

- NuGet 패키지 시스템이 MSBuild 아이템으로 설계됨
- SDK(`Microsoft.NET.Sdk`)가 MSBuild targets의 묶음임
- IDE 통합(VS, Rider, VS Code)이 MSBuild 프로젝트 평가에 의존

이것을 우회하는 범위를 확대하면 할수록, 사실상 **MSBuild의 열화 복제본** 을 만드는 격이 됩니다. SDK 팀은 이 함정을 인식하고, "확실히 안전한 범위 안에서만 우회하고, 조금이라도 불확실하면 MSBuild로 돌아간다"는 보수적 전략을 취하고 있습니다.

### Rust로 재작성해도 달라지지 않는 문제

Python/Node.js 생태계에서 Rust 기반 도구(uv, Bun 등)가 극적인 성능 개선을 보여준 것은 사실이지만, .NET의 빌드 성능 문제는 성격이 다릅니다. pip이나 npm이 느렸던 것은 "느린 런타임 위의 단순 I/O 작업"이었기 때문이고, MSBuild가 느린 것은 "하는 일 자체가 많기" 때문입니다. 빌드 엔진을 Rust로 재작성해도, 수백 개 targets 파일을 순차 평가하는 그 작업량은 변하지 않습니다.

그래서 SDK 팀의 전략 — 느린 경로를 빠르게 만드는 대신, **느린 경로를 아예 안 타게 하는 것** — 이 이 문제에 대한 가장 현실적인 해법입니다.

### Runtime Async의 성숙도

Runtime Async는 아직 활발히 개발 중이며, ReadyToRun 이미지에 async2 메서드를 컴파일하는 것은 아직 지원되지 않습니다. SynchronizationContext 처리, Reflection과의 호환성 등 해결해야 할 엣지 케이스가 남아 있습니다.

---

## 결론: 새로운 장르의 탄생

.NET 생태계에 **"프로젝트 기반의 정식 앱"과 "파일 하나짜리 가벼운 스크립트" 사이의 명확한 경계선** 이 성능 특성에 의해 자연스럽게 그어지고 있습니다. 그 경계선이 바로 **NuGet 의존성의 유무** 입니다.

NuGet 없이 BCL만으로 작성하는 코드는:

- ✅ `BuildLevel.Csc` 경로를 타서 빠르게 빌드
- ✅ Runtime Async로 async 코드가 더 빠르게 실행
- ✅ Native AOT로 단일 바이너리 배포 가능
- ✅ 프로젝트 파일 없이 `.cs` 하나로 완결

이것은 Python 스크립팅의 편의성, Go의 배포 단순성, 그리고 C#만의 타입 안전한 async/await를 결합한 **새로운 코딩 장르** 입니다. `.csproj`가 사라진 것이 아니라, `.csproj`가 필요하지 않은 영역이 명확하게 정의되고, 그 영역에서 최적의 개발 경험이 제공되는 것입니다.

```cs
#!/usr/bin/env dotnet run

// 이것이 NuGet-free single file C#의 미래입니다.
// 프로젝트 파일 없음. 패키지 의존성 없음.
// BCL만으로 충분한, 빠르고 타입 안전한 스크립팅.

var response = await new HttpClient().GetStringAsync("https://api.github.com/zen");
Console.WriteLine(response);
```

---

*이 글에서 다룬 기술들의 현재 상태:*

- *`dotnet run file.cs`: .NET 10에서 도입, 성능 최적화 진행 중 ([dotnet/sdk#48011](https://github.com/dotnet/sdk/issues/48011))*
- *Runtime Async: .NET 10에서 실험적 도입, .NET 11에서 활성화 예정 ([dotnet/runtime#94620](https://github.com/dotnet/runtime/issues/94620))*
- *`BuildLevel.Csc` 경로: dotnet/sdk의 `CSharpCompilerCommand`로 구현됨*

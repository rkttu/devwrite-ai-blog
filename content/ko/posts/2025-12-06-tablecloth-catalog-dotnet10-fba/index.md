---
title: "식탁보 프로젝트 카탈로그 빌더, .NET 10과 FBA로 현대화"
date: 2025-12-06T09:00:00+09:00
draft: false
slug: "tablecloth-catalog-dotnet10-fba"
tags:
  - 식탁보
  - .NET
  - 오픈소스
  - C#
categories:
  - 개발
translationKey: "tablecloth-catalog-dotnet10-fba"
description: "식탁보 프로젝트의 카탈로그 빌더가 .NET 10으로 업그레이드되고 File-Based App(FBA) 방식으로 단순화되었습니다."
tldr: ".csproj와 .sln 없이 단일 .cs 파일만으로 dotnet run --file로 바로 실행하는 .NET 10 FBA 방식과, Ctrl+C 두 번으로 안전하게 종료하는 Graceful Shutdown 구현을 다룹니다."
cover:
  image: "images/posts/tablecloth-catalog-dotnet10-fba.jpg"
  alt: "식탁보 프로젝트 카탈로그 빌더 업데이트"
---

## 식탁보 프로젝트란?

[식탁보(TableCloth)](https://github.com/yourtablecloth)는 한국의 인터넷 뱅킹 환경에서 필요한 보안 플러그인들을 Windows Sandbox 환경에서 안전하게 사용할 수 있도록 도와주는 오픈소스 프로젝트입니다. 다양한 금융 기관 웹사이트에서 요구하는 보안 프로그램들을 격리된 환경에서 실행하여 호스트 시스템의 안전을 보장합니다.

## 카탈로그 리포지토리란?

[TableClothCatalog](https://github.com/yourtablecloth/TableClothCatalog) 리포지토리는 식탁보 프로젝트에서 참조하는 금융 기관 사이트별 보안 프로그램 목록을 보관하는 저장소입니다. 각 은행, 증권사, 보험사 등의 웹사이트에서 요구하는 보안 플러그인 정보가 체계적으로 정리되어 있으며, 카탈로그 빌더 도구는 이 정보를 바탕으로 식탁보 앱에서 사용할 수 있는 형태로 가공합니다.

## 최근 카탈로그 빌더 업데이트

최근 이 리포지토리에 중요한 업데이트가 적용되었습니다. 이번 커밋에서는 카탈로그 빌더 도구가 .NET 10으로 업그레이드되고, 프로젝트 구조가 대폭 단순화되었습니다.

### 주요 변경 사항

#### .NET 10 업그레이드

```yaml
# 기존
dotnet-version: 8.0.x

# 변경
dotnet-version: 10.0.x
```

빌드 파이프라인이 .NET 8에서 .NET 10으로 업그레이드되었습니다. 이를 통해 최신 런타임의 성능 향상과 새로운 언어 기능을 활용할 수 있게 되었습니다.

#### File-Based App(FBA) 방식으로 전환

가장 눈에 띄는 변화는 프로젝트 구조의 단순화입니다. 기존에는 별도의 `.csproj` 프로젝트 파일과 솔루션 파일(`.sln`)을 사용했지만, 이번 업데이트에서는 이 파일들이 삭제되고 단일 C# 스크립트 파일(`catalogutil.cs`)로 통합되었습니다.

```csharp
#!/usr/bin/env dotnet
#:package IronSoftware.System.Drawing@2025.9.3
#:property PublishAot=false

using SixLabors.ImageSharp;
using SixLabors.ImageSharp.Formats.Png;
using System.Collections.Concurrent;
// ...
```

이것이 바로 .NET의 **File-Based App(FBA)** 방식입니다. FBA는 다음과 같은 장점을 제공합니다:

- **프로젝트 파일 불필요**: `.csproj` 없이 단일 `.cs` 파일로 애플리케이션 실행 가능
- **패키지 참조 인라인 선언**: `#:package` 지시문으로 NuGet 패키지 직접 참조
- **빌드 속성 인라인 설정**: `#:property` 지시문으로 빌드 속성 설정
- **셔뱅(Shebang) 지원**: `#!/usr/bin/env dotnet`으로 Unix 스타일 실행 지원

#### Graceful Shutdown 지원

새로운 버전에서는 프로세스 종료 시 더 안정적인 처리가 가능해졌습니다:

```csharp
// Graceful shutdown 타임아웃
var gracefulShutdownTimeout = TimeSpan.FromSeconds(5);

Console.CancelKeyPress += (sender, e) =>
{
    if (cts.IsCancellationRequested)
    {
        // 두 번째 Ctrl+C: 강제 종료
        Console.Out.WriteLine("Info: Force exit requested. Terminating immediately...");
        e.Cancel = false;
        return;
    }

    Console.Out.WriteLine($"Info: Cancellation requested. Shutting down gracefully (timeout: {gracefulShutdownTimeout.TotalSeconds}s)...");
    Console.Out.WriteLine("Info: Press Ctrl+C again to force exit.");
    e.Cancel = true; // 즉시 종료 방지
    cts.CancelAfter(gracefulShutdownTimeout);
    cts.Cancel();
};
```

주요 특징:

- **첫 번째 Ctrl+C**: Graceful shutdown 시작 (5초 타임아웃)
- **두 번째 Ctrl+C**: 즉시 강제 종료
- **SIGINT 표준 종료 코드(130)** 반환

#### 빌드 프로세스 단순화

```yaml
# 기존: 빌드 후 실행
- name: Build Catalog Builder Tool
  run: dotnet build src/TableCloth.CatalogBuilder/TableCloth.CatalogBuilder.csproj --configuration Release

- name: Run Catalog Builder Tool
  run: dotnet run --project src/TableCloth.CatalogBuilder/TableCloth.CatalogBuilder.csproj --configuration Release -- ./docs/ ./outputs/

# 변경: 직접 실행
- name: Run Catalog Builder Tool
  run: dotnet run --file src/catalogutil.cs -- ./docs/ ./outputs/
```

FBA 방식을 사용함으로써 별도의 빌드 단계가 필요 없어지고, `dotnet run --file` 명령어로 직접 스크립트를 실행할 수 있게 되었습니다.

## 삭제된 파일들

이번 업데이트에서 다음 파일들이 삭제되었습니다:

- `src/TableCloth.CatalogBuilder/TableCloth.CatalogBuilder.csproj`
- `src/TableClothCatalog.sln`

그리고 `src/TableCloth.CatalogBuilder/Program.cs`가 `src/catalogutil.cs`로 이름이 변경되고 내용이 개선되었습니다.

## 정리

이번 업데이트는 .NET 생태계의 최신 트렌드인 FBA 방식을 적극 활용하여 프로젝트 구조를 단순화한 좋은 사례입니다. 특히 작은 유틸리티 도구의 경우 별도의 프로젝트 파일 없이 단일 스크립트로 관리하는 것이 훨씬 효율적입니다.

식탁보 프로젝트에 관심이 있다면 [GitHub 리포지토리](https://github.com/yourtablecloth/TableCloth)를 방문해 보세요!

## 참고 링크

- [식탁보 프로젝트 GitHub](https://github.com/yourtablecloth)
- [TableClothCatalog 리포지토리](https://github.com/yourtablecloth/TableClothCatalog)
- [해당 커밋](https://github.com/yourtablecloth/TableClothCatalog/commit/8edbd2e9ca9bef3085932d39e88703391126f04d)

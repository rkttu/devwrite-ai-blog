---
title: "Evaluating .NET 11 Adoption Before Release"
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
  - .NET Development
translationKey: "dotnet-11-preview-7-adoption-guide"
description: "An adoption guide to .NET 11 Preview 7 covering its support cycle, hardware baseline, Runtime Async, C# 15, and framework changes."
cover:
  image: "images/posts/dotnet-11-preview-7-adoption-guide.webp"
  alt: "Bright purple illustration of dotnet bot flying toward a translucent number 11"
tldr: ".NET 11 adoption depends more on the x86-64-v2 baseline, Runtime Async, SDK defaults, and C# 15 than on its STS support term. Teams already running .NET 10 can compare the new capabilities with their validation and migration costs instead of upgrading for a longer support window."
license: "CC BY-NC 4.0"
---

Microsoft plans to release .NET 11 on November 10, 2026. As of August 23, 2026, .NET 11 Preview 7, released on August 11, is the latest build. Microsoft continues to refine the runtime, SDK, C# 15, ASP.NET Core, .NET MAUI, Entity Framework Core, and the rest of the product family. Features and behavior may still change before the final release. [Microsoft's .NET 11 Preview 7 announcement](https://devblogs.microsoft.com/dotnet/dotnet-11-preview-7/)

This article examines .NET 11 across five areas: the support cycle, hardware baseline, runtime and developer tooling, C# 15, and application frameworks. The focus is on changes that affect migration rather than the number of new features.

We will begin with support and execution environments before moving to Runtime Async and the SDK. We will then review the C# 15 type model and major ASP.NET Core and EF Core changes. The final section provides a validation sequence for the remaining preview period.

This article is based on preview information available on the following date.

> Baseline date: August 23, 2026
>
> Target version: .NET 11 Preview 7, SDK 11.0.100-preview.7
>
> Status: Preview features and the compatibility change list may change before the final release. Preview builds generally are not supported for production use.

## An STS Release That Does Not Extend the Support Window

The .NET 11 support cycle comes first. Microsoft classifies .NET 11 as an STS release and plans to support it for two years, from November 10, 2026 through November 9, 2028. LTS and STS releases have the same quality level and differ only in support duration. LTS releases receive patches and technical support for three years, while STS releases receive them for two. The [.NET 11 release plan](https://github.com/dotnet/core/blob/main/release-notes/11.0/README.md) and [.NET support policy](https://dotnet.microsoft.com/en-us/platform/support/policy) document this schedule.

Placing the current schedules side by side makes the upgrade decision easier to frame.

| Version | Release type | General availability | End of support |
| --- | --- | --- | --- |
| .NET 8 | LTS | November 14, 2023 | November 10, 2026 |
| .NET 9 | STS | November 12, 2024 | November 10, 2026 |
| .NET 10 | LTS | November 11, 2025 | November 14, 2028 |
| .NET 11 | STS | November 10, 2026, planned | November 9, 2028, planned |

Moving from .NET 10 LTS to .NET 11 does not extend the support window. Under the current plan, .NET 11 support ends five days earlier. Teams running .NET 10 can decide whether new capabilities, performance, and developer experience offset the migration cost. Teams running .NET 8 or .NET 9 can evaluate .NET 10 and .NET 11 together because both current versions reach end of support on the planned .NET 11 release date.

## A Hardware Baseline That Can Affect Existing Machines

.NET 11 raises the x86/x64 JIT and AOT minimum across operating systems from `x86-64-v1` to `x86-64-v2`. A .NET 11 application will not run on a CPU that lacks instructions such as `SSE3`, `SSSE3`, `SSE4.1`, `SSE4.2`, and `POPCNT`. [.NET 11 runtime minimum hardware requirements](https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-11/runtime#updated-minimum-hardware-requirements)

ReadyToRun targets also vary by operating system.

| Operating system | x86/x64 JIT and AOT minimum | ReadyToRun target |
| --- | --- | --- |
| macOS | `x86-64-v2` | `x86-64-v2` |
| Linux | `x86-64-v2` | `x86-64-v3` |
| Windows | `x86-64-v2` | `x86-64-v3` |

The ReadyToRun target rises to `x86-64-v3` on Linux and Windows, but the execution minimum does not rise to `v3`. Applications can still run on `v2` hardware. However, startup can take longer when the runtime must JIT-compile portions that cannot use the precompiled code.

On Arm64, Apple and Linux keep their existing execution minimum. Windows Arm64 requires the `LSE` instruction set and raises the ReadyToRun target to `armv8.2-a + RCPC`. The effect is likely limited on recent cloud instances, while older on-premises servers, edge devices, and software installed on customer hardware remain separate validation targets.

## Changes to Async Execution and Tooling Defaults

The runtime and SDK execution paths are the next area to examine. Runtime Async moves suspension and resumption into the runtime, while the SDK puts the NativeAOT CLI and MSBuild server on the default path. Both can affect execution and builds without large application code changes.

### Runtime Async Moves Async Execution into the Runtime

The C# compiler traditionally generates a state machine for every `async` method. Runtime Async V2 lets the runtime manage suspension and resumption. Microsoft intends this design to produce cleaner live call stacks, improve debugging, and reduce execution overhead. [.NET 11 Runtime Async documentation](https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-11/runtime#runtime-async)

Add the following property to a project file to test Runtime Async in application code.

```xml
<PropertyGroup>
  <Features>runtime-async=on</Features>
</PropertyGroup>
```

A `net11.0` project can use the feature without separately enabling `EnablePreviewFeatures`. The .NET 11 runtime libraries themselves are also built with Runtime Async. Application code still enables the feature explicitly.

Published examples show fewer compiler state-machine frames in live call stacks and expose the actual method call relationships more directly. Exception stack traces do not differ because the existing implementation already cleans them up. NativeAOT and ReadyToRun also support Runtime Async. Throughput and allocation improvements depend on an application's async call patterns, so load-test results from the target service provide the better adoption criterion.

### SDK and Test Tools Reduce Repeated Setup

Preview 7 enables the NativeAOT-based `dotnet` CLI path and the MSBuild server by default. It also adds run-level controls to `dotnet test` when using Microsoft.Testing.Platform. [What's new in the .NET 11 SDK and tooling](https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-11/sdk)

- **NativeAOT CLI path**: `dotnet --info`, help, selected `dotnet sln` commands, and tool discovery and execution use the NativeAOT path. Commands such as `build`, `run`, `test`, `pack`, and `publish`, which use MSBuild or NuGet in process, fall back to the managed CLI.

- **MSBuild server by default**: The SDK keeps a warm MSBuild worker between commands. Consecutive `dotnet build`, `dotnet test`, and `dotnet run` invocations can reduce MSBuild startup costs. If a custom build task assumes process isolation, `DOTNET_CLI_USE_MSBUILD_SERVER=false` provides a comparison with the previous behavior.

- **Test run policies**: In Microsoft.Testing.Platform mode, options such as `dotnet test --timeout 90s` and `dotnet test --maximum-failed-tests 5` limit the duration and failure count of the entire run. `Microsoft.Build.Traversal` projects can also aggregate test targets for execution.

- **Local container selection**: SDK container publishing now prefers `wslc` on Windows and `container` on macOS. Docker and Podman become fallback choices. A build environment that depends on a particular engine can select it explicitly with the `LocalRegistry` property.

These changes mean that an SDK-only comparison should record build time, process counts, and whether custom tasks preserve state to make the cause of a difference traceable.

## C# 15 Models Closed Sets of Types

C# 15 changes the type model in several areas. It includes collection-expression arguments, union types, closed hierarchies, extension indexers, labeled `break` and `continue`, and ongoing memory-safety work. Union types and closed hierarchies let the compiler understand a fixed set of possible types and check whether a `switch` is exhaustive. [What's new in C# 15](https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-15)

A union can represent all possible payment results as follows.

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

The `closed` modifier allows direct derived types to be declared only within the same assembly. Because the compiler can see every direct derived type, it can determine that a `switch` without a default arm is exhaustive. Closure does not automatically propagate through the entire hierarchy. An intermediate type must also use `closed` to restrict its descendants.

Some parts of the union specification are not implemented in Preview 7. Memory-safety improvements are also planned across multiple releases. Product code using C# 15 should therefore leave room to compare the preview syntax again with the final compiler and compatibility documentation.

## Library and Framework Changes Visible in Application Workloads

Application-level changes vary by workload. .NET 11 expands APIs for process execution, compression, serialization, diagnostics, and numerical computing. ASP.NET Core and EF Core also refine server resource management and query translation. [Overview of .NET 11 changes](https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-11/overview)

- **Base libraries**: `Process` gains APIs for execution and output capture. `System.IO.Compression` adds Zstandard compression, ZIP passwords, and CRC32 validation. `System.Text.Json` supports C# union serialization and polymorphism inference for closed type hierarchies. IEEE 754 decimal floating-point types and generic `Complex<T>` expand the numerical APIs. [.NET 11 Preview 7 library release notes](https://github.com/dotnet/core/blob/main/release-notes/11.0/preview/preview7/libraries.md)

- **ASP.NET Core**: Blazor Interactive Server can pause circuits for hidden browser tabs after an idle period and resume them when the user returns. This feature is enabled through a separate package and configuration. Preview 7 also includes Blazor SSR output caching, validation-message localization, and the OpenAPI 3.2 representation for Server-Sent Events. [ASP.NET Core Preview 7 release notes](https://github.com/dotnet/core/blob/main/release-notes/11.0/preview/preview7/aspnetcore.md)

- **Entity Framework Core**: The SQL Server provider translates `int.Parse` and several other numeric parsing methods into server-side `CAST` operations. A `GroupBy` aggregate that traverses a reference navigation can translate to one join and grouping operation instead of a correlated subquery. Because generated SQL can change, actual data distributions, execution plans, and timings remain the useful comparison points. [EF Core Preview 7 release notes](https://github.com/dotnet/core/blob/main/release-notes/11.0/preview/preview7/efcore.md)

Applications will not use every feature with equal weight. A service that exchanges archives can start with ZIP validation behavior. A Blazor Server service can measure how circuit pausing affects memory use. A data-intensive service can narrow its scope by comparing EF Core's generated SQL with the previous version.

## Validation Items Before General Availability

The pre-release validation sequence closes the review. Microsoft's [.NET 11 compatibility change list](https://learn.microsoft.com/en-us/dotnet/core/compatibility/11) is still in progress and is not complete. Preview 7 results should not be assumed to match the final release.

1. Collect the supported CPU instruction sets for production servers, build agents, and customer hardware.
2. Pin SDK `11.0.100-preview.7` in an isolated test environment and record build warnings and test results for the existing source.
3. Compare consecutive build times and custom task behavior with the MSBuild server enabled and disabled.
4. Apply Runtime Async only to services with substantial async traffic, then compare throughput, latency, allocations, and live call stacks with the existing implementation.
5. For ASP.NET Core and EF Core applications, compare generated OpenAPI documents, authentication flows, generated SQL for key LINQ queries, and execution plans.
6. Map compatibility changes related to compression, certificates, files and pipes, and host shutdown behavior to the features each service uses.
7. When the release candidate and final release become available, verify the status of preview features and review the compatibility list again.

## An Upgrade Decision Led by Execution Conditions

.NET 11 changes the async execution model, hardware baseline, type model, and default behavior of developer tools together. The execution environment and build path changes are too significant to evaluate as an API-only update.

Runtime Async and C# 15 are longer-term topics because they can affect code generation and type design in future .NET applications. The higher x86/x64 minimum, the default MSBuild server and NativeAOT CLI, and selected library behavior changes can have an immediate effect.

Teams running .NET 8 or .NET 9 can choose between .NET 10 LTS and .NET 11 STS as the November 10, 2026 end-of-support date approaches. Teams already on .NET 10 have little reason to rush for support duration alone. Products that run on older hardware or customer premises can investigate the CPU baseline first, while teams with current cloud environments and automated test systems can use Preview 7 to begin collecting compatibility evidence.

---
title: "A New Genre in .NET: The Era of NuGet-Free Single File C# Coding"
date: 2026-03-16T00:00:00+09:00
draft: false
slug: "nuget-free-single-file-csharp"
tags:
  - .NET
  - C#
  - File-Based App
  - Runtime Async
  - Performance Optimization
categories:
  - .NET Development
translationKey: "nuget-free-single-file-csharp"
description: "When .NET 10's file-based apps meet Runtime Async, fast and type-safe single file C# coding becomes possible using only the BCL — no NuGet required."
cover:
  image: "images/posts/nuget-free-single-file-csharp.webp"
  alt: "Concept image of code running from a single C# file"
tldr: "The combination of dotnet run file.cs's BuildLevel.Csc optimization and Runtime Async enables single file C# programs using only BCL — no NuGet packages — to achieve 200ms–630ms repeat execution times, opening a new coding genre that combines Python's convenience, Go's deployment simplicity, and C#'s type safety."
---

> C# isn't becoming as lightweight as a scripting language — scripting languages are becoming envious of how fast it's getting.

## Introduction

`dotnet run file.cs` — the so-called **file-based app** — introduced in .NET 10, lets you run C# code with just a single `.cs` file, without a `.csproj`. However, its current execution speed is roughly 1.5 seconds on Windows and 0.8 seconds on WSL2 for the first run. Compared to Python's `python script.py` at around 50ms, it's hard to call this "scripting" with a straight face.

But two major changes currently underway in the .NET ecosystem could fundamentally alter this picture:

1. **Build optimization for `dotnet run file.cs`** — A strategy to bypass MSBuild and call Roslyn directly
2. **Runtime Async (async2)** — Processing async/await at the runtime level, eliminating state machine overhead

When these two converge, **single file C# programs written using only the BCL without NuGet packages** could establish themselves as an independent coding genre. This post explores the technical foundations and future vision.

---

## File-Based Apps Today: The MSBuild Bottleneck

### The Essence: `.csproj` + `.cs` = A Single `.cs`

File-based apps are fundamentally different from C# scripts (`.csx`). `.csx` files are interpreted at runtime by a separate script host, while file-based apps are **converted to a virtual `.csproj` at compile time** and pass through the standard build pipeline. The output is a managed DLL identical to a regular project.

```cs
// These directives become the .csproj content
#:package System.CommandLine@2.0.0

// The actual code starts here
Console.WriteLine("Hello, file-based app!");
```

### The Problem: MSBuild's Weight

When you run `dotnet run hello.cs`, here's what happens internally:

| Step | Approx. Time | Description |
| ---- | ------------ | ----------- |
| CLI load | ~200ms | .NET runtime JIT, CLI command dispatch |
| MSBuild engine load | ~200ms | Build engine initialization |
| SDK targets evaluation | ~300ms | Sequential evaluation of hundreds of `.props`/`.targets` files |
| NuGet restore | ~100ms+ | Package dependency resolution (cached) |
| Roslyn compilation | ~200ms | Actual C# → IL conversion |
| Execution | ~50ms | Running the resulting DLL |

Out of a **total of ~1.5 seconds**, the actual "compile + run" takes only ~250ms. The rest is entirely MSBuild overhead.

---

## The Strategy to Bypass MSBuild: `BuildLevel.Csc`

The dotnet/sdk team recognized this bottleneck and implemented an optimized path that **identifies cases where MSBuild can be skipped entirely and calls the Roslyn compiler directly**.

### Three Build Levels

```text
dotnet run hello.cs
       │
       ▼
  Input change detection
       │
  ┌────┼────────────┐
  ▼    ▼            ▼
None  Csc          All
  │    │            │
  ▼    ▼            ▼
Skip  csc only     MSBuild full build
~200ms ~400-630ms  ~1.5s
```

- **`BuildLevel.None`**: Nothing changed, so run the previous build result as-is
- **`BuildLevel.Csc`**: Only `.cs` code changed, so request directly to the Roslyn compiler server — **complete MSBuild bypass**
- **`BuildLevel.All`**: Package or SDK settings changed, so execute a full MSBuild build

### Conditions for `BuildLevel.Csc`

To take this fast path:

- ✅ No `#:package` directives, or no changes to them
- ✅ No `#:sdk` directives, or no changes to them
- ✅ No implicit build files like `Directory.Build.props`
- ✅ No global property customization like `-c Release`
- ✅ Cached compiler arguments (`.rsp`) from a previous build exist

When all conditions are met, the SDK doesn't create a virtual project file or load MSBuild. It takes the cached `.rsp` file and **sends a request directly to the Roslyn compiler server via named pipe**.

```cs
// What actually happens in CSharpCompilerCommand.cs
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

### This Is a Mini Build System

`CSharpCompilerCommand` already reimplements parts of what MSBuild used to do, hard-coded in C#:

- AssemblyAttributes.cs generation
- GlobalUsings.g.cs generation
- AssemblyInfo.cs generation
- EditorConfig generation
- AppHost binary patching
- RuntimeConfig.json generation
- Compiler response file (.rsp) generation

This is a strategy of "caching what MSBuild did once and reusing it," not replacing MSBuild. The first run must go through MSBuild, and structural changes send it back to MSBuild.

### The Core Design Tension

The SDK team intentionally keeps the bypass scope narrow:

```cs
// Even adding just a Release build falls back to MSBuild
// Note that Release builds won't go through this optimized code path because
// `-c Release` translates to global property `Configuration=Release`
// and customizing global properties triggers a full MSBuild run.
```

Why? The more you expand the bypass scope, the more you're effectively **creating a separate build system just for file-based apps**, increasing the chance of behavioral divergence from MSBuild. This could break file-based apps' core principle — "it should behave identically when you grow up to a project."

---

## Runtime Async: A Fundamental Redesign of async/await

### Current async/await: Compiler-Generated State Machines

Currently, C#'s `async/await` is handled by the **compiler (Roslyn)**. When you write an `async` method, the compiler transforms it into a state machine struct and generates `IAsyncStateMachine.MoveNext()`.

```cs
// The code you write
async Task<int> FetchDataAsync()
{
    var data = await httpClient.GetStringAsync(url);
    return data.Length;
}

// What the compiler actually generates (simplified)
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
        // Actual logic...
    }
}
```

The costs of this approach:

- **State machine struct allocation** (even on hot paths)
- **`MoveNext()` call overhead**
- **ExecutionContext capture/restore**
- **IL code size increase** (state machine boilerplate)

### Runtime Async: The Runtime Handles It Directly

**Runtime Async**, experimentally introduced in .NET 10 and set to be fully enabled in .NET 11, flips this entire structure. Instead of the compiler creating state machines, **the JIT compiler and VM directly handle suspension/resumption of async methods**.

A new method attribute is added to the ECMA-335 specification:

```text
MethodImplOptions.Async = 0x2000
```

And `await` is no longer compiler magic but a **suspension point** recognized by the runtime:

```cs
// The await pattern recognized by the runtime
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

### Core Mechanism: Method Variant Pairs

The most important concept in Runtime Async's implementation is **variant pairs**. For every method that returns a `Task`, the runtime automatically generates two entry points:

- **Task-returning variant**: Same `Task<T>` return signature as before
- **Async variant**: Returns `T` directly, handling suspension through Continuation objects via a new calling convention

In async → async call chains where no suspension occurs (hot path), **the value is returned directly without allocating a Task object at all**. This is the key to the dramatic performance improvement.

### Implications from Benchmarks

```text
Current (async1): async method call → state machine allocation → Task allocation → await
Runtime Async:    async method call → (synchronous completion) direct value return, no Task allocation
```

According to the .NET team's experiments, Runtime Async showed **performance at least equal to or better than existing compiler-async**. In particular:

- **Synchronous completion (no suspension) path**: State machine and Task allocation completely eliminated, nearly identical cost to regular method calls
- **IL code size**: Significantly reduced as state machine boilerplate disappears
- **Full compatibility**: Drop-in replacement for existing async1

---

## The Convergence: The Rise of NuGet-Free Single File Apps

### Performance Spectrum

Expected performance after both optimizations are applied:

| Scenario | Current | BuildLevel.Csc | + Runtime Async |
| -------- | ------- | --------------- | --------------- |
| First run (`dotnet run hello.cs`) | ~1.5s | ~1.5s (same for first run) | ~1.5s |
| Repeat run (code changed) | ~1.5s | **~400-630ms** | **~400-630ms** |
| Repeat run (no changes) | ~1.5s | **~200ms** | **~200ms** |
| async call chain performance | Baseline | Baseline | **Significantly improved** |

`BuildLevel.Csc` reduces build time, while Runtime Async reduces async-related overhead during execution. The two improvements are **orthogonal**, producing a combined effect.

### The Conditions for NuGet-Free Are the Conditions for the Optimal Path

To maximize `BuildLevel.Csc` benefits:

- No `#:package` → No NuGet restore needed
- No `#:sdk` changes → No SDK targets re-evaluation needed
- No implicit build files → No MSBuild property re-evaluation needed

Code that satisfies these conditions is precisely **code that doesn't depend on NuGet packages**. And the .NET BCL already provides enough to accomplish a surprisingly wide range of tasks:

```cs
// ✅ All achievable with BCL alone

using System.Net.Http;                      // HTTP client
using System.Text.Json;                     // JSON serialization/deserialization
using System.Text.RegularExpressions;       // Regular expressions
using System.IO.Compression;                // ZIP, GZip
using System.Security.Cryptography;         // Hashing, encryption
using System.Threading.Channels;            // Producer-consumer pattern
using System.Collections.Concurrent;        // Concurrent collections
using System.Xml.Linq;                      // XML processing
using System.Diagnostics;                   // Process management
using System.Net;                           // DNS, IP, sockets
```

### Practical Use Cases

#### **CLI Utilities**

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

#### **Simple HTTP Client / API Testing**

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

With Runtime Async, synchronously completing calls in this `Parallel.ForEachAsync` + `await` chain are processed without state machine allocation.

#### **JSON Data Transformation Pipeline**

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

#### **System Administration Automation**

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

### When You Go Beyond NuGet

There are areas where BCL alone can't cover:

| Required Feature | Status |
| ---------------- | ------ |
| Databases (Npgsql, Dapper) | ❌ `#:package` required → `BuildLevel.All` |
| Cloud SDKs (Azure, AWS) | ❌ `#:package` required |
| Web frameworks (ASP.NET Core) | ❌ `#:sdk Microsoft.NET.Sdk.Web` required |
| Advanced CLI parsing | ❌ `#:package System.CommandLine` required |
| Test frameworks | ❌ `#:package` required |

Once you cross this boundary, `BuildLevel.Csc` benefits disappear, and you're back to a ~1.5-second full MSBuild build. This naturally **draws the line between "NuGet-free single file" and "project-based app"**.

---

## What Runtime Async Brings to File-Based Apps

### Reduced Code Size

Currently, `async` methods see significant IL size increases when the compiler transforms them into state machines. Runtime Async moves this transformation to the JIT, **reducing IL-level code size**. For file-based apps, this means:

- Faster compilation (less IL to process)
- Smaller output binaries
- Reduced Native AOT binary size from `dotnet publish file.cs`

### Hot Path Optimization

Runtime Async's variant pair mechanism **dramatically optimizes the synchronous completion path** in async method chains. A common pattern in NuGet-free single file apps:

```cs
// Most HTTP requests return "already completed" results
async Task<string> GetCachedDataAsync(string key)
{
    if (cache.TryGetValue(key, out var value))
        return value;  // ← Synchronous path: no Task allocation!

    var data = await FetchFromSourceAsync(key);
    cache[key] = data;
    return data;
}
```

Currently, a state machine struct is created every time this method is called. With Runtime Async, cache hits are processed at **the same cost as a regular method call**.

### `dotnet publish file.cs` + Native AOT

Publishing a file-based app with `dotnet publish` compiles it via Native AOT into a **dependency-free single native binary**. Combined with Runtime Async:

```bash
$ dotnet publish hello.cs
# → hello (Linux) / hello.exe (Windows)
# Single native binary, same experience as Go's go build
```

This is effectively identical to the "compile → single binary" experience offered by Go or Rust, but with C#'s rich BCL and the ergonomic advantage of async/await.

---

## Comparison: Positioning Among Other Language Ecosystems

| | Python | Go | C# (NuGet-free file-based) |
| --- | ------ | --- | -------------------------- |
| Single file execution | ✅ `python script.py` | ❌ (package required) | ✅ `dotnet run script.cs` |
| Repeat execution speed | ~50ms | N/A (compilation required) | ~200-600ms |
| Type safety | ❌ Dynamic typing | ✅ Static typing | ✅ Static typing |
| Async support | `asyncio` (limited) | goroutine | `async/await` (runtime-native) |
| Single binary deployment | ❌ (PyInstaller, etc.) | ✅ `go build` | ✅ `dotnet publish` + AOT |
| Standard library richness | ★★★★☆ | ★★★★★ | ★★★★★ |
| Ecosystem package access | pip | go mod | #:package (NuGet) |

Slower on first run than Python, but with overwhelming advantages in type safety and performance (especially in async scenarios). Single binary deployment similar to Go, with richer async/await support.

---

## Remaining Challenges and Limitations

### The MSBuild Ceiling

Despite all optimizations, file-based apps are fundamentally built on the MSBuild (SDK) platform. MSBuild is practically the identity of the .NET ecosystem:

- The NuGet package system is designed as MSBuild items
- The SDK (`Microsoft.NET.Sdk`) is a bundle of MSBuild targets
- IDE integration (VS, Rider, VS Code) depends on MSBuild project evaluation

The more you expand the bypass scope, the more you're effectively **creating a degraded replica of MSBuild**. The SDK team recognizes this trap and is taking a conservative strategy: "bypass only within clearly safe boundaries, and return to MSBuild at the slightest uncertainty."

### Rewriting in Rust Wouldn't Change the Problem

While it's true that Rust-based tools (uv, Bun, etc.) in the Python/Node.js ecosystem have shown dramatic performance improvements, .NET's build performance issue is different in nature. pip and npm were slow because they involved "simple I/O operations on a slow runtime." MSBuild is slow because "there's simply a lot of work to do." Even rewriting the build engine in Rust wouldn't change the workload of sequentially evaluating hundreds of targets files.

That's why the SDK team's strategy — instead of making the slow path faster, **avoiding the slow path entirely** — is the most realistic solution to this problem.

### Runtime Async Maturity

Runtime Async is still under active development. Compiling async2 methods into ReadyToRun images is not yet supported. Edge cases remain around SynchronizationContext handling, Reflection compatibility, and more.

---

## Conclusion: The Birth of a New Genre

A **clear boundary between "project-based production apps" and "lightweight single-file scripts"** is being naturally drawn in the .NET ecosystem by performance characteristics. That boundary is precisely the **presence or absence of NuGet dependencies**.

Code written using only the BCL without NuGet:

- ✅ Builds fast via the `BuildLevel.Csc` path
- ✅ Runs async code faster with Runtime Async
- ✅ Deploys as a single binary via Native AOT
- ✅ Self-contained in a single `.cs` file without project files

This is a **new coding genre** combining the convenience of Python scripting, Go's deployment simplicity, and C#'s type-safe async/await. It's not that `.csproj` has disappeared — it's that the domain where `.csproj` isn't needed has been clearly defined, and optimal developer experience is being provided within that domain.

```cs
#!/usr/bin/env dotnet run

// This is the future of NuGet-free single file C#.
// No project files. No package dependencies.
// Fast, type-safe scripting powered by BCL alone.

var response = await new HttpClient().GetStringAsync("https://api.github.com/zen");
Console.WriteLine(response);
```

---

*Current status of the technologies discussed in this post:*

- *`dotnet run file.cs`: Introduced in .NET 10, performance optimization in progress ([dotnet/sdk#48011](https://github.com/dotnet/sdk/issues/48011))*
- *Runtime Async: Experimentally introduced in .NET 10, full activation expected in .NET 11 ([dotnet/runtime#94620](https://github.com/dotnet/runtime/issues/94620))*
- *`BuildLevel.Csc` path: Implemented as `CSharpCompilerCommand` in dotnet/sdk*

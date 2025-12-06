---
title: "TableCloth Catalog Builder Modernized with .NET 10 and FBA"
date: 2025-12-06T12:00:00+09:00
draft: false
slug: "tablecloth-catalog-dotnet10-fba"
tags:
  - TableCloth
  - .NET
  - Open Source
  - C#
categories:
  - Development
translationKey: "tablecloth-catalog-dotnet10-fba"
tldr: "The TableCloth project's catalog builder has been upgraded to .NET 10 and simplified using the File-Based App (FBA) approach."
cover:
  image: "images/posts/tablecloth-catalog-dotnet10-fba.jpg"
  alt: "TableCloth Project Catalog Builder Update"
---

## What is the TableCloth Project?

[TableCloth](https://github.com/yourtablecloth) is an open-source project that helps users safely use security plugins required for Korean internet banking in a Windows Sandbox environment. It runs security programs required by various financial institution websites in an isolated environment, ensuring the safety of the host system.

## What is the Catalog Repository?

The [TableClothCatalog](https://github.com/yourtablecloth/TableClothCatalog) repository stores the list of security programs required for each financial institution site referenced by the TableCloth project. Security plugin information required by websites of banks, securities firms, and insurance companies is systematically organized here. The catalog builder tool processes this information into a format usable by the TableCloth app.

## Recent Catalog Builder Update

An important update has been applied to this repository recently. In this commit, the catalog builder tool was upgraded to .NET 10 and the project structure was significantly simplified.

### Key Changes

#### .NET 10 Upgrade

```yaml
# Before
dotnet-version: 8.0.x

# After
dotnet-version: 10.0.x
```

The build pipeline was upgraded from .NET 8 to .NET 10. This enables the use of the latest runtime performance improvements and new language features.

#### Transition to File-Based App (FBA)

The most notable change is the simplification of the project structure. Previously, separate `.csproj` project files and solution files (`.sln`) were used, but this update removed these files and consolidated everything into a single C# script file (`catalogutil.cs`).

```csharp
#!/usr/bin/env dotnet
#:package IronSoftware.System.Drawing@2025.9.3
#:property PublishAot=false

using SixLabors.ImageSharp;
using SixLabors.ImageSharp.Formats.Png;
using System.Collections.Concurrent;
// ...
```

This is .NET's **File-Based App (FBA)** approach. FBA provides the following advantages:

- **No project file required**: Run applications with a single `.cs` file without `.csproj`
- **Inline package references**: Reference NuGet packages directly with `#:package` directive
- **Inline build properties**: Set build properties with `#:property` directive
- **Shebang support**: Unix-style execution with `#!/usr/bin/env dotnet`

#### Graceful Shutdown Support

The new version enables more stable handling when terminating the process:

```csharp
// Graceful shutdown timeout
var gracefulShutdownTimeout = TimeSpan.FromSeconds(5);

Console.CancelKeyPress += (sender, e) =>
{
    if (cts.IsCancellationRequested)
    {
        // Second Ctrl+C: Force exit
        Console.Out.WriteLine("Info: Force exit requested. Terminating immediately...");
        e.Cancel = false;
        return;
    }

    Console.Out.WriteLine($"Info: Cancellation requested. Shutting down gracefully (timeout: {gracefulShutdownTimeout.TotalSeconds}s)...");
    Console.Out.WriteLine("Info: Press Ctrl+C again to force exit.");
    e.Cancel = true; // Prevent immediate termination
    cts.CancelAfter(gracefulShutdownTimeout);
    cts.Cancel();
};
```

Key features:

- **First Ctrl+C**: Initiates graceful shutdown (5-second timeout)
- **Second Ctrl+C**: Immediate forced termination
- **SIGINT standard exit code (130)** returned

#### Simplified Build Process

```yaml
# Before: Build then run
- name: Build Catalog Builder Tool
  run: dotnet build src/TableCloth.CatalogBuilder/TableCloth.CatalogBuilder.csproj --configuration Release

- name: Run Catalog Builder Tool
  run: dotnet run --project src/TableCloth.CatalogBuilder/TableCloth.CatalogBuilder.csproj --configuration Release -- ./docs/ ./outputs/

# After: Direct execution
- name: Run Catalog Builder Tool
  run: dotnet run --file src/catalogutil.cs -- ./docs/ ./outputs/
```

By using the FBA approach, a separate build step is no longer necessary, and the script can be executed directly with the `dotnet run --file` command.

## Deleted Files

The following files were deleted in this update:

- `src/TableCloth.CatalogBuilder/TableCloth.CatalogBuilder.csproj`
- `src/TableClothCatalog.sln`

Additionally, `src/TableCloth.CatalogBuilder/Program.cs` was renamed to `src/catalogutil.cs` with improved content.

## Summary

This update is a good example of actively utilizing the FBA approach, the latest trend in the .NET ecosystem, to simplify project structure. Especially for small utility tools, managing them as a single script without separate project files is much more efficient.

If you're interested in the TableCloth project, visit the [GitHub repository](https://github.com/yourtablecloth/TableCloth)!

## References

- [TableCloth Project GitHub](https://github.com/yourtablecloth)
- [TableClothCatalog Repository](https://github.com/yourtablecloth/TableClothCatalog)
- [Related Commit](https://github.com/yourtablecloth/TableClothCatalog/commit/8edbd2e9ca9bef3085932d39e88703391126f04d)

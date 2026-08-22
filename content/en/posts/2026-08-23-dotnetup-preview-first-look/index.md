---
title: "dotnetup Preview: Managing SDKs and Runtimes from global.json"
date: 2026-08-23T01:35:51+09:00
draft: false
slug: "dotnetup-preview-first-look"
description: "How dotnetup preview separates development SDKs from OS packages and manages global.json requirements, runtimes, and update state."
tags:
  - .NET
  - dotnetup
  - .NET SDK
  - global.json
  - Development Environment
categories:
  - .NET Development
translationKey: "dotnetup-preview-first-look"
cover:
  image: "images/posts/dotnetup-preview-first-look.webp"
  alt: "Illustration of a configuration file passing through a state manager into user-scoped SDK and runtime components"
tldr: "Like rustup, dotnetup lets developers retain system packages while managing development .NET SDKs and runtimes separately under a user account. It turns a repository's global.json into a tracked installation requirement and supports channel updates and shared-component cleanup."
license: "CC BY-NC 4.0"
---

Microsoft introduced `dotnetup`, a new tool for managing user-level .NET installations, in the prerecorded Microsoft Build 2026 session OD804, [“Simplifying .NET installs with .NET Up”](https://www.youtube.com/watch?v=ZMnyohA5yrw). As of August 22, 2026, the `release/dnup` branch of the `dotnet/sdk` repository provides preview installation instructions and command reference documentation for Windows, macOS, and Linux. This article examines the behavior available in the current preview through the problem statement and design goals presented in the session.

`dotnetup` installs .NET SDKs and runtimes under a user profile without administrator access. It reads a repository's `global.json`, tracks the required SDK channel, and updates or cleans up installation files shared by multiple requirements. You can also choose how shells and applications find the managed `dotnet` executable. This article covers installation, `global.json` interpretation, the separation of SDKs and runtimes, installation state management, and automation.

We will first examine the management gap left by existing installation methods. We will then follow the preview installation and repository-level SDK setup process. The final sections explain the runtime and update models and compare the current implementation with the OD804 roadmap.

> Baseline date: August 22, 2026. `dotnetup` is a preview, and command names and behavior may change. This article is based on the [official documentation in the `release/dnup` branch](https://github.com/dotnet/sdk/tree/release/dnup/documentation/general/dotnetup) and version `0.2.0-preview.1.26410.1`, downloaded on that date.

## A State Manager Closer to rustup Than an Installation Script

The reasons for bringing .NET installation paths under one management tool come first. The OD804 session contrasts Windows environments where Visual Studio manages the toolchain with all other cases. The latter mix operating-system package managers, web installers, the `dotnet-install` scripts, and version managers such as DNVM and mise. When installers and update cycles differ, every repository can require a different procedure for provisioning its SDK and removing old installations. [The problem statement in the session](https://www.youtube.com/watch?v=ZMnyohA5yrw&t=69s) presents this inconsistency as the tool's starting point.

The existing `dotnet-install` scripts also support non-administrator installation. Microsoft primarily positions them for CI environments where the SDK installation can disappear after each run. It has directed development environments toward installers instead. The [official `dotnet-install` documentation](https://learn.microsoft.com/dotnet/core/tools/dotnet-install-script) states this intended scope.

At this point, `dotnetup` resembles Rust's `rustup` more than an installation script. In environments such as Ubuntu, where [the SDK feature band in distribution packages can differ from newer SDK releases](https://learn.microsoft.com/dotnet/core/install/linux-ubuntu-install), the system package can remain in place while a newer development SDK is managed separately under the user account. The [initial dotnetdev forum post](https://forum.dotnetdev.kr/t/dotnetup-rustup-net-toolchain-manager/14805) emphasizes that this arrangement tracks different project channels without replacing the package manager or requiring administrator access.

`dotnetup` records the requested components and channels, then connects them to the versions actually installed. It can therefore resolve moving requirements such as `latest`, `lts`, and `10.0.1xx` again later. An exact version pins its requirement. This combination of downloading installation files and managing installation state distinguishes the tool from the existing scripts. The [official overview](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/index.md) lists installation, updates, removal, and environment configuration as its current scope.

## User-Level Installation Without Administrator Access

The preview installation and access modes show how the tool fits into an existing environment. On macOS and Linux, you can start with the official script.

```bash
curl -fsSL https://aka.ms/dotnet/dotnetup/preview/get-dotnetup.sh | bash
export PATH="$HOME/.dotnetup:$PATH"
dotnetup init
dotnetup --version
```

The script downloads the executable for the operating system and CPU, verifies its SHA-512 checksum, and places the `dotnetup` executable in `~/.dotnetup` by default. The [getting-started documentation](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/README.md) also covers the PowerShell procedure for Windows and `daily` build installation. In environments where security policy prohibits piping a download into a shell, you can save the script to a file, review it, and then run it.

`dotnetup init` asks for an SDK channel and an access mode. The access mode determines the precedence between the managed installation and an existing `dotnet` installation.

| Display name | Configuration value | Where the managed `dotnet` is visible |
| --- | --- | --- |
| Isolation Mode | `none` | Run it through `dotnetup dotnet <command>` without changing `PATH` |
| Terminal Mode | `shell` | Update the selected shell profile and apply it to processes started from that shell |
| Everywhere Mode | `everywhere` | Apply it to the Windows user environment and shell profile |

On macOS and Linux, Terminal Mode is the suggested default when `dotnetup` detects a supported shell. On Windows, it suggests Everywhere Mode. The default root for managed SDKs and runtimes lives under the operating system's user data directory rather than a system-managed location. The [environment configuration documentation](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/concepts/environment.md) describes the paths and environment-variable behavior.

In this test, the official preview script selected the macOS arm64 executable for `0.2.0-preview.1.26410.1` and completed checksum verification. OD804 presents Native AOT as a design choice for fast startup and a small runtime dependency. The downloaded file was also a platform-specific executable that ran without installing the .NET SDK first. This result is limited to the macOS arm64 test performed on August 22, 2026.

The first run displays a notice about usage telemetry. The same `DOTNET_CLI_TELEMETRY_OPTOUT=1` environment variable used by the existing .NET CLI disables transmission. When introducing the preview into automation, you can apply the [official telemetry guidance](https://aka.ms/dotnetup-telemetry) together with your organization's policy.

## A Channel Model That Turns global.json into an Installation Request

The next step turns a repository requirement into installation state. The following `global.json` allows the latest patch in the 10.0.1xx feature band.

```json
{
  "sdk": {
    "version": "10.0.100",
    "rollForward": "latestPatch"
  }
}
```

When you run `dotnetup sdk install` from the repository root, the tool searches from the current directory toward the file-system root for the nearest usable `global.json`. If you do not provide a channel and it cannot find a usable file, it selects `latest`. When it finds a file, it maps `sdk.version` and `rollForward` to an installation requirement according to the following rules.

| `rollForward` | Requirement tracked for `10.0.103` |
| --- | --- |
| Omitted or `latestPatch` | `10.0.1xx` |
| `latestFeature` | `10.0` |
| `latestMinor` | `10` |
| `latestMajor` | `latest` |
| `disable`, `patch`, `feature`, `minor`, or `major` | Exact version `10.0.103` |

This mapping serves a different purpose from the rules the .NET host uses to select one installed SDK. `dotnetup` decides which version to install and continue tracking, while the .NET host selects which installed SDK to run. The [official `global.json` documentation](https://learn.microsoft.com/dotnet/core/tools/global-json) treats SDK selection and runtime targeting as separate concerns. The [repository integration documentation](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/usecases/install-with-global-json.md) describes the `dotnetup` mapping.

In this test, `dotnetup` read the file above, recorded the requirement as `10.0.1xx`, and placed `10.0.111` in a separate installation root. `dotnetup list` displayed the full path of the `global.json` as the installation source, and the installed `dotnet --version` returned `10.0.111`. The version selected by the same command may change on another day.

Adding `--update-global-json` writes the concrete installed version back to `sdk.version`. It preserves other properties, formatting, and the detected text encoding. In a repository with `sdk.paths`, the first path can also become the installation root. A command-line `--install-path` takes precedence over `sdk.paths`.

## Separating a Current SDK from Older Runtimes

SDKs and runtimes have separate installation commands because they serve different roles. An SDK provides developer tools such as compilers, MSBuild, and the CLI. A runtime executes built applications and tests. Even when the latest SDK can build several target frameworks, running tests for those frameworks can require their corresponding runtimes.

The OD804 demo builds `net8.0`, `net9.0`, and `net10.0` tests with the .NET 10 SDK. The .NET 8 and .NET 9 tests then fail to start because their runtimes are missing. Instead of installing every older SDK side by side, the demo adds only the required runtimes.

```console
dotnetup runtime install 8.0 9.0 10.0
dotnetup runtime install aspnetcore@8.0 aspnetcore@10.0
dotnet --list-runtimes
```

A version without a component name selects the `Microsoft.NETCore.App` runtime. `aspnetcore@10.0` selects the ASP.NET Core runtime, and Windows also supports `windowsdesktop@10.0`. An exact runtime version creates a pinned requirement. The [component installation documentation](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/usecases/install-components.md) describes the currently supported command forms.

The runtime declaration shown inside `global.json` during the session was hypothetical syntax for a future design. The current preview documentation reads only SDK requirements from `global.json`. You specify runtimes directly with `dotnetup runtime install`. [The runtime demo in the session](https://www.youtube.com/watch?v=ZMnyohA5yrw&t=1505s) also notes that this syntax was not finalized.

## A Manifest That Separates Desired State from Installed Files

The update and cleanup model follows the installation. `dotnetup` records a requested channel separately from the concrete version placed on disk.

| State element | Recorded information | Purpose |
| --- | --- | --- |
| Installation specification | Component, channel or exact version, and request source | Determines the update scope and whether the requirement is pinned |
| Installation | Concrete version, architecture, installation root, and shared subcomponents | Calculates file validation and removal scope |
| Environment configuration | `dotnet` access mode and whether `dotnetup` is on `PATH` | Detects differences between the shell profile and current configuration |

The basic flow for reading and updating state uses the following commands.

```console
dotnetup list
dotnetup update
dotnetup list --format json
```

`dotnetup update` resolves every moving channel again and installs a newer version when available. It skips exact-version requirements. After a successful update, garbage collection removes versions no longer required by a remaining installation specification and subcomponents not shared by another installation. When several requirements point to the same installation, the files remain stored once. The [update documentation](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/usecases/update-installations.md) and [state model documentation](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/concepts/how-dotnetup-works.md) describe these responsibilities separately.

OD804 compares the manifest in the user data directory to a lock file for declared system state. That analogy does not make it a contract committed to a repository. `global.json` remains the repository contract, while the manifest acts more like a local ledger connecting installation specifications to physical files. The tool also maintains a hash file to detect manifest content that it did not write, so the state files should not be edited directly.

## A Development Boundary Shared by People and Automation

The same installation process can serve people and automated actors within a defined scope. OD804 divides the primary audience for `dotnetup` into developers and automated actors. Automation includes CI systems as well as LLM-based coding agents. An environment without administrator access can provision the SDK for a repository, and explicit commands and JSON output make its state readable.

Automation can avoid interactive first-time setup with commands such as these.

```console
dotnetup sdk install 10.0.1xx --no-progress --interactive false
dotnetup dotnet test -- --logger trx
dotnetup list --format json --no-verify
```

`dotnetup` disables first-use onboarding when it detects CI or redirected output. `--no-progress` keeps terminal progress rendering out of logs, while `--interactive false` prevents the command from waiting for input. Omit `--no-verify` when automation must verify that recorded files exist and remain valid. The [automation documentation](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/usecases/automation.md) covers these options.

`dotnetup dotnet` applies the environment for the default managed installation root only to its child process. It does not automatically select an arbitrary installation created with `--install-path`. For a custom root, run that root's `dotnet` executable directly or activate it with an environment script. The [command reference](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/reference/dotnetup-dotnet.md) documents this constraint.

`dotnetup dotnet` can also serve as the execution path for a file-based app. On a Unix environment that supports `env -S`, set the first line of `sample.cs` to `#!/usr/bin/env -S dotnetup dotnet` and make the file executable to run it with the managed SDK. Once the `dotnetup` CLI is available, the same path works in an environment without administrator access. [The follow-up example in the dotnetdev post](https://forum.dotnetdev.kr/t/dotnetup-rustup-net-toolchain-manager/14805/2) demonstrates this configuration.

The tool remains scoped to development environments. [The intended-use discussion in the session](https://www.youtube.com/watch?v=ZMnyohA5yrw&t=2055s) retains the existing guidance of using operating-system package managers for framework-dependent production deployments and self-contained deployment for other cases. The [.NET application publishing overview](https://learn.microsoft.com/dotnet/core/deploying/) distinguishes runtime inclusion across deployment modes.

## The Distance Between the Current Preview and the OD804 Roadmap

Some capabilities presented in OD804 are already part of the current command surface, while others are not yet documented publicly. The session divides the roadmap into internal preview, public preview, and post-GA periods. It mentions daily builds, selecting a specific SDK for a single command, self-update, signature verification, agent skills, and CI provider integration.

| Item | Result verified on August 22, 2026 |
| --- | --- |
| Stable, LTS, preview, daily, and numeric channels | Available as SDK and runtime channels |
| `global.json` integration | Supports SDK version and `rollForward`, `sdk.paths`, and optional file updates |
| SDK and runtime components | Supports installation, update, removal, and listing |
| Single-command execution | Provides the `dotnetup dotnet` forwarding command. This preview's help did not expose an option to select a specific SDK version for one command |
| `dotnetup` self-update | Not found in this preview's public command list |
| Runtime declaration in `global.json` | Remains hypothetical session syntax; current documentation covers SDK requirements only |
| Agent skills and CI provider integration | Long-term directions from the session, not found in the current public usage documentation |
| Download verification | The preview installation script verifies an SHA-512 checksum. Official documentation states that daily builds are not code-signed |

SHA-512 checksum verification and code-signature verification do not provide the same assurance. The current [getting-started documentation](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/README.md) describes checksum verification in the preview installation script. [The roadmap section of OD804](https://www.youtube.com/watch?v=ZMnyohA5yrw&t=2539s) presents signature verification for the .NET SDK, runtimes, and `dotnetup` itself as a public-preview goal.

Daily build channels can narrow the scope by major version, feature band, and preview phase, as in `11.0.1xx-daily`. The [daily channel documentation](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/channels/daily.md) warns that these builds are unsupported and not code-signed. They fit short-lived testing better than a long-running development environment.

The current documentation lives as [implementation documentation in the .NET SDK repository](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/index.md). The official overview also warns that distribution details can differ between internal releases. When returning to an installation example later, recording both `dotnetup --version` and `dotnetup --help` preserves the command surface available at that time.

## Pre-Adoption Checklist for the Preview

Before adopting the preview, you can use the [official getting-started documentation](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/README.md) and the requirements of the target environment as the basis for this sequence.

1. Recheck the installation URL and supported operating systems in the official getting-started documentation.
2. Choose Isolation Mode and run commands through `dotnetup dotnet` if the existing `dotnet` should remain the default.
3. Record how the repository's `global.json` and `rollForward` map to a `dotnetup` channel.
4. Separate environments that need a moving channel from builds that require an exact pinned version.
5. Test daily builds briefly in a separate installation root and record the version with the result.
6. Disable progress rendering and interactive input in CI, then inspect the exit code.
7. Set `DOTNET_CLI_TELEMETRY_OPTOUT=1` in environments that must not transmit telemetry.

## Connecting Development Declarations to Installed Toolchains

In summary, `dotnetup` connects desired .NET SDK and runtime state to installed files in a development environment. It does not replace `global.json` with a new format. Instead, it uses the repository's existing declaration as an input for installation and updates. Separating SDKs and runtimes into components is particularly useful for multi-target testing and work that moves across several repositories.

Over the longer term, self-update, broader signature verification, agent skills, and CI integration from the OD804 roadmap could expand the tool's management scope. The capabilities with an immediate effect are user-level installation, `global.json`-based SDK provisioning, separate runtime installation, and bulk updates for tracked channels. Preview and daily builds have different verification levels and should not be treated as equivalent.

The current preview is worth testing in a separate installation root when you work across several local .NET repositories or provision build environments for isolated agents. Production servers governed by operating-system package policies can retain existing deployment methods. Teams that pin an exact SDK can use an exact-version channel, while teams that follow patches within a feature band can base their choice on the mapping between `global.json` `rollForward` values and `dotnetup` channels.

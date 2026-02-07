---
title: "Open Source Contribution in the AI Era: Lessons from the HwpLibSharp Porting Project"
date: 2026-02-07T00:00:00+09:00
draft: false
slug: "hwplibsharp-upstream-management"
tags:
  - .NET
  - C#
  - Java
  - Open Source
  - AI
  - HWP
categories:
  - Development Experience
translationKey: "hwplibsharp-upstream-management"
description: "Sharing my experience porting Java hwplib to .NET with AI coding assistants, and building a 'Living Port' model of open source contribution that coexists with the upstream project."
tldr: "By embedding original Java file hints in C# source headers and letting AI analyze diffs, upstream sync time drops by over 80%. This post introduces a 'Living Port' maintenance strategy that coexists with the original rather than simply forking."
cover:
  image: "images/posts/hwplibsharp-upstream-management.jpg"
  alt: "Image symbolizing collaboration and code porting between open source projects"
---

# Open Source Contribution in the AI Era: Lessons from the HwpLibSharp Porting Project

I've been a Microsoft MVP for 17 years now. One of the most frequently asked questions I've received in the .NET community is "How do I work with HWP files in C#?" The official library from Hancom was built on Windows and COM, leaving virtually no solution for cross-platform .NET environments.

Then I discovered `hwplib` by [@neolord0](https://github.com/neolord0)—a pure Java open source library that parses the HWP file format. The thought immediately struck me: "Porting this to .NET would be a real contribution to the community." But it wasn't going to be easy. The codebase was massive, and it was still being actively updated.

In 2026, I started this work with the help of AI coding assistants.

## Not a One-Time Port, but Continuous Synchronization

At first glance, HWP isn't a format that changes frequently, so you might assume that a one-time port would suffice. But all technology keeps evolving—the upstream project is still actively maintained, and .NET itself continues to change. A one-time effort simply wouldn't be enough.

Traditional forks drift away from the original over time. Eventually, "our version" and "the original version" end up going their separate ways. That's the natural course of things, but I chose a different approach. Rather than a simple fork, I decided to establish a clear identity as a **"Ported Implementation" that lives and breathes alongside the original**.

```text
Upstream project: hwplib (Java)
       ↓ Periodic synchronization
Ported project: HwpLibSharp (C#)
       ↓ .NET-specific enhancements
Ecosystem expansion
```

That's why I wrote this in the README:

> "Decision-making and judgment priority for this project defers to the intentions of @neolord0, the author of the original project."

This wasn't just a matter of courtesy. For two projects to coexist long-term, it's essential to be clear from the start about who sets the direction.

## Porting with AI

Honestly, without AI coding assistants, the initial porting alone would have taken over six months. Upstream synchronization would have been out of the question entirely, and the project would have become yet another abandoned legacy codebase.

But working with AI made an entirely different approach possible.

### What AI Did Well

Syntax conversion was nearly flawless. Converting Java getters/setters to C# properties, adapting naming conventions to C# style, and transforming null checks to nullable reference types—most of this was automated successfully.

AI was also a huge help with library mapping. When replacing Apache POI with OpenMcdf, it quickly identified ".NET equivalents for what this Java library does." It also significantly reduced human error in the repetitive work of tracking upstream changes and reflecting them in the C# version.

### Automated Upstream Change Tracking

One particularly effective practice was **automated upstream change tracking** using AI agents. Whenever a new commit lands in the original hwplib project, the AI agent compares the changed Java source files against their corresponding C# counterparts to identify implementation differences.

To manage this synchronization systematically, I added a hint header at the top of every ported C# source file, explicitly mapping it back to its original Java source.

```csharp
// =====================================================================
// Java Original: kr/dogfoot/hwplib/util/compressors/Compressor.java
// Repository: https://github.com/neolord0/hwplib
// =====================================================================
```

With this header in place, the AI agent can immediately identify "this C# file corresponds to that Java file." When `Compressor.java` changes upstream, the AI locates the corresponding C# file, analyzes the diff, and reports any missing changes or implementation discrepancies. Instead of a human manually cross-referencing hundreds of files, the AI tells you "this section has diverged from the original and needs review."

![AI agent tracking upstream changes and comparing them against C# source files](image.png)

After adopting this approach, the time required for upstream synchronization dropped by over 80%. Previously, I had to read change logs and manually locate and update each related file. Now the AI automatically compiles the list of changes and their impact scope.

### What AI Couldn't Do

On the other hand, domain knowledge—the Section-Paragraph-Control structure of HWP files, the meaning of each control, and the unique characteristics of Korean word processor documents—was entirely my responsibility. Verifying whether AI's plausible-looking code suggestions were actually correct is still a job for humans.

Strategic decisions were the same. Whether to support Native AOT, how to make it work in Blazor WebAssembly, which .NET versions to target—these judgments require a broad understanding of the .NET ecosystem and insight into real user environments. For license text, defining the relationship with the original author, and reflecting the context of the Korean developer community, AI would draft and I would refine.

## Redesigning for the .NET Ecosystem

I didn't stop at simply moving code over. The APIs needed to be refined—without compromising the original project's philosophy and intent—so that .NET developers could use them naturally.

```csharp
// Blazor WebAssembly support (stream-based, no file system)
var hwpFile = HWPReader.FromStream(memoryStream);

// Native AOT compatible, async loading from URL
var hwpFile = await HWPReader.FromUrlAsync(url);
```

These features don't exist in the original Java version. But they're exactly what .NET developers would naturally expect. This made it possible to process HWP files in Azure Functions or render them in the browser with Blazor.

Something interesting happened along the way. Java developers saw the HwpLibSharp README, took ideas from it, and contributed back to the original project's documentation. The .NET version's usage examples ended up helping Java users too.

The text extraction examples for RAG (Retrieval-Augmented Generation) purposes were particularly actively discussed in both communities. What kind of text does an AI need to extract from an HWP document to understand it? That question transcends programming language boundaries.

## From Code Translator to Curator

As this project progressed, I felt my role itself changing. I started out as someone translating code, but now I'm closer to a **curator connecting two ecosystems**. Monitoring upstream changes, collecting requirements from the .NET community, reconciling the practices and philosophies of both worlds, and designing a sustainable synchronization process.

HwpLibSharp currently supports .NET Framework 4.7.2 through .NET 8 and is being used in actual government and public sector projects. But more meaningful than the range of support is that previously impossible scenarios have opened up:

- Serverless HWP processing with Azure Functions
- In-browser HWP rendering with Blazor WASM
- Reading HWP files in .NET MAUI mobile apps
- Integrating HWP documents into AI/LLM RAG pipelines

## Lessons Learned

**AI is an experience multiplier.** My 17 years of .NET experience manifested as several times the productivity through AI. Without that experience, I couldn't have pointed AI in the right direction in the first place. AI doesn't replace experience—it amplifies it.

**Know the boundaries of automation.** Automate syntax conversion, pattern application, and repetitive testing. But strategic decisions, domain validation, and community relationships must remain in human hands. Confusing these boundaries can quickly lead you astray.

**The concept of a "Living Port" rather than a fork.** A structure that doesn't compete with the original but coexists, adding value to each ecosystem. I believe this could be a new form of open source contribution.

**Contribution is more than code.** A single line in a README or one example can save someone three days of frustration. This is especially true in environments like Korea, where unique document formats are in play.

## Closing Thoughts

I built a community because I loved .NET, and I've maintained it for 17 years. The experience and network accumulated along the way are now creating new forms of value through AI as a tool.

The HwpLibSharp project was a blend of technical expertise, community contribution, and experimentation with AI-era development methodology. AI bought me time, and with that time I was able to help more people. Perhaps this is what open source contribution looks like in our current era.

---

**Project Links:**

- GitHub: [rkttu/HwpLibSharp](https://github.com/rkttu/libhwpsharp)
- NuGet: [HwpLibSharp](https://www.nuget.org/packages/HwpLibSharp/)
- Upstream project: [neolord0/hwplib](https://github.com/neolord0/hwplib)

Feedback and contributions are always welcome. Feel free to reach out via [GitHub Issues](https://github.com/rkttu/libhwpsharp/issues).

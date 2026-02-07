---
title: "Porting Java hwplib to .NET: An Open Source Journey with AI"
date: 2026-01-08T00:00:00+09:00
draft: false
slug: "hwplibsharp-dev-journey"
tags:
  - .NET
  - C#
  - Java
  - Open Source
  - AI
  - Porting
  - HWP
categories:
  - Development Experience
translationKey: "hwplibsharp-dev-journey"
cover:
  image: "images/posts/hwplibsharp-dev-journey.jpg"
  alt: "Abstract image representing code porting from Java to .NET"
description: "I completely ported the Java-based hwplib to .NET in just 3 weeks using AI coding assistants and Visual Studio 2026's agent-based debugger."
tldr: "The hardest part of porting 641 files and 50K lines of Java was replacing Apache POI with OpenMcdf and fixing zlib compression differences. VS 2026's agent debugger solved it by automatically setting breakpoints and tracing variables."
---

## It Started with Simple Curiosity

"I wish I could handle HWP files directly in .NET..."

I'm probably not the only .NET developer who has had this thought. HWP files are still widely used in Korea, especially in government agencies, but the .NET ecosystem lacked a proper open-source library to handle them.

Previously, the only way to work with HWP files in .NET was to use the HWP ActiveX control's COM type library that comes with Hangul (the word processor), limited to Windows. Unfortunately, even this support has been discontinued, leaving us with no options.

Then I discovered [hwplib](https://github.com/neolord0/hwplib), written in Java. This library, steadily maintained by neolord0, provided comprehensive support for reading and writing HWP files.

In the past, porting such a library would have been unthinkable without strong dedication and purpose. But with the emergence of advanced AI models, I felt curious about taking on this new challenge.

Here's the story of my 3-week journey.

## The Project by Numbers

Before diving into the story, let me present the scale of the Java project:

| Item | Details |
| ------ | ------ |
| Original Project | [neolord0/hwplib](https://github.com/neolord0/hwplib) (Java) |
| Ported Project | [rkttu/libhwpsharp](https://github.com/rkttu/libhwpsharp) (C#) |
| Target Frameworks | .NET Standard 2.0, .NET Framework 4.7.2, .NET 8 |
| Total Commits | 54 |
| Development Period | 2025-12-16 ~ 2026-01-08 (about 3 weeks) |
| Initial Ported Code | 641 files, 50,010 lines |

641 files, 50,000 lines. Honestly, when I first saw these numbers, I wondered, "Is this even possible?"

## Day One: Large-Scale Code Conversion with AI

### 50K Lines in One Day?

On December 16, 2025, I started the project. Under normal circumstances, converting 50K lines of Java code to C# would have taken months. But the AI coding assistant was a game changer.

I handed Java files to the AI and asked it to convert them to C#. Of course, mechanical conversion wasn't enough. Java and C# look similar but have many subtle differences.

```java
// Java
public byte getValue() { return value; }
public void setValue(byte value) { this.value = value; }
```

```csharp
// C#
public byte Value { get; set; }
```

The AI handled these pattern conversions well. But the real challenge was elsewhere.

## The Biggest Challenge: From Apache POI to OpenMcdf

### The OLE2 Compound Document Swamp

HWP files are based on Microsoft's OLE2 Compound File Binary Format. Simply put, it's a format where multiple "streams" are stored within a single file, like a folder structure.

In Java, the Apache POI library handles this format, but there's no direct equivalent in .NET. I had to use OpenMcdf instead, which unfortunately has a completely different API from Apache POI.

```java
// Java (Apache POI)
DirectoryEntry root = poiFs.getRoot();
DocumentInputStream stream = root.createDocumentInputStream("Section0");
```

```csharp
// C# (OpenMcdf)
CFStorage root = compoundFile.RootStorage;
CFStream stream = root.GetStream("Section0");
byte[] data = stream.GetData();
```

The concepts were similar, but the implementations were completely different. I was honestly anxious about whether the AI could understand, analyze, and refine these differences.

The data inside HWP files is compressed with zlib. Java and C#'s decompression libraries behave slightly differently, producing different results from the same input.

After hours of byte-by-byte comparison and debugging, I found the cause: the zlib header handling was different. Fortunately, thanks to the meticulous unit tests created by neolord0, I could discover these issues. This is where I experienced the power of Visual Studio 2026's "agent-based debugger."

As many of you know, Visual Studio 2026 has been refactored to leverage AI agents more powerfully than any previous version. While it's common to focus on "auto-writing" code with agents like VS Code, what was fascinating in this porting project was how, when running unit tests in debug mode and encountering failures, the agent would immediately identify "what's wrong," set breakpoints on its own, track variables and call stacks through the internal MCP server, and respond accordingly.

Of course, not all problems could be solved this way, but without this tool support, I might never have finished.

## The Thrill of 100% Test Pass

### From Red to Green

The original hwplib project had test cases created by neolord0. These tests were like a lighthouse for me. I had a clear goal: "Just pass all of these."

The first test run was devastating. Only 3 out of 47 passed. Red X marks filled the screen. But I couldn't give up. I tracked down each failure, fixed the code, and ran the tests again.

Fixing Section parsing made 5 more pass. Fixing control parsing turned 10 more green. Table handling, GSO (graphic) objects... Like fitting puzzle pieces, I solved them one by one.

And finally, that moment came.

```text
Tests Passed: 47/47
```

I stared at the monitor. I checked multiple times if it was really 47/47. I had coffee and ran it again. Still 47/47. Finally, I could breathe.

This was what I had been working towards.

## The Journey for More Users

### "Does it work on macOS?"

The joy of passing tests was short-lived. Reality came knocking. The first question was predictable.

> "Can I use this on Mac?"

Oops. I had initially used `System.Drawing` for image processing, which is essentially Windows-only. With cross-platform being the norm since .NET Core, having a Windows-only library felt like a significant limitation.

After some thought, I decided to switch to **SkiaSharp**. It's a .NET wrapper for Google's Skia graphics engine that works identically on Windows, macOS, and Linux. Rewriting all the image-related code was tedious, but it was worth it to reach more developers.

### "We're still on .NET Framework 4.7.2..."

The second challenge was more painful. Corporate environments are more conservative than you'd think. No matter how good .NET 8 is, many places can't move away from .NET Framework due to legacy system compatibility.

The problem was... I had enthusiastically used all the latest C# 12 syntax.

```csharp
// C# 12 - File-scoped namespace (one line!)
namespace HwpLib.Reader;

public class HwpReader { }
```

To use this on .NET Framework, I had to revert to the old syntax.

```csharp
// C# 8 compatible - Traditional namespace (braces required)
namespace HwpLib.Reader
{
    public class HwpReader { }
}
```

"Just add braces, right?" you might think. True. But that's **582 files**.

The result was a massive diff: 51,480 lines added, 49,701 lines deleted. Opening that commit on GitHub would freeze the browser. I also had to downgrade the C# language version step by step from 12.0 to 8.0. `required` keyword, `init` accessor, file-scoped namespaces... It felt like going back in time, giving up all the convenient features one by one.

But thanks to this pain, libhwpsharp now works on almost every .NET environment from .NET Framework 4.7.2 to .NET 8.

## What I Learned from Collaborating with AI

After three weeks with this project, I developed my own know-how for collaborating with AI.

### When AI Shines

The most impressive aspect was efficiency in repetitive tasks. Converting hundreds of Java files to C# would take a human days of tedious work. But for AI, it was just "convert this to C#" and done.

Adding XML documentation comments was similar. I needed to add over 2,000 lines of API documentation to 111 files. I just told the AI "explain what this class does in comments," and it understood the context and generated appropriate descriptions.

But the real game changer in this project was **Visual Studio 2026's agent-based debugger**.

Honestly, AI coding assistants are everywhere now. VS Code has them, JetBrains IDEs have them, you can even use them in web browsers. Code auto-completion and generation features have become commodities. But Visual Studio 2026 differentiated itself elsewhere.

When running unit tests in debug mode and encountering failures, the agent starts working on its own. You don't even need to ask "What's wrong?" The agent sets breakpoints by itself, tracks variable values, and analyzes the call stack. Watching it collect debugger state in real-time through the internal MCP server and find the root cause of problems felt like having a senior developer doing pair debugging with me.

This feature particularly shone when tracking the zlib decompression issue. Same byte array input in Java and C#, different results. Normally, I would have had to set breakpoints in both codebases and spend hours comparing byte by byte. But the agent-based debugger started analyzing on its own with just the request "track why these two results are different," and pinpointed the difference in header handling.

This is Visual Studio 2026's **moat**, in my opinion. Anyone can generate code, but the deep integration of debugger and AI is something only Microsoft, with decades of experience building debugging tools, can do. Without this feature, this project might have taken 3 months instead of 3 weeks.

### When Humans Are Still Needed

But I couldn't leave everything to AI. When I asked "What should I use instead of Apache POI?", AI offered several options, but judging and deciding which library actually fit the project was my job.

Debugging especially still felt like human territory. When tracking why zlib decompression results differed, asking AI "Why is this different?" didn't yield clear answers. I had to dump byte arrays myself and compare Java and C#'s behavior to find the cause.

### A New Definition of Pair Programming

In conclusion, AI was like the best junior developer. It does what you tell it really well. Fast, tireless, no complaints. But deciding "what to tell it" is still the senior's job.

However, Visual Studio 2026's agent-based debugger slightly changed this equation. In code generation, AI plays the junior role, but in debugging, AI actually acted more like a senior. When I was stuck thinking "why isn't this working?", the agent would formulate hypotheses, verify them, and point out "this seems to be the problem."

Traditional pair programming was one person coding while the other reviews alongside. But AI-era pair programming is different. For coding, AI writes and humans review. For debugging, AI analyzes and humans judge. Roles flexibly change depending on the situation.

What I realized through this project is that in the AI era, developers spend more time on "deciding what code to write" than actually writing code. And good tools help make those decisions faster and more accurate. Visual Studio 2026 was such a tool.

## Wrapping Up

The 3-week journey has ended. 54 commits, 641 files, over 50K lines of code.

Now [libhwpsharp](https://github.com/rkttu/libhwpsharp) is deployed on NuGet, and anyone can handle HWP files in .NET projects. Of course, there's still a long way to go. When encountering various HWP files in the field, unexpected edge cases will surely emerge.

Still, taking that first step, and confirming that with AI, I could take on projects of a scale I never would have attempted alone—that alone made this a meaningful experience.

If you need to work with HWP files in .NET, please try it and share your feedback!

## Future Plans

libhwpsharp is just the beginning. neolord0 has created several other useful projects besides hwplib, and I plan to port them to .NET as well.

### Porting hwpxlib

The first goal is [hwpxlib](https://github.com/neolord0/hwpxlib). HWPX is an open document format newly introduced by Hancom, using an XML-based compressed file structure instead of the traditional binary HWP format. With HWPX adoption growing, especially in government agencies, .NET needs to be able to handle this format too.

Fortunately, since HWPX is XML-based, porting should be easier than HWP. After struggling in the OLE2 compound document swamp, a ZIP + XML combination feels like a vacation.

### HWP → HWPX Conversion Tool

The second goal is porting neolord0's HWP to HWPX conversion tool. There's clearly demand for migrating legacy HWP files to the new HWPX format. Once this tool is ported, the complete pipeline for Korean document processing in the .NET ecosystem will be complete.

I'll share these projects on the blog when they're done. Stay tuned!

## Technical Details

Finally, here are the main technical challenges I encountered during development.

### Apache POI → OpenMcdf Transition

| Aspect | Java (POI) | C# (OpenMcdf) |
| ------ | ------------ | --------------- |
| Directory Access | `DirectoryEntry` | `CFStorage` |
| Stream Reading | `DocumentInputStream` | `CFStream` |
| Resource Management | `close()` | `Dispose()` / `using` |

### Overcoming Language Differences

| Java | C# | Solution |
| ------ | ----- | ---------- |
| `byte` (signed) | `byte` (unsigned) | Use `sbyte` or convert |
| `getXxx()` / `setXxx()` | Property | Auto-convert |
| `Iterator<T>` | `foreach` | Use LINQ |
| throws declaration | None | try-catch pattern |

## Acknowledgments

This project would not have been possible without [neolord0](https://github.com/neolord0) (Park Sung-kyun)'s [hwplib](https://github.com/neolord0/hwplib).

The HWP file format has sparse official documentation and subtle version-specific differences, making reverse engineering challenging. Despite this, Park Sung-kyun has steadily developed and maintained hwplib for years. The meticulously written unit tests, clear code structure, and release under Apache License 2.0 made this porting project possible.

The 47 test cases especially served as a lighthouse during the porting process. Having the clear goal of "just pass these" allowed me to complete the project in just 3 weeks.

This is how the open-source ecosystem grows—standing on each other's shoulders. Someone's quiet dedication opens new possibilities for others. The seed that Park Sung-kyun planted in the Java ecosystem is now sprouting in the .NET ecosystem.

Thank you sincerely. 🙏

## Links

- **GitHub**: [rkttu/libhwpsharp](https://github.com/rkttu/hwplibsharp)
- **NuGet**: [HwpLibSharp](https://www.nuget.org/packages/HwpLibSharp/)
- **Original Project**: [neolord0/hwplib](https://github.com/neolord0/hwplib)

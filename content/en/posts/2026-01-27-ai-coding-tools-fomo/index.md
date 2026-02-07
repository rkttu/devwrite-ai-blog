---
title: "How Not to Be Swayed by FOMO About AI Coding Tools"
date: 2026-01-27T00:00:00+09:00
draft: false
slug: "ai-coding-tools-fomo"
tags:
  - AI
  - Coding Tools
  - Developer Culture
  - Productivity
categories:
  - Developer Culture
translationKey: "ai-coding-tools-fomo"
cover:
  image: "images/posts/ai-coding-tools-fomo.jpg"
  alt: "A balanced relationship between AI coding tools and developers"
description: "Don't be swayed by AI coding tool hype. Deep utilization of synchronous sessions with HITL is a more practical productivity strategy than parallel agents."
tldr: "Don't be swayed by AI coding tool hype. Deep utilization of synchronous sessions with HITL is a more practical productivity strategy than parallel agents."
---

When following news from the AI coding tools industry these days, you'll notice that every time a new tool emerges, messages like "this is the future" and "you'll fall behind if you don't use it" are emphasized to an almost excessive degree. Background agents, parallel AI sessions, autonomous coding—new concepts appear every week, making you feel like you're falling behind the times if you don't adopt them.

But is it really healthy to take these messages at face value? I don't think so.

## How Hype Is Created

There are structural reasons for the hype in the AI coding tools industry. Executives of companies that need to generate revenue from AI technology are in a position where they must satisfy investors and shareholders. This creates a dual audience problem in their messaging. They promise "productivity improvements" to developers while simultaneously providing investors with narratives of "market dominance" and "indispensable tools."

In this process, "half-truths" pour out. "AI is revolutionizing coding" isn't wrong, but it gets packaged together with the leap that "you'll be left behind if you don't use this tool right now." Complete lies are easily refuted, but exaggerated truths are difficult to verify.

These messages start from AI companies, pass through executives and technical leaders of some forward-thinking companies as well as influencers, and reach practicing developers. The problem is that intermediary spreaders tend to amplify rather than filter the message because of their own interests. The image of "adopting the latest technology" itself becomes their market positioning and sales tool.

## The Promise and Reality of Background Agents

One of the recently emphasized trends is "background agents." Features like VS Code's Agent HQ and Google Antigravity's Manager View are representative examples. The core promise of these tools is that if you delegate a task, the AI will autonomously execute it in a separate environment, and developers can do other work. Claims that running multiple agents in parallel will multiply productivity by several times also accompany this.

However, there's a fundamental problem with this promise. Background agents are essentially designed in a direction that intentionally removes Human-In-The-Loop (HITL). The concepts of "asynchronous work," "autonomous execution," and "review after delegation" inherently presuppose eliminating intermediate intervention points.

Accidents are already occurring in practice. There have been reports of Google's Antigravity agent deleting an entire hard drive partition. When working in a traditional chat window, you can check results at each step and intervene midway, but with background agents, it's difficult to notice even when things are going in the wrong direction until completion.

## The Contradiction Between Disclaimers and Marketing

An interesting point is that all AI service providers include disclaimers stating "AI can make mistakes, so please verify." Yet at the same time, their marketing emphasizes "agents that work autonomously." If you take both messages seriously, the utility of parallel agents is quite limited.

The claim that "you need to run multiple agents in parallel for real productivity" directly conflicts with the warning to "always review AI output." If even a single session's output requires verification, running five simultaneously multiplies the verification burden fivefold—it doesn't multiply productivity fivefold. The bottleneck simply moves from generation to verification; total throughput doesn't increase linearly.

Paradoxically, even with five people working in parallel, quality isn't guaranteed without management and review. Coordination costs increase, consistency breaks down, and quality variance in outputs grows. This is a fact that has been repeatedly verified in software engineering for decades. There's no reason why AI agents should be exempt from this principle.

## The Attitude Tech Leaders Need

From the perspective of a CTO or technical decision-maker, the most important virtue in this situation is "calm distance and judgment." The problem is that this is structurally difficult to practice. If you make calm judgments, you risk being evaluated as "passive about innovation" or "out of touch with trends," and the correctness of that judgment can only be verified years later.

Looking at the bigger picture, executives who must make decisions without deep understanding of technology (an anchor) have no choice but to rely on external signals. But since most of those signals come from sources with vested interests, they end up in a vulnerable state where they easily become anxious and easily become impatient.

One practical alternative is a Lab strategy. Securing space where the organization can learn and evaluate new technologies while controlling the scope and cost of experiments. Allow aggressive tool choices in areas where failure costs are low (internal tools, prototypes), and maintain proven tools for core business areas. This way, you can maintain the narrative of "we're actively utilizing AI tools" while managing actual business risk.

## The Importance of Harness: The Horse and Harness Metaphor

Recently, Anthropic researcher Boris Cherny presented an interesting metaphor. "Claude is the horse, and Claude Code is the harness. To ride a horse, you need a saddle, and that saddle makes a big difference when riding." According to his explanation, the reason AI coding didn't work properly for so long was not only because models weren't good enough, but also because the scaffolding (tools) on top of the models wasn't good enough.

The important point in this metaphor is that the human programmer is still in the loop. Just as you use harness to guide a horse in the desired direction, developers control AI through tools. And the quality of those tools greatly influences the quality of the output.

## Rediscovering Traditional IDE Infrastructure: The Visual Studio 2026 Case

{{< youtube oTEU-FLCDuk >}}

In this context, Visual Studio 2026's debugger agent is noteworthy. When a unit test fails, this feature autonomously performs the following process: collects context from the workspace (test code, related sources, recent modifications), forms hypotheses about the cause of failure, modifies code based on analysis, runs tests in the debugger to verify, and if problems persist, refines hypotheses using debugger insights, repeating until tests pass.

The key here is that all of this operates on top of IDE infrastructure accumulated over decades. Breakpoint manipulation, real-time variable state tracking, call stack analysis, symbol resolution, profiling—these are capabilities that lightweight terminal-based agents cannot easily implement. "Forming and verifying hypotheses" by AI only becomes meaningful automation when backed by such infrastructure.

From a .NET developer's perspective, switching to terminal-based tools following trends doesn't necessarily mean productivity improvement. Rather, mature traditional IDEs combined with AI can generate stronger synergy. New isn't always better.

## Deepening Synchronous Sessions: A Realistic Alternative

If you don't have confidence or trust in background agents or modes that run without HITL, there's no reason to force yourself to use them. Instead, looking deeper at synchronous session-based workflows that maintain HITL, as we do now, is a strategy that secures both safety and efficiency.

As proficiency increases in areas like systematizing prompt patterns, optimizing context provision methods, deep utilization of IDE integration features, and appropriate work unit division, you develop criteria to soberly evaluate the value of new tools when they appear.

## Conclusion: Depth of Tool Use Over Tool Novelty

If the warning to "please verify" is a substantive operational guideline rather than a formalistic disclaimer, the appropriate way to use current AI tools is deep utilization of single or few sessions with HITL maintained. Parallel autonomous agents will only become a meaningful option after AI reliability becomes much higher than it is now.

The depth of tool use has a greater impact on practical productivity than tool novelty. And this becomes real competitiveness that isn't swayed by hype. Whenever new tools appear, I encourage you to develop the habit of first asking "what actual problem does this solve?"

Tools are means, not identity.

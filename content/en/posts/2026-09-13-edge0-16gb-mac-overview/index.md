---
title: "Edge0 Part 1: A 35B Local LLM and Grounded Agent on a 16GB Mac"
date: "2026-09-13T09:00:00+09:00"
draft: false
slug: "edge0-16gb-mac-overview"
translationKey: "edge0-16gb-mac-overview"
description: "Running Edge0-35B on a 16GB M2 MacBook Air, with official-document grounding, Korean translation, and practical limits for a local RAG agent."
tags: ["Edge0", "Local LLM", "RAG", "Apple Silicon", "Microsoft Learn"]
categories: ["Artificial Intelligence"]
tldr: "I ran Edge0-35B on a 16GB M2 MacBook Air and supplied Microsoft Learn references for technical answers. This article separates execution feasibility, changes in grounded answers, and input-length effects to explain how the model and host share responsibility."
cover:
  image: "images/posts/edge0-16gb-mac-overview.webp"
  alt: "Glass blocks above a silver laptop and stacked storage devices representing local model inference."
  caption: "AI-generated illustration based on the article's topic."
license: "CC BY-NC 4.0"
---

As of September 13, 2026, Edge0 provides an MLX backend for Apple Silicon and the `Edge0-35B-A3B-preview` model. I ran the model on a 16GB M2 MacBook Air, then built a technical expert agent that answers using Microsoft Learn references.

This series covers the requirements for running a 35B-class model, changes in answers after adding references, Korean input and output, streaming measurements, and conditions for an internal PoC. The complete runnable code is available in the [Edge0 Microsoft Technology Expert Agent Gist](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d).

This first article starts with my experience running the model. It compares experiments with external references and shorter inputs, then outlines the agent implemented in the rest of the series.

The following scope applies to the release status and measurements:

> I checked the public documentation on September 13, 2026. The model is in preview, and its configuration and performance may change. Timings and answer examples come from individual experiments I ran; they do not establish performance across all devices or questions.

## A 35B model that reads required weights from SSD

Edge0's memory strategy starts with the sparse MoE architecture. According to the [project description](https://github.com/Edge0-AI/Edge0), Edge0 keeps expert weights on SSD and reads the portions needed for inference. Its memory behavior therefore differs from loading the entire model into RAM at startup.

The public model and my test environment have the following characteristics:

| Item | Value | Scope |
| --- | --- | --- |
| Public model | `Edge0-35B-A3B-preview` | A 35B-class MoE model with 4-bit quantization |
| Model file size | About 23GB | Checkpoint size on SSD |
| Official memory measurement | About 2.9GiB | Peak active MLX allocator memory with a short context |
| My test device | M2 MacBook Air, 16GB | The laptop used in this series |
| Initial generation experiment | About 43.8 seconds for 128 tokens | One specific input and execution setup |

The official memory figure does not represent total system memory use. The operating system, tokenizer, caches, and context length add to the overall footprint. The [architecture documentation](https://github.com/Edge0-AI/Edge0/blob/main/docs/architecture.md) explains how the runtime loads weights.

The model generated text on my device. This established that it could run on a 16GB laptop, while response speed and answer accuracy remained separate evaluation tasks.

## Shifting answer generation toward external evidence

In zero-shot experiments that supplied only a question, I saw incorrect explanations of the compilation models used by C# Native AOT and Rust. Similar errors appeared with English questions. I did not run a quality evaluation with enough questions to judge the model's overall performance from these observations.

I therefore reduced the amount of factual knowledge I expected the model to supply on its own. I used questions about .NET Native AOT and JIT that I could assess myself, and included the [Microsoft Learn documentation for Native AOT](https://learn.microsoft.com/dotnet/core/deploying/native-aot/).

The resulting agent divides responsibilities as follows. The original diagram labels are retained:

```text
Edge0
    질문과 문서의 내용 파악
    관련 근거 선택
    근거에 따른 답변 생성

외부 시스템과 Python 호스트
    공식 문서 검색
    입력 자료 구성
    대화 상태 관리
    한국어 입출력 처리
```

The experiment focused on whether the model could read supplied documents and construct an answer suited to the question.

## An answer that acknowledged insufficient evidence

I compared three ways to provide context: the question alone, the question with Microsoft Learn material, and a stronger instruction to answer only within the supplied material. In this series, I call these reference inputs grounding material.

With references available, the model explained native code generation at publish time and whether JIT was used. It also reflected restrictions on runtime code generation and dynamic loading. I checked these answers against the [limitations of Native AOT deployment](https://learn.microsoft.com/dotnet/core/deploying/native-aot/#limitations-of-native-aot-deployment).

When I asked about CoreCLR Dynamic PGO details absent from the grounding material, I received this response:

```text
The supplied reference does not provide enough information.
```

That answer marked the boundary of the available evidence. A single response does not guarantee the same behavior every time, but it gave me a reason to include an insufficient-evidence rule in later prompts.

## Testing an incorrect premise in the question

I also tested how the model handled a question containing errors. I presented the claims that Native AOT uses runtime JIT to generate code it could not find at publish time, and that `Reflection.Emit` fills that gap. I asked the model to assess both claims using Microsoft Learn material.

The model rejected both claims. The [official documentation](https://learn.microsoft.com/dotnet/core/deploying/native-aot/) states that Native AOT applications do not use a JIT compiler while running and do not support runtime code generation such as `System.Reflection.Emit`.

In this experiment, the model assessed the question's premises against the supplied references. I carried that approach into the agent by displaying sources alongside the answer so readers could compare it with the original documentation.

## Processing time as the input material shrinks

I compared total processing time while reducing the amount of grounding material for the same question. This is also why the [sample code](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d) limits the number and length of search results.

| Grounding material size | Total processing time | Answer observation |
| --- | --- | --- |
| About 6.7KB | About 94 seconds | Baseline answer |
| About 3.4KB | About 78 seconds | Answer compared after reducing the material |
| About 1.7KB | About 48 seconds | Core answer retained |

These are individual execution records, not a benchmark with controlled repetition counts and cache states. Material size is measured in bytes and differs from the number of input tokens the model processes. These results alone cannot attribute the entire time reduction to shorter prefill.

Selecting passages relevant to the question can reduce the input sent to the model. I continued comparing answer quality and latency so that shorter references would not remove essential evidence.

## An agent that connects search and translation

The final sample accepts a Korean question, searches and generates an answer in English, then translates the answer into Korean. A Python host controls this sequence in the [complete Gist](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d).

The original flow diagram shows the call order:

```text
한국어 질문
    ↓
질문 정규화와 Apple Translation
    ↓
Microsoft Learn 검색
    ↓
관련 구절을 그라운딩 자료로 구성
    ↓
Edge0-35B의 영어 응답 스트리밍
    ↓
문장 단위 Apple Translation
    ↓
한국어 답변과 출처 출력
```

Because the Python host manages search and state, the implementation does not depend on autonomous tool selection by the model. The model reads documents and synthesizes an answer.

Model inference and translation run on the Mac, but Microsoft Learn search sends queries to an external service. The local RAG setup in this series includes internet search and is not fully offline.

## Follow-up experiments after establishing feasibility

These experiments established that a 35B-class model could run on my 16GB M2 MacBook Air and construct answers from official documentation. Recording both errors without references and changes after adding them helped me divide responsibilities between the model and its host.

Input length and the wait for the first response directly affect the current setup. Faster hardware and other backends remain subjects for later comparison. {{< series-link slug="edge0-setup-microsoft-learn-translation" text="Part 2" >}} prepares the Edge0 server, Microsoft Learn CLI, and Apple Translation, including per-terminal virtual environments and the model path.

Read the series in order:

1. {{< series-link slug="edge0-16gb-mac-overview" text="This article" >}}
2. {{< series-link slug="edge0-setup-microsoft-learn-translation" text="Microsoft Learn and Apple Translation Setup" >}}
3. {{< series-link slug="edge0-local-rag-agent" text="A Local RAG Agent with Microsoft Learn Search" >}}
4. {{< series-link slug="edge0-streaming-ttft-metrics" text="Measuring TTFT and Streaming Output Rate" >}}
5. {{< series-link slug="edge0-real-benchmark-and-poc" text="M2 Air 16GB Measurements and an Internal PoC" >}}

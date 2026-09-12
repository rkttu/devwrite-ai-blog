---
title: "Edge0 Part 5: M2 Air 16GB Measurements and an Internal PoC"
date: "2026-09-17T09:00:00+09:00"
draft: false
slug: "edge0-real-benchmark-and-poc"
translationKey: "edge0-real-benchmark-and-poc"
description: "Analyze an Edge0 RAG run on a 16GB M2 MacBook Air: 53.47-second TTFT, event-based output rate, grounding limits, and conditions for an internal PoC."
tags: ["Edge0", "Local LLM", "RAG", "Apple Silicon", "Microsoft Learn"]
categories: ["Artificial Intelligence"]
tldr: "One request took about 2.6 seconds through search, then 53.47 seconds from the Edge0 request to first content and 82.11 seconds to stream completion. This article interprets the roughly 4.15 events-per-second rate from 119 content events and defines follow-up comparisons within the limits of a single run."
cover:
  image: "images/posts/edge0-real-benchmark-and-poc.webp"
  alt: "A laptop on a measurement platform beside test instruments and a desktop computer, representing a proof of concept."
  caption: "AI-generated illustration based on the article's topic."
license: "CC BY-NC 4.0"
---

I ran an agent that connects Microsoft Learn search, Edge0 streaming, and sentence-by-sentence Korean translation on a 16GB M2 MacBook Air. The [sample Gist](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d), checked on September 13, 2026, includes the complete code and an execution result with a TTFT of 53.47 seconds.

This final article covers the test question, time through search and first response, evidence behind the answer, interpretation of output rate, follow-up optimization, and conditions for an internal PoC. The results use the client-side measurements described in {{< series-link slug="edge0-streaming-ttft-metrics" text="Part 4" >}}.

We start with the execution logs and metrics, compare the stages, and distinguish what the current result supports from what requires further experiments.

The following scope applies when comparing the numbers:

> I checked the documentation on September 13, 2026. These figures come from a single run with a particular question and set of search results. This record does not establish all software versions, cache states, or repeated measurements from that run. The value labeled `tok/s` was calculated from SSE events containing content.

## A single run with a Native AOT question

The experiment used a 16GB M2 MacBook Air and `Edge0-35B-A3B-preview`. The Python host searched Microsoft Learn and used Apple Translation for input and output, as described in the [Gist's run instructions](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d).

I entered the following question:

```text
NativeAOT에서 Reflection.Emit을 사용할 수 있는지도 설명해주세요.
```

The experiment checked whether the model could read retrieved official documentation and judge support for runtime code generation, rather than evaluating its general knowledge. I do not generalize this one result into average device performance or answer quality for other questions.

## The wait between search completion and first response

Status messages in the [sample code](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d) show elapsed time from the start of input processing. TTFT uses a separate reference timestamp at the start of the Edge0 request.

### About 2.6 seconds for question conversion and search

The experiment's Korean progress messages recorded this sequence through search completion. The current Gist displays the same types of messages in English:

```text
[   0.0s] 한국어 질문 정규화
[   1.3s] 영어 검색 질의 생성 완료
[   1.3s] Microsoft Learn 검색
[   2.6s] 관련 문서 3개 검색 완료

근거 자료
  [1] Native AOT deployment
  [2] Introduction to AOT warnings
  [3] ASP.NET Core support for Native AOT
```

The roughly 2.6-second interval includes Korean question normalization, English query generation, and Microsoft Learn search. In this run, that interval was shorter than the subsequent wait for the first response.

### A TTFT of 53.47 seconds after the Edge0 request

After passing the search results to the server, the host displayed waiting status until the first content arrived:

```text
[   2.6s] Edge0-35B에 요청 전달
[   7.6s] Edge0 처리 중, 첫 토큰 대기 5초
[  12.6s] Edge0 처리 중, 첫 토큰 대기 10초
[  17.7s] Edge0 처리 중, 첫 토큰 대기 15초
[  22.7s] Edge0 처리 중, 첫 토큰 대기 20초
[  27.7s] Edge0 처리 중, 첫 토큰 대기 25초
[  32.7s] Edge0 처리 중, 첫 토큰 대기 30초
[  37.7s] Edge0 처리 중, 첫 토큰 대기 35초
[  42.8s] Edge0 처리 중, 첫 토큰 대기 40초
[  47.8s] Edge0 처리 중, 첫 토큰 대기 45초
[  52.8s] Edge0 처리 중, 첫 토큰 대기 50초
[  56.1s] 첫 토큰 수신 (TTFT 53.5초)
```

The time from input-processing start to first content was about 56.1 seconds, while TTFT measured from the Edge0 request was 53.47 seconds. The two values use different starting points.

TTFT can include client processing, server queueing, tokenization, prefill, and the first generation step. Without server-side instrumentation, I do not interpret all 53.47 seconds as prefill time. In this record, waiting for first content after the Edge0 request was the longest interval.

## Checking the generated answer against official documentation

After the first English content arrived, the host accumulated sentences, translated them, and displayed the Korean answer. The following reproduces the generated result from the experiment:

```text
전문가> 아니요, 네이티브 AOT 애플리케이션에서는
`System.Reflection.Emit`를 사용할 수 없습니다.

네이티브 AOT는 `System.Reflection.Emit`를 포함하는
런타임 코드 생성을 명시적으로 금지합니다 [1].

컴파일러는 `RequiresDynamicCodeAttribute`를 사용하는
메서드에 대해 네이티브 코드를 생성할 수 없습니다.

이러한 경고는 해당 멤버가 AOT와 근본적으로 호환되지
않음을 나타냅니다.

가장 좋은 해결 방법은 네이티브 AOT로 빌드할 때 메서드를
호출하지 않고 AOT와 호환되는 다른 것을 사용하는 것입니다 [2].
```

The central judgment, that `System.Reflection.Emit` is unsupported, matches the [Native AOT limitations](https://learn.microsoft.com/dotnet/core/deploying/native-aot/#limitations-of-native-aot-deployment). The meaning and handling of individual AOT warnings can be assessed at the relevant call sites using the [AOT warning documentation](https://learn.microsoft.com/dotnet/core/deploying/native-aot/fixing-warnings#react-to-aot-warnings). Verifying that one judgment does not validate every other explanation in the generated answer.

The host displayed those two documents along with the [Native AOT support documentation for ASP.NET Core](https://learn.microsoft.com/aspnet/core/fundamentals/native-aot). Readers can match citation numbers in the answer to those sources.

## Output rate calculated from content events

The final log recorded a TTFT of 53.47 seconds, total generation time of 82.11 seconds, a completion count of 119, 28.64 seconds after the first response, and 4.15 `tok/s`. Applying the actual definitions in the [measurement code](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d) gives the following interpretation:

| Metric | Measured value | Interpretation |
| --- | --- | --- |
| Question processing and search | About 2.6 seconds | Input-processing start to source selection |
| TTFT | 53.47 seconds | Edge0 request reference time to first content receipt |
| Total generation time | 82.11 seconds | Edge0 request reference time to end of stream reception |
| Content-event count | 119 | Count stored in the sample's `completion_tokens` field |
| Time after first response | 28.64 seconds | First content receipt to reception end |
| Event-based output rate | About 4.15 events/second | 119 ÷ 28.64, labeled `tok/s` in the original log |

Once the first response began, translated sentences appeared progressively. TTFT ends at receipt of the first English content; the first Korean sentence requires additional buffering and translation time. Total generation time likewise does not measure the point when all Korean translation and display have finished.

These measurements can compare changes within the same setup. Comparing token throughput across models or servers requires aligned token counts and measurement intervals. The current figures do not establish the server's pure internal decode performance.

## Follow-up comparisons of grounding length and cache state

In a separate experiment, reducing grounding from about 6.7KB to about 1.7KB reduced total processing time from about 94 seconds to about 48 seconds while retaining the core answer. The {{< series-link slug="edge0-16gb-mac-overview" text="comparison in Part 1" >}} and the [Gist's input limits](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d) provide variables for further experiments.

The cost of processing long inputs may affect latency, but the earlier comparison did not control cache state or repetition counts. The following comparisons can narrow down the causes:

1. Fix the question and search results and record a baseline run.
2. Rerank the material, reduce grounding size, and compare whether the answer retains its essential evidence.
3. Check support and conditions for prefix caching, then measure before and after enabling it.
4. Record cache state separately for requests immediately after process startup and for repeated requests.
5. Repeat measurements on other Apple Silicon devices with identical input and generation length.
6. Compare additional backends when released, using the same requests and measurement definitions.

This sequence describes future comparisons. The current sample does not implement a reranking model or prefix caching. The first comparison can examine how shortening references affects both answer evidence and the wait for the first response.

## Conditions for an internal PoC and other backends

The M2 MacBook Air experiment checked whether a single user's question could complete the entire search, inference, and translation flow. The [Edge0 architecture](https://github.com/Edge0-AI/Edge0/blob/main/docs/architecture.md) separates the inference core from backends, while a service layer for multiple user sessions can be built separately.

### Request control on Mac mini and Mac Studio

A follow-up PoC on other hardware could place a host for authentication, sessions, search, and policy between clients and the inference server. The following diagram is a proposed extension, not a list of features implemented in the current CLI:

```text
사내 클라이언트
    ↓
사용자 인터페이스와 API 어댑터
    ↓
에이전트 호스트
    ├─ 인증과 세션
    ├─ 문서 검색과 접근 권한
    ├─ 요청 수 제한과 대기열
    └─ 상태 및 응답 이벤트
    ↓
Edge0 서버
```

The [current 35B server documentation](https://github.com/Edge0-AI/Edge0/blob/main/docs/models/edge0-35b.md#http-api) describes processing generation requests one at a time through a FIFO queue. Distinguishing that behavior from continuous batching across multiple sessions helps assess concurrency and waiting time.

Internal technical-document search, product-manual question answering, and operational-procedure guidance are examples of bounded tasks for follow-up experiments. The current CLI does not implement authentication, document-level permission filtering, or multi-user sessions; an internal service would address those layers separately. Adapters exposing the Responses API format or AG-UI are also future work.

### Comparisons after a CUDA backend becomes available

[Edge0's public support scope](https://github.com/Edge0-AI/Edge0#requirements) targets Apple Silicon through MLX, with a CUDA backend on the roadmap. The Mac results therefore do not establish the same behavior on NVIDIA GPUs.

If another backend becomes available with a compatible API, the Python host's search and translation flow could be reused. Keeping the question, grounding material, generation length, and measurement definitions identical would make hardware and backend comparisons easier to interpret.

## The local agent's demonstrated scope for a bounded task

A 35B-class model, official-document search, and on-device translation completed a single request on a 16GB laptop. The setup assigned document interpretation and answer generation to the model, while the host handled search and state management.

The measured 53.47-second TTFT directly affects interactive use on this device. Shorter references and measurements separated by cache state are initial comparison candidates; multi-user operation and other backends remain to be validated. A service that needs fast responses and a technical-document experiment that tolerates waiting can use different evaluation criteria.

The complete code and installation procedure are in the [series Gist](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d). Starting reproduction with a bounded question and reference set makes it possible to assess answer sources, time to first output, and operating scope alongside model size.

Read the series in order:

1. {{< series-link slug="edge0-16gb-mac-overview" text="A 35B Local LLM and Grounded Agent on a 16GB Mac" >}}
2. {{< series-link slug="edge0-setup-microsoft-learn-translation" text="Microsoft Learn and Apple Translation Setup" >}}
3. {{< series-link slug="edge0-local-rag-agent" text="A Local RAG Agent with Microsoft Learn Search" >}}
4. {{< series-link slug="edge0-streaming-ttft-metrics" text="Measuring TTFT and Streaming Output Rate" >}}
5. {{< series-link slug="edge0-real-benchmark-and-poc" text="This article" >}}

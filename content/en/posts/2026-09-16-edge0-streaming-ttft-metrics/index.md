---
title: "Edge0 Part 4: Measuring TTFT and Streaming Output Rate"
date: "2026-09-16T09:00:00+09:00"
draft: false
slug: "edge0-streaming-ttft-metrics"
translationKey: "edge0-streaming-ttft-metrics"
description: "Measure first-response latency and output rate from Edge0 SSE streams, with progress messages, Korean sentence translation, and event-count limitations."
tags: ["Edge0", "Local LLM", "RAG", "Apple Silicon", "Microsoft Learn"]
categories: ["Artificial Intelligence"]
tldr: "A worker thread receives the Edge0 stream while the main thread displays progress and Korean answers. The sample separates TTFT from total request time and distinguishes an SSE content-event rate from the server’s internal decode performance."
cover:
  image: "images/posts/edge0-streaming-ttft-metrics.webp"
  alt: "Blue glass panels following an initial gap along a timing rail between a timing instrument and a laptop."
  caption: "AI-generated illustration based on the article's topic."
license: "CC BY-NC 4.0"
---

As of September 13, 2026, the [Python sample for this series](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d) records first-response latency and output rate while receiving Edge0 SSE responses. This article connects the grounding prompt from {{< series-link slug="edge0-local-rag-agent" text="Part 3" >}} to an actual generation request.

The article covers measurement boundaries, progress display, stream reception in a worker thread, sentence-by-sentence Korean translation, and interpretation of the results. In my 16GB M2 MacBook Air experiment, the first response took tens of seconds, so I recorded the time before and after it separately.

We start with metric definitions, separate response reception from display, translate generated sentences, and print the final metrics. Use `microsoft_expert_agent.py` in the Gist for the complete program.

The measurements have the following scope:

> I checked public material on September 13, 2026. The sample assumes `Edge0-35B-A3B-preview` and its public streaming interface. It records client-observed times and content-event counts; it does not separately instrument server-side prefill, decode, and queue time.

## Measurements bounded by first content and stream completion

[Gist's `StreamStats`](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d) saves a reference timestamp immediately before starting the worker thread that handles the request. It then records the first nonempty content and the end of stream reception.

| Metric | Calculation | Scope |
| --- | --- | --- |
| TTFT | Request reference time to first content receipt | Client-observed wait for initial output |
| Total generation time | Request reference time to reception end | Excludes search and completion of all Korean translation |
| Completion count | Number of SSE events containing content | A token-count estimate based on current transport behavior |
| Time after first response | First content receipt to reception end | Includes network reception and termination handling |
| Output rate | Completion count divided by time after first response | Throughput measured in content events |

### An object for timestamps and completion counts

This measurement object retains the existing sample's field names and formulas:

```python
from dataclasses import dataclass


@dataclass
class StreamStats:
    request_started: float = 0.0
    first_token_at: float | None = None
    done_at: float | None = None
    completion_tokens: int = 0

    @property
    def ttft(self) -> float | None:
        if self.first_token_at is None:
            return None

        return self.first_token_at - self.request_started

    @property
    def total_generation_time(self) -> float | None:
        if self.done_at is None:
            return None

        return self.done_at - self.request_started

    @property
    def decode_time(self) -> float | None:
        if self.first_token_at is None or self.done_at is None:
            return None

        return self.done_at - self.first_token_at

    @property
    def output_tokens_per_second(self) -> float | None:
        duration = self.decode_time

        if not duration or duration <= 0:
            return None

        return self.completion_tokens / duration
```

TTFT can include thread startup, HTTP processing, server queueing, tokenization, prefill, and the first generation step. Likewise, a field named `decode_time` does not represent only the server's internal decode time.

## Status display while waiting for the first response

A delayed first output makes it difficult to tell whether a request is still progressing. The [sample's `Activity`](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d) displays processing stages and elapsed time in the terminal. It reports states observed by the program rather than the model's internal reasoning.

### An output helper with elapsed time

The helper calculates elapsed time whenever it prints a status message. The complete executable imports `time` before using this class:

```python
class Activity:
    def __init__(self):
        self.started = time.perf_counter()

    def show(self, message: str):
        elapsed = time.perf_counter() - self.started

        print(
            f"[{elapsed:6.1f}s] {message}",
            flush=True,
        )
```

### Waiting messages from the experiment

The recorded run used Korean progress messages, as shown below. The current Gist uses English progress messages while retaining Korean questions and answers:

```text
[   2.6s] Edge0-35B에 요청 전달
[   7.6s] Edge0 처리 중, 첫 토큰 대기 5초
[  12.6s] Edge0 처리 중, 첫 토큰 대기 10초
[  17.7s] Edge0 처리 중, 첫 토큰 대기 15초
```

The main thread prints a message roughly every five seconds until the first content arrives. These messages do not establish which internal stage the server is currently executing.

## Receiving SSE responses in a worker thread

[Edge0's HTTP API](https://github.com/Edge0-AI/Edge0/blob/main/docs/models/edge0-35b.md#http-api) supports `/v1/chat/completions` requests with `stream: true`. The sample uses the Flask transport and handles reception in a separate thread.

This excerpt extracts content from `data:` lines and places it on a queue. The complete executable defines `requests`, `json`, `queue`, `time`, and constants such as the server address:

```python
def edge0_worker(
    messages: list[dict],
    events: queue.Queue,
):
    try:
        response = requests.post(
            f"{EDGE0_BASE_URL}/v1/chat/completions",
            json={
                "model": EDGE0_MODEL,
                "messages": messages,
                "temperature": 0.0,
                "seed": 42,
                "max_tokens": MAX_TOKENS,
                "stream": True,
            },
            stream=True,
            timeout=600,
        )

        response.raise_for_status()

        for raw_line in response.iter_lines(
            decode_unicode=True,
        ):
            if not raw_line:
                continue

            if not raw_line.startswith("data:"):
                continue

            payload = raw_line[5:].strip()

            if payload == "[DONE]":
                break

            event = json.loads(payload)

            delta = (
                event["choices"][0]
                .get("delta", {})
                .get("content")
                or ""
            )

            if delta:
                events.put(
                    (
                        "token",
                        delta,
                        time.perf_counter(),
                    )
                )

        events.put(
            (
                "done",
                None,
                time.perf_counter(),
            )
        )

    except Exception as exc:
        events.put(
            (
                "error",
                exc,
                time.perf_counter(),
            )
        )
```

The server documentation describes sending an SSE event for each token, followed by `[DONE]`. The sample queues only events containing content, so it does not count every protocol event as generated output.

This excerpt assumes the expected response format. The complete Gist includes supporting error handling for JSON and `choices`, but does not separately validate whether the stream ended because `[DONE]` was received or because the connection simply ended. When comparing results, you can also check whether the response completed normally.

## Finalizing TTFT and forwarding content in the main thread

[Gist's `stream_edge0_with_progress()`](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d) waits for events with a one-second timeout and saves the receipt timestamp when the first content event arrives.

The function connects status display, content delivery, completion, and error handling:

```python
def stream_edge0_with_progress(
    messages: list[dict],
    activity: Activity,
    stats: StreamStats,
):
    events = queue.Queue()

    worker = threading.Thread(
        target=edge0_worker,
        args=(messages, events),
        daemon=True,
    )

    stats.request_started = time.perf_counter()
    worker.start()

    last_progress = 0

    while True:
        try:
            kind, value, event_time = events.get(
                timeout=1.0
            )

        except queue.Empty:
            if stats.first_token_at is None:
                waited = int(
                    time.perf_counter()
                    - stats.request_started
                )

                if (
                    waited >= 5
                    and waited - last_progress >= 5
                ):
                    activity.show(
                        "Edge0 처리 중, "
                        f"첫 토큰 대기 {waited}초"
                    )

                    last_progress = waited

            continue

        if kind == "token":
            stats.completion_tokens += 1

            if stats.first_token_at is None:
                stats.first_token_at = event_time

                activity.show(
                    "첫 토큰 수신 "
                    f"(TTFT {stats.ttft:.1f}초)"
                )

            yield value

        elif kind == "done":
            stats.done_at = event_time
            break

        elif kind == "error":
            stats.done_at = event_time
            raise value
```

`completion_tokens` increases by one for each `token` event. This is a lightweight estimate based on the current server's per-token transport; it is not guaranteed to equal an exact token count obtained by retokenizing the output. Counts can differ if the transport batches multiple tokens or includes empty content.

Benchmarks comparing servers can use server-reported usage or counts from the same tokenizer. The sample's current values are primarily useful for comparing input size and wait time within the same setup.

## Korean translation after buffering English sentences

Sending tiny English stream fragments directly to a translator can lose context. The [complete sample](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d) buffers content and sends portions it identifies as sentences to Apple Translation.

### A sentence buffer based on punctuation

The following function returns a list of strings judged to be sentences and the remaining buffer. The complete file imports `re` earlier:

```python
SENTENCE_PATTERN = re.compile(
    r'(.+?[.!?](?:["\')\]]+)?)'
    r'(?:\s+|$)',
    re.DOTALL,
)


def pop_complete_sentences(
    buffer: str,
) -> tuple[list[str], str]:
    sentences = []
    last_end = 0

    for match in SENTENCE_PATTERN.finditer(buffer):
        sentences.append(
            match.group(1).strip()
        )

        last_end = match.end()

    if not sentences:
        return [], buffer

    return (
        sentences,
        buffer[last_end:],
    )
```

The regular expression treats whitespace after punctuation or the current buffer's end as a boundary. It is not a complete sentence segmenter that accounts for abbreviations, decimal points, code notation, or fragments that have yet to arrive. The full loop also translates any buffer remaining after the response ends.

### Generation time and the first Korean display

Korean output updates by sentence. After the first English content arrives, sentence buffering and translation add time before the user can read the first Korean answer. TTFT and that first Korean display therefore measure different points.

The worker thread records reception timestamps, while the main thread handles translation and display. Consequently, `done_at` marks the end of stream reception, not the completion of all Korean translation and screen output.

## Metric output and future UI integration

[Gist's `print_metrics()`](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d) prints the final measurements. The main loop calls it after question translation, search, grounding construction, Edge0 reception, and sentence translation.

The existing sample prints results with these labels and units:

```python
def print_metrics(
    stats: StreamStats,
):
    print()
    print("측정")

    if stats.ttft is not None:
        print(
            f"  TTFT              "
            f"{stats.ttft:.2f}초"
        )

    if stats.total_generation_time is not None:
        print(
            f"  총 생성 시간       "
            f"{stats.total_generation_time:.2f}초"
        )

    print(
        f"  생성 토큰 수       "
        f"{stats.completion_tokens}"
    )

    if stats.decode_time is not None:
        print(
            f"  첫 토큰 이후 시간  "
            f"{stats.decode_time:.2f}초"
        )

    if stats.output_tokens_per_second is not None:
        print(
            f"  출력 속도          "
            f"{stats.output_tokens_per_second:.2f} tok/s"
        )
```

The labels `생성 토큰 수` and `tok/s` refer to the content-event estimate described above. That distinction matters when comparing the figures with other servers or tokenizers.

The status display can also support a future web UI. An adapter could turn start and end states, search progress, and response content into events. Integration with a protocol such as AG-UI remains future design work; the current CLI does not implement it.

## Separating first-output latency from subsequent throughput

The sample records time to first content separately from the remaining stream-reception time. While the worker receives the response, the main thread displays waiting status and translates English sentences into Korean.

Grounding length and the wait for the first response directly affect the current user experience. Tokenizer-based completion counts and UI protocol integration remain follow-up work. {{< series-link slug="edge0-real-benchmark-and-poc" text="Part 5" >}} interprets a run with a TTFT of 53.47 seconds and an event-based output rate of about 4.15 events per second.

Read the series in order:

1. {{< series-link slug="edge0-16gb-mac-overview" text="A 35B Local LLM and Grounded Agent on a 16GB Mac" >}}
2. {{< series-link slug="edge0-setup-microsoft-learn-translation" text="Microsoft Learn and Apple Translation Setup" >}}
3. {{< series-link slug="edge0-local-rag-agent" text="A Local RAG Agent with Microsoft Learn Search" >}}
4. {{< series-link slug="edge0-streaming-ttft-metrics" text="This article" >}}
5. {{< series-link slug="edge0-real-benchmark-and-poc" text="M2 Air 16GB Measurements and an Internal PoC" >}}

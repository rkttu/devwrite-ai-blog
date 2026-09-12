---
title: "Edge0 연재 4: 스트리밍 응답의 TTFT와 출력 속도 계측"
date: "2026-09-16T09:00:00+09:00"
draft: false
slug: "edge0-streaming-ttft-metrics"
translationKey: "edge0-streaming-ttft-metrics"
description: "Edge0의 SSE 응답을 받으며 첫 응답 대기 시간과 이후 출력 속도를 측정합니다. 대기 상태 표시, 문장 단위 한국어 번역, 이벤트 수 기반 토큰 추정의 한계를 설명합니다."
tags: ["Edge0", "로컬 LLM", "RAG", "Apple Silicon", "Microsoft Learn"]
categories: ["인공지능"]
tldr: "작업 스레드가 Edge0 스트림을 수신하고 메인 스레드가 대기 상태와 한국어 답변을 표시하도록 구성합니다. TTFT와 요청 전체 시간을 나누어 기록하며 SSE 콘텐츠 이벤트 수로 계산한 출력 속도를 서버 내부의 순수 디코드 성능과 구분합니다."
license: "CC BY-NC 4.0"
---

2026년 9월 13일 기준으로 [연재의 Python 샘플](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)은 Edge0의 SSE 응답을 수신하면서 첫 응답 대기 시간과 출력 속도를 기록합니다. 이번 글에서는 {{< series-link slug="edge0-local-rag-agent" text="3편" >}}에서 만든 그라운딩 프롬프트를 실제 생성 요청으로 연결합니다.

이번 글은 측정 시점, 대기 상태 표시, 작업 스레드의 스트림 수신, 문장 단위 한국어 번역, 측정값 해석을 다룹니다. M2 MacBook Air 16GB 실험에서 첫 응답까지 수십 초를 기다렸으므로 생성 전후의 시간을 나누어 기록했습니다.

측정값의 정의부터 살펴보겠습니다. 서버 응답을 받는 코드와 화면 출력을 분리한 뒤 생성 문장을 번역하고 마지막에 지표를 출력하는 순서로 설명합니다. 전체 프로그램은 Gist의 `microsoft_expert_agent.py`를 기준으로 사용합니다.

아래 계측은 다음 범위에서 해석합니다.

> 공개 자료는 2026년 9월 13일에 확인했습니다. `Edge0-35B-A3B-preview`와 공개 스트리밍 인터페이스를 전제로 합니다. 샘플은 클라이언트가 관찰한 시간과 콘텐츠 이벤트 수를 기록하며 서버 내부의 프리필, 디코드, 대기 시간을 각각 계측하지는 않습니다.

## 첫 응답과 스트림 종료를 기준으로 한 측정값

샘플에서 기록하는 시간의 범위를 정리하겠습니다. [Gist의 `StreamStats`](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)는 요청을 처리할 작업 스레드를 시작하기 직전에 기준 시각을 저장합니다. 이후 처음으로 비어 있지 않은 콘텐츠를 받은 시점과 스트림 수신을 끝낸 시점을 기록합니다.

| 지표 | 계산 기준 | 해석 범위 |
| --- | --- | --- |
| TTFT | 요청 기준 시각부터 첫 콘텐츠 수신까지 | 클라이언트에서 관찰한 첫 출력 대기 시간 |
| 총 생성 시간 | 요청 기준 시각부터 수신 종료까지 | 검색과 전체 한국어 번역 완료 시간은 제외 |
| 생성량 | 콘텐츠가 있는 SSE 이벤트 수 | 현재 전송 동작을 전제로 한 토큰 수 추정 |
| 첫 응답 이후 시간 | 첫 콘텐츠 수신부터 수신 종료까지 | 네트워크 수신과 종료 처리도 포함하는 시간 |
| 출력 속도 | 생성량을 첫 응답 이후 시간으로 나눈 값 | 콘텐츠 이벤트 기준의 처리율 |

### 시각과 생성량을 저장하는 객체

기존 샘플의 필드명과 계산식을 유지한 측정 객체는 다음과 같습니다.

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

TTFT에는 스레드 시작, HTTP 처리, 서버 대기열, 토큰화, 프리필과 첫 생성 단계의 시간이 함께 들어갈 수 있습니다. `decode_time`이라는 필드명도 서버 내부의 순수 디코드 시간만을 의미하지는 않습니다.

## 첫 응답을 기다리는 동안의 상태 표시

대기 중 표시할 상태를 짚어보겠습니다. 첫 출력이 늦어지면 사용자는 요청이 진행 중인지 알기 어렵습니다. [샘플의 `Activity`](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)는 요청 처리 단계와 경과 시간을 터미널에 표시합니다. 모델의 내부 추론 내용 대신 프로그램이 관찰한 상태를 보여 줍니다.

### 경과 시간을 붙이는 출력 함수

상태 메시지를 출력할 때마다 경과 시간을 계산합니다. 전체 실행 파일은 `time` 모듈을 가져온 상태에서 이 클래스를 사용합니다.

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

### 실험 당시의 대기 메시지

한국어 안내문을 사용한 실행 기록에서는 다음과 같이 대기 시간을 표시했습니다. 현재 Gist의 안내문은 영어이며 질문과 답변에는 한국어를 사용합니다.

```text
[   2.6s] Edge0-35B에 요청 전달
[   7.6s] Edge0 처리 중, 첫 토큰 대기 5초
[  12.6s] Edge0 처리 중, 첫 토큰 대기 10초
[  17.7s] Edge0 처리 중, 첫 토큰 대기 15초
```

메인 스레드는 첫 콘텐츠를 받기 전까지 약 5초 간격으로 안내를 출력합니다. 이 표시만으로 서버가 내부적으로 어느 단계에 있는지 판단하지는 않습니다.

## 작업 스레드에서 수신하는 SSE 응답

[Edge0의 HTTP API](https://github.com/Edge0-AI/Edge0/blob/main/docs/models/edge0-35b.md#http-api)는 `/v1/chat/completions`와 `stream: true` 요청을 지원합니다. 샘플은 Flask 전송 계층을 사용하며 수신 작업을 별도 스레드에서 처리합니다.

다음 발췌 코드는 응답의 `data:` 행에서 콘텐츠를 꺼내 큐에 전달합니다. `requests`, `json`, `queue`, `time`과 서버 주소 등의 상수는 전체 실행 파일에서 정의합니다.

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

서버 문서는 토큰마다 SSE 이벤트를 보내고 마지막에 `[DONE]`을 전송하는 흐름을 설명합니다. 샘플은 내용이 있는 이벤트만 큐에 넣으므로 프로토콜의 모든 이벤트를 생성량으로 세지는 않습니다.

이 발췌는 정상적인 응답 형식을 전제로 합니다. 전체 Gist에는 JSON과 `choices`를 읽는 보조 오류 처리가 있지만, 스트림이 끝난 경우와 `[DONE]`을 받은 경우를 별도로 구분해 검증하는 처리는 포함하지 않습니다. 따라서 결과를 비교할 때에는 응답이 정상적으로 끝났는지도 함께 확인할 수 있습니다.

## 메인 스레드의 TTFT 확정과 콘텐츠 전달

메인 스레드의 수신 시각 처리를 확인하겠습니다. [Gist의 `stream_edge0_with_progress()`](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)는 1초 단위로 이벤트를 기다리고 첫 콘텐츠 이벤트가 오면 수신 시각을 저장합니다.

다음 함수는 상태 표시와 콘텐츠 전달, 종료 및 오류 처리를 연결합니다.

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

`completion_tokens`는 `token` 이벤트를 받을 때마다 1씩 증가합니다. 현재 서버의 토큰별 전송을 가정한 가벼운 추정이며 토크나이저로 다시 센 정확한 생성 토큰 수와 같다고 보장하지는 않습니다. 전송 계층이 여러 토큰을 묶거나 빈 콘텐츠를 포함하면 차이가 발생할 수 있습니다.

서버를 비교하는 벤치마크에서는 서버가 제공하는 사용량이나 같은 토크나이저로 센 토큰 수를 기준으로 사용할 수 있습니다. 이 샘플의 값은 우선 동일한 구성에서 입력량과 대기 시간의 변화를 비교하는 데 사용합니다.

## 영어 문장을 모은 뒤 수행하는 한국어 번역

영어 스트림의 작은 조각을 바로 번역기에 전달하면 문맥을 잃기 쉽습니다. [전체 샘플](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)은 콘텐츠를 버퍼에 모으고 문장 경계로 판단한 부분을 Apple Translation에 전달합니다.

### 구두점을 기준으로 나누는 문장 버퍼

다음 함수는 문장으로 판단한 문자열 목록과 남은 버퍼를 반환합니다. 전체 파일은 앞에서 `re` 모듈을 가져옵니다.

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

이 정규식은 구두점 뒤의 공백이나 현재 버퍼의 끝을 경계로 취급합니다. 약어, 소수점, 코드 표기와 아직 도착하지 않은 후속 조각까지 고려하는 완전한 문장 분리기는 아닙니다. 응답이 끝난 뒤 남은 버퍼도 번역하도록 전체 루프에서 처리합니다.

### 생성 시점과 한국어 표시 시점의 차이

한국어 출력은 문장 단위로 갱신합니다. 첫 영어 콘텐츠를 받은 뒤에도 문장 버퍼를 채우고 번역하는 시간이 추가되므로 TTFT와 사용자가 처음 한국어 답변을 읽는 시점은 다릅니다.

작업 스레드는 수신 시각을 기록하고 메인 스레드는 번역과 출력을 처리합니다. 따라서 측정 객체의 `done_at`은 스트림 수신 종료를 가리키며 한국어 번역과 화면 출력 전체가 끝난 시각을 의미하지 않습니다.

## 측정값 출력과 UI 확장 범위

측정값 출력과 UI 연결 범위를 다루겠습니다. [Gist의 `print_metrics()`](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)는 마지막 지표 출력을 담당합니다. 메인 루프는 질문 번역, 검색, 그라운딩 구성, Edge0 수신, 문장 번역을 거친 뒤 이 함수를 호출합니다.

기존 샘플은 다음과 같은 이름과 단위로 결과를 출력합니다.

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

출력 문구의 `생성 토큰 수`와 `tok/s`는 앞에서 설명한 콘텐츠 이벤트 기반 추정을 가리킵니다. 서로 다른 서버나 토크나이저와 수치를 비교할 때에는 이 차이를 반영할 수 있습니다.

이 상태 표시는 이후 웹 UI를 연결할 때에도 사용할 수 있습니다. 실행 시작과 종료, 검색 중 상태, 응답 콘텐츠를 이벤트로 변환하는 어댑터를 추가하면 됩니다. AG-UI 같은 프로토콜과의 연결은 후속 설계 범위로 남아 있으며 현재 CLI에서는 해당 프로토콜을 구현하지 않았습니다.

## 첫 출력 대기와 이후 처리율의 분리

여기까지 정리하면 샘플은 첫 콘텐츠 수신까지의 시간과 이후 스트림 수신 시간을 나누어 기록합니다. 작업 스레드가 응답을 받는 동안 메인 스레드는 대기 상태를 표시하고 영어 문장을 한국어로 번역합니다.

현재 구성에서는 그라운딩 길이와 첫 응답 대기 시간이 사용 경험에 직접 영향을 줍니다. 토크나이저 기반 생성량 측정과 UI 프로토콜 연결은 후속 과제로 남깁니다. {{< series-link slug="edge0-real-benchmark-and-poc" text="5편" >}}에서는 TTFT 53.47초와 이벤트 기반 출력 속도 약 4.15회/초를 기록한 실행 결과를 해석합니다.

연재의 다른 글은 다음 순서로 읽을 수 있습니다.

1. {{< series-link slug="edge0-16gb-mac-overview" text="16GB Mac의 35B 로컬 LLM과 근거 기반 에이전트" >}}
2. {{< series-link slug="edge0-setup-microsoft-learn-translation" text="Microsoft Learn과 Apple Translation 실행 환경" >}}
3. {{< series-link slug="edge0-local-rag-agent" text="Microsoft Learn 검색을 연결한 로컬 RAG 에이전트" >}}
4. {{< series-link slug="edge0-streaming-ttft-metrics" text="현재 글" >}}
5. {{< series-link slug="edge0-real-benchmark-and-poc" text="M2 Air 16GB 실측 결과와 사내 PoC 확장 조건" >}}

---
title: "Edge0 연재 3: Microsoft Learn 검색을 연결한 로컬 RAG 에이전트"
date: "2026-09-15T09:00:00+09:00"
draft: false
slug: "edge0-local-rag-agent"
translationKey: "edge0-local-rag-agent"
description: "한국어 질문 정규화, Apple Translation 호출, Microsoft Learn 검색을 Python으로 연결합니다. 근거 자료의 수와 길이를 제한하고 최근 대화만 요청에 포함하는 RAG 구성을 설명합니다."
tags: ["Edge0", "로컬 LLM", "RAG", "Apple Silicon", "Microsoft Learn"]
categories: ["인공지능"]
tldr: "Python 호스트가 질문 번역과 Microsoft Learn 검색을 수행하고 Edge0에는 선택한 자료를 읽어 답하도록 요청합니다. URL 중복 제거, 참고 자료 번호, 근거 부족 응답 규칙과 최근 두 턴의 요청 문맥을 통해 입력량과 답변 근거를 관리합니다."
cover:
  image: "images/posts/edge0-local-rag-agent.webp"
  alt: "문서의 강조 구절을 확대하는 돋보기와 선택한 문서 세 장을 담은 유리 상자"
  caption: "글의 주제를 바탕으로 AI로 생성했습니다."
license: "CC BY-NC 4.0"
---

2026년 9월 13일 기준으로 [샘플 Gist](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)는 Edge0 서버, Microsoft Learn CLI, Apple Translation을 Python으로 연결하는 코드를 제공합니다. {{< series-link slug="edge0-setup-microsoft-learn-translation" text="2편" >}}에서 준비한 실행 환경을 바탕으로 이번 글에서는 검색 자료를 모델 입력으로 만드는 부분을 설명합니다.

이번 글에서는 호스트와 모델의 역할 분담, 질문 정규화와 번역, 검색 결과 선택, 그라운딩 프롬프트와 대화 문맥 관리를 다룹니다. 호스트가 검색 순서를 결정하고 모델은 전달받은 자료를 읽어 답을 구성합니다.

데이터 구조와 입력 처리부터 살펴보겠습니다. 검색한 구절에 출처 번호를 붙이고 현재 질문과 함께 전달한 뒤 후속 질문에 필요한 문맥을 구성합니다. 스트리밍 요청과 성능 계측은 4편에서 다룹니다.

본문의 코드와 공개 버전은 다음 범위로 구분합니다.

> 공개 자료는 2026년 9월 13일에 확인했습니다. 본문에서는 RAG 흐름을 설명하기 위해 코드를 발췌하고 전체 실행 파일의 일부 보조 처리를 생략합니다. `Edge0-35B-A3B-preview`의 동작과 외부 도구의 응답 형식은 이후 달라질 수 있습니다.

## 검색과 문맥 구성을 맡는 Python 호스트

호스트가 담당하는 범위를 정리하겠습니다. [전체 Python 코드](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)에서 호스트는 입력을 정규화하고 번역한 뒤 Microsoft Learn을 검색합니다. 검색 결과의 URL 중복을 제거하고 자료의 길이를 제한하며 최근 대화를 요청에 포함합니다.

모델에 맡기는 작업은 질문과 문서의 관계 파악, 답변에 사용할 근거 선택, 영어 답변 생성으로 좁힙니다. 제공한 자료로 사실을 확인할 수 없으면 부족하다고 답하도록 프롬프트에 명시합니다.

검색 결과는 제목, URL, 본문을 담는 `Source` 객체로 관리합니다. 입력량을 제한하는 상수도 함께 정의합니다.

```python
from dataclasses import dataclass


@dataclass
class Source:
    title: str
    url: str
    content: str

MAX_SOURCES = 3
MAX_SOURCE_CHARS = 1800
```

`MAX_SOURCE_CHARS`로 각 검색 구절의 문자 수를 제한합니다. 호스트가 출처 제목, URL, 시스템 프롬프트와 대화 기록을 이 한도 밖에서 추가하므로 전체 요청 크기는 별도로 계산할 수 있습니다.

## 간접 의문문을 직접 의문문으로 바꾸는 규칙

한국어 질문 정규화는 [Gist의 `normalize_korean_question()`](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)에서 처리합니다. 생성 여부를 묻는 질문이 번역 과정에서 생성 방법을 묻는 요청으로 바뀌는 사례를 줄이기 위해 정해진 문형을 변환합니다.

다음 함수는 네 가지 패턴에 맞는 문장을 직접 의문문과 후속 요청으로 나눕니다.

```python
import re


def make_followup(action: str) -> str:
    if action == "알려주세요":
        return "그 여부도 알려주세요."

    if action == "확인해주세요":
        return "그 여부도 확인해주세요."

    return "그 여부도 설명해주세요."


def normalize_korean_question(text: str) -> str:
    suffix = (
        r"\s*(?:함께\s*)?"
        r"(설명해주세요|알려주세요|확인해주세요)"
        r"\.?$"
    )

    patterns = [
        (
            rf"^(.*)할 수 있는지도{suffix}",
            lambda m:
                f"{m.group(1)}할 수 있습니까? "
                f"{make_followup(m.group(2))}",
        ),
        (
            rf"^(.*)되는지도{suffix}",
            lambda m:
                f"{m.group(1)}됩니까? "
                f"{make_followup(m.group(2))}",
        ),
        (
            rf"^(.*)하는지도{suffix}",
            lambda m:
                f"{m.group(1)}합니까? "
                f"{make_followup(m.group(2))}",
        ),
        (
            rf"^(.*)필요한지도{suffix}",
            lambda m:
                f"{m.group(1)}필요합니까? "
                f"{make_followup(m.group(2))}",
        ),
    ]

    for pattern, replacement in patterns:
        match = re.match(pattern, text)

        if match:
            return replacement(match)

    return text
```

패턴이 일치하지 않으면 입력을 그대로 반환합니다. 새로운 문형을 추가할 때에는 원문과 변환 결과, 영어 번역을 함께 비교하면 질문의 의미가 유지되는지 확인할 수 있습니다.

## Swift CLI로 전달하는 영어 번역 요청

번역 호출은 Python의 하위 프로세스로 분리합니다. [Apple Translation 초기화 API](https://developer.apple.com/documentation/translation/translationsession/init%28installedsource%3Atarget%3Apreferredstrategy%3A%29)를 감싼 `apple_translate` 실행 파일은 2편에서 준비했습니다.

다음 코드는 입력을 구두점 기준으로 나누고 각 구간을 정규화한 뒤 영어로 번역합니다.

```python
import subprocess


TRANSLATOR = "./apple_translate"


def run_process(args: list[str]) -> str:
    result = subprocess.run(
        args,
        check=True,
        capture_output=True,
        text=True,
    )

    return result.stdout.strip()


def translate(
    text: str,
    source: str,
    target: str,
) -> str:
    return run_process([
        TRANSLATOR,
        source,
        target,
        text,
    ])

def split_korean_input(text: str) -> list[str]:
    return [
        part.strip()
        for part in re.split(
            r"(?<=[?!])\s+|(?<=\.)\s+",
            text,
        )
        if part.strip()
    ]

def translate_question_to_english(
    question: str,
) -> str:
    translated = []

    for segment in split_korean_input(question):
        normalized = normalize_korean_question(segment)

        english = translate(
            normalized,
            "ko",
            "en",
        )

        translated.append(english)

    return " ".join(translated)
```

이 분할 함수는 물음표, 느낌표, 마침표 뒤의 공백을 기준으로 동작합니다. 약어와 제품명에 포함된 구두점까지 구별하는 문장 분석기는 아니므로 복잡한 입력에서는 분할 결과를 확인할 수 있습니다.

본문의 `translate_question_to_english()`는 흐름을 설명하기 위해 영어 문자열만 반환합니다. Gist의 전체 실행 파일은 원문, 정규화 결과, 영어 번역을 담은 추적 정보도 함께 반환하므로 전체 프로그램을 실행할 때에는 Gist 파일을 기준으로 사용합니다.

## 중복 URL과 긴 검색 구절의 제한

Microsoft Learn 검색 결과를 선택하는 과정을 짚어보겠습니다. [Learn CLI](https://github.com/MicrosoftDocs/mcp#-microsoft-learn-cli)의 `--json` 옵션으로 결과를 받은 뒤 URL과 본문이 있는 항목만 선택합니다.

검색 함수는 같은 URL을 한 번만 사용하고 최대 세 개의 구절을 반환합니다.

```python
import json


def search_microsoft_learn(
    query_text: str,
) -> list[Source]:
    raw = run_process([
        "mslearn",
        "search",
        query_text,
        "--json",
    ])

    data = json.loads(raw)

    results = (
        data.get("results")
        or data.get("value")
        or []
    )

    sources = []
    seen_urls = set()

    for item in results:
        url = (
            item.get("contentUrl")
            or item.get("url")
            or item.get("href")
            or ""
        )

        if not url or url in seen_urls:
            continue

        content = (
            item.get("content")
            or item.get("snippet")
            or item.get("description")
            or ""
        ).strip()

        if not content:
            continue

        seen_urls.add(url)

        sources.append(
            Source(
                title=item.get(
                    "title",
                    "(untitled)",
                ),
                url=url,
                content=content[:MAX_SOURCE_CHARS],
            )
        )

        if len(sources) >= MAX_SOURCES:
            break

    return sources
```

여러 필드명을 확인하는 처리는 샘플에서 예상하는 JSON 형식에 대응합니다. 모든 응답 형식을 지원하는 검증 계층으로 보지는 않습니다. 관련 구절이 없으면 전체 실행 파일은 해당 질문의 생성을 진행하지 않고 검색 결과가 없다는 안내를 출력합니다.

검색 결과 전체를 그대로 넣는 대신 질문에 필요한 구절을 사용하면 입력량을 줄일 수 있습니다. 이 샘플은 별도의 재정렬 모델을 사용하지 않으므로 결과 순서에 따른 선택과 문자 수 제한의 영향을 함께 관찰합니다.

## 출처 번호와 근거 범위를 담은 프롬프트

출처 번호와 답변 범위를 전달하는 프롬프트를 다루겠습니다. [Gist의 `build_grounding()`과 `build_user_prompt()`](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)가 각 자료에 제목과 URL을 포함해 모델이 답변에 출처 번호를 붙일 수 있도록 구성합니다.

### 현재 질문과 함께 전달하는 참고 자료

선택한 검색 구절을 번호가 있는 참고 자료로 묶고 현재 질문 앞에 배치합니다.

```python
def build_grounding(
    sources: list[Source],
) -> str:
    blocks = []

    for index, source in enumerate(
        sources,
        start=1,
    ):
        blocks.append(
            f"[{index}] {source.title}\n"
            f"URL: {source.url}\n\n"
            f"{source.content}"
        )

    return "\n\n---\n\n".join(blocks)

def build_user_prompt(
    question: str,
    sources: list[Source],
) -> str:
    grounding = build_grounding(sources)

    return f"""
Microsoft Learn references:

<references>
{grounding}
</references>

Question:
{question}

Answer the question using the references above.
""".strip()
```

자료와 질문을 구분하면 호스트가 어떤 근거를 전달했는지 확인하기 쉽습니다. 다만 `<references>` 태그 자체가 자료의 신뢰성이나 모델의 지시 준수를 보장하지는 않습니다.

### 근거 부족과 출처 표기를 지정한 시스템 프롬프트

시스템 프롬프트는 자료가 뒷받침하는 사실을 우선 사용하고 확인할 수 없는 사실은 부족하다고 밝히도록 지정합니다.

```python
SYSTEM_PROMPT = """
You are a Microsoft technology expert.

Answer using the supplied Microsoft Learn references
as the primary source of factual information.

Rules:
- Prefer facts explicitly supported by the references.
- If the references do not establish a fact, say so.
- Do not invent API names, product behavior, limits,
  or version details.
- Ignore unrelated search results.
- Use short plain-text paragraphs.
- Cite supporting references using [1], [2], [3].
""".strip()
```

이 규칙으로 모델의 답변 방향을 제한합니다. 생성한 인용 번호와 실제 근거의 일치 여부는 출력한 출처를 대조해 확인할 수 있습니다.

## 최근 두 턴으로 제한하는 요청 문맥

후속 질문에 포함하는 대화 문맥을 확인하겠습니다. [전체 코드](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)는 직전 주제를 검색 질의의 보조 정보로 사용합니다. 이전 그라운딩 자료를 대화 기록에 추가하지 않고 사용자 질문과 모델의 영어 답변을 기록합니다.

다음 함수는 가장 최근 사용자 질문을 찾아 현재 질문과 함께 검색 질의를 구성합니다.

```python
MAX_HISTORY_TURNS = 2

def make_search_query(
    current_question: str,
    history: list[dict],
) -> str:
    previous_user = None

    for message in reversed(history):
        if message["role"] == "user":
            previous_user = message["content"]
            break

    if previous_user is None:
        return current_question

    return (
        f"Previous topic: {previous_user}\n"
        f"Current question: {current_question}"
    )
```

모델 요청을 만들 때에는 `history[-MAX_HISTORY_TURNS * 2:]`로 최근 두 턴의 질문과 답변만 선택합니다. 현재 질문의 그라운딩 자료는 해당 요청에만 추가하므로 이전 검색 구절이 요청마다 누적되는 것을 피할 수 있습니다.

이 설정은 모델에 보내는 대화 문맥을 제한합니다. 전체 샘플의 `history` 리스트는 세션 동안 질문과 답변을 계속 보관하며 `/clear` 명령으로 비웁니다. 최근 두 턴만 메모리에 저장하는 구현과는 구분됩니다.

## 입력량과 답변 근거를 함께 관리하는 흐름

여기까지 정리하면 Python 호스트는 한국어 질문을 영어 검색 질의로 바꾸고 관련 구절을 선택해 현재 요청의 근거로 구성합니다. 출처 번호와 근거 부족 응답 규칙을 함께 전달하며 모델에 보내는 과거 대화는 최근 두 턴으로 제한합니다.

현재 입력량에는 검색 결과의 수, 구절 길이와 대화 문맥이 직접 영향을 줍니다. 검색 재정렬과 더 정교한 문장 정규화는 후속 과제로 남깁니다. {{< series-link slug="edge0-streaming-ttft-metrics" text="4편" >}}에서는 준비한 프롬프트를 Edge0 서버에 전달하고 첫 응답 대기 시간과 이후 출력 속도를 측정합니다.

연재의 다른 글은 다음 순서로 읽을 수 있습니다.

1. {{< series-link slug="edge0-16gb-mac-overview" text="16GB Mac의 35B 로컬 LLM과 근거 기반 에이전트" >}}
2. {{< series-link slug="edge0-setup-microsoft-learn-translation" text="Microsoft Learn과 Apple Translation 실행 환경" >}}
3. {{< series-link slug="edge0-local-rag-agent" text="현재 글" >}}
4. {{< series-link slug="edge0-streaming-ttft-metrics" text="스트리밍 응답의 TTFT와 출력 속도 계측" >}}
5. {{< series-link slug="edge0-real-benchmark-and-poc" text="M2 Air 16GB 실측 결과와 사내 PoC 확장 조건" >}}

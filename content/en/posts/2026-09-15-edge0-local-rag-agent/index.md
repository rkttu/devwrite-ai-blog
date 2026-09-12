---
title: "Edge0 Part 3: A Local RAG Agent with Microsoft Learn Search"
date: "2026-09-15T09:00:00+09:00"
draft: false
slug: "edge0-local-rag-agent"
translationKey: "edge0-local-rag-agent"
description: "Connect Korean question normalization, Apple Translation, and Microsoft Learn search in Python, with bounded grounding and recent conversation context."
tags: ["Edge0", "Local LLM", "RAG", "Apple Silicon", "Microsoft Learn"]
categories: ["Artificial Intelligence"]
tldr: "The Python host translates questions and searches Microsoft Learn, while Edge0 reads selected references to answer. URL deduplication, source numbers, insufficient-evidence rules, and a two-turn request history control input size and traceability."
cover:
  image: "images/posts/edge0-local-rag-agent.webp"
  alt: "A magnifying glass over highlighted document passages and a glass box holding three selected reference cards."
  caption: "AI-generated illustration based on the article's topic."
license: "CC BY-NC 4.0"
---

As of September 13, 2026, the [sample Gist](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d) provides Python code that connects the Edge0 server, Microsoft Learn CLI, and Apple Translation. Building on the environment from {{< series-link slug="edge0-setup-microsoft-learn-translation" text="Part 2" >}}, this article explains how retrieved material becomes model input.

The article covers the division of work between host and model, question normalization and translation, search-result selection, grounding prompts, and conversation context. The host determines the search sequence; the model reads the supplied material and constructs an answer.

We start with data structures and input processing. Retrieved passages receive source numbers and accompany the current question, while recent conversation supplies context for follow-up questions. Part 4 covers streaming requests and performance measurements.

The code excerpts and release information have the following scope:

> I checked public material on September 13, 2026. The article excerpts code to explain the RAG flow and omits some supporting logic from the complete executable. The behavior of `Edge0-35B-A3B-preview` and external-tool response formats may change.

## A Python host for search and context construction

In the [complete Python code](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d), the host normalizes and translates input, then searches Microsoft Learn. It removes duplicate result URLs, limits passage length, and includes recent conversation in the request.

The model's role is narrower: relate the question to the documents, select evidence for the answer, and generate an English response. The prompt explicitly asks it to acknowledge when the supplied material cannot establish a fact.

Search results use a `Source` object containing a title, URL, and content. The same excerpt defines input limits:

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

`MAX_SOURCE_CHARS` limits the character count of each search passage. The host adds source titles, URLs, the system prompt, and conversation history outside that limit, so total request size can be calculated separately.

## Rules for turning indirect questions into direct questions

[Gist's `normalize_korean_question()`](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d) handles Korean question normalization. It transforms fixed sentence patterns to reduce cases where translation changes a question about whether something is generated into a request explaining how to generate it.

This function splits sentences matching four patterns into a direct question and a follow-up request:

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

If no pattern matches, the input is returned unchanged. When adding a pattern, comparing the original, normalized wording, and English translation helps check that the question retains its meaning.

## English translation through the Swift CLI

Translation runs in a subprocess launched by Python. Part 2 prepared the `apple_translate` executable around [Apple's Translation initializer](https://developer.apple.com/documentation/translation/translationsession/init%28installedsource%3Atarget%3Apreferredstrategy%3A%29).

The following code splits input at punctuation, normalizes each segment, and translates it into English:

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

The splitter uses whitespace after question marks, exclamation marks, and periods. It is not a sentence parser that distinguishes punctuation inside abbreviations and product names, so complex inputs can benefit from checking the split result.

For clarity, the `translate_question_to_english()` shown here returns only the English string. The complete Gist also returns tracing information containing the original question, normalized wording, and English translation. Use the Gist file when running the entire program.

## Removing duplicate URLs and limiting long passages

The host receives results through the [Learn CLI](https://github.com/MicrosoftDocs/mcp#-microsoft-learn-cli) with `--json`, then selects entries that have both a URL and content.

The search function uses each URL once and returns at most three passages:

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

Checking several field names accommodates the JSON shapes the sample expects. This is not a validation layer that supports every possible response format. If no relevant passages are found, the complete executable skips generation for that question and displays a no-results message.

Using passages needed for the question instead of entire results can reduce input size. The sample does not use a separate reranking model, so result order and character limits both affect the selection.

## Prompts with source numbers and evidence boundaries

[Gist's `build_grounding()` and `build_user_prompt()`](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d) include a title and URL for each source so the model can cite source numbers in its answer.

### References attached to the current question

Selected passages are assembled into numbered references and placed before the current question:

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

Separating references from the question makes it easier to inspect the evidence supplied by the host. The `<references>` tags themselves do not guarantee the material's reliability or the model's adherence to instructions.

### A system prompt for insufficient evidence and citations

The system prompt prioritizes facts supported by the references and asks the model to identify facts it cannot establish:

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

These rules constrain the intended direction of the answer. Comparing the generated citation numbers with the displayed sources lets readers check whether the cited evidence supports the response.

## Request context limited to the last two turns

The [complete code](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d) uses the previous topic as supporting information for a follow-up search query. History stores user questions and the model's English answers, without adding previous grounding material.

This function finds the most recent user question and combines it with the current question to form a search query:

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

When constructing a model request, `history[-MAX_HISTORY_TURNS * 2:]` selects only questions and answers from the last two turns. Grounding for the current question is added only to that request, preventing earlier search passages from accumulating in each subsequent prompt.

This setting limits the conversation context sent to the model. The complete sample's `history` list still retains questions and answers throughout the session until `/clear` empties it. It does not store only two turns in memory.

## Managing input size alongside answer evidence

The Python host turns Korean questions into English search queries, selects relevant passages, and supplies them as evidence for the current request. It also supplies source numbers and an insufficient-evidence rule, while limiting past conversation sent to the model to the last two turns.

The number of search results, passage length, and conversation context directly affect current input size. Search reranking and more refined sentence normalization remain follow-up work. {{< series-link slug="edge0-streaming-ttft-metrics" text="Part 4" >}} sends the prepared prompt to the Edge0 server and measures the wait for the first response and the subsequent output rate.

Read the series in order:

1. {{< series-link slug="edge0-16gb-mac-overview" text="A 35B Local LLM and Grounded Agent on a 16GB Mac" >}}
2. {{< series-link slug="edge0-setup-microsoft-learn-translation" text="Microsoft Learn and Apple Translation Setup" >}}
3. {{< series-link slug="edge0-local-rag-agent" text="This article" >}}
4. {{< series-link slug="edge0-streaming-ttft-metrics" text="Measuring TTFT and Streaming Output Rate" >}}
5. {{< series-link slug="edge0-real-benchmark-and-poc" text="M2 Air 16GB Measurements and an Internal PoC" >}}

---
title: "Edge0 Part 2: Microsoft Learn and Apple Translation Setup"
date: "2026-09-14T09:00:00+09:00"
draft: false
slug: "edge0-setup-microsoft-learn-translation"
translationKey: "edge0-setup-microsoft-learn-translation"
description: "Set up Edge0, Microsoft Learn CLI, and Apple Translation, including per-terminal environments, macOS API requirements, and Korean question normalization."
tags: ["Edge0", "Local LLM", "RAG", "Apple Silicon", "Microsoft Learn"]
categories: ["Artificial Intelligence"]
tldr: "Run the Edge0-35B server and Python agent in separate terminals, then connect document search and on-device translation. This guide covers model paths, the macOS 26.4 translation API, installed language resources, and normalization of Korean indirect questions."
cover:
  image: "images/posts/edge0-setup-microsoft-learn-translation.webp"
  alt: "A compute device, document cards, and translucent speech bubbles connected in front of a laptop."
  caption: "AI-generated illustration based on the article's topic."
license: "CC BY-NC 4.0"
---

As of September 13, 2026, the sample in this series uses Edge0-35B, Microsoft Learn CLI, and the macOS Translation framework. Following the responsibilities established in {{< series-link slug="edge0-16gb-mac-overview" text="Part 1" >}}, the inference server and Python agent host run in separate terminals.

This article covers installing Edge0 and its model, starting the streaming server, searching official documentation, translating between Korean and English, and normalizing questions. The complete files are `README.md`, `apple_translate.swift`, and `microsoft_expert_agent.py` in the [sample Gist](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d).

We start with requirements and installation. After starting the server in the first terminal, we prepare search and translation tools, then set up the second terminal for the agent.

The procedure uses the following release and API requirements:

> I checked the documentation on September 13, 2026. The configuration of `Edge0-35B-A3B-preview` may change. The Swift example uses `TranslationSession(installedSource:target:preferredStrategy:)`, which requires macOS 26.4 or later and an SDK that includes this API.

## Requirements for Edge0 and the 35B model

The experiment uses an Apple Silicon Mac, Python 3.12, Node.js 22 or later, and Xcode Command Line Tools. It also requires space for about 23GB of model files and Korean and English translation resources. The [official README](https://github.com/Edge0-AI/Edge0) describes supported environments and model contents.

### Repository and Python virtual environment

Clone the repository in your working directory, activate a virtual environment, and install the sample dependencies:

```bash
git clone https://github.com/Edge0-AI/Edge0.git
cd Edge0

python3.12 -m venv .venv
source .venv/bin/activate

pip install -e '.[dev,fetch]'
pip install flask requests
```

Subsequent commands use the Edge0 repository root as the working directory. `flask` provides streaming transport, and `requests` handles HTTP calls from the Python host.

### Model download and path configuration

Download the 35B model with the official script, then set the model path in the current shell:

```bash
python scripts/fetch_models.py \
  --tier edge0-35b \
  --target-dir models

export EDGE0_35B_MODEL="$PWD/models/edge0-35b"
```

The `models/edge0-35b/` directory includes configuration, model weights, the tokenizer, and LoRA and pre-router adapters. Use the complete directory, including the adapters, as the model path.

## The streaming server in the first terminal

The [Edge0 35B model documentation](https://github.com/Edge0-AI/Edge0/blob/main/docs/models/edge0-35b.md) describes SSE streaming through the Flask transport and the `/healthz` endpoint. This sample binds the server to `127.0.0.1:8083`.

### Reactivating the environment and starting the server

In a new terminal, set the working directory, virtual environment, and model environment variable again. Replace `/path/to/Edge0` with the actual clone location:

```bash
cd /path/to/Edge0
source .venv/bin/activate

export EDGE0_35B_MODEL="$PWD/models/edge0-35b"

edge0 serve edge0-35b \
  --host 127.0.0.1 \
  --port 8083 \
  --flask
```

Keep this terminal open while the server runs. A virtual environment activated in another terminal does not automatically apply to a new shell.

### Checking health from another shell

Use this request in another terminal to check the server response:

```bash
curl http://127.0.0.1:8083/healthz
```

A successful response confirms that the HTTP server is reachable at that address. Actual text generation is checked later by submitting a question through the agent.

## Microsoft Learn search and input limits

Microsoft provides the [Learn MCP server and CLI](https://github.com/MicrosoftDocs/mcp#-microsoft-learn-cli). The Python host launches `mslearn` as a subprocess and reads its JSON output. This gives the sample document search without implementing the MCP transport directly.

### Installing the CLI and checking search

Install the CLI in the Node.js environment, then search for Native AOT documentation:

```bash
npm install -g @microsoft/learn-cli

mslearn search \
  ".NET NativeAOT Reflection.Emit" \
  --json
```

Search sends queries to the external Microsoft Learn service. Even with local Edge0 inference and translation, this stage uses a network connection.

### Limiting the number and length of passages

The sample uses relevant passages returned by search rather than fetching complete pages. The [full code](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d) limits input with these constants:

```python
MAX_SOURCES = 3
MAX_SOURCE_CHARS = 1800
```

It selects up to three results and passes up to 1,800 characters from each passage. This is a character limit, not a size in KB or a model token count. You can compare answer quality and wait time while adjusting these limits and retaining the evidence needed for the question.

## A Swift CLI for Apple Translation

The example wraps [Apple's TranslationSession initializer](https://developer.apple.com/documentation/translation/translationsession/init%28installedsource%3Atarget%3Apreferredstrategy%3A%29). The `preferredStrategy` argument is available on macOS 26.4 or later. Build the following code with an operating system and SDK that support that API.

### Entry point for languages and text

Save the following source as `apple_translate.swift` in the Edge0 repository root:

```swift
import Foundation
import Translation

@main
struct AppleTranslateCLI {
    static func main() async {
        guard CommandLine.arguments.count >= 4 else {
            fputs(
                "usage: apple_translate <source> <target> <text>\n",
                stderr
            )
            exit(2)
        }

        let source = Locale.Language(
            identifier: CommandLine.arguments[1]
        )

        let target = Locale.Language(
            identifier: CommandLine.arguments[2]
        )

        let text = CommandLine.arguments
            .dropFirst(3)
            .joined(separator: " ")

        do {
            let session = TranslationSession(
                installedSource: source,
                target: target,
                preferredStrategy: .lowLatency
            )

            let response = try await session.translate(text)

            print(response.targetText)
        }
        catch {
            fputs(
                "translation error: \(error)\n",
                stderr
            )
            exit(1)
        }
    }
}
```

The CLI takes a source language, target language, and text as arguments, then writes the translation to standard output. The `installedSource` initializer assumes the required language resources are already installed.

### Compilation and a first translation

Use `-parse-as-library` for the `@main` entry point in this single Swift file, then test translation:

```bash
xcrun swiftc \
  -parse-as-library \
  apple_translate.swift \
  -o apple_translate

./apple_translate ko en \
  "NativeAOT에서 Reflection.Emit을 사용할 수 있습니까?"
```

Omitting `-parse-as-library` can produce a compilation error involving `@main` and top-level code in a single file. If `TranslationError.Cause.notInstalled` occurs, check whether the Korean and English translation resources are installed. Translation runs on-device after those resources are available.

## Korean normalization that preserves the question's meaning

When testing NLLB 600M, NLLB 1.3B, and Apple Translation, I encountered translations that changed a question about whether code is generated into a request explaining how to generate it. The [sample normalization function](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d) handles several specific Korean sentence patterns.

The original question, mistranslation, and normalized wording illustrate this distinction:

- **Original question**: “런타임에 새로운 실행 코드를 생성하는지도 함께 설명해주세요.” asks whether new executable code is generated at runtime.

- **Mistranslation observed**: “Explain how to generate new executable code at runtime.” changes the question from whether code is generated to how to generate it.

- **After normalization**: “런타임에 새로운 실행 코드를 생성합니까? 그 여부도 함께 설명해주세요.” uses a direct question to ask whether code is generated.

The function rewrites fixed patterns such as `~할 수 있는지도`, `~되는지도`, `~하는지도`, and `~필요한지도` into direct questions. Sentences that do not match the regular expressions pass to the translator unchanged. This is not a general-purpose correction system that understands and rewrites arbitrary Korean sentences.

## Preparing the agent in the second terminal

Save `microsoft_expert_agent.py` from the [Gist](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d) in the Edge0 repository root, alongside the translation executable.

Activate the virtual environment in the second terminal independently of the server terminal:

```bash
cd /path/to/Edge0
source .venv/bin/activate

pip install requests
```

Before running the agent, check the components in this order:

1. Confirm that the Edge0 server is running in the first terminal.
2. Check the `/healthz` response from the second terminal.
3. Check the JSON results from `mslearn search`.
4. Test Korean-to-English and English-to-Korean translation with `./apple_translate`.
5. Run `python microsoft_expert_agent.py` from the repository root.

Parts 3 and 4 explain the search, prompt construction, streaming, and measurement portions of the full agent separately.

## Three components that can be checked independently

The Edge0 server, Microsoft Learn search, and Apple Translation can each be run and checked on their own. The Python host connects them into a flow that answers Korean questions.

Per-terminal environments, model paths, and the translation API's operating-system requirements directly affect execution. Search reranking and shorter grounding inputs remain subjects for later performance comparisons. {{< series-link slug="edge0-local-rag-agent" text="Part 3" >}} connects question normalization, search-result selection, and conversation context in Python.

Read the series in order:

1. {{< series-link slug="edge0-16gb-mac-overview" text="A 35B Local LLM and Grounded Agent on a 16GB Mac" >}}
2. {{< series-link slug="edge0-setup-microsoft-learn-translation" text="This article" >}}
3. {{< series-link slug="edge0-local-rag-agent" text="A Local RAG Agent with Microsoft Learn Search" >}}
4. {{< series-link slug="edge0-streaming-ttft-metrics" text="Measuring TTFT and Streaming Output Rate" >}}
5. {{< series-link slug="edge0-real-benchmark-and-poc" text="M2 Air 16GB Measurements and an Internal PoC" >}}

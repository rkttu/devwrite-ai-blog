---
title: "OpenAI Codex CLI를 Claude·Gemini·Llama 위에서 돌리기 — C# 50줄로"
date: 2026-05-27T00:00:00+09:00
draft: false
slug: "cadenza-agent"
tags:
  - C#
  - .NET
  - AI
  - Codex CLI
  - OpenRouter
  - Cadenza
categories:
  - .NET 개발
translationKey: "cadenza-agent"
description: "OpenAI Codex CLI는 Responses API에 lock-in 돼 있습니다. Cadenza.Agent로 IChatClient 앞단에 Responses 호환 서버를 세우면, OpenRouter를 통해 Codex의 두뇌를 자유롭게 고를 수 있습니다."
cover:
  image: "images/posts/cadenza-agent.webp"
  alt: "C# 50줄로 OpenAI Codex CLI를 임의의 LLM에 연결하는 개념 이미지"
tldr: "Codex CLI는 OpenAI Responses API에만 묶여 있지만, `model_providers` config의 `wire_api = \"responses\"`가 탈출구입니다. Cadenza.Agent SDK를 쓰면 단일 `.cs` 파일로 Responses 호환 HTTP 서버를 띄울 수 있고, 백엔드를 OpenRouter·Ollama·Anthropic·Azure OpenAI 어느 것으로 향하게 해도 같은 wire 포맷이 유지됩니다."
---

> OpenAI의 [Codex CLI](https://github.com/openai/codex)는 훌륭한 에디터 에이전트 UX를 제공합니다(shell 도구, `apply_patch`, plan tracking이 모두 갖춰져 있습니다). 문제는 2026년 2월 기준 OpenAI **Responses API**만 지원한다는 점입니다. Chat Completion 지원은 제거됐고(`codex-rs/model-provider-info/src/lib.rs`의 `WireApi` enum에는 `Responses`만 남아 있습니다), Chat Completion만 지원하는 엔드포인트(Ollama, LM Studio, 즐겨 쓰는 Llama runner)는 그대로 막혀버립니다. 이 글은 .NET 10 file-based 프로그램과 `Microsoft.Extensions.AI`의 `IChatClient` 추상화를 활용해 50줄짜리 C# 한 파일로 Responses 호환 서버를 세우고, OpenRouter를 거쳐 Codex CLI가 임의의 모델 위에서 동작하도록 만든 과정을 정리합니다.

---

## 들어가며

Codex CLI는 Responses를 말하는 **어떤** 서버와도 행복하게 대화합니다. `model_provider` config 블록이 정확히 이걸 위해 존재합니다. 즉, 원하는 모델로 백킹되는 Responses 호환 HTTP 엔드포인트를 세울 수만 있다면, Codex는 일반화된 프론트엔드가 되고 두뇌는 사용자가 고를 수 있습니다.

요즘 저는 다음 트릭을 즐겨 씁니다. `Microsoft.Extensions.AI`의 벤더 중립 `IChatClient` 추상화 위에서, OpenAI Chat Completion 서버와 Responses API 서버를 동시에 굴리는 50줄짜리 C# 스크립트를 띄웁니다. 백엔드는 [OpenRouter](https://openrouter.ai/)로 향하게 합니다(API 키 하나로 Claude, Gemini, Llama, GPT 등 수백 개 모델을 쓸 수 있습니다). 그리고 Codex에게 OpenAI 대신 이 로컬 스크립트와 대화하라고 알려줍니다.

최종 결과는 **OpenAI Codex CLI가 Anthropic의 Claude 3.5 Sonnet 위에서 동작** 하는 상태입니다(또는 그날 끌리는 다른 모델 위에서).

## 구성 요소

제가 직접 배포하는 [Cadenza.Agent](https://www.nuget.org/packages/Cadenza.Agent) 라는 MSBuild SDK를 사용합니다. 단일 `.cs` 파일을 실행 가능한 에이전트 서버로 바꿔주는 SDK이며, .NET 10의 file-based 프로그램용 단일 파일 스크립팅 SDK 패밀리의 일부입니다(`dotnet run script.cs` 와 같은 발상이지만 더 풍부한 Tier-1 API(`Tool`, `UseOllama`, `UseOpenAi`, `Run` 등)를 제공합니다). Agent 변종은 다음을 노출합니다.

- `POST /v1/chat/completions` — Aider / Continue / Cursor / Copilot BYOK / sgpt 용
- `POST /v1/responses` — Codex CLI 용

둘 다 사용자가 구성한 동일한 `IChatClient` 로 백킹됩니다. 백엔드를 바꿔도 wire 포맷은 그대로입니다.

LLM 쪽은 OpenRouter를 사용합니다. OpenAI의 Chat Completion wire 포맷을 다른 base URL로 그대로 제공하기 때문에, `Microsoft.Extensions.AI.OpenAI` 의 `ChatClient` 를 그대로 꽂아 쓸 수 있습니다. 환경변수 하나, 임의의 모델.

Codex 설정은 `CODEX_HOME` 환경변수 트릭을 활용합니다. `~/.codex/config.toml` 을 편집하는 대신, Codex가 가리키는 디렉터리를 샘플 전용으로 따로 만들면 거기서 새 `config.toml` 을 읽습니다. 덕분에 사용자의 글로벌 config를 절대 건드리지 않는 자급자족 샘플을 만들 수 있습니다.

## 스크립트

전체 백엔드, 파일 하나입니다.

```csharp
#!/usr/bin/env dotnet run
#:sdk Cadenza.Agent@1.0.14

using System.ClientModel;
using OpenAI;

var apiKey = Env.Get("OPENROUTER_API_KEY")
    ?? throw new InvalidOperationException("OPENROUTER_API_KEY env var missing");
var model = Env.Get("OPENROUTER_MODEL") ?? "anthropic/claude-3.5-sonnet";

ServedModelName = "cadenza-codex-openrouter";

// 샘플 전용 Codex home 디렉터리 생성.
var codexHome = Path.Combine(Env.Cwd, ".cadenza-codex-openrouter");
MakeDir(codexHome);

var catalogPath = Path.Combine(codexHome, "cadenza-catalog.json").Replace('\\', '/');
var configToml = $"""
    model          = "cadenza-codex-openrouter"
    model_provider = "cadenza"
    model_catalog_json = "{catalogPath}"

    [model_providers.cadenza]
    name     = "Cadenza.Agent (OpenRouter-backed)"
    base_url = "http://localhost:8080/v1"
    wire_api = "responses"
    env_key  = "CADENZA_API_KEY"
    stream_idle_timeout_ms = 300000
    """;
WriteText(Path.Combine(codexHome, "config.toml"), configToml);

// Catalog JSON: Codex에 우리가 제공하는 모델 id를 선언해서 "Defaulting to
// fallback metadata" 경고를 막습니다. 필드는 codex-rs/protocol/src/
// openai_models.rs의 ModelInfo schema 기준 — 모든 키가 필수입니다.
var catalogJson = """
    {
      "models": [{
        "slug": "cadenza-codex-openrouter",
        "display_name": "Cadenza (OpenRouter)",
        "description": "OpenRouter-backed agent served by Cadenza.Agent",
        "supported_reasoning_levels": [],
        "shell_type": "default",
        "visibility": "list",
        "supported_in_api": true,
        "priority": 50,
        "availability_nux": null,
        "upgrade": null,
        "base_instructions": "",
        "supports_reasoning_summaries": false,
        "support_verbosity": false,
        "default_verbosity": null,
        "apply_patch_tool_type": "freeform",
        "truncation_policy": { "mode": "tokens", "limit": 8192 },
        "supports_parallel_tool_calls": true,
        "context_window": 200000,
        "max_context_window": 200000,
        "auto_compact_token_limit": 180000,
        "effective_context_window_percent": 95,
        "experimental_supported_tools": []
      }]
    }
    """;
WriteText(Path.Combine(codexHome, "cadenza-catalog.json"), catalogJson);

WriteLine($"Codex config generated at: {codexHome}");
WriteLine("In another terminal, run:");
WriteLine($"  $env:CODEX_HOME      = \"{codexHome}\"");
WriteLine($"  $env:CADENZA_API_KEY = \"any-non-empty-string\"");
WriteLine($"  codex");

// OpenRouter를 LLM 백엔드로 연결.
var openAiOptions = new OpenAIClientOptions { Endpoint = new Uri("https://openrouter.ai/api/v1") };
var chatClient = new OpenAI.Chat.ChatClient(model, new ApiKeyCredential(apiKey), openAiOptions)
    .AsIChatClient();

UseChatClient(chatClient);

await Run();
```

그게 다입니다. 프로젝트 파일도, `.csproj` 도, `Program.cs` 도 없습니다. 맨 위의 `#:sdk` 디렉티브가 .NET 10 file-based 프로그램 시스템에 "이 스크립트는 `Cadenza.Agent` SDK를 쓴다"고 알려주고, SDK가 HTTP 서버, Responses wire 포맷, 모든 패키지 레퍼런스를 끌어다 붙이면서 `Tool`, `UseOllama`, `UseChatClient`, `Run` 을 namespace 없이 바로 호출할 수 있는 이름으로 노출합니다.

## 실행

스크립트를 `agent-codex-openrouter.cs` 로 저장한 뒤 다음과 같이 실행합니다.

```pwsh
# Terminal 1 — 에이전트 서버 기동
$env:OPENROUTER_API_KEY = "sk-or-v1-..."
$env:OPENROUTER_MODEL   = "anthropic/claude-3.5-sonnet"  # 또는 다른 OpenRouter slug
dotnet run agent-codex-openrouter.cs
```

첫 실행은 의존성(`Microsoft.Extensions.AI`, OpenAI SDK, ASP.NET Core)을 가져옵니다. 그 이후로는 1초 안에 부팅됩니다. 스크립트가 두 번째 터미널에 붙여 넣을 정확한 내용을 출력해 줍니다.

```text
Codex config generated at: D:\work\.cadenza-codex-openrouter

In another terminal, run:
  $env:CODEX_HOME      = "D:\work\.cadenza-codex-openrouter"
  $env:CADENZA_API_KEY = "any-non-empty-string"
  codex
```

이 내용을 다른 터미널에 그대로 붙여 넣고 `codex` 를 실행하면, Codex UX를 통해 Claude 3.5 Sonnet(또는 선택한 OpenRouter 모델)과 대화하는 상태가 됩니다. `shell`, `apply_patch` 같은 도구는 Codex가 매 요청마다 직접 보내고, 에이전트는 그걸 모델에 그대로 전달한 뒤 모델이 내뱉는 `function_call` 출력을 다시 Codex로 스트림해서 Codex가 로컬에서 실행하게 합니다.

## 내부에서 일어나는 일

Codex가 `POST /v1/responses` 를 보내면 에이전트는 다음과 같이 처리합니다.

1. **Responses input 파싱**. Codex는 `message` / `function_call` / `function_call_output` 배열을 보내는데, 이를 `Microsoft.Extensions.AI` 의 `IList<ChatMessage>` 형태로 평탄화합니다.
2. **`previous_response_id` 존중**. Codex는 매 턴마다 전체 히스토리를 다시 보내는 대신 이 id로 연쇄를 만듭니다. 에이전트는 과거 턴들을 bounded in-memory dictionary로 들고 있으면서 context를 재구성합니다.
3. **Codex의 도구를 passthrough**. Codex의 `shell`, `apply_patch`, `update_plan` 은 raw 스키마로 도착합니다. 이들을 JSON 스키마만 있고 실제 핸들러는 없는 `PassthroughFunction` 인스턴스로 모델에 선언합니다. 이 엔드포인트에서는 function-invocation 미들웨어를 우회하므로, 모델이 내뱉는 함수 호출은 그대로 Codex로 스트림됩니다.
4. **`IChatClient.GetStreamingResponseAsync` 호출**. 구성한 백엔드(OpenRouter, Ollama, OpenAI, Anthropic, Azure OpenAI)로 디스패치됩니다.
5. **Responses SSE로 다시 emit**. `ChatResponseUpdate` 스트림을 Codex가 기대하는 ~15개의 SSE 이벤트 타입으로 번역합니다(`response.created`, `response.in_progress`, `response.output_item.added`, `response.output_text.delta`, `response.function_call_arguments.delta`, `response.completed` 등).

이걸 composable 하게 만드는 핵심은 `IChatClient` 추상화입니다. Cadenza.Agent는 OpenRouter가 "사실은 Anthropic-한 번-Claude-다음번-Llama"라는 사실에 관심이 없습니다. 그냥 chat client 하나를 보고, 호출하고, 돌아온 걸 Codex가 원하는 wire 포맷으로 직렬화할 뿐입니다.

## `CODEX_HOME` 패턴

이 부분은 잠깐 멈춰서 칭찬하고 싶습니다. Codex CLI는 `CODEX_HOME` 환경변수를 honor 해서 `config.toml` 을 어디서 읽을지 override 합니다(`~/.codex/` 대신 사용자가 가리키는 디렉터리에서 읽습니다). 샘플은 이걸 최대한 활용합니다. 자기만의 `config.toml` 과 `cadenza-catalog.json` 이 들어 있는 sample-local 디렉터리를 만들고, 정확히 어떤 `$env:CODEX_HOME = ...` 줄을 붙여 넣어야 하는지 출력해 줍니다.

결과적으로 **글로벌 `~/.codex/config.toml` 이 그대로 보존**됩니다. 서로 다른 샘플(Ollama 백엔드, OpenRouter 백엔드, gpt-5 reasoning effort 튜닝)이 각자 격리된 디렉터리를 가지게 되고, 10개를 동시에 둬도 서로 안 부딪힙니다. 동료와 설정을 공유하고 싶다면 `.cs` 파일 하나만 건네면 됩니다. 동료의 codex 명령은 그 스크립트가 생성한 로컬 디렉터리를 가리키게 됩니다.

## "Defaulting to fallback metadata" 경고 해제

Codex가 모르는 모델 id를 가리키면 context window와 출력 limit에 기본 metadata로 폴백하고, 매 턴마다 경고를 출력합니다.

```text
⚠ Model metadata for `cadenza-codex-openrouter` not found.
   Defaulting to fallback metadata; this can degrade performance and cause issues.
```

이건 `model_catalog_json` config 키가 우리 slug를 선언한 JSON 파일을 가리키게 하면 사라집니다. 스키마는 `codex-rs/protocol/src/openai_models.rs::ModelInfo` 이며 필수 필드가 17개입니다. 샘플은 완전한 catalog 항목을 포함합니다. 만약 더 작은 context window를 가진 모델(예: `openai/gpt-4o-mini` 의 128K)로 바꾼다면, `context_window` 와 `max_context_window` 를 그에 맞춰 낮춰야 합니다. Codex는 이 숫자에 맞춰 prompt를 truncate 하므로, 과대 선언은 실제 backing 모델에서 조용히 token overflow를 일으킵니다.

추가 주의: `model_catalog_json` 은 Codex의 번들 카탈로그와 **merge되지 않고 대체**됩니다. `gpt-5-codex` 같이 기존 슬러그를 같이 쓰고 싶다면 우리 JSON에도 같이 넣어둬야 합니다.

## 만난 footgun 하나 (고친 이야기)

처음 돌렸을 때 Codex가 시작을 거부했습니다.

```text
Error loading configuration: failed to parse model_catalog_json path
`...\cadenza-catalog.json` as JSON: expected value at line 1 column 1
```

원인은 BOM이었습니다. .NET의 `Encoding.UTF8` 은 BOM-emitting variant 이므로, `File.WriteAllText(path, content, Encoding.UTF8)` 는 데이터 앞에 `EF BB BF` 를 prepend 합니다. Rust의 `serde_json`(Codex가 쓰는 라이브러리)은 이걸 거부합니다. RFC 8259 spec을 엄격히 준수하므로, JSON 구현은 BOM을 추가해선 안 됩니다.

Cadenza의 `Fs.WriteText` 도 그 BOM-emitting 기본값을 그대로 물려받고 있었습니다. `new UTF8Encoding(encoderShouldEmitUTF8Identifier: false)` 로 바꿔서 SDK `1.0.14` 로 출시했습니다. 같은 수정이 `Console.OutputEncoding` 에도 적용됩니다. 그게 없으면 `dotnet-script | jq` 가 파이프를 깨뜨립니다.

엄격한 파서로 파일을 쓰는 본인의 .NET 코드도 점검할 만한 부분입니다. 만약 `File.WriteAllText(path, text, Encoding.UTF8)` 을 거친다면, BOM을 emit 하고 있는 상태입니다. 한 줄짜리 수정으로 해결됩니다.

```csharp
File.WriteAllText(path, text, new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
```

## 이 패턴이 의미 있는 이유

Codex CLI의 tool loop는 정말 유용합니다. Responses API lock-in은 그대로 두면 열린 도구 생태계를 죽이는 종류의 vendor coupling으로 느껴집니다. `model_providers` config + `wire_api = "responses"` 라는 탈출구는 OpenAI가 명시적으로 "다른 곳에서 쓰고 싶을 수 있다는 걸 인정한다"고 말한 것이며, 그 제안을 받아들이는 게 올바른 행동입니다.

여러분이 통제하는 Responses 서버가 한 번 생기면 생태계가 열립니다.

- Codex를 무료 로컬 Ollama 모델 위에 올려 오프라인 작업을 하고 싶다면? `UseChatClient` 를 `UseOllama` 로 바꾸면 됩니다. 같은 스크립트, 같은 Codex config, 다른 두뇌.
- 모든 Codex 세션이 보게 될 프로젝트 핀 시스템 프롬프트를 주입하고 싶다면? `Run()` 호출 전에 넣으면 됩니다.
- 모든 Codex 턴을 감사 목적으로 로깅하고 싶다면? `IChatClient` 를 본인의 미들웨어로 감싸면 됩니다.
- prompt 크기에 따라 OpenRouter와 로컬 모델을 라운드 로빈하고 싶다면? C#으로 로직 쓰고 같은 엔드포인트로 제공하면 됩니다.

이걸 지속 가능하게 만드는 건 단일 파일 포맷입니다. 유지보수해야 할 프로젝트도 없고, 관리해야 할 SDK도 없고, 배포해야 할 별도 바이너리도 없습니다. 그냥 레포에 복사해 넣을 `.cs` 파일 하나입니다. `dotnet run script.cs` 가 동작하는 환경이라면(.NET 10 이상에서 동작합니다) 스크립트가 실행됩니다.

## 직접 해보기

.NET 10 설치 후 다음과 같이 실행합니다.

```pwsh
dotnet new install Cadenza.Templates
dotnet new cadenza-agent -n my-codex-backend -o ./my-codex-backend
cd my-codex-backend
# my-codex-backend.cs를 위의 OpenRouter 패턴으로 편집
$env:OPENROUTER_API_KEY = "sk-or-v1-..."
dotnet run my-codex-backend.cs
```

또는 [Cadenza 레포](https://github.com/rkttu/cadenza/tree/main/samples)에서 바로 실행 가능한 샘플을 받아도 됩니다. `agent-codex-openrouter.cs` 가 위에 적은 그 버전입니다. 레포에는 `agent-codex-backend.cs`(Ollama 변형)와 `agent-openrouter.cs`(Aider / Continue / Cursor용 Chat Completion 변형)도 같이 들어 있습니다.

이게 도움이 됐다면 어떤 백엔드를 연결했는지 알려주세요. 누군가 fine-tuned 로컬 모델과 오프라인용 로컬 fallback 조합으로 Codex를 돌리는지가 다음 실험거리입니다. 궁금합니다.

---

*Cadenza는 MIT 라이선스입니다. 소스: <https://github.com/rkttu/cadenza>. 글 작성 시점 기준 `Cadenza.Agent` 패키지는 `1.0.14` 입니다.*

---
title: "Running OpenAI Codex CLI on Top of Claude, Gemini, or Llama — in 50 Lines of C#"
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
  - .NET Development
translationKey: "cadenza-agent"
description: "OpenAI Codex CLI is locked into the Responses API. Cadenza.Agent stands up a Responses-compatible HTTP server in front of any IChatClient, so via OpenRouter you can swap Codex's brain at will."
cover:
  image: "images/posts/cadenza-agent.webp"
  alt: "Conceptual image of wiring OpenAI Codex CLI to any LLM with 50 lines of C#"
tldr: "Codex CLI only speaks the OpenAI Responses API, but its `model_providers` config — specifically `wire_api = \"responses\"` — is the escape hatch. With the Cadenza.Agent SDK, a single `.cs` file becomes a Responses-compatible HTTP server, and the same wire format keeps working whether the backend points at OpenRouter, Ollama, Anthropic, or Azure OpenAI."
---

> OpenAI's [Codex CLI](https://github.com/openai/codex) ships a great editor-agent UX — shell tools, `apply_patch`, plan tracking, all of it. The catch: as of February 2026, it only speaks the OpenAI **Responses API**. Chat Completion support was removed (the `WireApi` enum in `codex-rs/model-provider-info/src/lib.rs` now has only `Responses`), which leaves Chat-Completion-only endpoints — Ollama, LM Studio, your favourite Llama runner — locked out. This post walks through how I used .NET 10 file-based programs and the `IChatClient` abstraction from `Microsoft.Extensions.AI` to stand up a Responses-compatible server in a single 50-line C# file, with OpenRouter as the backend, so that Codex CLI can run on top of whichever model I feel like that day.

---

## Setting the Stage

Codex CLI is happy to talk to **any** server that speaks Responses. The `model_provider` config block exists exactly for this. So if you can stand up a Responses-compatible HTTP endpoint backed by the model of your choice, Codex becomes a generalized front-end and the brain is yours to pick.

The trick I've been enjoying lately: spin up a 50-line C# script that runs both an OpenAI Chat Completion server and a Responses API server on top of the vendor-neutral `IChatClient` abstraction from `Microsoft.Extensions.AI`. Point the backend at [OpenRouter](https://openrouter.ai/) — one API key, hundreds of models including Claude, Gemini, Llama, and GPT — and tell Codex to talk to this local script instead of OpenAI.

The end result: **OpenAI Codex CLI running on top of Anthropic's Claude 3.5 Sonnet** (or any other model I'm in the mood for).

## The Moving Parts

I use an MSBuild SDK I publish myself, [Cadenza.Agent](https://www.nuget.org/packages/Cadenza.Agent). It turns a single `.cs` file into an executable agent server. It's part of a family of single-file scripting SDKs for .NET 10 file-based programs — same spirit as `dotnet run script.cs`, but with a richer Tier-1 API (`Tool`, `UseOllama`, `UseOpenAi`, `Run`, etc.). The Agent variant exposes:

- `POST /v1/chat/completions` — for Aider / Continue / Cursor / Copilot BYOK / sgpt
- `POST /v1/responses` — for Codex CLI

Both are backed by the same `IChatClient` you configure. Swap the backend, and the wire format stays put.

For the LLM side I use OpenRouter. It exposes OpenAI's Chat Completion wire format under a different base URL, so I can plug it straight into `Microsoft.Extensions.AI.OpenAI`'s `ChatClient`. One environment variable, any model.

The Codex config leans on the `CODEX_HOME` environment variable trick: instead of editing `~/.codex/config.toml`, I make Codex point at a sample-local directory that contains its own `config.toml`. That keeps the global config untouched and makes the sample fully self-contained.

## The Script

The entire backend in a single file:

```csharp
#!/usr/bin/env dotnet run
#:sdk Cadenza.Agent@1.0.14

using System.ClientModel;
using OpenAI;

var apiKey = Env.Get("OPENROUTER_API_KEY")
    ?? throw new InvalidOperationException("OPENROUTER_API_KEY env var missing");
var model = Env.Get("OPENROUTER_MODEL") ?? "anthropic/claude-3.5-sonnet";

ServedModelName = "cadenza-codex-openrouter";

// Sample-local Codex home directory.
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

// Catalog JSON: declares our model id to Codex so the "Defaulting to
// fallback metadata" warning goes away. Field set is from the ModelInfo
// schema in codex-rs/protocol/src/openai_models.rs — every key is required.
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

// Wire OpenRouter as the LLM backend.
var openAiOptions = new OpenAIClientOptions { Endpoint = new Uri("https://openrouter.ai/api/v1") };
var chatClient = new OpenAI.Chat.ChatClient(model, new ApiKeyCredential(apiKey), openAiOptions)
    .AsIChatClient();

UseChatClient(chatClient);

await Run();
```

That's all of it. No project file, no `.csproj`, no `Program.cs`. The `#:sdk` directive at the top tells the .NET 10 file-based program system that this script uses the `Cadenza.Agent` SDK, and the SDK in turn brings in the HTTP server, the Responses wire format, every package reference, and exposes `Tool`, `UseOllama`, `UseChatClient`, and `Run` as plain identifiers you call without namespaces.

## Running It

Save the script as `agent-codex-openrouter.cs`, then:

```pwsh
# Terminal 1 — boot the agent server
$env:OPENROUTER_API_KEY = "sk-or-v1-..."
$env:OPENROUTER_MODEL   = "anthropic/claude-3.5-sonnet"  # or any other OpenRouter slug
dotnet run agent-codex-openrouter.cs
```

The first run pulls the dependencies (`Microsoft.Extensions.AI`, the OpenAI SDK, ASP.NET Core). After that it boots in under a second. The script prints exactly what to paste into the second terminal:

```text
Codex config generated at: D:\work\.cadenza-codex-openrouter

In another terminal, run:
  $env:CODEX_HOME      = "D:\work\.cadenza-codex-openrouter"
  $env:CADENZA_API_KEY = "any-non-empty-string"
  codex
```

Paste that into another terminal, run `codex`, and you're now driving Claude 3.5 Sonnet (or whichever OpenRouter model you picked) through the Codex UX. Tools like `shell` and `apply_patch` are sent by Codex on every request; the agent forwards them to the model verbatim, then streams the model's `function_call` output back to Codex so Codex can execute them locally.

## What's Happening Under the Hood

When Codex sends `POST /v1/responses`, the agent does the following:

1. **Parse the Responses input.** Codex sends arrays of `message` / `function_call` / `function_call_output`. The agent flattens that into an `IList<ChatMessage>` for `Microsoft.Extensions.AI`.
2. **Honour `previous_response_id`.** Codex builds a chain via that id instead of re-sending the full history each turn — so the agent keeps past turns in a bounded in-memory dictionary and rebuilds context as needed.
3. **Pass Codex's tools through.** Codex's `shell`, `apply_patch`, and `update_plan` arrive as raw schemas. We declare them to the model as `PassthroughFunction` instances that carry only the JSON schema and have no real handler. The function-invocation middleware is bypassed for this endpoint, so any function calls the model emits get streamed straight back to Codex.
4. **Call `IChatClient.GetStreamingResponseAsync`.** That dispatches to whichever backend you configured — OpenRouter, Ollama, OpenAI, Anthropic, Azure OpenAI.
5. **Re-emit as Responses SSE.** The `ChatResponseUpdate` stream is translated into the ~15 SSE event types Codex expects: `response.created`, `response.in_progress`, `response.output_item.added`, `response.output_text.delta`, `response.function_call_arguments.delta`, `response.completed`, and friends.

The key to making this composable is the `IChatClient` abstraction. Cadenza.Agent doesn't care that OpenRouter is "actually Anthropic-this-call-then-Llama-the-next." It sees a single chat client, calls it, and serializes the result into whatever wire format Codex wants.

## The `CODEX_HOME` Pattern

Worth stopping on. Codex CLI honours the `CODEX_HOME` environment variable and overrides where it reads `config.toml` from — instead of `~/.codex/`, it reads from whatever directory you point at. The sample takes full advantage: it creates a sample-local directory with its own `config.toml` and `cadenza-catalog.json`, and prints the exact `$env:CODEX_HOME = ...` line you need to paste.

The payoff: **the global `~/.codex/config.toml` stays untouched.** Different samples — Ollama backend, OpenRouter backend, gpt-5 reasoning-effort tuning — get their own isolated directories. You can keep ten of them around without collisions. Want to share your setup with a teammate? Hand them the `.cs` file. Their `codex` command will point at the local directory the script creates.

## Silencing the "Defaulting to fallback metadata" Warning

If Codex points at a model id it doesn't recognise, it falls back to default metadata for context window and output limits, and prints a warning every turn:

```text
⚠ Model metadata for `cadenza-codex-openrouter` not found.
   Defaulting to fallback metadata; this can degrade performance and cause issues.
```

This disappears once the `model_catalog_json` config key points at a JSON file declaring our slug. The schema is `codex-rs/protocol/src/openai_models.rs::ModelInfo` — 17 required fields. The sample includes the full catalog entry. If you swap in a model with a smaller context window (say the 128K of `openai/gpt-4o-mini`), drop `context_window` and `max_context_window` to match. Codex truncates the prompt to those numbers, so over-declaring quietly causes token overflow on the actual backing model.

One more thing: `model_catalog_json` **replaces** Codex's bundled catalog rather than merging with it. If you want to keep an existing slug like `gpt-5-codex` alongside yours, include it in your JSON too.

## One Footgun I Hit (and Fixed)

The first time I ran this, Codex refused to start:

```text
Error loading configuration: failed to parse model_catalog_json path
`...\cadenza-catalog.json` as JSON: expected value at line 1 column 1
```

The culprit was a BOM. .NET's `Encoding.UTF8` is the BOM-emitting variant, so `File.WriteAllText(path, content, Encoding.UTF8)` prepends `EF BB BF` to the data. Rust's `serde_json` (the library Codex uses) rejects that — it follows RFC 8259 strictly, and JSON implementations must not add a BOM.

Cadenza's `Fs.WriteText` inherited that BOM-emitting default. I switched to `new UTF8Encoding(encoderShouldEmitUTF8Identifier: false)` and shipped it as SDK `1.0.14`. The same fix applies to `Console.OutputEncoding`; without it, `dotnet-script | jq` breaks the pipe.

Worth auditing in your own .NET code if you write files for strict parsers: if it goes through `File.WriteAllText(path, text, Encoding.UTF8)`, you're emitting a BOM. The one-line fix:

```csharp
File.WriteAllText(path, text, new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
```

## Why This Pattern Matters

Codex CLI's tool loop is genuinely useful. The Responses API lock-in, left alone, feels like the kind of vendor coupling that kills an open tooling ecosystem. The `model_providers` config plus `wire_api = "responses"` escape hatch is OpenAI explicitly acknowledging "you might want to use this somewhere else" — and taking them up on the offer is the right move.

Once you have a Responses server you control, the ecosystem opens up.

- Want Codex on top of a free local Ollama model for offline work? Swap `UseChatClient` for `UseOllama`. Same script, same Codex config, different brain.
- Want to inject a project-pinned system prompt that every Codex session sees? Add it before `Run()`.
- Want to log every Codex turn for audit? Wrap the `IChatClient` in your own middleware.
- Want to round-robin between OpenRouter and a local model based on prompt size? Write the logic in C# and serve it from the same endpoint.

The single-file format is what makes this sustainable. There's no project to maintain, no SDK to manage, no separate binary to ship. Just a `.cs` file you can paste into a repo. Anywhere `dotnet run script.cs` works (which is .NET 10 or later), the script runs.

## Try It Yourself

After installing .NET 10:

```pwsh
dotnet new install Cadenza.Templates
dotnet new cadenza-agent -n my-codex-backend -o ./my-codex-backend
cd my-codex-backend
# Edit my-codex-backend.cs to follow the OpenRouter pattern above
$env:OPENROUTER_API_KEY = "sk-or-v1-..."
dotnet run my-codex-backend.cs
```

Or grab a ready-to-run sample from the [Cadenza repo](https://github.com/rkttu/cadenza/tree/main/samples) — `agent-codex-openrouter.cs` is the version shown above. The repo also ships `agent-codex-backend.cs` (Ollama variant) and `agent-openrouter.cs` (Chat Completion variant for Aider / Continue / Cursor).

If this helped, let me know which backend you wired up. I'm especially curious whether anyone runs Codex against a fine-tuned local model with a local fallback for offline use — that's the experiment I want to try next.

---

*Cadenza is MIT-licensed. Source: <https://github.com/rkttu/cadenza>. At the time of writing the `Cadenza.Agent` package is at `1.0.14`.*

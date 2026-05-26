---
title: "OpenAI Codex CLIをClaude・Gemini・Llamaの上で動かす — C# 50行で"
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
  - .NET 開発
translationKey: "cadenza-agent"
description: "OpenAI Codex CLIはResponses APIにロックインされています。Cadenza.AgentでIChatClientの前段にResponses互換サーバーを立てれば、OpenRouter経由でCodexの頭脳を自由に選べます。"
cover:
  image: "images/posts/cadenza-agent.webp"
  alt: "C# 50行でOpenAI Codex CLIを任意のLLMに繋ぐコンセプト画像"
tldr: "Codex CLIはOpenAI Responses APIだけに縛られていますが、`model_providers`設定の`wire_api = \"responses\"`が抜け道になります。Cadenza.Agent SDKを使えば単一の`.cs`ファイルでResponses互換HTTPサーバーを立てられ、バックエンドをOpenRouter・Ollama・Anthropic・Azure OpenAIのどれに向けても同じwireフォーマットが維持されます。"
---

> OpenAIの[Codex CLI](https://github.com/openai/codex)は優れたエディタエージェントUXを提供します（shellツール、`apply_patch`、plan tracking がすべて揃っています）。問題は、2026年2月時点でOpenAI **Responses API**だけをサポートしていることです。Chat Completionサポートは削除されており（`codex-rs/model-provider-info/src/lib.rs`の`WireApi` enumには`Responses`のみが残っています）、Chat Completionのみをサポートするエンドポイント（Ollama、LM Studio、お気に入りのLlama runner）はそのまま閉ざされてしまいます。本記事は.NET 10のfile-basedプログラムと`Microsoft.Extensions.AI`の`IChatClient`抽象化を活用し、50行のC#一ファイルでResponses互換サーバーを立て、OpenRouterを介してCodex CLIを任意のモデル上で動作させた過程をまとめます。

---

## はじめに

Codex CLIはResponsesを話す**どんな**サーバーとも気持ちよく対話します。`model_provider` configブロックがまさにこのために存在します。つまり、好きなモデルでバックされたResponses互換HTTPエンドポイントを立てさえすれば、Codexは汎用フロントエンドになり、頭脳はユーザーが選べます。

最近私が気に入っているトリックは次のとおりです。`Microsoft.Extensions.AI`のベンダー中立な`IChatClient`抽象化の上で、OpenAI Chat CompletionサーバーとResponses APIサーバーを同時に動かす50行のC#スクリプトを起動します。バックエンドは[OpenRouter](https://openrouter.ai/)に向けます（APIキー1つで Claude、Gemini、Llama、GPTなど数百のモデルを使えます）。そしてCodexに対して、OpenAIではなくこのローカルスクリプトと対話するよう設定します。

最終的な結果は、**OpenAI Codex CLIがAnthropicのClaude 3.5 Sonnetの上で動作する**状態です（あるいはその日に使いたい別のモデルの上でも）。

## 構成要素

私が自分で公開している[Cadenza.Agent](https://www.nuget.org/packages/Cadenza.Agent)というMSBuild SDKを使います。単一の`.cs`ファイルを実行可能なエージェントサーバーに変換するSDKで、.NET 10のfile-basedプログラム向け単一ファイルスクリプティングSDKファミリーの一部です（`dotnet run script.cs`と同じ発想ですが、より豊富なTier-1 API（`Tool`、`UseOllama`、`UseOpenAi`、`Run`など）を提供します）。Agentバリアントは次を公開します。

- `POST /v1/chat/completions` — Aider / Continue / Cursor / Copilot BYOK / sgpt 向け
- `POST /v1/responses` — Codex CLI 向け

どちらもユーザーが構成した同じ`IChatClient`でバックされます。バックエンドを変えても wireフォーマットはそのままです。

LLM側はOpenRouterを使います。OpenAIのChat Completion wireフォーマットを別のbase URLでそのまま提供するので、`Microsoft.Extensions.AI.OpenAI`の`ChatClient`をそのまま挿して使えます。環境変数1つ、任意のモデル。

Codexの設定は`CODEX_HOME`環境変数のトリックを活用します。`~/.codex/config.toml`を編集する代わりに、Codexが指すディレクトリをサンプル専用に別途作っておけば、そこから新しい`config.toml`を読みます。これでユーザーのグローバル設定に一切触れない、自己完結型のサンプルが作れます。

## スクリプト

バックエンドのすべて、ファイル1つです。

```csharp
#!/usr/bin/env dotnet run
#:sdk Cadenza.Agent@1.0.14

using System.ClientModel;
using OpenAI;

var apiKey = Env.Get("OPENROUTER_API_KEY")
    ?? throw new InvalidOperationException("OPENROUTER_API_KEY env var missing");
var model = Env.Get("OPENROUTER_MODEL") ?? "anthropic/claude-3.5-sonnet";

ServedModelName = "cadenza-codex-openrouter";

// サンプル専用のCodex homeディレクトリを作成。
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

// Catalog JSON: Codex に提供するモデル id を宣言して "Defaulting to
// fallback metadata" 警告を防ぎます。フィールドは codex-rs/protocol/src/
// openai_models.rs の ModelInfo スキーマ基準 — すべてのキーが必須です。
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

// OpenRouter を LLM バックエンドとして接続。
var openAiOptions = new OpenAIClientOptions { Endpoint = new Uri("https://openrouter.ai/api/v1") };
var chatClient = new OpenAI.Chat.ChatClient(model, new ApiKeyCredential(apiKey), openAiOptions)
    .AsIChatClient();

UseChatClient(chatClient);

await Run();
```

これがすべてです。プロジェクトファイルも、`.csproj`も、`Program.cs`もありません。一番上の`#:sdk`ディレクティブが.NET 10のfile-basedプログラムシステムに「このスクリプトは`Cadenza.Agent` SDKを使う」と知らせ、SDKがHTTPサーバー、Responses wireフォーマット、すべてのパッケージ参照を引き込みつつ、`Tool`、`UseOllama`、`UseChatClient`、`Run`を名前空間なしですぐ呼べる名前として公開します。

## 実行

スクリプトを`agent-codex-openrouter.cs`として保存し、次のように実行します。

```pwsh
# Terminal 1 — エージェントサーバー起動
$env:OPENROUTER_API_KEY = "sk-or-v1-..."
$env:OPENROUTER_MODEL   = "anthropic/claude-3.5-sonnet"  # または別のOpenRouter slug
dotnet run agent-codex-openrouter.cs
```

初回実行では依存関係（`Microsoft.Extensions.AI`、OpenAI SDK、ASP.NET Core）を取得します。それ以降は1秒以内に起動します。スクリプトが2つ目のターミナルに貼り付ける正確な内容を出力してくれます。

```text
Codex config generated at: D:\work\.cadenza-codex-openrouter

In another terminal, run:
  $env:CODEX_HOME      = "D:\work\.cadenza-codex-openrouter"
  $env:CADENZA_API_KEY = "any-non-empty-string"
  codex
```

この内容を別のターミナルにそのまま貼り付けて`codex`を実行すれば、Codex UXを通じてClaude 3.5 Sonnet（または選択したOpenRouterモデル）と対話する状態になります。`shell`や`apply_patch`のようなツールはCodexが毎リクエストごとに直接送ってきて、エージェントはそれをモデルにそのまま渡し、モデルが吐き出す`function_call`の出力を再びCodexにストリームしてCodexがローカルで実行します。

## 内部で起きていること

Codexが`POST /v1/responses`を送ると、エージェントは次のように処理します。

1. **Responsesのinputをパース**。Codexは`message` / `function_call` / `function_call_output`の配列を送ってくるので、これを`Microsoft.Extensions.AI`の`IList<ChatMessage>`形式に平坦化します。
2. **`previous_response_id`を尊重**。Codexは毎ターン全履歴を再送する代わりにこのidで連鎖を作ります。エージェントは過去のターンを bounded in-memory dictionaryで保持し、コンテキストを再構築します。
3. **Codexのツールをpassthrough**。Codexの`shell`、`apply_patch`、`update_plan`はraw schemaで到着します。これらをJSONスキーマだけを持ち実際のハンドラを持たない`PassthroughFunction`インスタンスとしてモデルに宣言します。このエンドポイントではfunction-invocationミドルウェアをバイパスするので、モデルが吐き出す関数呼び出しはそのままCodexにストリームされます。
4. **`IChatClient.GetStreamingResponseAsync`を呼び出し**。構成したバックエンド（OpenRouter、Ollama、OpenAI、Anthropic、Azure OpenAI）にディスパッチされます。
5. **Responses SSEとして再emit**。`ChatResponseUpdate`ストリームをCodexが期待する約15個のSSEイベントタイプに翻訳します（`response.created`、`response.in_progress`、`response.output_item.added`、`response.output_text.delta`、`response.function_call_arguments.delta`、`response.completed`など）。

これをcomposableにする鍵は`IChatClient`抽象化です。Cadenza.AgentはOpenRouterが「実はAnthropic-今回-Claude-次回-Llama」であることに関心がありません。ただchat client 1つを見て、呼び出し、戻ってきたものをCodexが望むwireフォーマットでシリアライズするだけです。

## `CODEX_HOME`パターン

ここは少し立ち止まって称賛したい部分です。Codex CLIは`CODEX_HOME`環境変数をhonorして`config.toml`をどこから読むかをoverrideします（`~/.codex/`の代わりにユーザーが指すディレクトリから読みます）。サンプルはこれを最大限活用します。自分専用の`config.toml`と`cadenza-catalog.json`が入っているsample-localディレクトリを作り、貼り付けるべき正確な`$env:CODEX_HOME = ...`行を出力してくれます。

その結果、**グローバルの`~/.codex/config.toml`はそのまま保たれます**。異なるサンプル（Ollamaバックエンド、OpenRouterバックエンド、gpt-5 reasoning effortチューニング）がそれぞれ隔離されたディレクトリを持ち、10個並べてもぶつかりません。同僚と設定を共有したい場合は、`.cs`ファイルを1つ渡すだけです。同僚のcodexコマンドはそのスクリプトが生成したローカルディレクトリを指すようになります。

## 「Defaulting to fallback metadata」警告の解消

Codexが知らないモデルidを指すと、context windowと出力limitに既定のmetadataでフォールバックし、毎ターン警告を出します。

```text
⚠ Model metadata for `cadenza-codex-openrouter` not found.
   Defaulting to fallback metadata; this can degrade performance and cause issues.
```

これは`model_catalog_json` configキーが我々のslugを宣言したJSONファイルを指すようにすれば消えます。スキーマは`codex-rs/protocol/src/openai_models.rs::ModelInfo`で、必須フィールドが17個あります。サンプルには完全なcatalogエントリが含まれています。もしより小さなcontext windowを持つモデル（例: `openai/gpt-4o-mini`の128K）に切り替える場合は、`context_window`と`max_context_window`をそれに合わせて下げる必要があります。Codexはこの数値に合わせてpromptをtruncateするので、過大宣言は実際のbackingモデルで静かにtoken overflowを引き起こします。

もう一点注意: `model_catalog_json`はCodexのバンドルカタログと**マージされずに置換**されます。`gpt-5-codex`のような既存slugを併用したい場合は、我々のJSONにも含めておく必要があります。

## 出会ったfootgun 1つ (修正した話)

最初に動かしたとき、Codexが起動を拒否しました。

```text
Error loading configuration: failed to parse model_catalog_json path
`...\cadenza-catalog.json` as JSON: expected value at line 1 column 1
```

原因はBOMでした。.NETの`Encoding.UTF8`はBOM-emitting variantなので、`File.WriteAllText(path, content, Encoding.UTF8)`はデータの前に`EF BB BF`をprependします。Rustの`serde_json`（Codexが使うライブラリ）はこれを拒否します。RFC 8259 specを厳密に遵守するため、JSON実装はBOMを追加してはいけません。

Cadenzaの`Fs.WriteText`もそのBOM-emittingデフォルトをそのまま引き継いでいました。`new UTF8Encoding(encoderShouldEmitUTF8Identifier: false)`に変更してSDK `1.0.14`としてリリースしました。同じ修正が`Console.OutputEncoding`にも適用されます。それがないと`dotnet-script | jq`がパイプを壊します。

厳密なパーサ向けにファイルを書く自分の.NETコードも点検する価値があります。もし`File.WriteAllText(path, text, Encoding.UTF8)`を経由するなら、BOMをemitしている状態です。1行の修正で解決します。

```csharp
File.WriteAllText(path, text, new UTF8Encoding(encoderShouldEmitUTF8Identifier: false));
```

## このパターンが意味を持つ理由

Codex CLIのtool loopは本当に有用です。Responses APIのlock-inをそのまま放置すれば、開いたツールエコシステムを殺すたぐいのvendor couplingに感じられます。`model_providers` config + `wire_api = "responses"`という抜け道は、OpenAIが明示的に「他の場所でも使いたいかもしれないことを認める」と言ったものであり、その提案を受け入れるのが正しい行動です。

ユーザーが制御するResponsesサーバーが一度できれば、エコシステムが開きます。

- Codexを無料のローカルOllamaモデルの上で動かしてオフライン作業をしたい? `UseChatClient`を`UseOllama`に置き換えるだけ。同じスクリプト、同じCodex config、別の頭脳。
- すべてのCodexセッションに見せるプロジェクトピンのシステムプロンプトを注入したい? `Run()`の呼び出し前に入れるだけ。
- すべてのCodexのターンを監査用にロギングしたい? `IChatClient`を自分のミドルウェアで包むだけ。
- promptのサイズに応じてOpenRouterとローカルモデルをラウンドロビンしたい? C#でロジックを書いて同じエンドポイントから提供するだけ。

これを持続可能にしているのは単一ファイル形式です。維持すべきプロジェクトもなく、管理すべきSDKもなく、配布すべき別バイナリもありません。ただレポにコピーして入れる`.cs`ファイル1つです。`dotnet run script.cs`が動く環境であれば（.NET 10以上で動きます）、スクリプトは実行されます。

## 自分で試してみる

.NET 10をインストール後、次のように実行します。

```pwsh
dotnet new install Cadenza.Templates
dotnet new cadenza-agent -n my-codex-backend -o ./my-codex-backend
cd my-codex-backend
# my-codex-backend.csを上のOpenRouterパターンに編集
$env:OPENROUTER_API_KEY = "sk-or-v1-..."
dotnet run my-codex-backend.cs
```

または[Cadenzaレポ](https://github.com/rkttu/cadenza/tree/main/samples)からそのまま実行可能なサンプルを取得することもできます。`agent-codex-openrouter.cs`が上に示したバージョンです。レポには`agent-codex-backend.cs`（Ollamaバリアント）と`agent-openrouter.cs`（Aider / Continue / Cursor向けのChat Completionバリアント）も同梱されています。

これが役に立ったらどのバックエンドを繋いだか教えてください。誰かがfine-tunedローカルモデルとオフライン用のローカルfallbackの組み合わせでCodexを動かしているかどうかが次の実験課題です。気になっています。

---

*CadenzaはMITライセンスです。ソース: <https://github.com/rkttu/cadenza>。記事執筆時点で`Cadenza.Agent`パッケージは`1.0.14`です。*

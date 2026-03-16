---
title: "RoleEntryPointからFoundryCBAgentまで — .NET開発者が見たMicrosoft Foundry Hosted Agentのアーキテクチャ"
date: 2026-03-17T00:00:00+09:00
draft: false
slug: "hosted-agent-deep-dive"
tags:
  - Azure
  - .NET
  - AIエージェント
  - PaaS
  - Microsoft Foundry
categories:
  - クラウド
translationKey: "hosted-agent-deep-dive"
description: "Microsoft Foundry Hosted Agentのアーキテクチャを、Windows Azure Cloud Servicesから続く.NET PaaSの系譜の中で分析します。"
cover:
  image: "images/posts/hosted-agent-deep-dive.webp"
  alt: "クラウドプラットフォームアーキテクチャのコンセプトイメージ"
tldr: "Hosted AgentはCloud ServicesのRoleEntryPointと同じ設計原則で、アダプターがHTTP/SSE/認証を処理し、開発者はIAgentInvocation.InvokeAsyncの実装に集中します。プレビュー段階ですが、この契約ベースのアーキテクチャを理解しておけば、GA後のマイグレーションパスを確保できます。"
---

> この記事は2026年3月時点で、パブリックプレビュー状態にあるMicrosoft Foundry Hosted Agentの設計を、.NETアーキテクチャの系譜の中で分析します。現時点でプロダクション利用を推奨する記事ではなく、エンタープライズAIアーキテクトが注目すべき設計の方向性に焦点を当てています。

---

## エージェントをプロダクションに載せるということ

エンタープライズでAIエージェントをプロダクションにデプロイしようとする際、現在の選択肢は2つです。

**宣言的エージェント。** Microsoft Foundryポータルでプロンプトとツールを組み合わせて作るno-code方式です。素早く作成できますが、複雑な分岐ロジックやマルチステップワークフロー、外部システムとの精密な連携をコードで制御できません。一定レベルを超えた瞬間に限界に突き当たります。

**セルフホストコンテナ。** エージェントロジックをコードで直接記述し、コンテナに入れてデプロイする方式です。自由度は完全ですが、HTTPサーバー構成、認証、会話状態管理、スケーリング、モニタリング、バージョン管理をすべて自前で実装する必要があります。そして決定的に、コンテナ内でエージェントが何をしているか **プラットフォームには一切わかりません。** LLMをどう呼び出したか、ツールをどの順序で使ったか、なぜそのレスポンスを生成したかがブラックボックスです。

Hosted Agentはこの間の空白を埋めます。コードレベルの自由度を維持しつつ、エージェントの動作がプラットフォームに構造的に透明に公開される第3の道です。

---

## Windows Azureを覚えていますか

現在のMicrosoft Azureは、2010年2月に **Windows Azure** という名前で商用リリースされました。2014年3月にMicrosoft Azureにリブランディングされるまで、このプラットフォームのアイデンティティは現在とはかなり異なっていました。

Windows Azureは本質的に **PaaSプラットフォーム** でした。VMを直接操作するIaaSは当初存在せず、2012年になってようやくVirtual Machinesが追加されました。出発点はCloud Services（Web Role、Worker Role）、SQL Azure（現在のAzure SQL Database）、Storage Servicesのようなマネージドサービスでした。開発者がインフラを意識せずコードと設定ファイルだけでデプロイすることが核心の約束であり、これは当時AWSがEC2中心のIaaSで市場を切り開いていたのとは根本的に異なるアプローチでした。

2014年のリブランディング後、AzureはAWSを強く意識しながらIaaS機能を急速に拡充しました。VM、VNET、Load Balancer、そして後のAKSまで。市場で「クラウド＝仮想マシンを借りて使うこと」という認識が支配的だった時期にIaaSを強化したのは商業的に正しい判断でしたが、その過程でWindows Azure時代のPaaS中心の哲学は多少希薄化しました。

しかしMicrosoftの本来の強みは常にPaaSとSaaSにありました。.NET Framework、Visual Studio、SQL Server、Office 365、SharePoint — この会社は開発者とインフォメーションワーカーに **マネージドプラットフォーム** 上で働かせることに30年以上の歴史を持っています。Windows Azure時代のCloud Servicesはその哲学のクラウド拡張であり、その後のApp Service、Azure Functions、Container Appsも同じ文脈にあります。

この背景を理解すると、Hosted Agentがなぜこの形で設計されたかが明確になります。MicrosoftはAIエージェントという新しいワークロードに対して、IaaS的アプローチ（セルフホストコンテナを直接管理）ではなくPaaS的アプローチ（プラットフォームがホスティングし、開発者はロジックに集中）を選択したのです。これはAWSがBedrock Agentsで取る方向とも、GoogleがVertex AI Agent Builderで取る方向とも異なります。MicrosoftのPaaS DNAがAI時代に再び発現したと見ることができます。

---

## どこかで見たパターン

.NET開発者であれば、そしてAzureの歴史を共に歩んできた開発者であれば、Hosted Agentのアーキテクチャに強いデジャヴを感じるでしょう。

Windows Azure Cloud Servicesの時代を思い出してみましょう。あの時も「開発者はビジネスロジックだけを書き、プラットフォームが提供するホストプロセスがそのロジックを包んでインフラに載せる」というのが核心の約束でした。`RoleEntryPoint`を継承し、`OnStart()`、`Run()`、`OnStop()`を実装すれば、`WaWorkerHost.exe`がそのコードをロードして実行し、Fabric Controllerがインスタンスのプロビジョニングとヘルスモニタリングを担当していました。

Hosted Agentの構造は、このパターンをAIエージェントドメインに再解釈したものです。

| Windows Azure Cloud Services | Microsoft Foundry Hosted Agent |
| --- | --- |
| `RoleEntryPoint` 抽象クラス | `FoundryCBAgent` / `IAgentInvocation` インターフェース |
| `OnStart()`, `Run()`, `OnStop()` | `InvokeAsync()` + liveness/readinessプローブ |
| `WaIISHost.exe` / `WaWorkerHost.exe` | AgentServerアダプター内蔵Kestrelサーバー |
| `.csdef` + `.cscfg` | `agent.yaml` + 環境変数 |
| Fabric Controller | Agent Service Runtime |
| DiagnosticMonitor (WAD) | OpenTelemetry自動計装 + Application Insights |
| Input/Internal Endpoint宣言 | Foundry Responses APIプロトコル自動公開 |

核心的な共通点は3つです。プラットフォームのホストプロセスが開発者コードをロードする構造、プラットフォームが定義した契約（contract）に合わせてコードを書くルール、インフラの関心事がプラットフォームに移転する効果。15年前にCloud Servicesで機能したこの設計原則が、今AIエージェントという新しいワークロードに再び適用されています。

---

## Hosting Adapterの実体：事前構成されたKestrel

.NETの観点からHosting Adapterの実体を正確に把握することが重要です。

`Azure.AI.AgentServer.Core`パッケージはASP.NET CoreのKestrelサーバー、DIコンテナ、ミドルウェアパイプラインを共有しています。一般的なASP.NET Coreアプリと技術スタックの基盤は同じです。違いは、`WebApplicationBuilder`を直接構成する代わりに、**アダプターパッケージが提供する事前構成されたホストを使用する** という点です。

一般的なASP.NET Coreアプリで`Program.cs`に`builder.Services.AddXxx()`、`app.MapPost()`、`app.UseMiddleware()`を直接組み合わせるのとは異なり、Hosted Agentではこの組み合わせが完了した状態で`IAgentInvocation.InvokeAsync`だけを実装します。ルーティング（`/responses`、`/liveness`、`/readiness`）、SSEストリーミング用のchunkedレスポンス設定、OpenTelemetryミドルウェア登録、認証処理パイプラインがすべてアダプター内部で構成完了した状態で提供されます。

```text
技術スタックの垂直断面：

┌─────────────────────────────────────────┐
│  IAgentInvocation.InvokeAsync           │  ← 開発者が実装
│  (エージェントビジネスロジック)               │
├─────────────────────────────────────────┤
│  Azure.AI.AgentServerアダプター層          │  ← パッケージが提供
│  - Foundry Responses APIプロトコル変換      │
│  - SSEストリーミングイベントシリアライズ       │
│  - OpenTelemetry自動計装                   │
│  - OAuth consent処理                      │
│  - Tool Clientプロビジョニング              │
├─────────────────────────────────────────┤
│  ASP.NET Coreミドルウェアパイプライン         │  ← 共有スタック
│  Kestrel HTTPサーバー                      │
│  DIコンテナ、設定システム                     │
└─────────────────────────────────────────┘
```

Python側ではStarlette（ASGIフレームワーク）を内蔵Webサーバーとして使用しています。「アダプターが組み込みWebサーバーを内蔵する」というアーキテクチャパターンは同じですが、各言語でそのエコシステムで最も自然なWebスタックを選択しています。

---

## なぜアダプターを迂回できないのか

「Foundryが期待するエンドポイントスペックを直接実装すればいいのではないか」という疑問が出るかもしれません。`/responses`、`/liveness`、`/readiness`の3つのパスを合わせるだけでは？

これが単純なRESTエンドポイント数個を合わせる問題ではない理由は、**HTTPプロトコルレベルでの再定義が要求されるから** です。

エージェントのレスポンスは一般的なJSON一塊ではありません。`ResponseTextDeltaEvent` → `ResponseTextDoneEvent` → `ResponseContentPartDoneEvent` → `ResponseOutputItemDoneEvent` → `ResponseCompletedEvent`と続く **順序が決まったイベントチェーン** です。これがHTTPレスポンスとして出る際にはchunked transfer encodingベースのSSEストリームでなければならず、各イベントのJSONスキーマ、シーケンスナンバリング、終了条件までプロトコルが規定しています。

.NETの`IAgentInvocation`実装コードを見ると、この構造が明確になります。`InvokeAsync`が`IAsyncEnumerable<ResponseStreamEvent>`を返し、アダプターがこのストリームを受け取ってSSEに変換します。各イベントにはシーケンス番号（`seq`）が付与され、`ResponseOutputItemDoneEvent`には完成したコンテンツが、`ResponseCompletedEvent`には完全なレスポンスオブジェクトが含まれている必要があります。

これを自前で実装するということは、「このパスで、この順序で、このスキーマのイベントをチャンク単位でストリーミングしつつ、非同期ジェネレーターのバックプレッシャー処理と接続切断時のクリーンアップまで正しく行う」という意味になります。ここにOpenTelemetry spanの開始/終了タイミング、OAuth consentが必要な状況での特殊レスポンスフォーマットまで加えると、事実上アダプターパッケージを最初から作り直すのと変わりません。

正確な表現はこうです：**エージェントロジックは何でも書けるが、HTTPサーバー層はアダプターパッケージが提供するものを使うのが公式パス。**「Webサーバーを自由に選ぶ」ではなく、「アダプターが提供する事前構成されたWebサーバーの上で、ビジネスロジック実装の自由度が完全である」ということです。

Cloud Services時代、IISを直接設定してWeb Roleのように動作させることはできたかもしれませんが、`RoleEntryPoint`を継承して`.csdef`を書いてこそFabric Controllerがそのインスタンスを管理できた — まったく同じ文脈です。

---

## エンタープライズAIが見落としていること：契約ベースの透明性

Hosted Agentの本当の価値は「実装が簡素化される」ことではありません。

セルフホストコンテナ方式の根本的な問題は **不透明性** です。コンテナ内でエージェントがLLMをどう呼び出し、ツールをどの順序で使い、なぜそのレスポンスを生成したかをプラットフォームは知ることができません。開発者がどれだけ熱心にロギングしても、それは開発者の自発的な努力であり、プラットフォームが保証する構造ではありません。

Hosted Agentでは、アダプターが強制するプロトコル契約のおかげで、エージェントの動作がプラットフォームに構造的に公開されます。

**オブザーバビリティが契約レベルで保証されます。** アダプターがHTTPリクエスト、モデル呼び出し、ツール使用を自動で計装します。開発者がOpenTelemetryを設定する必要はありません。FoundryポータルのTracesタブで、エージェントがどのような判断を経てレスポンスに到達したかを確認できます。

**定量的評価がプラットフォームに統合されます。** アダプターが強制するレスポンスプロトコルのおかげで、プラットフォームがレスポンス構造を理解でき、Intent Resolution、Task Adherence、Tool Call Accuracyのようなビルトイン評価メトリクスを直接適用できます。セルフホストコンテナでは、この評価パイプラインを一から別途構築する必要があります。

**ガバナンスがアイデンティティレベルで適用されます。** パブリッシュ前はプロジェクトのシステム割り当てマネージドIDで動作し、パブリッシュ時に専用エージェントアイデンティティが分離され、Microsoft Entraエージェントレジストリに登録されます。組織レベルで「どのエージェントがどのリソースにアクセス可能か」を中央で制御できます。

**会話状態がプラットフォーム管理です。** コンテナ自体はステートレスなHTTPサーバーとして動作し、「このユーザーと以前どのような会話をしたか」はAgent Service Runtimeが`CreateResponse`リクエスト内にコンテキストとして注入します。開発者が会話状態ストアを自前で実装する必要はありません。

これがPoCからプロダクションに進む際の決定的な違いです。セキュリティチームは「エージェントが何をしたか追跡可能か」を問い、コンプライアンスチームは「エージェントのアクセス権限は管理されているか」を問い、経営陣は「エージェントの品質をどう測定するか」を問います。セルフホストコンテナ方式ではこれらすべての質問に「自前で実装しました」と答えなければなりませんが、Hosted Agentでは「プラットフォームが保証します」と答えることができます。

---

## ランタイム動作モデル

実際の運用環境でHosted Agentの動作を正確に理解することが重要です。

エージェントコードを含むアセンブリは「セッションごとにインスタンス化されるエージェント」ではなく、「リクエストのたびに注入されたコンテキストに基づいてステートレスにレスポンスを生成するサービス」として動作します。

```text
[ユーザーAセッション] ──┐
[ユーザーBセッション] ──┤   Agent Service Runtime
[ユーザーCセッション] ──┘   (会話状態管理 + ルーティング)
                            │
                   ┌────────┼────────┐
                   ▼        ▼        ▼
               [Replica 1] [Replica 2] [Replica 3]
               (同一コンテナイメージ、ステートレス)
               (各リクエストに該当セッションの会話コンテキストが注入)
```

セッションごとに別のコンテナが起動するわけではありません。少数のレプリカが多数のセッションのリクエストを処理し、各リクエストに該当セッションの会話コンテキストがプラットフォームから注入されます。エージェントロジックは1つですが、会話の連続性はプラットフォームが保証する構造です。

`min-replicas 0`に設定するとscale-to-zeroも可能で、最初のリクエスト時にコールドスタートが発生します。持続的なレスポンス遅延が許容されない環境では`min-replicas 1`以上を維持することが推奨されます。

---

## コードで見るHosted Agent：MCPツール統合の例

アーキテクチャの議論をコードレベルで具体化します。Microsoftの公式サンプルの中から、Hosted AgentでMCPサーバーをツールとして使用するC#の例を中心に、先述した概念がコードでどのように実現されるかを解説します。

### 環境設定とエージェント定義

```csharp
var endpoint = Environment.GetEnvironmentVariable("AZURE_FOUNDRY_PROJECT_ENDPOINT")
    ?? throw new InvalidOperationException("AZURE_FOUNDRY_PROJECT_ENDPOINT is not set.");
var model = Environment.GetEnvironmentVariable("AZURE_FOUNDRY_PROJECT_MODEL_ID") ?? "gpt-4.1-mini";

const string AgentName = "MicrosoftLearnAgent";
const string AgentInstructions = "You answer questions by searching the Microsoft Learn content only.";
```

最初に注目すべきは、エージェントコードにHTTPサーバー構成コードが **一切ない** という点です。Kestrel設定、ルートマッピング、ミドルウェアパイプライン — 一般的なASP.NET Coreアプリであれば必ず必要なこれらのコードが見当たりません。これが先述した「アダプターが事前構成されたKestrelを提供する」の実体です。開発者が定義するのはエージェントの名前、指示文、使用するモデルだけです。

### MCPツール宣言

```csharp
var mcpTool = new MCPToolDefinition(
    serverLabel: "microsoft_learn",
    serverUrl: "https://learn.microsoft.com/api/mcp");
mcpTool.AllowedTools.Add("microsoft_docs_search");
```

`MCPToolDefinition`は3つのことを宣言します。`serverLabel`はこのMCPサーバーの一意な識別子、`serverUrl`はリモートMCPサーバーのエンドポイント、`AllowedTools`はそのサーバーが公開するツールの中でこのエージェントが使用できるツールの許可リストです。

ここで重要なのは、MCPサーバーとの実際の通信を **エージェントコードが直接行わない** という点です。セルフホストコンテナ方式であれば、MCPクライアントを初期化し、ツールリストを列挙し、呼び出し結果をパースするコードを自前で書く必要があります。Hosted Agentではツール定義を宣言するだけで、Agent Service RuntimeがMCPサーバーとの通信をプラットフォームレベルで管理します。これが「契約ベースの透明性」の具体例です — プラットフォームがツール呼び出しを仲介するため、どのツールがいつ呼び出されたかを自動的に追跡できます。

### Persistent Agentの作成

```csharp
var persistentAgentsClient = new PersistentAgentsClient(endpoint, new DefaultAzureCredential());

var agentMetadata = await persistentAgentsClient.Administration.CreateAgentAsync(
    model: model,
    name: AgentName,
    instructions: AgentInstructions,
    tools: [mcpTool]);
```

`PersistentAgentsClient`はFoundryサービスにエージェントを **サーバーサイドで登録** します。この呼び出し以降、エージェントはFoundryポータルで確認できる管理対象リソースとなります。`DefaultAzureCredential`は開発環境ではAzure CLI認証を、デプロイ環境ではManaged Identityを自動的に選択します — 先述のアイデンティティ切り替え構造のクライアント側実装です。

### ツール承認ポリシーと実行

```csharp
var runOptions = new ChatClientAgentRunOptions()
{
    ChatOptions = new()
    {
        RawRepresentationFactory = (_) => new ThreadAndRunOptions()
        {
            ToolResources = new MCPToolResource(serverLabel: "microsoft_learn")
            {
                RequireApproval = new MCPApproval("never"),
            }.ToToolResources()
        }
    }
};
```

`RequireApproval`はMCPツール呼び出しに対する承認ポリシーです。`"never"`は自動実行、`"always"`は毎回ユーザーの承認を要求します。これはセルフホストコンテナでは自前で実装すべきHuman-in-the-Loopパターンをプラットフォームが標準化したものです。エンタープライズ環境で「このエージェントが外部ツールを呼び出す際に必ず人間の承認を経なければならない」というポリシーをコード1行で適用できます。

```csharp
AIAgent agent = await persistentAgentsClient.GetAIAgentAsync(agentMetadata.Value.Id);
AgentSession session = await agent.CreateSessionAsync();

var response = await agent.RunAsync(
    "Please summarize the Azure AI Agent documentation related to MCP Tool calling?",
    session,
    runOptions);

Console.WriteLine(response);
```

`agent.RunAsync()`が呼ばれると、リクエストはFoundryのAgent Service Runtimeに転送され、RuntimeがMCPサーバーへのツール呼び出しを仲介し、LLMにコンテキストを渡し、最終レスポンスをストリーミングイベントとして返します。開発者のコードではこのプロセス全体が単一の`await`呼び出しに抽象化されています。

```csharp
await persistentAgentsClient.Administration.DeleteAgentAsync(agent.Id);
```

最後のクリーンアップコードは、エージェントがFoundryの管理対象リソースであることを示しています。セルフホストコンテナであれば「コンテナを停止する」ですが、Hosted Agentでは「エージェントを削除する」です。管理単位がインフラではなくエージェント自体です。

### このコードが語ること

コード全体で、HTTP、ストリーミング、プロトコル、認証、状態管理に関するコードは **一行もありません。** 開発者が書いたのは「どのモデルを使うか、どのツールを使うか、どの指示を与えるか、承認ポリシーは何か」だけです。残りはすべてプラットフォームが処理します。

これは`RoleEntryPoint`で`OnStart()`と`Run()`だけを実装すれば残りをFabric Controllerが処理したのと同じパターンです。15年の時間差を置いて、同じ設計哲学がAIエージェントドメインで繰り返されています。

---

## 現実確認：まだ青写真である

率直に言うべきことがあります。

2026年3月現在、Hosted Agentはパブリックプレビューです。そしてHosted Agent以前に、no-codeエージェントでMCPサーバーを接続して2ターン以上の会話を試みるとエージェントがクラッシュするレベルです。会話状態にツール呼び出し履歴が蓄積しシリアライズ/デシリアライズ過程で問題が発生するか、MCPセッションのライフサイクル管理が会話ターンの境界で適切に処理されていないように見えます。

MCPサーバー統合の制約事項すらまだ規定されていない状態です。どのトランスポートをサポートすべきか（SSEかStreamable HTTPか）、どのMCPプロトコルバージョンを要求するか、ツールスキーマに制約があるかといった基本的な仕様がパブリックドキュメントにありません。MCPプロトコル自体も進化中で、Foundryがどのバージョンとトランスポートを公式サポートするか確定していません。

プレビュー段階の明示的な制約もあります。AzureサブスクリプションあたりHosted Agentを含むFoundryリソース100個、リソースあたり最大200のHosted Agent、レプリカは最小2、最大5まで。プライベートネットワーキングもまだサポートされていません。課金は2026年4月1日以降に開始予定です。

これをすべて総合すると、現時点でHosted Agentまで導入するのは時期尚早です。PoCを進めるなら、セルフホストコンテナでLLM APIを直接呼び出す方式のほうが予測可能です。プラットフォーム透明性を犠牲にする代わりに、クラッシュの原因を直接制御できるからです。

---

## それでも今知っておくべき理由

Hosted Agentのアーキテクチャを今理解しておくことは、GA後のマイグレーションパスを確保するためです。

セルフホストコンテナでPoCを進める場合でも、エージェントのビジネスロジックを`CreateResponse` → `Response | Stream[ResponseStreamEvent]`の契約に近い形で設計しておけば、後からアダプターで包むのは比較的単純な作業になります。.NETでは`IAgentInvocation.InvokeAsync(CreateResponseRequest, AgentInvocationContext, CancellationToken)`のシグネチャを念頭に置いてロジックを構成すれば良いでしょう。

そしてこのアーキテクチャが安定化した時に最大の恩恵を受けるのは、複雑なエージェントロジックをコードで精密に制御しつつエンタープライズガバナンス要件を満たす必要がある組織です。まさに今「宣言的エージェントでは不足で、セルフホストコンテナでは手に負えない」間で挟まれているチームです。

MicrosoftはCloud ServicesからApp Serviceへ、App ServiceからAzure Functionsへ、FunctionsからContainer Appsへと続くマネージドコンピュートの抽象化レベルを着実に上げてきました。Hosted Agentはその系譜の最新地点で、AIエージェントという特定のワークロードに合わせたドメイン特化PaaSを試みています。`RoleEntryPoint`から`FoundryCBAgent`まで、15年にわたる「プラットフォームがホストプロセスを提供し、開発者はビジネスロジックに集中する」という約束がAI時代にも有効かを検証する実験が、今進行中です。

---

*この記事は[/dev/write](https://devwrite.ai)ニュースレターで発行されました。*

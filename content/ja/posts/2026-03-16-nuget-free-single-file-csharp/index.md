---
title: ".NETの新ジャンル：NuGet-Free Single File C#コーディングの時代"
date: 2026-03-16T00:00:00+09:00
draft: false
slug: "nuget-free-single-file-csharp"
tags:
  - .NET
  - C#
  - File-Based App
  - Runtime Async
  - パフォーマンス最適化
categories:
  - .NET開発
translationKey: "nuget-free-single-file-csharp"
description: ".NET 10のfile-based appとRuntime Asyncが組み合わさると、NuGetなしでBCLだけで高速かつ型安全なシングルファイルC#コーディングが可能になります。"
cover:
  image: "images/posts/nuget-free-single-file-csharp.webp"
  alt: "単一のC#ファイルで実行されるコードのコンセプトイメージ"
tldr: "dotnet run file.csのBuildLevel.Csc最適化とRuntime Asyncの組み合わせにより、NuGetパッケージなしでBCLのみを使用するシングルファイルC#プログラムが繰り返し実行200ms〜630msの性能を達成し、Pythonの利便性、Goのデプロイの簡潔さ、C#の型安全性を兼ね備えた新しいコーディングジャンルが開かれます。"
---

> C#がスクリプト言語のように軽くなるのではなく、スクリプト言語が羨むほど速くなるということです。

## はじめに

.NET 10で導入された`dotnet run file.cs`——いわゆる** file-based app**——は、`.csproj`ファイルなしで単一の`.cs`ファイルだけでC#コードを実行できる機能です。しかし、現在この機能の実行速度は初回実行基準でWindowsで約1.5秒、WSL2で約0.8秒レベルです。Pythonの`python script.py`が50ms前後であることと比較すると、まだ「スクリプティング」と呼ぶには物足りない水準です。

しかし、現在.NETエコシステムで同時に進行中の2つの大きな変化が、この状況を根本的に変える可能性があります：

1. **`dotnet run file.cs`のビルド最適化** — MSBuildをバイパスしてRoslynを直接呼び出す戦略
2. **Runtime Async (async2)** — async/awaitをランタイムレベルで処理し、ステートマシンのオーバーヘッドを除去

この2つが組み合わさると、** NuGetパッケージなしでBCLだけで書くシングルファイルC#プログラム** が独立したコーディングジャンルとして確立される可能性があります。この記事では、その技術的基盤と将来像を描きます。

---

## File-Based Appの現状：MSBuildというボトルネック

### 本質：`.csproj` + `.cs` = 1つの`.cs`

File-based appはC#スクリプト（`.csx`）とは根本的に異なります。`.csx`は別のスクリプトホストがランタイムで解釈しますが、file-based appは** コンパイル時に仮想`.csproj`に変換** されて正規のビルドパイプラインを通ります。出力は通常のプロジェクトと同一のmanaged DLLです。

```cs
// これらのディレクティブが.csprojの内容になる
#:package System.CommandLine@2.0.0

// ここからが実際のコード
Console.WriteLine("Hello, file-based app!");
```

### 問題：MSBuildの重さ

`dotnet run hello.cs`を実行すると内部で起こること：

| ステップ | 所要時間（概算） | 説明 |
| -------- | ---------------- | ---- |
| CLIロード | ~200ms | .NETランタイムJIT、CLIコマンドディスパッチ |
| MSBuildエンジンロード | ~200ms | ビルドエンジン初期化 |
| SDK targets評価 | ~300ms | 数百の`.props`/`.targets`ファイルの順次評価 |
| NuGet restore | ~100ms+ | パッケージ依存性解決（キャッシュ済みの場合） |
| Roslynコンパイル | ~200ms | 実際のC# → IL変換 |
| 実行 | ~50ms | 結果のDLL実行 |

**合計約1.5秒** のうち実際の「コンパイル＋実行」は約250msに過ぎません。残りはすべてMSBuild関連のオーバーヘッドです。

---

## MSBuildをバイパスする戦略：`BuildLevel.Csc`

dotnet/sdkチームはこのボトルネックを認識し、** MSBuildを完全にスキップできるケースを識別してRoslynコンパイラを直接呼び出す** 最適化パスを実装しました。

### 3段階のビルドレベル

```text
dotnet run hello.cs
       │
       ▼
  入力変更検出
       │
  ┌────┼────────────┐
  ▼    ▼            ▼
None  Csc          All
  │    │            │
  ▼    ▼            ▼
スキップ cscのみ呼出  MSBuildフルビルド
~200ms ~400-630ms  ~1.5s
```

- **`BuildLevel.None`**：何も変わっていないので前回のビルド結果をそのまま実行
- **`BuildLevel.Csc`**：`.cs`コードだけが変わったのでRoslynコンパイラサーバーに直接リクエスト — **MSBuild完全バイパス**
- **`BuildLevel.All`**：パッケージやSDK設定が変わったのでMSBuildフルビルドを実行

### `BuildLevel.Csc`の条件

この高速パスを通るには：

- ✅ `#:package`ディレクティブがないか変更なし
- ✅ `#:sdk`ディレクティブがないか変更なし
- ✅ `Directory.Build.props`などimplicit build fileなし
- ✅ `-c Release`のようなグローバルプロパティカスタマイズなし
- ✅ 前回ビルドのキャッシュされたコンパイラ引数（`.rsp`）が存在

これらすべての条件を満たすと、SDKは仮想プロジェクトファイルを作成せず、MSBuildをロードせず、キャッシュされた`.rsp`ファイルを持って** Roslynコンパイラサーバーに直接named pipeでリクエスト** を送ります。

```cs
// CSharpCompilerCommand.csで実際に起こること
var buildRequest = BuildServerConnection.CreateBuildRequest(
    requestId: EntryPointFileFullPath,
    language: RequestLanguage.CSharpCompile,
    arguments: ["/noconfig", "/nologo", $"@{rspPath}"],
    workingDirectory: BaseDirectory,
    tempDirectory: Path.GetTempPath(),
    ...);

var pipeName = BuildServerConnection.GetPipeName(clientDirectory: ClientDirectory);
var responseTask = BuildServerConnection.RunServerBuildRequestAsync(buildRequest, pipeName, ...);
```

### これはミニビルドシステムである

`CSharpCompilerCommand`はすでにMSBuildが担っていた作業の一部をC#でハードコーディングして再実装しています：

- AssemblyAttributes.cs生成
- GlobalUsings.g.cs生成
- AssemblyInfo.cs生成
- EditorConfig生成
- AppHostバイナリパッチ
- RuntimeConfig.json生成
- コンパイラ応答ファイル（.rsp）生成

これは「MSBuildが一度行った結果をキャッシュして再利用する」という戦略であり、MSBuildを置き換えるものではありません。初回実行は必ずMSBuildを通り、構造的な変更があれば再びMSBuildに戻ります。

### 設計上の核心的な緊張

SDKチームはこのバイパス範囲を意図的に狭く維持しています：

```cs
// Releaseビルドを付けただけでMSBuildに戻る
// Note that Release builds won't go through this optimized code path because
// `-c Release` translates to global property `Configuration=Release`
// and customizing global properties triggers a full MSBuild run.
```

理由は、バイパス範囲を広げるほど、事実上** file-based appのためだけの別個のビルドシステム** を作ることになり、MSBuildとの動作の乖離が大きくなるためです。File-based appの核心原則——「プロジェクトに移行（grow-up）した際に同一に動作しなければならない」——が崩れる可能性があります。

---

## Runtime Async：async/awaitの根本的な再設計

### 現在のasync/await：コンパイラが生成するステートマシン

現在のC#の`async/await`は** コンパイラ（Roslyn）** が処理しています。`async`メソッドを書くと、コンパイラがこれをステートマシン構造体に変換し、`IAsyncStateMachine.MoveNext()`を生成します。

```cs
// 開発者が書くコード
async Task<int> FetchDataAsync()
{
    var data = await httpClient.GetStringAsync(url);
    return data.Length;
}

// コンパイラが実際に生成するコード（簡略化）
struct <FetchDataAsync>d__0 : IAsyncStateMachine
{
    public int <>1__state;
    public AsyncTaskMethodBuilder<int> <>t__builder;
    public TaskAwaiter<string> <>u__1;

    public void MoveNext()
    {
        switch (<>1__state)
        {
            case 0: goto Label_Await;
            // ...
        }
        // 実際のロジック...
    }
}
```

この方式のコスト：

- **ステートマシン構造体の割り当て**（ホットパスでも）
- **`MoveNext()`呼び出しオーバーヘッド**
- **ExecutionContextのキャプチャ/復元**
- **ILコードサイズの増加**（ステートマシンのボイラープレート）

### Runtime Async：ランタイムが直接処理

.NET 10で実験的に導入され、.NET 11で本格的に有効化される** Runtime Async** は、この構造全体をひっくり返します。コンパイラがステートマシンを作る代わりに、** JITコンパイラとVMが直接asyncメソッドの中断/再開を処理** します。

ECMA-335仕様に新しいメソッド属性が追加されます：

```text
MethodImplOptions.Async = 0x2000
```

そして`await`はもはやコンパイラの魔法ではなく、ランタイムが認識する** suspension point** になります：

```cs
// ランタイムが認識するawaitパターン
namespace System.Runtime.CompilerServices
{
    public static class AsyncHelpers
    {
        [MethodImpl(MethodImplOptions.Async)]
        public static T Await<T>(Task<T> task);

        [MethodImpl(MethodImplOptions.Async)]
        public static void Await(ValueTask task);
        // ...
    }
}
```

### コアメカニズム：Method Variant Pairs

Runtime Asyncの実装で最も重要なコンセプトは** variant pairs** です。`Task`を返すすべてのメソッドに対して、ランタイムが自動的に2つのエントリーポイントを生成します：

- **Task-returning variant**：従来と同じ`Task<T>`返却シグネチャ
- **Async variant**：`T`を直接返却しつつ、中断が必要な場合はContinuationオブジェクトを通じて処理する新しい呼び出し規約

async → async呼び出しチェーンで中断が発生しない場合（ホットパス）、** Taskオブジェクトを一切割り当てずに値を直接返却** します。これが劇的なパフォーマンス改善の核心です。

### ベンチマークからの示唆

```text
現在（async1）：asyncメソッド呼び出し → ステートマシン割り当て → Task割り当て → await
Runtime Async：asyncメソッド呼び出し → （同期完了時）値を直接返却、Task割り当てなし
```

.NETチームの実験結果によると、Runtime Asyncは** 既存のcompiler-asyncと少なくとも同等かそれ以上のパフォーマンス** を示しました。特に：

- **同期完了（suspensionなし）パス**：ステートマシンとTaskの割り当てが完全に除去され、通常のメソッド呼び出しとほぼ同等のコスト
- **ILコードサイズ**：ステートマシンのボイラープレートが消滅し大幅に縮小
- **完全な互換性**：既存のasync1とdrop-in replacement可能

---

## 2つの変化の合流：NuGet-Free Single File Appの台頭

### パフォーマンススペクトラム

両方の最適化が適用された後の予想パフォーマンス：

| シナリオ | 現在 | BuildLevel.Csc | + Runtime Async |
| -------- | ---- | --------------- | --------------- |
| 初回実行（`dotnet run hello.cs`） | ~1.5s | ~1.5s（初回は同じ） | ~1.5s |
| 繰り返し実行（コード変更あり） | ~1.5s | **~400-630ms** | **~400-630ms** |
| 繰り返し実行（変更なし） | ~1.5s | **~200ms** | **~200ms** |
| async呼び出しチェーン性能 | 基準 | 基準 | **大幅に改善** |

`BuildLevel.Csc`はビルド時間を、Runtime Asyncは実行時間中のasync関連オーバーヘッドを削減します。2つの改善は** 直交（orthogonal）** しており、合算効果を生みます。

### NuGet-Freeの条件こそ最適パスの条件

`BuildLevel.Csc`の恩恵を最大限に受けるには：

- `#:package`なし → NuGet restore不要
- `#:sdk`変更なし → SDK targets再評価不要
- implicit build fileなし → MSBuildプロパティ再評価不要

この条件を満たすコードは正確に** NuGetパッケージに依存しないコード** です。そして.NET BCLが提供するものだけでも驚くほど多くのことが可能です：

```cs
// ✅ すべてBCLだけで可能なもの

using System.Net.Http;                      // HTTPクライアント
using System.Text.Json;                     // JSONシリアライゼーション
using System.Text.RegularExpressions;       // 正規表現
using System.IO.Compression;                // ZIP, GZip
using System.Security.Cryptography;         // ハッシュ、暗号化
using System.Threading.Channels;            // プロデューサー・コンシューマーパターン
using System.Collections.Concurrent;        // 並行コレクション
using System.Xml.Linq;                      // XML処理
using System.Diagnostics;                   // プロセス管理
using System.Net;                           // DNS, IP, ソケット
```

### 実用的な使用シナリオ

#### **CLIユーティリティ**

```cs
#!/usr/bin/env dotnet run
// file: cleanup.cs

var targetDir = args.Length > 0 ? args[0] : ".";
var cutoff = DateTime.Now.AddDays(-30);

foreach (var file in Directory.EnumerateFiles(targetDir, "*.log", SearchOption.AllDirectories))
{
    if (File.GetLastWriteTime(file) < cutoff)
    {
        File.Delete(file);
        Console.WriteLine($"Deleted: {file}");
    }
}
```

#### **簡易HTTPクライアント / APIテスト**

```cs
// file: api-check.cs

using var client = new HttpClient();
var endpoints = new[] {
    "https://api.example.com/health",
    "https://api.example.com/status",
};

await Parallel.ForEachAsync(endpoints, async (url, ct) =>
{
    try
    {
        var sw = Stopwatch.StartNew();
        var response = await client.GetAsync(url, ct);
        Console.WriteLine($"{url} → {response.StatusCode} ({sw.ElapsedMilliseconds}ms)");
    }
    catch (Exception ex)
    {
        Console.WriteLine($"{url} → FAILED: {ex.Message}");
    }
});
```

Runtime Asyncが適用されると、この`Parallel.ForEachAsync` + `await`チェーンで同期完了する呼び出しはステートマシン割り当てなしに処理されます。

#### **JSONデータ変換パイプライン**

```cs
// file: transform.cs

using System.Text.Json;

var input = args.Length > 0 ? File.ReadAllText(args[0]) : Console.In.ReadToEnd();
var doc = JsonDocument.Parse(input);

var result = doc.RootElement.EnumerateArray()
    .Where(e => e.GetProperty("status").GetString() == "active")
    .Select(e => new {
        Id = e.GetProperty("id").GetInt32(),
        Name = e.GetProperty("name").GetString(),
    });

Console.WriteLine(JsonSerializer.Serialize(result, new JsonSerializerOptions { WriteIndented = true }));
```

#### **システム管理自動化**

```cs
// file: sysinfo.cs

using System.Runtime.InteropServices;

Console.WriteLine($"OS: {RuntimeInformation.OSDescription}");
Console.WriteLine($"Architecture: {RuntimeInformation.OSArchitecture}");
Console.WriteLine($"Framework: {RuntimeInformation.FrameworkDescription}");
Console.WriteLine($"Processors: {Environment.ProcessorCount}");
Console.WriteLine($"Memory: {GC.GetGCMemoryInfo().TotalAvailableMemoryBytes / 1024 / 1024:N0} MB");
Console.WriteLine($"Host: {Environment.MachineName}");
Console.WriteLine($"User: {Environment.UserName}");
```

### NuGetを超える瞬間

NuGetなしでBCLだけではカバーできない領域があります：

| 必要な機能 | 状態 |
| ---------- | ---- |
| データベース（Npgsql, Dapper） | ❌ `#:package`必要 → `BuildLevel.All` |
| クラウドSDK（Azure, AWS） | ❌ `#:package`必要 |
| Webフレームワーク（ASP.NET Core） | ❌ `#:sdk Microsoft.NET.Sdk.Web`必要 |
| 高度なCLIパース | ❌ `#:package System.CommandLine`必要 |
| テストフレームワーク | ❌ `#:package`必要 |

この境界を超えると`BuildLevel.Csc`の恩恵が失われ、約1.5秒のMSBuildフルビルドに戻ります。これが自然と**「NuGet-freeシングルファイル」と「プロジェクトベースアプリ」の間の境界線** を引きます。

---

## Runtime AsyncがFile-Based Appにもたらす未来

### コードサイズの削減

現在、`async`メソッドはコンパイラがステートマシンに変換する際にILサイズが大幅に増加します。Runtime Asyncはこの変換をJITが担当するため、** ILレベルのコードサイズが縮小** します。File-based appにおいてこれは：

- より高速なコンパイル（処理すべきILが減少）
- より小さな出力バイナリ
- `dotnet publish file.cs`で生成するNative AOTバイナリサイズの縮小

### ホットパス最適化

Runtime Asyncのvariant pairメカニズムは、asyncメソッドチェーンにおける** 同期完了パスを劇的に最適化** します。NuGet-freeシングルファイルアプリでよくあるパターン：

```cs
// 大半のHTTPリクエストは「既に完了した」結果を返す
async Task<string> GetCachedDataAsync(string key)
{
    if (cache.TryGetValue(key, out var value))
        return value;  // ← 同期パス：Task割り当てなし！

    var data = await FetchFromSourceAsync(key);
    cache[key] = data;
    return data;
}
```

現在はこのメソッドが呼び出されるたびにステートマシン構造体が生成されます。Runtime Asyncでは、キャッシュヒット時に** 通常のメソッド呼び出しと同等のコスト** で処理されます。

### `dotnet publish file.cs` + Native AOT

File-based appを`dotnet publish`するとNative AOTでコンパイルして** 依存性のない単一ネイティブバイナリ** を生成できます。Runtime Asyncとの組み合わせにより：

```bash
$ dotnet publish hello.cs
# → hello (Linux) / hello.exe (Windows)
# 単一ネイティブバイナリ、Goのgo buildと同じ体験
```

これはGoやRustが提供する「コンパイル → 単一バイナリ」の体験と事実上同じです。しかし、C#の豊富なBCLとasync/awaitの人間工学的優位性が加わります。

---

## 比較：他の言語エコシステムとの位置づけ

| | Python | Go | C#（NuGet-free file-based） |
| --- | ------ | --- | --------------------------- |
| シングルファイル実行 | ✅ `python script.py` | ❌（パッケージ必要） | ✅ `dotnet run script.cs` |
| 繰り返し実行速度 | ~50ms | N/A（コンパイル必要） | ~200-600ms |
| 型安全性 | ❌ 動的型付け | ✅ 静的型付け | ✅ 静的型付け |
| 非同期サポート | `asyncio`（限定的） | goroutine | `async/await`（runtime-native） |
| 単一バイナリデプロイ | ❌（PyInstaller等必要） | ✅ `go build` | ✅ `dotnet publish` + AOT |
| 標準ライブラリの充実度 | ★★★★☆ | ★★★★★ | ★★★★★ |
| エコシステムパッケージアクセス | pip | go mod | #:package（NuGet） |

Pythonより初回実行は遅いものの、型安全性とパフォーマンス（特にasyncシナリオ）で圧倒的な優位性があります。Goと同等の単一バイナリデプロイが可能でありながら、より豊富なasync/awaitサポートを提供します。

---

## 残された課題と限界

### MSBuildという天井

すべての最適化にもかかわらず、file-based appは根本的にMSBuild（SDK）環境の上に構築されています。MSBuildは.NETエコシステムのアイデンティティそのものです：

- NuGetパッケージシステムがMSBuildアイテムとして設計されている
- SDK（`Microsoft.NET.Sdk`）がMSBuild targetsのバンドルである
- IDE統合（VS, Rider, VS Code）がMSBuildプロジェクト評価に依存している

バイパス範囲を拡大すればするほど、事実上** MSBuildの劣化コピー** を作ることになります。SDKチームはこの罠を認識し、「確実に安全な範囲内でのみバイパスし、少しでも不確実ならMSBuildに戻る」という保守的な戦略を取っています。

### Rustで書き直しても変わらない問題

Python/Node.jsエコシステムでRustベースのツール（uv, Bun等）が劇的なパフォーマンス改善を見せたのは事実ですが、.NETのビルドパフォーマンス問題は性質が異なります。pipやnpmが遅かったのは「遅いランタイム上の単純なI/O操作」だったからであり、MSBuildが遅いのは「やるべき作業自体が多い」からです。ビルドエンジンをRustで書き直しても、数百のtargetsファイルを順次評価するその作業量は変わりません。

だからこそSDKチームの戦略——遅いパスを速くする代わりに、** 遅いパスを一切通らないようにする**——がこの問題に対する最も現実的な解法です。

### Runtime Asyncの成熟度

Runtime Asyncはまだ活発に開発中であり、ReadyToRunイメージへのasync2メソッドのコンパイルはまだサポートされていません。SynchronizationContextの処理やReflectionとの互換性など、解決すべきエッジケースが残っています。

---

## 結論：新しいジャンルの誕生

.NETエコシステムに**「プロジェクトベースの正式なアプリ」と「ファイル1つの軽量スクリプト」の間の明確な境界線** がパフォーマンス特性によって自然に引かれています。その境界線はまさに** NuGet依存の有無** です。

NuGetなしでBCLだけで書くコードは：

- ✅ `BuildLevel.Csc`パスを通って高速にビルド
- ✅ Runtime Asyncでasyncコードがより高速に実行
- ✅ Native AOTで単一バイナリデプロイが可能
- ✅ プロジェクトファイルなしで`.cs`1つで完結

これはPythonスクリプティングの利便性、Goのデプロイの簡潔さ、そしてC#ならではの型安全なasync/awaitを組み合わせた** 新しいコーディングジャンル** です。`.csproj`が消えたのではなく、`.csproj`が不要な領域が明確に定義され、その領域で最適な開発体験が提供されるということです。

```cs
#!/usr/bin/env dotnet run

// これがNuGet-free single file C#の未来です。
// プロジェクトファイルなし。パッケージ依存なし。
// BCLだけで十分な、高速で型安全なスクリプティング。

var response = await new HttpClient().GetStringAsync("https://api.github.com/zen");
Console.WriteLine(response);
```

---

*この記事で取り上げた技術の現在の状態：*

- *`dotnet run file.cs`：.NET 10で導入、パフォーマンス最適化進行中（[dotnet/sdk#48011](https://github.com/dotnet/sdk/issues/48011)）*
- *Runtime Async：.NET 10で実験的に導入、.NET 11で有効化予定（[dotnet/runtime#94620](https://github.com/dotnet/runtime/issues/94620)）*
- *`BuildLevel.Csc`パス：dotnet/sdkの`CSharpCompilerCommand`として実装済み*

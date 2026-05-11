---
title: "C#からHugging Faceモデルを呼ぶ：DotNetPy 0.6.0でWhisper・sentence-transformers・Stable Diffusionを動かす"
date: 2026-05-11T00:00:00+09:00
draft: false
slug: "dotnetpy-huggingface-from-csharp"
tags:
  - .NET
  - C#
  - Python
  - HuggingFace
  - AI
  - 機械学習
  - Native AOT
categories:
  - .NET開発
translationKey: "dotnetpy-huggingface-from-csharp"
description: "DotNetPy 0.6.0でCPythonのC APIを.NETから直接呼び、Whisper・sentence-transformers・Stable Diffusionを動かした記録と、PEP 703 free-threadedビルドで設計を検証した過程をまとめます。"
cover:
  image: "images/posts/dotnetpy-huggingface-from-csharp.webp"
  alt: "C#とPythonが出会う機械学習インターロップの概念図"
tldr: "DotNetPy 0.6.0はCPythonのC APIを直接呼び出して.NETからPythonを実行するライブラリで、Whisper・sentence-transformers・Stable Diffusion TurboのサンプルがNative AOTとPEP 703 free-threaded CPythonビルドの両方で動作します。並列MLワーカーは`Python.CreateIsolated()`の一行で隔離された実行器を作るだけで構築できます。"
---

<!--
クロスポスティング情報:
- 英語版の正典(canonical): https://dev.to/rkttu/speech-search-and-stable-diffusion-calling-huggingface-from-c-2bkk
- このブログでは /dev/write 読者向けに再構成しています。
-->

> 週末に小さなC#ライブラリ [DotNetPy](https://github.com/rkttu/dotnetpy) の0.6.0をリリースしました。CPythonのC APIを直接呼び出して、.NETアプリの中でPythonを動かすインターロップライブラリです。本記事は0.6.0に含まれる3つの機械学習サンプル（`sentence-transformers`による意味検索、Whisperによる音声認識、Stable Diffusion Turboによる画像生成）をどうまとめたか、そしてその過程でPEP 703 free-threaded CPythonをどのように検証したかを記録したものです。

---

## 出発点：手元にあるのはC#だけ、モデルはHugging Faceにある

数か月ごとに同じパターンが繰り返されます。字幕用にWhisperが必要、検索用にsentence-transformerが必要、ときにはStable Diffusionのようなモデルを使いたい。しかし手元にあるのはC#一つだけ。こんなとき、よく取られる回避策にはそれぞれ決定的な欠点があります。

- **ONNXに変換する。** 画像系やエンコーダ系のモデルにはよく合いますが、新しいアーキテクチャやdiffusionパイプラインでは、変換そのものが別プロジェクトになります。
- **Pythonマイクロサービスとして立ち上げる。** プロセスが2つ、デプロイのシナリオが2つ、そしてホットパスにネットワークホップが1つ追加されます。
- **外部APIを呼び出す。** コストがかかり、インターネット接続が必要で、データが箱の外に出ます。
- **[pythonnet](https://github.com/pythonnet/pythonnet) や [CSnakes](https://github.com/tonybaloney/csnakes) を使う。** 堅実な選択肢ですが、pythonnetはまだNative AOTをサポートしておらず、CSnakesはSource Generatorベースのワークフローを強制します。さらに、両ライブラリともfree-threaded CPythonビルドに対する公開された検証結果をまだ出していません。

私はもう少し薄い選択肢が欲しかったのです。**C#コードの中にPythonスニペットを文字列としてインラインで書き、配列をそのまま渡し、JSON形式で結果を受け取り、全体がAOTコンパイルされて単一バイナリになる** 形です。それがDotNetPyの目標であり、以下の3つのサンプルはすべてGPUのない普通のWindows 11ノートPCで最初から最後まで動作します。

---

## サンプル1 — `sentence-transformers` による意味検索

最初のサンプルは小さなコーパスを埋め込み、クエリをエンコードして、最も類似する上位K件の文を返します。戻り値は`DotNetPyValue`で、内部的にはJSONドキュメントをラップしたもので、`GetString()`・`GetInt32()`・`GetDouble()`、そしてパスベースのプロパティアクセスを通じて.NETの世界に戻ってきます。

```csharp
using DotNetPy;
using DotNetPy.Uv;

using var project = PythonProject.CreateBuilder()
    .WithProjectName("dotnetpy-ml-embeddings")
    .WithPythonVersion("==3.12.*")
    .AddDependencies(
        "sentence-transformers==2.7.0",
        "transformers==4.40.2",
        "torch>=2.2,<2.5")
    .Build();

await project.InitializeAsync();
var executor = project.GetExecutor();

executor.Execute(@"
import numpy as np
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
");

var corpus = new[]
{
    "Python is a popular programming language for data science.",
    "C# and .NET are great for building enterprise applications.",
    "Rust offers memory safety without garbage collection.",
    "Pizza is delicious with various toppings.",
    // …
};
var query = "Tell me about programming languages";

using var hits = executor.ExecuteAndCapture(@"
corpus_emb = model.encode(corpus, normalize_embeddings=True)
query_emb = model.encode([query], normalize_embeddings=True)[0]
sims = corpus_emb @ query_emb
top_idx = np.argsort(-sims)[:3]
result = [
    {'rank': int(rank + 1), 'score': float(sims[i]), 'text': corpus[int(i)]}
    for rank, i in enumerate(top_idx)
]
", new Dictionary<string, object?> { { "corpus", corpus }, { "query", query } });

foreach (var hit in hits!.RootElement.EnumerateArray())
{
    Console.WriteLine($"  {hit.GetProperty("rank").GetInt32()}. " +
                      $"[{hit.GetProperty("score").GetDouble():F3}] " +
                      $"{hit.GetProperty("text").GetString()}");
}
```

実際の出力はこうなります。

```text
  1. [0.578] Python is a popular programming language for data science.
  2. [0.370] C# and .NET are great for building enterprise applications.
  3. [0.203] Rust offers memory safety without garbage collection.
```

ここで興味深いのは **2つの世界の境界** です。`corpus` は.NETの`string[]`、`query`は.NETの`string`ですが、Python側では自然にネイティブのlistとstrとして到着します。スコア付きの結果はJSONドキュメント一塊で返ってきて、.NET側では普段通り`JsonElement`APIで読めば終わりです。

---

## サンプル2 — Whisperによる音声認識

形はほぼ同じで、モダリティだけが変わります。`.wav`や`.flac`のパスを渡せば、テキストとチャンク単位のタイムスタンプが返ってきます。1つの重要なポイントは、**音声バイト列は.NET ↔ Pythonの境界を絶対に越えない** ということです。Pythonがファイルを直接開き、境界を越えるのは構造化されたトランスクリプトだけです。

```csharp
var executor = project.GetExecutor();
executor.Execute(@"
from transformers import pipeline
import torch
asr = pipeline(
    'automatic-speech-recognition',
    model='openai/whisper-base.en',
    chunk_length_s=30,
    return_timestamps=True,
    torch_dtype=torch.float32,
)
");

using var transcript = executor.ExecuteAndCapture(@"
out = asr(audio_path)
chunks = [
    {'start': float(c['timestamp'][0]), 'end': float(c['timestamp'][1]),
     'text': c['text'].strip()}
    for c in out.get('chunks', [])
    if c['timestamp'][0] is not None and c['timestamp'][1] is not None
]
result = {'text': out['text'].strip(), 'chunks': chunks}
", new Dictionary<string, object?> { { "audio_path", audioPath } });

Console.WriteLine($"\"{transcript!.GetString("text")}\"");
foreach (var c in transcript.RootElement.GetProperty("chunks").EnumerateArray())
    Console.WriteLine($"  [{c.GetProperty("start").GetDouble():F2}s → " +
                      $"{c.GetProperty("end").GetDouble():F2}s] " +
                      $"{c.GetProperty("text").GetString()}");
```

サンプルに同梱されているパブリックドメインのJFKクリップを実行すると、こんな結果が出ます。

```text
"And so my fellow Americans, ask not what your country can do for you,
 ask what you can do for your country."

  [0.00s → 11.00s] And so my fellow Americans, ask not what your country can
                   do for you, ask what you can do for your country.
```

`whisper-base.en`は290 MBのモデルで、11秒のクリップを私のノートPCのCPUでtranscribeするのに約7秒かかります。2回目以降の実行ではモデルと仮想環境がキャッシュされ、初回のダウンロードコストは消えます。

---

## サンプル3 — Stable Diffusion Turboによるテキスト→画像

`stabilityai/sd-turbo`は1ステップのdiffusionモデルです。CPUで512×512の画像を1枚生成するのに約30秒、最近のGPUなら2秒前後です。ここでも.NET側は画像バイトを見ません。PythonがPNGをディスクに保存し、メタデータだけが返ってきます。

```csharp
executor.Execute(@"
import torch
from diffusers import AutoPipelineForText2Image
pipe = AutoPipelineForText2Image.from_pretrained(
    'stabilityai/sd-turbo',
    torch_dtype=torch.float32,
    safety_checker=None, requires_safety_checker=False,
)
pipe.set_progress_bar_config(disable=True)
");

using var meta = executor.ExecuteAndCapture(@"
import time, os
t0 = time.time()
img = pipe(prompt=prompt, num_inference_steps=1, guidance_scale=0.0).images[0]
elapsed = time.time() - t0
out_path = os.path.join(out_dir, 'generated.png')
img.save(out_path)
result = {
    'path': out_path,
    'width': img.size[0],
    'height': img.size[1],
    'size_bytes': os.path.getsize(out_path),
    'elapsed_seconds': elapsed,
}
", new Dictionary<string, object?>
{
    { "prompt", "a serene mountain lake at sunset, oil painting style" },
    { "out_dir", outDir },
});

Console.WriteLine($"  Saved:   {meta!.GetString("path")}");
Console.WriteLine($"  Size:    {meta.GetInt32("width")}×{meta.GetInt32("height")} px, " +
                  $"{meta.GetInt32("size_bytes"):N0} bytes");
Console.WriteLine($"  Inference: {meta.GetDouble("elapsed_seconds"):F2}s");
```

出力は次の通りです。

```text
  Saved:   .../samples/ml-image-gen/output/generated.png
  Size:    512×512 px, 434,242 bytes
  Inference: 31.19s
```

3つのサンプルを通して強調したいパターンが1つあります。**境界を越えるのは構造化データだけ** ということです。PNGバイト（〜400KB）、埋め込み行列、float32のテンソルはすべてPython側に留まります。.NET側では小さなプロンプト1行が入って、小さなJSONオブジェクト1つが返ってくるのが見えるだけです。この分離こそがNative AOT互換性を可能にする最も重要な設計判断です。

---

## インストールと最初の実行

ライブラリ自体は普通のNuGetパッケージです。

```bash
dotnet add package DotNetPy --version 0.6.0
```

上記のサンプルをそのまま試したい場合、リポジトリの [`samples/`](https://github.com/rkttu/dotnetpy/tree/main/samples) ディレクトリには3つのMLサンプルに加え、AOTでビルドしたネイティブDLLをCエクスポート経由で呼び出す [`native-aot`](https://github.com/rkttu/dotnetpy/tree/main/samples/native-aot) コンシューマが入っています。DotNetPyをC / C++ / Rustホストに埋め込む経路です。

MLサンプル群は [uv](https://docs.astral.sh/uv/) を使ってC#の中から宣言的にPython + Hugging Faceスタックをプロビジョニングします。

```csharp
using var project = PythonProject.CreateBuilder()
    .WithProjectName("my-app")
    .WithPythonVersion("==3.12.*")
    .AddDependencies("transformers==4.40.2", "torch>=2.2,<2.5")
    .Build();

await project.InitializeAsync();
```

これだけです。別途Pythonをインストールする必要もなく、自分でvenvを作る必要もありません。

---

## 本当に気を遣った部分 — PEP 703 free-threaded Python

インターロップライブラリの観点から興味深い変曲点が2025〜26年に到来しました。CPython 3.13に **free-threadedビルド** （`t` 接尾辞が付いた`python3.13t`）が導入され、GILが消え、同時に走るスレッド群が *本当に* 並列でPythonコードを実行できるようになりました。MLサービングには素晴らしい変化です。1つのプロセスの中に推論ワーカーを複数置きたくなるからです。同時に、既存のGIL前提で書かれていた多くのライブラリの暗黙的な不変条件が崩れる時点でもあります。

特にpythonnetもこの作業を進めており、[PR #2721](https://github.com/pythonnet/pythonnet/pull/2721) で必要な作業が5つのカテゴリに整理されています。

1. Refcountレイアウトの変更（`ob_refcnt` がsplit構造に変わる）
2. 並列なtype / objectキャッシュの競合
3. `Reflection.Emit` のスレッド安全性
4. `GCHandle` スロット所有権のアトミック性
5. Finalizer / `Py_Finalize` の競合

DotNetPy 0.6.0を作るとき、私はpythonnetのPRをある種の **監査用チェックリスト** として活用しました。5つのカテゴリを1つずつ当てはめて、DotNetPyが同じ罠に陥るかを点検したのです。結果として、**5項目のうち4項目はDotNetPyの設計自体が該当事項を回避していました。** .NETとPythonの型システムを橋渡ししない、CLR型をPythonのサブクラスにしない、`Reflection.Emit`を使わない、Pythonに`GCHandle`スロットを公開しない、`Py_Finalize`を呼ばないからです。5番目の項目（finalizer / shutdown）は、`SafeHandle.ReleaseHandle`の`Py_DecRef`呼び出しの周りに明示的な`PyGILState_Ensure`ガードを置いて解決しました。

監査の過程で実際に発見され、0.6.0で修正した問題は次の通りです。

- **共有`__main__` globals内の内部一時変数名の衝突。** すべてのヘルパー変数（`_json_result`・`_is_valid` など）を`Interlocked.Increment`で呼び出しごとに一意に発行するように変更し、同時に走る2つの呼び出し元が同じスロットを取り合わないようにしました。
- **`Evaluate` が共有 `result` グローバルを漏らしていた問題。** 同じパターンで解決しました。呼び出しごとに一意のシンク名を発行し、`finally` できれいに片付けます。
- 上記2つの修正と微妙に絡む第3の問題はリリース時点でも残っています。ユーザー変数注入（`Execute` / `ExecuteAndCapture` の`variables:`パラメータ）は依然として共有`__main__` globalsに入ります。並列の呼び出し元が同じユーザー変数名を使うと衝突がそのまま残ります。

3番目の問題への解決策が0.6.0の最も目立つ追加機能、隔離された実行器のファクトリメソッドです。

```csharp
using var iso = Python.CreateIsolated();
iso.Execute("import json");
iso.Execute("data = {'k': 1}");   // `data` はこの実行器だけが見えます
```

`CreateIsolated()`は自分自身のPython dict（`__builtins__`を事前に埋め込み済み）を所有する実行器を作ります。隔離された実行器同士は、共有シングルトン、そして他の隔離実行器と同じプロセス内で共存しますが、お互いの間に変数が漏れません。

おかげで並列MLパターンが非常に簡潔になります。

```csharp
Parallel.For(0, Environment.ProcessorCount, threadId =>
{
    using var iso = Python.CreateIsolated();
    iso.Execute("import torch; from transformers import pipeline");
    iso.Execute(@"
asr = pipeline('automatic-speech-recognition',
               model='openai/whisper-base.en')
");
    using var r = iso.ExecuteAndCapture(@"
out = asr(audio_path)
result = {'text': out['text']}
", new Dictionary<string, object?> { { "audio_path", path } });

    Console.WriteLine(r?.GetString("text"));
});
```

free-threaded CPythonビルドの上では、このループは **本当に並列で動きます。** すべてのワーカーが自分の`asr`パイプラインと自分のPythonネームスペースを持ちます。既存のGILビルドでは同じコードが正しく動くものの、インタプリタで直列化されます。どのみちこれはどのインターロップライブラリを使ってもぶつかる壁で、DotNetPyが解決できる問題ではありません。

3つのビルドの組み合わせでマトリクス検証を済ませました。

| Pythonビルド | ユニットテスト | Native AOTコンシューマ |
| --- | --- | --- |
| CPython 3.13 (GIL, auto-discovered) | 209 / 1 / **0** | 8 / 8 ✅ |
| CPython 3.13.13t (free-threaded) | 205 / 5 / **0** | 8 / 8 ✅ |
| CPython 3.14.4t (free-threaded) | 205 / 5 / **0** | 8 / 8 ✅ |

全体の監査結果は [`docs/FREETHREADED-AUDIT.md`](https://github.com/rkttu/dotnetpy/blob/main/docs/FREETHREADED-AUDIT.md) にまとめてあります。意図的に公開ドキュメントとして残しました。「検証しました」と言うとき、その言葉が正確に何を意味するのかを読者が直接読めるようにするためです。

---

## 正直に書いておく限界

いくつかの点ははっきり書いておく必要があります。

- **DotNetPyはまだ0.6.0。** 実験段階であり、プロダクション安定段階ではありません。少なくないパターンがまだ整理中です。
- **Python MLスタック自体が完全にfree-threadedではありません。** PyTorchのFTサポートは活発に移行中で、NumPy 2.1+ がPEP 703をサポートしています。`transformers`と`diffusers`は動作はしますが、内部のC拡張モジュールの状態はまちまちです。上流スタックが追いつくまでは、DotNetPyのインターロップ層ではfree-threaded環境の整合性は得られますが、Python側のML性能自体はライブラリ内部のロックで直列化される可能性があります。
- **Native AOTパブリッシュはプラットフォーム別のCツールチェーンを要求します。** Windowsは Visual Studio C++ build tools、Linuxは`clang` / `lld`が必要です。AOTコンパイルする一般の.NETアプリと同じ制約です。
- **JSONマーシャリングがデータプレーン。** すべての結果変数はPython側でシリアライズされ、.NET側で`System.Text.Json`によってデシリアライズされます。Native AOT互換性を得るための意図的なトレードオフです。結果オブジェクトが非常に大きいワークロードであれば、複数の値を1回のcapture呼び出しの中にまとめ、小さな構造化サマリだけを返すパターンを推奨します。

---

## さらに知りたい方へ

- **コード**: <https://github.com/rkttu/dotnetpy>
- **NuGet**: `dotnet add package DotNetPy --version 0.6.0`
- **サンプル**: [`samples/ml-embeddings`](https://github.com/rkttu/dotnetpy/tree/main/samples/ml-embeddings)、[`samples/ml-whisper`](https://github.com/rkttu/dotnetpy/tree/main/samples/ml-whisper)、[`samples/ml-image-gen`](https://github.com/rkttu/dotnetpy/tree/main/samples/ml-image-gen) — それぞれ`dotnet run sample.cs`一発で完結します。
- **Free-threaded監査ドキュメント**: [`docs/FREETHREADED-AUDIT.md`](https://github.com/rkttu/dotnetpy/blob/main/docs/FREETHREADED-AUDIT.md)
- **pythonnet / CSnakes / IronPythonとの比較（意思決定ツリー付き）**: [`docs/COMPARISON.md`](https://github.com/rkttu/dotnetpy/blob/main/docs/COMPARISON.md)
- **英語原文**: [dev.to](https://dev.to/rkttu/speech-search-and-stable-diffusion-calling-huggingface-from-c-2bkk)

「C#で先ほど発表されたばかりのHugging Faceモデルをどう動かすか」という問いに、1つの答えになれれば嬉しいです。Issue、PR、コメントすべて歓迎します。同じ悩みを抱えている.NETコミュニティの方がいれば、ぜひ試してフィードバックをください。

---

*この記事は [/dev/write](https://devwrite.ai) ニュースレターで発行されました。*

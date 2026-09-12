---
title: "Edge0連載 2: Microsoft LearnとApple Translationの実行環境"
date: "2026-09-14T09:00:00+09:00"
draft: false
slug: "edge0-setup-microsoft-learn-translation"
translationKey: "edge0-setup-microsoft-learn-translation"
description: "Edge0サーバー、Microsoft Learn CLI、Apple Translationを接続する環境を構成します。ターミナルごとの仮想環境、翻訳APIの条件、韓国語の質問を正規化する理由を説明します。"
tags: ["Edge0", "ローカルLLM", "RAG", "Apple Silicon", "Microsoft Learn"]
categories: ["人工知能"]
tldr: "Edge0-35BサーバーとPythonエージェントを別々のターミナルで実行し、文書検索とオンデバイス翻訳を接続します。モデルパス、macOS 26.4以降の翻訳API、言語リソースの導入、韓国語の間接疑問文への対処を準備します。"
cover:
  image: "images/posts/edge0-setup-microsoft-learn-translation.webp"
  alt: "ノートPCの前で接続した演算装置、文書カード、半透明の吹き出し。"
  caption: "記事のテーマを基にAIで生成したイメージです。"
license: "CC BY-NC 4.0"
---

2026年9月13日時点で、この連載のサンプルはEdge0-35B、Microsoft Learn CLI、macOSのTranslationフレームワークを使用します。{{< series-link slug="edge0-16gb-mac-overview" text="第1回" >}}で決めた役割分担に沿って、推論サーバーとPythonエージェントのホストを別々のターミナルで実行します。

この記事ではEdge0とモデルの導入、ストリーミングサーバーの起動、公式文書の検索、韓国語と英語の翻訳、質問の正規化を扱います。ファイル全体は[サンプルGist](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)の`README.md`、`apple_translate.swift`、`microsoft_expert_agent.py`にあります。

実行条件とインストール手順から説明します。最初のターミナルでサーバーを起動した後、検索ツールと翻訳CLIを準備し、二つ目のターミナルでエージェントを実行できる状態にします。

以下の手順は、次の公開バージョンとAPI条件を前提にしています。

> 文書は2026年9月13日に確認しました。`Edge0-35B-A3B-preview`の構成は今後変わる可能性があります。Swiftの例で使用する`TranslationSession(installedSource:target:preferredStrategy:)`は、macOS 26.4以降と、このAPIを含むSDKを前提とします。

## Edge0と35Bモデルの導入条件

実験にはApple Silicon Mac、Python 3.12、Node.js 22以降、Xcode Command Line Toolsを使用します。約23GBのモデルファイルを保存する空き容量と、韓国語および英語の翻訳リソースも用意します。対応環境とモデルファイルの構成は[公式README](https://github.com/Edge0-AI/Edge0)に記載されています。

### リポジトリとPython仮想環境

作業ディレクトリでリポジトリを取得し、仮想環境を有効にしてサンプルの依存関係をインストールします。

```bash
git clone https://github.com/Edge0-AI/Edge0.git
cd Edge0

python3.12 -m venv .venv
source .venv/bin/activate

pip install -e '.[dev,fetch]'
pip install flask requests
```

以後のコマンドはEdge0リポジトリのルートを作業ディレクトリにします。`flask`はストリーミング転送、`requests`はPythonホストのHTTPリクエストに使用します。

### モデルのダウンロードとパスの指定

公式スクリプトで35Bモデルを取得し、現在のシェルにモデルパスを設定します。

```bash
python scripts/fetch_models.py \
  --tier edge0-35b \
  --target-dir models

export EDGE0_35B_MODEL="$PWD/models/edge0-35b"
```

`models/edge0-35b/`には、設定、モデルの重み、トークナイザー、LoRAとプリルーターのアダプターが含まれます。アダプターを含むディレクトリ全体をモデルパスとして指定します。

## 最初のターミナルで動かすストリーミングサーバー

Edge0の[35Bモデル文書](https://github.com/Edge0-AI/Edge0/blob/main/docs/models/edge0-35b.md)は、Flask転送層によるSSEストリーミングと、状態確認用の`/healthz`を説明しています。このサンプルでは接続先を`127.0.0.1:8083`に設定します。

### 仮想環境の再有効化とサーバー起動

新しいターミナルでは、作業パス、仮想環境、モデルの環境変数を再設定します。`/path/to/Edge0`は、リポジトリを取得した実際のパスに置き換えます。

```bash
cd /path/to/Edge0
source .venv/bin/activate

export EDGE0_35B_MODEL="$PWD/models/edge0-35b"

edge0 serve edge0-35b \
  --host 127.0.0.1 \
  --port 8083 \
  --flask
```

サーバーの実行中は最初のターミナルを開いたままにします。別のターミナルで有効にした仮想環境は、新しいシェルに自動では適用されません。

### 別のシェルからの状態確認

別のターミナルから次のリクエストを送り、サーバーの応答を確認します。

```bash
curl http://127.0.0.1:8083/healthz
```

成功すると、指定したアドレスのHTTPサーバーへ接続できることを確認できます。文章の生成は、後でエージェントに質問を送る段階で確かめます。

## Microsoft Learn検索と入力資料の制限

Microsoftは[Learn MCPサーバーとCLI](https://github.com/MicrosoftDocs/mcp#-microsoft-learn-cli)を提供しています。Pythonホストは`mslearn`を子プロセスとして起動し、JSONの結果を読み取ります。サンプル内でMCP転送層を直接実装せずに、同じ文書検索機能を使用できます。

### CLIの導入と検索確認

Node.js環境にCLIをインストールし、Native AOTの検索結果を確認します。

```bash
npm install -g @microsoft/learn-cli

mslearn search \
  ".NET NativeAOT Reflection.Emit" \
  --json
```

検索はMicrosoft Learnの外部サービスへクエリを送信します。Edge0の推論と翻訳をローカルで実行していても、検索にはネットワーク接続を使用します。

### 関連箇所の件数と長さの制限

サンプルはページ全体を取得せず、検索結果が返す関連箇所を使用します。[コード全体](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)では、次の定数で入力を制限します。

```python
MAX_SOURCES = 3
MAX_SOURCE_CHARS = 1800
```

最大3件を選び、それぞれ最大1,800文字を渡します。この上限は文字数であり、KBやモデルのトークン数とは異なります。質問に必要な根拠を残しながら上限を調整し、回答品質と待ち時間を比較できます。

## Apple Translationを呼び出すSwift CLI

例では[AppleのTranslationSession初期化API](https://developer.apple.com/documentation/translation/translationsession/init%28installedsource%3Atarget%3Apreferredstrategy%3A%29)を使用します。`preferredStrategy`引数はmacOS 26.4以降で利用できます。OSとコンパイル用SDKがこのAPIに対応する環境で、以下のコードをビルドします。

### 翻訳する言語とテキストを受け取るエントリーポイント

次のソースをEdge0リポジトリのルートに`apple_translate.swift`として保存します。

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

CLIは原文の言語、翻訳先の言語、テキストを引数で受け取り、翻訳結果を標準出力へ返します。`installedSource`方式は、言語リソースを事前にインストールしていることを前提にします。

### コンパイルと最初の翻訳

単一のSwiftファイルで`@main`エントリーポイントを使うために`-parse-as-library`を指定し、翻訳を試します。

```bash
xcrun swiftc \
  -parse-as-library \
  apple_translate.swift \
  -o apple_translate

./apple_translate ko en \
  "NativeAOT에서 Reflection.Emit을 사용할 수 있습니까?"
```

`-parse-as-library`を省略すると、単一ファイル内の`@main`とトップレベルコードに関するコンパイルエラーが発生する場合があります。`TranslationError.Cause.notInstalled`が発生した場合は、韓国語と英語の翻訳リソースのインストール状況を確認します。リソースの導入後は、翻訳をオンデバイスで処理します。

## 質問の意味を保つ韓国語の正規化

NLLB 600M、NLLB 1.3B、Apple Translationを試した際、生成の有無を尋ねた質問が、生成方法を説明する依頼に翻訳される例がありました。この連載では[サンプルの正規化関数](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)で一部の文型に対処します。

実験で使用した質問、誤訳、正規化後の文を比較すると、次のようになります。

- **元の質問**：「런타임에 새로운 실행 코드를 생성하는지도 함께 설명해주세요.」と質問しました。実行時に新しい実行コードを生成するかどうかを尋ねています。

- **誤訳の例**：「Explain how to generate new executable code at runtime.」と翻訳されました。生成の有無を尋ねる質問が、生成方法を説明する依頼に変わっています。

- **正規化後**：「런타임에 새로운 실행 코드를 생성합니까? 그 여부도 함께 설명해주세요.」に書き換えました。直接疑問文で生成の有無を尋ねています。

正規化関数は`~할 수 있는지도`、`~되는지도`、`~하는지도`、`~필요한지도`など、決められたパターンを直接疑問文に変換します。正規表現に一致しない文は、そのまま翻訳器に渡します。韓国語の文章全体を理解して修正する汎用的な校正機能としては扱いません。

## 二つ目のターミナルでのエージェント実行準備

[Gist](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)の`microsoft_expert_agent.py`をEdge0リポジトリのルートに保存し、翻訳用の実行ファイルも同じ場所に配置します。

二つ目のターミナルでは、サーバーのターミナルとは別に仮想環境を有効にします。

```bash
cd /path/to/Edge0
source .venv/bin/activate

pip install requests
```

実行前に、次の順序で構成要素を確認できます。

1. 最初のターミナルでEdge0サーバーの実行状態を確認します。
2. 二つ目のターミナルから`/healthz`の応答を確認します。
3. `mslearn search`のJSON検索結果を確認します。
4. `./apple_translate`で韓国語と英語の翻訳を確認します。
5. リポジトリのルートで`python microsoft_expert_agent.py`を実行します。

第3回と第4回では、エージェント全体のコードから検索、プロンプト構成、ストリーミング、計測を分けて説明します。

## 個別に確認できる三つの構成要素

Edge0サーバー、Microsoft Learn検索、Apple Translationは、それぞれ独立して実行と確認ができます。Pythonホストは三つの構成要素を接続し、韓国語の質問に答える流れを制御します。

現在の実行には、ターミナルごとの仮想環境、モデルパス、翻訳APIのOS条件が直接影響します。検索結果の再ランキングや、より短いグラウンディング資料は、今後の性能比較に残しています。{{< series-link slug="edge0-local-rag-agent" text="第3回" >}}では質問の正規化から検索結果の選択、会話コンテキストの構成までをPythonで接続します。

連載は次の順序で構成しています。

1. {{< series-link slug="edge0-16gb-mac-overview" text="16GB Macで動かす35BローカルLLMと根拠に基づくエージェント" >}}
2. {{< series-link slug="edge0-setup-microsoft-learn-translation" text="現在の記事" >}}
3. {{< series-link slug="edge0-local-rag-agent" text="Microsoft Learn検索を組み込むローカルRAGエージェント" >}}
4. {{< series-link slug="edge0-streaming-ttft-metrics" text="ストリーミング応答のTTFTと出力速度の計測" >}}
5. {{< series-link slug="edge0-real-benchmark-and-poc" text="M2 Air 16GBでの実測と社内PoCへの拡張条件" >}}

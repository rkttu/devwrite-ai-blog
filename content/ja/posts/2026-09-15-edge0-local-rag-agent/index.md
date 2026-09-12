---
title: "Edge0連載 3: Microsoft Learn検索を組み込むローカルRAGエージェント"
date: "2026-09-15T09:00:00+09:00"
draft: false
slug: "edge0-local-rag-agent"
translationKey: "edge0-local-rag-agent"
description: "韓国語の質問の正規化、Apple Translation、Microsoft Learn検索をPythonで接続します。根拠資料の件数と長さを制限し、直近の会話だけをモデルに渡すRAG構成を説明します。"
tags: ["Edge0", "ローカルLLM", "RAG", "Apple Silicon", "Microsoft Learn"]
categories: ["人工知能"]
tldr: "Pythonホストが質問の翻訳とMicrosoft Learn検索を実行し、Edge0は選択した資料を読んで回答します。URLの重複除去、出典番号、根拠不足を示すルール、直近2ターンの要求コンテキストにより、入力の量と回答の根拠を管理します。"
license: "CC BY-NC 4.0"
---

2026年9月13日時点で、[サンプルGist](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)はEdge0サーバー、Microsoft Learn CLI、Apple TranslationをPythonで接続するコードを提供しています。{{< series-link slug="edge0-setup-microsoft-learn-translation" text="第2回" >}}で準備した環境を基に、今回は検索した資料をモデルの入力に変える部分を説明します。

この記事では、ホストとモデルの役割分担、質問の正規化と翻訳、検索結果の選択、グラウンディング用プロンプト、会話コンテキストの管理を扱います。ホストが検索の順序を決め、モデルは渡された資料を読んで回答を構成します。

データ構造と入力処理から説明します。検索した箇所に出典番号を付け、現在の質問と一緒に渡した後、続く質問に必要な文脈を構成します。ストリーミング要求と性能計測は第4回で扱います。

本文のコードと公開バージョンは、次の範囲で扱います。

> 公開資料は2026年9月13日に確認しました。本文ではRAGの流れを説明するためにコードを抜粋し、実行ファイル全体に含まれる一部の補助処理を省略しています。`Edge0-35B-A3B-preview`の動作や外部ツールの応答形式は、今後変わる可能性があります。

## 検索とコンテキスト構成を担うPythonホスト

[Pythonコード全体](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)では、ホストが入力を正規化して翻訳し、Microsoft Learnを検索します。検索結果の重複URLを除き、資料の長さを制限し、直近の会話をリクエストに含めます。

モデルの役割は、質問と文書の関係を把握し、回答に使う根拠を選び、英語で回答を生成することに絞ります。資料から事実を確認できない場合は、根拠が不足していると回答するようプロンプトに指定します。

検索結果はタイトル、URL、本文を持つ`Source`オブジェクトで管理します。入力の量を制限する定数も一緒に定義します。

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

`MAX_SOURCE_CHARS`は各検索箇所の文字数を制限します。出典タイトル、URL、システムプロンプト、会話履歴はこの上限の外で追加するため、リクエスト全体のサイズは別途計算できます。

## 間接疑問文を直接疑問文に変えるルール

韓国語の質問の正規化は、[Gistの`normalize_korean_question()`](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)が処理します。生成の有無を尋ねた質問が翻訳時に生成方法を尋ねる依頼へ変わる例を減らすため、決められた文型を変換します。

次の関数は四つのパターンに一致する文を、直接疑問文と後続の依頼に分けます。

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

パターンに一致しなければ、入力をそのまま返します。文型を追加する際には、原文、変換結果、英語訳を比較すると、質問の意味を維持できているか確認できます。

## Swift CLIへの英語翻訳要求

翻訳はPythonから起動する子プロセスに分離します。[Apple Translationの初期化API](https://developer.apple.com/documentation/translation/translationsession/init%28installedsource%3Atarget%3Apreferredstrategy%3A%29)をラップした`apple_translate`実行ファイルは、第2回で準備しました。

次のコードは入力を句読点で分割し、それぞれを正規化して英語に翻訳します。

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

この分割関数は、疑問符、感嘆符、ピリオドの後の空白を基準に動作します。略語や製品名の中の句読点まで区別する構文解析器ではないため、複雑な入力では分割結果を確認できます。

本文の`translate_question_to_english()`は、流れを説明するために英語の文字列だけを返します。Gistの実行ファイル全体は、原文、正規化結果、英語訳を含む追跡情報も返すため、プログラム全体を実行する際はGistのファイルを使用します。

## 重複URLと長い検索箇所の制限

[Learn CLI](https://github.com/MicrosoftDocs/mcp#-microsoft-learn-cli)の`--json`で結果を受け取り、URLと本文の両方を持つ項目だけを選びます。

検索関数は同じURLを一度だけ使い、最大三つの箇所を返します。

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

複数のフィールド名を確認する処理は、サンプルが想定するJSON形式に対応するためのものです。すべての応答形式に対応する検証層としては扱いません。関連箇所が見つからなければ、実行ファイル全体はその質問の生成を進めず、検索結果がない旨を表示します。

検索結果全体をそのまま入力せず、質問に必要な箇所を使うと入力を減らせます。このサンプルは別の再ランキングモデルを使用しないため、結果の順序と文字数の制限が選択に与える影響を併せて観察します。

## 出典番号と根拠の範囲を示すプロンプト

[Gistの`build_grounding()`と`build_user_prompt()`](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)は、各資料にタイトルとURLを含め、モデルが出典番号を回答に付けられるよう構成します。

### 現在の質問と一緒に渡す参照資料

選択した検索箇所を番号付きの参照資料にまとめ、現在の質問の前に配置します。

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

資料と質問を分けると、ホストが渡した根拠を確認しやすくなります。ただし、`<references>`タグ自体が資料の信頼性やモデルの指示遵守を保証するわけではありません。

### 根拠不足と出典表記を指定するシステムプロンプト

システムプロンプトは、資料に裏付けられた事実を優先し、確認できない事実は根拠不足として示すよう指定します。

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

このルールで回答の方向を制限します。生成した引用番号と実際の根拠が一致するかは、表示された出典と照合して確認できます。

## 直近2ターンに限定する要求コンテキスト

[コード全体](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)は、直前の話題を検索クエリの補助情報として使用します。以前のグラウンディング資料は会話履歴に追加せず、ユーザーの質問とモデルの英語回答を保存します。

次の関数は直近のユーザー質問を探し、現在の質問と組み合わせて検索クエリを構成します。

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

モデルへのリクエストを作る際は、`history[-MAX_HISTORY_TURNS * 2:]`で直近2ターンの質問と回答だけを選びます。現在の質問のグラウンディング資料はそのリクエストにだけ追加するため、過去の検索箇所が毎回の入力に累積することを避けられます。

この設定が制限するのは、モデルへ送る会話コンテキストです。サンプル全体の`history`リストはセッション中の質問と回答を保持し続け、`/clear`で空にします。メモリ上に直近2ターンだけを保存する実装とは異なります。

## 入力量と回答の根拠を管理する流れ

Pythonホストは韓国語の質問を英語の検索クエリに変え、関連箇所を選んで現在のリクエストの根拠にします。出典番号と根拠不足を示すルールも渡し、モデルへ送る過去の会話は直近2ターンに制限します。

現在の入力の量には、検索結果の件数、箇所の長さ、会話コンテキストが直接影響します。検索の再ランキングと、より細かな文の正規化は今後の課題として残しています。{{< series-link slug="edge0-streaming-ttft-metrics" text="第4回" >}}では準備したプロンプトをEdge0サーバーに渡し、最初の応答までの待ち時間と、その後の出力速度を計測します。

連載は次の順序で構成しています。

1. {{< series-link slug="edge0-16gb-mac-overview" text="16GB Macで動かす35BローカルLLMと根拠に基づくエージェント" >}}
2. {{< series-link slug="edge0-setup-microsoft-learn-translation" text="Microsoft LearnとApple Translationの実行環境" >}}
3. {{< series-link slug="edge0-local-rag-agent" text="現在の記事" >}}
4. {{< series-link slug="edge0-streaming-ttft-metrics" text="ストリーミング応答のTTFTと出力速度の計測" >}}
5. {{< series-link slug="edge0-real-benchmark-and-poc" text="M2 Air 16GBでの実測と社内PoCへの拡張条件" >}}

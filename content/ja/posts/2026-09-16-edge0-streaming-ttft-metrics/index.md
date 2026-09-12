---
title: "Edge0連載 4: ストリーミング応答のTTFTと出力速度の計測"
date: "2026-09-16T09:00:00+09:00"
draft: false
slug: "edge0-streaming-ttft-metrics"
translationKey: "edge0-streaming-ttft-metrics"
description: "Edge0のSSE応答から最初の出力までの待ち時間と出力速度を計測します。待機状態の表示、文単位の韓国語翻訳、イベント数を使ったトークン推定の限界を説明します。"
tags: ["Edge0", "ローカルLLM", "RAG", "Apple Silicon", "Microsoft Learn"]
categories: ["人工知能"]
tldr: "ワーカースレッドがEdge0のストリームを受信し、メインスレッドが待機状態と韓国語の回答を表示します。TTFTとリクエスト全体の時間を分けて記録し、SSEコンテンツイベント数から求めた出力速度をサーバー内部のデコード性能と区別します。"
cover:
  image: "images/posts/edge0-streaming-ttft-metrics.webp"
  alt: "時間を測る装置とノートPCの間のレール上で、最初の空白区間に続いて並ぶ青いガラスのパネル。"
  caption: "記事のテーマを基にAIで生成したイメージです。"
license: "CC BY-NC 4.0"
---

2026年9月13日時点で、[連載のPythonサンプル](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)はEdge0のSSE応答を受信しながら、最初の応答までの待ち時間と出力速度を記録します。今回は{{< series-link slug="edge0-local-rag-agent" text="第3回" >}}で作ったグラウンディング用プロンプトを実際の生成リクエストへ接続します。

この記事では、計測時点、待機状態の表示、ワーカースレッドでの受信、文単位の韓国語翻訳、計測値の解釈を扱います。16GBのM2 MacBook Airでの実験では最初の応答まで数十秒かかったため、その前後の時間を分けて記録しました。

計測値の定義から説明します。サーバー応答の受信と画面出力を分離し、生成文を翻訳して最後に指標を表示する順に進めます。プログラム全体にはGistの`microsoft_expert_agent.py`を使用します。

以下の計測は、次の範囲で解釈します。

> 公開資料は2026年9月13日に確認しました。`Edge0-35B-A3B-preview`と公開ストリーミングインターフェースを前提とします。サンプルはクライアントが観測した時間とコンテンツイベント数を記録し、サーバー内部のプリフィル、デコード、待機時間を個別には計測しません。

## 最初のコンテンツと受信終了を基準にした計測値

[Gistの`StreamStats`](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)は、リクエストを処理するワーカースレッドを起動する直前に基準時刻を保存します。その後、空でない最初のコンテンツを受信した時刻と、ストリームの受信を終えた時刻を記録します。

- **TTFT**：リクエストの基準時刻から最初のコンテンツを受信するまでの時間を測ります。クライアントが観測した最初の出力までの待ち時間を表します。

- **総生成時間**：リクエストの基準時刻からストリームの受信が終わるまでの時間を測ります。検索時間は含まず、韓国語翻訳がすべて完了する時点までは測りません。

- **生成量**：コンテンツを含むSSEイベント数を数えます。現在の転送動作を前提に、この値をトークン数の推定値として使います。

- **最初の応答後の時間**：最初のコンテンツを受信してからストリームの受信が終わるまでの時間を測ります。ネットワーク受信や終了処理にかかる時間も含みます。

- **出力速度**：生成量を最初の応答後の時間で割ります。コンテンツイベント単位で処理率を計算します。

### 時刻と生成量を保存するオブジェクト

既存サンプルのフィールド名と計算式を保持した計測オブジェクトを示します。

```python
from dataclasses import dataclass


@dataclass
class StreamStats:
    request_started: float = 0.0
    first_token_at: float | None = None
    done_at: float | None = None
    completion_tokens: int = 0

    @property
    def ttft(self) -> float | None:
        if self.first_token_at is None:
            return None

        return self.first_token_at - self.request_started

    @property
    def total_generation_time(self) -> float | None:
        if self.done_at is None:
            return None

        return self.done_at - self.request_started

    @property
    def decode_time(self) -> float | None:
        if self.first_token_at is None or self.done_at is None:
            return None

        return self.done_at - self.first_token_at

    @property
    def output_tokens_per_second(self) -> float | None:
        duration = self.decode_time

        if not duration or duration <= 0:
            return None

        return self.completion_tokens / duration
```

TTFTには、スレッド起動、HTTP処理、サーバーのキュー待ち、トークン化、プリフィル、最初の生成ステップの時間が含まれる場合があります。`decode_time`という名前のフィールドも、サーバー内部の純粋なデコード時間だけを意味しません。

## 最初の応答を待つ間の状態表示

最初の出力が遅いと、ユーザーはリクエストが進んでいるか判断しにくくなります。[サンプルの`Activity`](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)は、処理段階と経過時間をターミナルに表示します。モデル内部の推論ではなく、プログラムが観測した状態を示します。

### 経過時間を付ける出力関数

状態メッセージを表示するたびに経過時間を計算します。実行ファイル全体は、このクラスより前に`time`モジュールをインポートしています。

```python
class Activity:
    def __init__(self):
        self.started = time.perf_counter()

    def show(self, message: str):
        elapsed = time.perf_counter() - self.started

        print(
            f"[{elapsed:6.1f}s] {message}",
            flush=True,
        )
```

### 実験時の待機メッセージ

韓国語の案内を使った実験ログでは、次のように待ち時間を表示しました。現在のGistでは案内を英語で表示し、質問と回答に韓国語を使います。

```text
[   2.6s] Edge0-35B에 요청 전달
[   7.6s] Edge0 처리 중, 첫 토큰 대기 5초
[  12.6s] Edge0 처리 중, 첫 토큰 대기 10초
[  17.7s] Edge0 처리 중, 첫 토큰 대기 15초
```

メインスレッドは、最初のコンテンツを受信するまで約5秒間隔で案内を表示します。この表示だけで、サーバー内部の処理段階を特定することはできません。

## ワーカースレッドで受信するSSE応答

[Edge0のHTTP API](https://github.com/Edge0-AI/Edge0/blob/main/docs/models/edge0-35b.md#http-api)は、`/v1/chat/completions`と`stream: true`のリクエストに対応します。サンプルはFlask転送層を使用し、受信を別スレッドで処理します。

次の抜粋は、応答の`data:`行からコンテンツを取り出してキューへ渡します。`requests`、`json`、`queue`、`time`やサーバーアドレスなどの定数は、実行ファイル全体で定義しています。

```python
def edge0_worker(
    messages: list[dict],
    events: queue.Queue,
):
    try:
        response = requests.post(
            f"{EDGE0_BASE_URL}/v1/chat/completions",
            json={
                "model": EDGE0_MODEL,
                "messages": messages,
                "temperature": 0.0,
                "seed": 42,
                "max_tokens": MAX_TOKENS,
                "stream": True,
            },
            stream=True,
            timeout=600,
        )

        response.raise_for_status()

        for raw_line in response.iter_lines(
            decode_unicode=True,
        ):
            if not raw_line:
                continue

            if not raw_line.startswith("data:"):
                continue

            payload = raw_line[5:].strip()

            if payload == "[DONE]":
                break

            event = json.loads(payload)

            delta = (
                event["choices"][0]
                .get("delta", {})
                .get("content")
                or ""
            )

            if delta:
                events.put(
                    (
                        "token",
                        delta,
                        time.perf_counter(),
                    )
                )

        events.put(
            (
                "done",
                None,
                time.perf_counter(),
            )
        )

    except Exception as exc:
        events.put(
            (
                "error",
                exc,
                time.perf_counter(),
            )
        )
```

サーバーの文書は、トークンごとにSSEイベントを送り、最後に`[DONE]`を送信する流れを説明しています。サンプルはコンテンツがあるイベントだけをキューに入れるため、プロトコルの全イベントを生成量として数えるわけではありません。

この抜粋は正常な応答形式を前提とします。Gist全体にはJSONと`choices`を読む補助的なエラー処理がありますが、ストリームが終了した場合と`[DONE]`を受け取った場合を区別して検証する処理はありません。結果を比較する際には、応答が正常に完了したかも併せて確認できます。

## メインスレッドでのTTFT確定とコンテンツの受け渡し

[Gistの`stream_edge0_with_progress()`](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)は、1秒のタイムアウトでイベントを待ち、最初のコンテンツイベントが届くと受信時刻を保存します。

次の関数は、状態表示、コンテンツの受け渡し、終了処理、エラー処理を接続します。

```python
def stream_edge0_with_progress(
    messages: list[dict],
    activity: Activity,
    stats: StreamStats,
):
    events = queue.Queue()

    worker = threading.Thread(
        target=edge0_worker,
        args=(messages, events),
        daemon=True,
    )

    stats.request_started = time.perf_counter()
    worker.start()

    last_progress = 0

    while True:
        try:
            kind, value, event_time = events.get(
                timeout=1.0
            )

        except queue.Empty:
            if stats.first_token_at is None:
                waited = int(
                    time.perf_counter()
                    - stats.request_started
                )

                if (
                    waited >= 5
                    and waited - last_progress >= 5
                ):
                    activity.show(
                        "Edge0 처리 중, "
                        f"첫 토큰 대기 {waited}초"
                    )

                    last_progress = waited

            continue

        if kind == "token":
            stats.completion_tokens += 1

            if stats.first_token_at is None:
                stats.first_token_at = event_time

                activity.show(
                    "첫 토큰 수신 "
                    f"(TTFT {stats.ttft:.1f}초)"
                )

            yield value

        elif kind == "done":
            stats.done_at = event_time
            break

        elif kind == "error":
            stats.done_at = event_time
            raise value
```

`completion_tokens`は`token`イベントを受け取るたびに1増えます。現在のサーバーがトークンごとに送信することを前提にした簡易な推定であり、トークナイザーで数え直した正確な生成トークン数との一致は保証しません。転送層が複数トークンをまとめたり、空のコンテンツを含めたりすると差が生じる場合があります。

サーバー間のベンチマークでは、サーバーが返す使用量や、同じトークナイザーで数えたトークン数を基準にできます。このサンプルの値は、まず同じ構成で入力の量や待ち時間の変化を比較するために使います。

## 英語の文を蓄積した後の韓国語翻訳

英語ストリームの小さな断片をすぐ翻訳器に渡すと、文脈を失いやすくなります。[サンプル全体](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)はコンテンツをバッファーに蓄積し、文の境界と判断した部分をApple Translationへ渡します。

### 句読点を基準に分割する文バッファー

次の関数は、文と判断した文字列の一覧と残りのバッファーを返します。ファイル全体は、この前に`re`モジュールをインポートしています。

```python
SENTENCE_PATTERN = re.compile(
    r'(.+?[.!?](?:["\')\]]+)?)'
    r'(?:\s+|$)',
    re.DOTALL,
)


def pop_complete_sentences(
    buffer: str,
) -> tuple[list[str], str]:
    sentences = []
    last_end = 0

    for match in SENTENCE_PATTERN.finditer(buffer):
        sentences.append(
            match.group(1).strip()
        )

        last_end = match.end()

    if not sentences:
        return [], buffer

    return (
        sentences,
        buffer[last_end:],
    )
```

この正規表現は、句読点の後の空白、または現在のバッファーの末尾を境界として扱います。略語、小数点、コード表記、まだ到着していない断片まで考慮する完全な文分割器ではありません。応答終了後の残りのバッファーも、全体のループで翻訳します。

### 生成時刻と韓国語表示時刻の違い

韓国語の出力は文単位で更新します。最初の英語コンテンツを受信した後も、文の蓄積と翻訳に時間がかかるため、TTFTとユーザーが最初の韓国語回答を読める時点は異なります。

ワーカースレッドが受信時刻を記録し、メインスレッドが翻訳と表示を処理します。そのため、計測オブジェクトの`done_at`はストリーム受信の終了を示し、韓国語翻訳と画面出力全体の完了時刻は示しません。

## 計測値の表示とUI拡張の範囲

[Gistの`print_metrics()`](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)は、最後に計測値を表示します。メインループは、質問の翻訳、検索、グラウンディング構成、Edge0応答の受信、文の翻訳を経て、この関数を呼びます。

既存サンプルは、次の名前と単位で結果を表示します。

```python
def print_metrics(
    stats: StreamStats,
):
    print()
    print("측정")

    if stats.ttft is not None:
        print(
            f"  TTFT              "
            f"{stats.ttft:.2f}초"
        )

    if stats.total_generation_time is not None:
        print(
            f"  총 생성 시간       "
            f"{stats.total_generation_time:.2f}초"
        )

    print(
        f"  생성 토큰 수       "
        f"{stats.completion_tokens}"
    )

    if stats.decode_time is not None:
        print(
            f"  첫 토큰 이후 시간  "
            f"{stats.decode_time:.2f}초"
        )

    if stats.output_tokens_per_second is not None:
        print(
            f"  출력 속도          "
            f"{stats.output_tokens_per_second:.2f} tok/s"
        )
```

表示文の`생성 토큰 수`と`tok/s`は、前述のコンテンツイベントに基づく推定を指します。別のサーバーやトークナイザーの数値と比較する場合は、この違いを反映できます。

この状態表示は、後でWeb UIを接続する際にも利用できます。実行の開始と終了、検索中の状態、応答コンテンツをイベントに変換するアダプターを追加する構成です。AG-UIなどのプロトコルとの接続は今後の設計範囲にあり、現在のCLIには実装していません。

## 最初の出力までの待ち時間と後続処理率の分離

サンプルは、最初のコンテンツ受信までの時間と、その後のストリーム受信時間を分けて記録します。ワーカースレッドが応答を受け取る間、メインスレッドは待機状態を表示し、英語の文を韓国語に翻訳します。

現在の構成では、グラウンディングの長さと最初の応答までの待ち時間が使用感に直接影響します。トークナイザーに基づく生成量の計測とUIプロトコルの接続は、今後の課題として残しています。{{< series-link slug="edge0-real-benchmark-and-poc" text="第5回" >}}では、TTFTが53.47秒、イベント単位の出力速度が約4.15回/秒だった実行結果を解釈します。

連載は次の順序で構成しています。

1. {{< series-link slug="edge0-16gb-mac-overview" text="16GB Macで動かす35BローカルLLMと根拠に基づくエージェント" >}}
2. {{< series-link slug="edge0-setup-microsoft-learn-translation" text="Microsoft LearnとApple Translationの実行環境" >}}
3. {{< series-link slug="edge0-local-rag-agent" text="Microsoft Learn検索を組み込むローカルRAGエージェント" >}}
4. {{< series-link slug="edge0-streaming-ttft-metrics" text="現在の記事" >}}
5. {{< series-link slug="edge0-real-benchmark-and-poc" text="M2 Air 16GBでの実測と社内PoCへの拡張条件" >}}

---
title: "dotnetup プレビュー: global.json からの SDK とランタイム管理"
date: 2026-08-23T01:35:51+09:00
draft: false
slug: "dotnetup-preview-first-look"
description: "dotnetup プレビューが OS パッケージと開発用 SDK を分離し、global.json、ランタイム、更新状態を管理する仕組みを整理します。"
tags:
  - .NET
  - dotnetup
  - .NET SDK
  - global.json
  - 開発環境
categories:
  - .NET 開発
translationKey: "dotnetup-preview-first-look"
cover:
  image: "images/posts/dotnetup-preview-first-look.webp"
  alt: "構成ファイルが状態管理ツールを経由してユーザー単位の SDK とランタイムコンポーネントへ接続されるイラスト"
tldr: "dotnetup は rustup と同様に、システムパッケージを維持しながら、開発用の .NET SDK とランタイムをユーザーアカウントで個別に管理します。リポジトリの global.json を追跡可能なインストール要件へ結び付け、チャネル更新と共有コンポーネントの整理もサポートします。"
license: "CC BY-NC 4.0"
---

Microsoft は Microsoft Build 2026 の事前収録セッション OD804 [「Simplifying .NET installs with .NET Up」](https://www.youtube.com/watch?v=ZMnyohA5yrw)で、ユーザー単位の .NET インストールを管理する新しいツール `dotnetup` を紹介しました。2026年8月22日現在、`dotnet/sdk` リポジトリの `release/dnup` ブランチでは、Windows、macOS、Linux 向けのプレビュー版インストール手順とコマンドリファレンスを公開しています。この記事では、セッションが示した課題と設計意図をもとに、現在のプレビューで確認できる動作を整理します。

`dotnetup` は管理者権限を使わず、ユーザープロファイル配下に .NET SDK とランタイムをインストールします。リポジトリの `global.json` を読み取って必要な SDK チャネルを追跡し、複数の要件が共有するインストールファイルを更新または整理します。シェルやアプリケーションが管理対象の `dotnet` を見つける方法も選択できます。この記事では、インストール方法、`global.json` の解釈、SDK とランタイムの分離、インストール状態の管理、自動化での利用を扱います。

最初に、既存のインストール方法に残っていた管理上の空白を確認します。次に、プレビュー版のインストールとリポジトリ単位の SDK 準備をたどります。後半ではランタイムと更新モデルを説明し、現在の実装と OD804 のロードマップの差を検討します。

> 基準日: 2026年8月22日。`dotnetup` はプレビュー段階であり、コマンド名や動作が変わる可能性があります。この記事は [`release/dnup` ブランチの公式ドキュメント](https://github.com/dotnet/sdk/tree/release/dnup/documentation/general/dotnetup)と、同日にダウンロードした `0.2.0-preview.1.26410.1` を基準にしています。

## インストールスクリプトより rustup に近い状態管理ツール

.NET のインストール経路を一つの管理ツールへまとめる理由から確認します。OD804 セッションは、Windows で Visual Studio がツールチェーンを管理する場合と、それ以外の場合を対比しています。後者では、オペレーティングシステムのパッケージマネージャー、Web インストーラー、`dotnet-install` スクリプト、DNVM や mise のようなバージョン管理ツールが混在します。インストール主体と更新周期が異なると、必要な SDK を準備して古いインストールを削除する手順もリポジトリごとに変わります。[セッションの課題定義](https://www.youtube.com/watch?v=ZMnyohA5yrw&t=69s)は、この差をツールが解決しようとする出発点として示しています。

既存の `dotnet-install` スクリプトも、管理者権限を使わないインストールをサポートします。ただし、Microsoft はこのスクリプトを、実行のたびに SDK が消えても問題のない CI 環境で主に使うものと説明しています。開発環境にはインストーラーを案内してきました。[`dotnet-install` の公式ドキュメント](https://learn.microsoft.com/dotnet/core/tools/dotnet-install-script)が、この利用範囲を明記しています。

この点で `dotnetup` は、インストールスクリプトより Rust の `rustup` に近いツールチェーンマネージャーです。Ubuntu のように、[ディストリビューションパッケージの SDK 機能バンドと新しい SDK 配布に差が生じる環境](https://learn.microsoft.com/dotnet/core/install/linux-ubuntu-install)では、システムパッケージを維持したまま、開発用の新しい SDK だけをユーザーアカウントで分離して管理できます。パッケージマネージャーを置き換えたり管理者権限を取得したりせず、プロジェクトごとに異なるチャネルを追跡できる点を、[dotnetdev の初期紹介記事](https://forum.dotnetdev.kr/t/dotnetup-rustup-net-toolchain-manager/14805)でも強調しています。

`dotnetup` は、要求したコンポーネントとチャネルを記録したうえで、実際にインストールしたバージョンへ結び付けます。そのため、`latest`、`lts`、`10.0.1xx` のように移動する要件を後から再解決できます。正確なバージョンを指定すると、その要件を固定します。インストールファイルの取得とインストール状態の管理を一つのコマンド体系に収めた点で、既存のスクリプトと役割が分かれます。[公式概要](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/index.md)は、インストール、更新、削除、環境構成を現在の対象範囲として説明しています。

## 管理者権限を使わないユーザー単位インストール

プレビュー版のインストールとアクセスモードを整理します。macOS と Linux では、公式スクリプトから開始できます。

```bash
curl -fsSL https://aka.ms/dotnet/dotnetup/preview/get-dotnetup.sh | bash
export PATH="$HOME/.dotnetup:$PATH"
dotnetup init
dotnetup --version
```

スクリプトはオペレーティングシステムと CPU に合う実行ファイルをダウンロードし、SHA-512 チェックサムを検証してから、既定では `~/.dotnetup` に `dotnetup` 実行ファイルを配置します。Windows 向けの PowerShell 手順と `daily` ビルドのインストール方法は、[開始ドキュメント](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/README.md)で確認できます。セキュリティポリシーでパイプ実行を許可しない環境では、スクリプトをファイルへ保存して内容を確認した後に実行できます。

`dotnetup init` は SDK チャネルとアクセスモードを尋ねます。アクセスモードは、既存の `dotnet` インストールに対する優先順位を決めます。

| 表示名 | 設定値 | 管理対象の `dotnet` を利用する範囲 |
| --- | --- | --- |
| Isolation Mode | `none` | `PATH` を変更せず `dotnetup dotnet <command>` で実行 |
| Terminal Mode | `shell` | 選択したシェルプロファイルを更新し、そのシェルから起動したプロセスへ適用 |
| Everywhere Mode | `everywhere` | Windows のユーザー環境とシェルプロファイルへ適用 |

macOS と Linux では、対応するシェルを検出すると Terminal Mode を推奨候補として表示します。Windows では Everywhere Mode を推奨します。`dotnetup` が管理する SDK とランタイムの既定ルートは、オペレーティングシステムごとのユーザーデータディレクトリ配下にあり、システム管理の場所には書き込みません。[環境構成ドキュメント](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/concepts/environment.md)が、パスと環境変数の動作を説明しています。

今回の確認では、公式プレビュースクリプトが macOS arm64 用の `0.2.0-preview.1.26410.1` 実行ファイルを選択し、チェックサム検証を完了しました。OD804 は、高速な起動と小さなランタイム依存関係のために Native AOT を採用する設計を説明しています。ダウンロードしたファイルも、.NET SDK を先にインストールしなくても実行できるプラットフォーム固有の実行ファイルでした。この結果は、2026年8月22日に実施した macOS arm64 での確認に限られます。

初回実行時には、利用状況テレメトリの収集について通知します。既存の .NET CLI と同じ `DOTNET_CLI_TELEMETRY_OPTOUT=1` 環境変数で送信を停止できます。プレビュー版を自動化環境へ導入する場合は、[公式のテレメトリ案内](https://aka.ms/dotnetup-telemetry)と組織のポリシーを合わせて適用できます。

## global.json をインストール要件へ変換するチャネルモデル

リポジトリの要件をインストール状態へ変える流れを確認します。次の `global.json` は、10.0.1xx 機能バンド内の最新パッチを許可します。

```json
{
  "sdk": {
    "version": "10.0.100",
    "rollForward": "latestPatch"
  }
}
```

リポジトリルートで `dotnetup sdk install` を実行すると、ツールは現在のディレクトリからファイルシステムのルートへ向かって、最も近い利用可能な `global.json` を探します。コマンドラインでチャネルを指定せず、利用できるファイルもない場合は `latest` を選択します。ファイルを見つけると、`sdk.version` と `rollForward` を次の規則でインストール要件へ対応付けます。

| `rollForward` | `10.0.103` から追跡する要件 |
| --- | --- |
| 省略または `latestPatch` | `10.0.1xx` |
| `latestFeature` | `10.0` |
| `latestMinor` | `10` |
| `latestMajor` | `latest` |
| `disable`、`patch`、`feature`、`minor`、`major` | 正確なバージョン `10.0.103` |

この対応付けは、.NET ホストがインストール済み SDK の一つを選ぶ規則とは目的が異なります。`dotnetup` はどのバージョンをインストールして継続的に追跡するかを決め、.NET ホストはインストール済み SDK のうち実行するものを選びます。[`global.json` の公式ドキュメント](https://learn.microsoft.com/dotnet/core/tools/global-json)は、SDK の選択とランタイムの対象指定を別の項目として説明しています。`dotnetup` の変換規則は、[リポジトリ連携ドキュメント](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/usecases/install-with-global-json.md)で確認できます。

今回の確認では、`dotnetup` が上記のファイルを読み取り、要件を `10.0.1xx` として記録して `10.0.111` を別のインストールルートへ配置しました。`dotnetup list` はインストール元として該当する `global.json` の絶対パスを表示し、インストールした `dotnet --version` は `10.0.111` を返しました。同じコマンドでも、別の日にはチャネルが指すバージョンが変わる可能性があります。

`--update-global-json` を追加すると、インストールした具体的なバージョンを `sdk.version` へ反映します。ほかのプロパティ、書式、検出したテキストエンコーディングは維持します。`sdk.paths` があるリポジトリでは、最初のパスをインストールルートとして使うこともできます。コマンドラインの `--install-path` が `sdk.paths` より優先されます。

## 最新 SDK と過去のランタイムの分離

SDK とランタイムを分けてインストールする理由を扱います。SDK はコンパイラ、MSBuild、CLI などの開発ツールを提供します。ランタイムはビルドしたアプリケーションやテストを実行します。最新の SDK で複数のターゲットフレームワークをビルドできても、各バージョンのテストを実行するには対応するランタイムが別途必要になる場合があります。

OD804 のデモでは、.NET 10 SDK で `net8.0`、`net9.0`、`net10.0` のテストをビルドした後、.NET 8 と .NET 9 のランタイムがないため二つのテストが開始できない状況を示しています。以前の SDK 全体を並べてインストールする代わりに、必要なランタイムだけを追加する方法を次のように実演しています。

```console
dotnetup runtime install 8.0 9.0 10.0
dotnetup runtime install aspnetcore@8.0 aspnetcore@10.0
dotnet --list-runtimes
```

バージョンだけを指定すると `Microsoft.NETCore.App` ランタイムを選択します。`aspnetcore@10.0` は ASP.NET Core ランタイムを選択し、Windows では `windowsdesktop@10.0` も利用できます。正確なランタイムバージョンを指定すると、固定要件として保存します。[コンポーネントのインストールドキュメント](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/usecases/install-components.md)が、現在サポートするコマンド形式を説明しています。

セッションで示した `global.json` 内のランタイム宣言は、将来の構想を説明するための仮想的な構文でした。現在のプレビュードキュメントは、`global.json` から SDK 要件だけを読み取ります。ランタイムは `dotnetup runtime install` へ直接指定します。[セッションのランタイムデモ](https://www.youtube.com/watch?v=ZMnyohA5yrw&t=1505s)でも、この構文が確定していないと説明しています。

## 要求状態と実際のインストールを分けるマニフェスト

インストール後の更新と整理の仕組みを確認します。`dotnetup` は、ユーザーが要求したチャネルとディスクへ配置した具体的なバージョンを分けて記録します。

| 状態要素 | 記録する内容 | 用途 |
| --- | --- | --- |
| インストール仕様 | コンポーネント、チャネルまたは正確なバージョン、要求元 | 更新範囲と固定要件かどうかの判断 |
| インストール項目 | 具体的なバージョン、アーキテクチャ、インストールルート、共有サブコンポーネント | ファイル検証と削除範囲の計算 |
| 環境構成 | `dotnet` のアクセスモードと `dotnetup` の `PATH` への追加状態 | シェルプロファイルと現在の設定の差を検出 |

状態を表示して更新する基本的な流れは次のとおりです。

```console
dotnetup list
dotnetup update
dotnetup list --format json
```

`dotnetup update` は各移動チャネルを再解決し、新しいバージョンをインストールします。正確なバージョン要件は処理を省略します。更新に成功すると、残っているインストール仕様が要求しなくなったバージョンと、ほかのインストール項目が共有しないサブコンポーネントをガベージコレクションで整理します。複数の要件が同じインストールを指す場合、ファイルは一つだけ保持します。[更新ドキュメント](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/usecases/update-installations.md)と[状態モデルのドキュメント](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/concepts/how-dotnetup-works.md)が、この動作を分けて説明しています。

OD804 は、ユーザーデータディレクトリのマニフェストを宣言したシステム状態に対するロックファイルに例えています。この比喩は、リポジトリへコミットする契約を意味しません。リポジトリの契約は `global.json` が担い、マニフェストは各コンピューターでインストール仕様と実際のファイルを結び付ける台帳に近いものです。ツールは、自身が記録した状態からマニフェストの内容が変わっていないかを検査するハッシュファイルも維持するため、状態ファイルを直接編集しません。

## 人と自動化が共有する開発用途の境界

同じインストール手順を人と自動化された実行主体が使える範囲を確認します。OD804 は `dotnetup` の主な利用者を開発者と自動化された実行主体に分けています。自動化には LLM ベースのコーディングエージェントだけでなく CI も含まれます。管理者権限を与えないサンドボックスでもリポジトリに合う SDK を準備でき、明示的なコマンドと JSON 出力から状態を読み取れるためです。

自動化では、対話的な初期設定に依存しない次の形式を利用できます。

```console
dotnetup sdk install 10.0.1xx --no-progress --interactive false
dotnetup dotnet test -- --logger trx
dotnetup list --format json --no-verify
```

`dotnetup` は CI またはリダイレクトされた出力を検出すると、初回利用時の案内を無効にします。`--no-progress` はターミナル向けの進行表示がログへ混ざることを防ぎ、`--interactive false` は入力待ちを止めます。記録済みファイルの存在と有効性を検査する自動化では、`--no-verify` を外します。詳しいオプションは[自動化ドキュメント](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/usecases/automation.md)で確認できます。

`dotnetup dotnet` は、管理対象となる既定のインストールルートの環境を子プロセスだけに適用します。以前に任意の `--install-path` で作成したインストールを自動では選択しません。カスタムルートでは、その中の `dotnet` 実行ファイルを直接呼び出すか、環境スクリプトで有効にします。この制約は[コマンドリファレンス](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/reference/dotnetup-dotnet.md)に記載されています。

`dotnetup dotnet` は、File-based App の実行経路としても利用できます。`env -S` をサポートする Unix 環境で `sample.cs` の先頭行を `#!/usr/bin/env -S dotnetup dotnet` とし、実行権限を付与すると、管理対象の SDK でファイルを直接実行できます。システムに `dotnetup` CLI を準備すれば、管理者権限のない環境でも同じ実行経路を構成できます。[dotnetdev 記事の追加例](https://forum.dotnetdev.kr/t/dotnetup-rustup-net-toolchain-manager/14805/2)が、この構成を示しています。

ツールの対象範囲は開発環境にとどまります。[セッションの利用対象に関する説明](https://www.youtube.com/watch?v=ZMnyohA5yrw&t=2055s)は、運用環境のフレームワーク依存展開ではオペレーティングシステムのパッケージマネージャーを使い、それ以外では自己完結型展開を選択する従来の方針を維持しています。展開形態によるランタイムの同梱範囲は、[.NET アプリケーションの発行概要](https://learn.microsoft.com/dotnet/core/deploying/)で区別できます。

## 現在のプレビューと OD804 ロードマップの差

OD804 で予告した機能の一部は現在のコマンド表面に入り、残りは公開ドキュメントでまだ確認できません。セッションは、内部プレビュー、公開プレビュー、GA 後の期間に分けて、日次ビルド、一つのコマンドで特定の SDK を選ぶ実行方法、自己更新、署名検証、エージェントスキル、CI プロバイダー統合を示しました。

| 項目 | 2026年8月22日の確認結果 |
| --- | --- |
| 安定版、LTS、プレビュー、日次ビルド、数値チャネル | SDK とランタイムのチャネルとして提供 |
| `global.json` 連携 | SDK バージョンと `rollForward`、`sdk.paths`、任意のファイル更新をサポート |
| SDK とランタイムのコンポーネント | インストール、更新、削除、一覧表示をサポート |
| 一つのコマンドでの実行 | `dotnetup dotnet` 転送コマンドを提供。特定の SDK バージョンをコマンドオプションで選ぶ機能は、このプレビューのヘルプでは確認できず |
| `dotnetup` の自己更新 | このプレビューの公開コマンド一覧では確認できず |
| `global.json` のランタイム宣言 | セッションの仮想構文にとどまり、現在のドキュメントは SDK 要件だけを説明 |
| エージェントスキルと CI プロバイダー統合 | セッションが示した長期的な方向であり、現在の公開利用ドキュメントでは確認できず |
| ダウンロード検証 | プレビューのインストールスクリプトは SHA-512 チェックサムを検証。日次ビルドはコード署名されていないと公式ドキュメントが明記 |

SHA-512 チェックサム検証とコード署名検証は、同じ保証を提供しません。現在の[開始ドキュメント](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/README.md)は、プレビューのインストールスクリプトによるチェックサム検証を案内しています。OD804 の[ロードマップ部分](https://www.youtube.com/watch?v=ZMnyohA5yrw&t=2539s)は、.NET SDK、ランタイム、`dotnetup` 自体の署名検証を公開プレビューの目標として説明しました。

日次ビルドのチャネルは `11.0.1xx-daily` のように、メジャーバージョン、機能バンド、プレビュー段階まで範囲を狭めて指定できます。[日次チャネルのドキュメント](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/channels/daily.md)は、サポート対象のリリースではなく、コード署名も行っていないと警告しています。長期間維持する開発環境より、短期間のテストに合う選択です。

現在のドキュメントは、[.NET SDK リポジトリ内の実装ドキュメント](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/index.md)として公開されています。公式概要も、配布方法が内部リリースごとに変わる可能性を明記しています。ブログのインストール例を後から再利用する場合、`dotnetup --version` と `dotnetup --help` を一緒に記録すると、その時点のコマンド表面を残せます。

## プレビュー導入前の確認項目

プレビューを導入する前に、[公式の開始ドキュメント](https://github.com/dotnet/sdk/blob/release/dnup/documentation/general/dotnetup/README.md)と対象環境の要件を基準として、次の手順を利用できます。

1. 公式の開始ドキュメントでインストール URL と対応オペレーティングシステムを再確認します。
2. 既存の `dotnet` を既定のまま維持する場合は Isolation Mode を選び、`dotnetup dotnet` で実行します。
3. リポジトリの `global.json` と `rollForward` がどのチャネルへ対応するかを記録します。
4. 移動チャネルが必要な環境と、正確なバージョン固定が必要なビルドを分けます。
5. 日次ビルドは別のインストールルートで短期間テストし、結果にバージョンを残します。
6. CI では進行表示と対話入力を無効にし、終了コードを検査します。
7. テレメトリを送信しない環境では `DOTNET_CLI_TELEMETRY_OPTOUT=1` を設定します。

## 開発環境の宣言とインストールを結ぶ dotnetup

ここまでをまとめると、`dotnetup` は開発環境における .NET SDK とランタイムの要求状態をインストール済みファイルへ結び付けます。`global.json` を新しい形式で置き換えず、リポジトリがすでに持つ宣言をインストールと更新の入力として利用します。SDK とランタイムをコンポーネントへ分けたコマンド体系は、複数ターゲットのテストや複数リポジトリを移動する作業で特に役立ちます。

長期的には、OD804 が示した自己更新、署名検証の拡大、エージェントスキル、CI 統合がツールの管理範囲を広げる可能性があります。すぐに影響する機能は、ユーザー権限でのインストール、`global.json` に基づく SDK の準備、ランタイムの分離インストール、追跡対象チャネルの一括更新です。プレビュー版と日次ビルドでは検証水準が異なるため、同じ信頼水準として扱いません。

複数の .NET リポジトリをローカルで扱う場合や、隔離したエージェントがビルド環境を準備する場合は、現在のプレビューを別のインストールルートで試す選択肢があります。オペレーティングシステムのパッケージポリシーが重要な運用サーバーでは、既存の展開方法を維持できます。チームが SDK バージョンを正確に固定する場合は正確なバージョンチャネルを使い、機能バンド内のパッチを追跡する場合は `global.json` の `rollForward` と `dotnetup` チャネルの対応を判断基準にできます。

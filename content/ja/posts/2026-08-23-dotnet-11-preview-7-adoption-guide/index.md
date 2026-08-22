---
title: "リリースを控えた .NET 11 の変更点と導入判断"
date: 2026-08-23T00:52:15+09:00
draft: false
slug: "dotnet-11-preview-7-adoption-guide"
tags:
  - .NET
  - .NET 11
  - C# 15
  - ASP.NET Core
  - Entity Framework Core
categories:
  - .NET 開発
translationKey: "dotnet-11-preview-7-adoption-guide"
description: ".NET 11 Preview 7 のサポート期間、ハードウェア基準、Runtime Async、C# 15、フレームワークの変更から導入判断の基準を整理します。"
cover:
  image: "images/posts/dotnet-11-preview-7-adoption-guide.webp"
  alt: "dotnet bot が半透明の数字11へ飛んでいく明るい紫色のイラスト"
tldr: ".NET 11 の導入判断では、STS のサポート期間より x86-64-v2 の基準、Runtime Async、SDK の既定動作、C# 15 の変更が大きく影響します。.NET 10 を運用中であれば、サポート期間ではなく新機能と検証コストを基準に比較できます。"
license: "CC BY-NC 4.0"
---

Microsoft は .NET 11 の正式版を 2026年11月10日にリリースする予定です。2026年8月23日現在、8月11日に公開された .NET 11 Preview 7 が最新ビルドです。Microsoft はランタイムと SDK、C# 15、ASP.NET Core、.NET MAUI、Entity Framework Core を含む製品群を引き続き調整しています。正式リリースまでに機能や動作が変わる可能性も残っています。[Microsoft による .NET 11 Preview 7 の発表](https://devblogs.microsoft.com/dotnet/dotnet-11-preview-7/)

この記事では .NET 11 の変更を、サポート期間、ハードウェア基準、ランタイムと開発ツール、C# 15、アプリケーションフレームワークという五つの軸で整理します。機能の数より、既存サービスの移行に影響する点を中心に扱います。

最初にサポート期間と実行環境を扱い、次に Runtime Async と SDK を確認します。その後で C# 15 の型モデルと ASP.NET Core、EF Core の主な機能を検討します。最後に正式リリース前に適用できる確認手順を示します。

この記事は、次の基準日に公開されていたプレビュー資料をもとに作成しました。

> 基準日: 2026年8月23日
>
> 対象バージョン: .NET 11 Preview 7、SDK 11.0.100-preview.7
>
> 状態: プレビュー機能と互換性変更の一覧は正式リリースまでに変わる可能性があります。プレビュービルドは一般に本番環境での利用をサポートしません。

## サポート期間を延ばさない STS リリース

.NET 11 のサポート期間から整理します。Microsoft は .NET 11 を STS に分類し、2026年11月10日から2028年11月9日までの2年間サポートする予定です。LTS と STS の品質水準は同じで、サポート期間だけが異なります。LTS は3年間、STS は2年間にわたってパッチと技術サポートを提供します。この予定は [.NET 11 のリリース計画](https://github.com/dotnet/core/blob/main/release-notes/11.0/README.md)と [.NET のサポートポリシー](https://dotnet.microsoft.com/en-us/platform/support/policy)で確認できます。

現行バージョンの予定を並べると、アップグレードの判断基準が見えてきます。

| バージョン | リリース種別 | 正式リリース日 | サポート終了日 |
| --- | --- | --- | --- |
| .NET 8 | LTS | 2023年11月14日 | 2026年11月10日 |
| .NET 9 | STS | 2024年11月12日 | 2026年11月10日 |
| .NET 10 | LTS | 2025年11月11日 | 2028年11月14日 |
| .NET 11 | STS | 2026年11月10日予定 | 2028年11月9日予定 |

.NET 10 LTS から .NET 11 へ移行しても、サポート終了日は延びません。現在の計画では、.NET 11 のサポートが5日早く終了します。.NET 10 を運用しているチームは、新機能、性能、開発体験が移行コストに見合うかを基準に判断できます。.NET 8 または .NET 9 を運用している場合は、両バージョンのサポートが .NET 11 のリリース予定日に終了するため、.NET 10 と .NET 11 を同時に候補として検討できます。

## 既存機器に影響するハードウェア基準

.NET 11 は、すべてのオペレーティングシステムで x86/x64 の JIT および AOT の最低基準を `x86-64-v1` から `x86-64-v2` へ引き上げます。`SSE3`、`SSSE3`、`SSE4.1`、`SSE4.2`、`POPCNT` などの命令をサポートしない CPU では .NET 11 アプリケーションを実行できません。[.NET 11 ランタイムの最低ハードウェア要件](https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-11/runtime#updated-minimum-hardware-requirements)

ReadyToRun の対象もオペレーティングシステムによって異なります。

| オペレーティングシステム | x86/x64 JIT および AOT の最低基準 | ReadyToRun の対象 |
| --- | --- | --- |
| macOS | `x86-64-v2` | `x86-64-v2` |
| Linux | `x86-64-v2` | `x86-64-v3` |
| Windows | `x86-64-v2` | `x86-64-v3` |

Linux と Windows の ReadyToRun 対象は `x86-64-v3` へ上がりますが、実行時の最低基準まで `v3` になるわけではありません。`v2` をサポートする機器でも実行できます。ただし、事前コンパイル済みのコードを利用できない部分では JIT コンパイルが増え、起動時間が長くなる可能性があります。

Arm64 では Apple と Linux の実行時最低基準を維持します。Windows Arm64 は `LSE` 命令を必須とし、ReadyToRun の対象を `armv8.2-a + RCPC` へ引き上げます。新しいクラウドインスタンスへの影響は限定的と考えられますが、古い社内サーバー、エッジ機器、顧客環境へインストールする製品は個別の確認対象です。

## 非同期実行と開発ツールの既定動作の変化

ランタイムと SDK の実行経路を確認します。Runtime Async は中断と再開の管理をランタイムへ移し、SDK は NativeAOT CLI と MSBuild サーバーを既定の経路に配置します。どちらもアプリケーションコードを大幅に変えなくても、実行とビルドの過程に影響する可能性があります。

### Runtime Async による非同期実行のランタイム移行

従来の C# コンパイラは `async` メソッドごとにステートマシンを生成します。Runtime Async V2 は中断と再開の状態をランタイムで管理します。Microsoft はこの構造によってライブコールスタックを簡潔にし、デバッグ体験と実行時オーバーヘッドを改善しようとしています。[.NET 11 Runtime Async の説明](https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-11/runtime#runtime-async)

アプリケーションコードで Runtime Async を試す場合は、プロジェクトファイルに次の設定を追加します。

```xml
<PropertyGroup>
  <Features>runtime-async=on</Features>
</PropertyGroup>
```

`net11.0` プロジェクトでは `EnablePreviewFeatures` を別途有効にしなくても、この機能を利用できます。.NET 11 のランタイムライブラリ自体も Runtime Async を適用してビルドされています。アプリケーションコードでは引き続き機能を明示的に有効化します。

公開された例では、ライブコールスタックからコンパイラのステートマシンフレームが減り、実際のメソッド呼び出し関係が把握しやすくなります。例外オブジェクトに記録されるスタックトレースは従来の方式でも整理されるため差はありません。NativeAOT と ReadyToRun も Runtime Async をサポートします。スループットと割り当て量の改善幅はアプリケーションの非同期呼び出しパターンによって変わるため、対象サービスの負荷試験結果を正式導入の判断材料にできます。

### 反復作業を減らす SDK とテストツール

Preview 7 は NativeAOT ベースの `dotnet` CLI 経路と MSBuild サーバーを既定で有効にしました。また、Microsoft.Testing.Platform を使用する `dotnet test` に、実行全体を制御するオプションを追加しました。[.NET 11 の SDK とツールの変更点](https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-11/sdk)

- **NativeAOT CLI 経路**: `dotnet --info`、ヘルプ、一部の `dotnet sln` コマンド、ツールの検索と実行は NativeAOT 経路を使用します。`build`、`run`、`test`、`pack`、`publish` のようにプロセス内で MSBuild または NuGet を利用するコマンドは、マネージド CLI へフォールバックします。

- **既定の MSBuild サーバー**: SDK はウォームアップ済みの MSBuild ワーカープロセスをコマンド間で維持します。連続する `dotnet build`、`dotnet test`、`dotnet run` では MSBuild の起動コストを削減できます。カスタムビルドタスクがプロセス分離を前提とする場合は、`DOTNET_CLI_USE_MSBUILD_SERVER=false` を指定して従来の動作と比較できます。

- **テスト実行ポリシー**: Microsoft.Testing.Platform モードでは、`dotnet test --timeout 90s` や `dotnet test --maximum-failed-tests 5` のようなオプションで実行全体の時間と失敗数を制限できます。`Microsoft.Build.Traversal` プロジェクトもテスト対象を集約して実行できます。

- **ローカルコンテナの選択**: SDK のコンテナ発行機能は Windows で `wslc`、macOS で `container` を優先します。Docker と Podman はフォールバック候補になります。特定のエンジンの動作に依存するビルド環境では、`LocalRegistry` プロパティで対象を固定できます。

これらの変更により、SDK だけを入れ替えた比較試験でも、ビルド時間、プロセス数、カスタムタスクの状態維持を同時に記録すると原因を切り分けやすくなります。

## 閉じた型集合を表現する C# 15

C# 15 の型モデルの変更を確認します。このバージョンには、コレクション式の引数、ユニオン型、閉じた階層、拡張インデクサ、ラベル付き `break` と `continue`、メモリ安全性に関する作業が含まれます。ユニオン型と閉じた階層により、コンパイラは取り得る型の集合を把握し、`switch` の網羅性を検査できます。[C# 15 の新機能](https://learn.microsoft.com/en-us/dotnet/csharp/whats-new/csharp-15)

ユニオン型で決済結果を表現すると、次のようにすべてのケースを分けられます。

```csharp
public record Paid(string TransactionId);
public record Declined(string Reason);
public record Pending(DateTimeOffset RetryAt);

public union PaymentResult(Paid, Declined, Pending);

static string Describe(PaymentResult result) => result switch
{
    Paid paid => $"승인: {paid.TransactionId}",
    Declined declined => $"거절: {declined.Reason}",
    Pending pending => $"재시도: {pending.RetryAt:O}",
};
```

`closed` 修飾子は、同じアセンブリ内でのみ直接派生型を宣言できるようにします。コンパイラがすべての直接派生型を把握できるため、既定の分岐がない `switch` でも網羅性を検査します。閉鎖性は下位階層全体へ自動的に伝播しません。中間型の下まで制限する場合は、その型にも `closed` を指定します。

ユニオン型仕様の一部は Preview 7 でもまだ実装されていません。メモリ安全性の改善も複数のリリースにわたって進める予定です。C# 15 の機能を製品コードへ反映する場合は、現在の構文を最終仕様とみなさず、正式版のコンパイラと互換性ドキュメントを改めて比較できる余地を残します。

## アプリケーション層で見えるライブラリとフレームワークの変化

アプリケーション層の改善はワークロードごとに分けて確認します。.NET 11 の基本ライブラリは、プロセス実行、圧縮、シリアル化、診断、数値演算の範囲を広げます。ASP.NET Core と EF Core もサーバーリソース管理とクエリ変換を改善します。[.NET 11 の変更点の概要](https://learn.microsoft.com/en-us/dotnet/core/whats-new/dotnet-11/overview)

- **基本ライブラリ**: `Process` に実行と出力収集を扱う API が追加されます。`System.IO.Compression` は Zstandard 圧縮、ZIP パスワード、CRC32 検証をサポートします。`System.Text.Json` は C# ユニオン型のシリアル化と閉じた型階層のポリモーフィズム推論をサポートします。IEEE 754 の10進浮動小数点型とジェネリックな `Complex<T>` も数値処理の範囲を広げます。[.NET 11 Preview 7 ライブラリリリースノート](https://github.com/dotnet/core/blob/main/release-notes/11.0/preview/preview7/libraries.md)

- **ASP.NET Core**: Blazor Interactive Server は、非表示のブラウザタブにあるサーキットを一定時間後に停止し、ユーザーが戻ると再開できます。この機能は別パッケージと設定で有効にします。Preview 7 には Blazor SSR の出力キャッシュ、検証メッセージのローカライズ、OpenAPI 3.2 による Server-Sent Events の表現も含まれます。[ASP.NET Core Preview 7 リリースノート](https://github.com/dotnet/core/blob/main/release-notes/11.0/preview/preview7/aspnetcore.md)

- **Entity Framework Core**: SQL Server プロバイダーは `int.Parse` と複数の数値解析メソッドをサーバー側の `CAST` に変換します。参照ナビゲーションをたどる `GroupBy` 集計は、相関サブクエリではなく一つの結合とグループ化へ変換できます。既存クエリの SQL 形式が変わる可能性があるため、実際のデータ分布で実行計画と処理時間を比較できます。[EF Core Preview 7 リリースノート](https://github.com/dotnet/core/blob/main/release-notes/11.0/preview/preview7/efcore.md)

すべてのアプリケーションが各機能を同じ割合で利用するわけではありません。圧縮ファイルを交換するサービスは ZIP の検証動作から確認できます。Blazor Server のサービスはサーキット停止がメモリ使用量に与える影響を測定できます。データアクセスの比重が大きいサービスは、EF Core が生成した SQL を以前のバージョンと比較する方法で範囲を絞れます。

## 正式リリース前の確認項目

正式リリース前の検証手順を確認します。Microsoft が公開している [.NET 11 の互換性変更一覧](https://learn.microsoft.com/en-us/dotnet/core/compatibility/11)はまだ作成中で、完全な一覧ではありません。そのため、Preview 7 の試験結果と正式版の結果が同じだとは仮定しません。

1. 本番サーバー、ビルドエージェント、顧客環境の機器がサポートする CPU 命令セットを収集します。
2. 分離した試験環境で SDK `11.0.100-preview.7` を固定し、既存ソースのビルド警告とテスト結果を記録します。
3. MSBuild サーバーを有効にした状態と無効にした状態で、連続ビルド時間とカスタムタスクの動作を比較します。
4. 非同期呼び出しが多いサービスに限って Runtime Async を適用し、スループット、遅延、割り当て量、ライブコールスタックを従来方式と比較します。
5. ASP.NET Core と EF Core のアプリケーションでは、生成した OpenAPI ドキュメント、認証フロー、主要な LINQ クエリの SQL と実行計画を比較します。
6. 圧縮、証明書、ファイルとパイプ、ホスト終了動作に関する互換性変更を、各サービスが利用する機能と対応づけます。
7. RC と正式版が公開されたら、プレビューで使用した機能の状態と互換性一覧を改めて確認します。

## サポート期間より実行条件が先に見えるアップグレード

ここまで整理すると、.NET 11 は非同期実行構造、ハードウェア基準、型モデル、開発ツールの既定動作を同時に変更します。API の追加だけで判断するには、実行環境とビルド経路の変化が大きいリリースです。

Runtime Async と C# 15 が今後の .NET アプリケーションのコード生成と型設計へ与える影響は、長期的に確認する対象です。x86/x64 の最低基準引き上げ、MSBuild サーバーと NativeAOT CLI の既定有効化、一部ライブラリの動作変更は、すぐに影響する可能性があります。

.NET 8 または .NET 9 を運用するチームは、2026年11月10日のサポート終了に合わせて .NET 10 LTS と .NET 11 STS のどちらへ移行するかを選べます。.NET 10 をすでに運用している場合、サポート期間だけを理由に急ぐ余地は多くありません。古い機器や顧客環境へインストールする製品では CPU 基準から調査し、新しいクラウド環境と自動テスト基盤がある場合は Preview 7 で互換性情報を集める順序が適しています。

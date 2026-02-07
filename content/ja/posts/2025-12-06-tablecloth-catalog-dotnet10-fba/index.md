---
title: "TableClothカタログビルダー、.NET 10とFBAで現代化"
date: 2025-12-06T09:00:00+09:00
draft: false
slug: "tablecloth-catalog-dotnet10-fba"
tags:
  - TableCloth
  - .NET
  - オープンソース
  - C#
categories:
  - 開発
translationKey: "tablecloth-catalog-dotnet10-fba"
description: "TableClothプロジェクトのカタログビルダーが.NET 10にアップグレードされ、File-Based App（FBA）方式で簡素化されました。"
tldr: ".NET 10 FBAなら.csprojや.slnなしで単一.csファイルをdotnet run --fileでそのまま実行可能。Ctrl+Cの2段階ハンドラで安全に終了するGraceful Shutdownの実装も解説します。"
cover:
  image: "images/posts/tablecloth-catalog-dotnet10-fba.jpg"
  alt: "TableClothプロジェクト カタログビルダーアップデート"
---

## TableClothプロジェクトとは

[TableCloth](https://github.com/yourtablecloth)は、韓国のインターネットバンキング環境で必要なセキュリティプラグインをWindows Sandbox環境で安全に使用できるようにするオープンソースプロジェクトです。様々な金融機関のウェブサイトで要求されるセキュリティプログラムを隔離された環境で実行し、ホストシステムの安全を確保します。

## カタログリポジトリとは

[TableClothCatalog](https://github.com/yourtablecloth/TableClothCatalog)リポジトリは、TableClothプロジェクトで参照する金融機関サイト別のセキュリティプログラムリストを保管する保存場所です。銀行、証券会社、保険会社などのウェブサイトで要求されるセキュリティプラグイン情報が体系的に整理されており、カタログビルダーツールはこの情報を基にTableClothアプリで使用可能な形式に加工します。

## 最近のカタログビルダーアップデート

最近、このリポジトリに重要なアップデートが適用されました。今回のコミットでは、カタログビルダーツールが.NET 10にアップグレードされ、プロジェクト構造が大幅に簡素化されました。

### 主な変更点

#### .NET 10アップグレード

```yaml
# 変更前
dotnet-version: 8.0.x

# 変更後
dotnet-version: 10.0.x
```

ビルドパイプラインが.NET 8から.NET 10にアップグレードされました。これにより、最新ランタイムのパフォーマンス向上と新しい言語機能を活用できるようになりました。

#### File-Based App（FBA）方式への移行

最も目立つ変化はプロジェクト構造の簡素化です。従来は別途の`.csproj`プロジェクトファイルとソリューションファイル（`.sln`）を使用していましたが、今回のアップデートでこれらのファイルが削除され、単一のC#スクリプトファイル（`catalogutil.cs`）に統合されました。

```csharp
#!/usr/bin/env dotnet
#:package IronSoftware.System.Drawing@2025.9.3
#:property PublishAot=false

using SixLabors.ImageSharp;
using SixLabors.ImageSharp.Formats.Png;
using System.Collections.Concurrent;
// ...
```

これが.NETの**File-Based App（FBA）**方式です。FBAは以下のような利点を提供します：

- **プロジェクトファイル不要**：`.csproj`なしで単一の`.cs`ファイルでアプリケーション実行可能
- **インラインパッケージ参照**：`#:package`ディレクティブでNuGetパッケージを直接参照
- **インラインビルドプロパティ設定**：`#:property`ディレクティブでビルドプロパティを設定
- **シバン（Shebang）サポート**：`#!/usr/bin/env dotnet`でUnixスタイルの実行をサポート

#### Graceful Shutdownサポート

新しいバージョンでは、プロセス終了時により安定した処理が可能になりました：

```csharp
// Graceful shutdown タイムアウト
var gracefulShutdownTimeout = TimeSpan.FromSeconds(5);

Console.CancelKeyPress += (sender, e) =>
{
    if (cts.IsCancellationRequested)
    {
        // 2回目のCtrl+C：強制終了
        Console.Out.WriteLine("Info: Force exit requested. Terminating immediately...");
        e.Cancel = false;
        return;
    }

    Console.Out.WriteLine($"Info: Cancellation requested. Shutting down gracefully (timeout: {gracefulShutdownTimeout.TotalSeconds}s)...");
    Console.Out.WriteLine("Info: Press Ctrl+C again to force exit.");
    e.Cancel = true; // 即時終了を防止
    cts.CancelAfter(gracefulShutdownTimeout);
    cts.Cancel();
};
```

主な特徴：

- **1回目のCtrl+C**：Graceful shutdown開始（5秒タイムアウト）
- **2回目のCtrl+C**：即時強制終了
- **SIGINT標準終了コード（130）**を返却

#### ビルドプロセスの簡素化

```yaml
# 変更前：ビルド後に実行
- name: Build Catalog Builder Tool
  run: dotnet build src/TableCloth.CatalogBuilder/TableCloth.CatalogBuilder.csproj --configuration Release

- name: Run Catalog Builder Tool
  run: dotnet run --project src/TableCloth.CatalogBuilder/TableCloth.CatalogBuilder.csproj --configuration Release -- ./docs/ ./outputs/

# 変更後：直接実行
- name: Run Catalog Builder Tool
  run: dotnet run --file src/catalogutil.cs -- ./docs/ ./outputs/
```

FBA方式を使用することで、別途のビルド段階が不要になり、`dotnet run --file`コマンドで直接スクリプトを実行できるようになりました。

## 削除されたファイル

今回のアップデートで以下のファイルが削除されました：

- `src/TableCloth.CatalogBuilder/TableCloth.CatalogBuilder.csproj`
- `src/TableClothCatalog.sln`

また、`src/TableCloth.CatalogBuilder/Program.cs`が`src/catalogutil.cs`にリネームされ、内容が改善されました。

## まとめ

今回のアップデートは、.NETエコシステムの最新トレンドであるFBA方式を積極的に活用してプロジェクト構造を簡素化した好例です。特に小規模なユーティリティツールの場合、別途のプロジェクトファイルなしで単一スクリプトとして管理する方がはるかに効率的です。

TableClothプロジェクトに興味がある方は、[GitHubリポジトリ](https://github.com/yourtablecloth/TableCloth)をご覧ください。

## 参考リンク

- [TableClothプロジェクト GitHub](https://github.com/yourtablecloth)
- [TableClothCatalogリポジトリ](https://github.com/yourtablecloth/TableClothCatalog)
- [該当コミット](https://github.com/yourtablecloth/TableClothCatalog/commit/8edbd2e9ca9bef3085932d39e88703391126f04d)

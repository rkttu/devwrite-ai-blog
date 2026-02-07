---
title: "テーブルからカードへ：TableClothカタログUIの現代化"
date: 2025-12-08T00:00:00+09:00
draft: false
slug: "tablecloth-catalog-ui-refactoring"
tags:
  - TableCloth
  - オープンソース
  - C#
  - Web開発
  - XSL
  - Generic Host
categories:
  - 開発
translationKey: "tablecloth-catalog-ui-refactoring"
description: "TableClothカタログページがモダンなカードUIに刷新され、カテゴリフィルター機能が追加されました。Generic Hostパターンの適用と品質管理ツールも新たに導入されました。"
tldr: "TableClothカタログページがモダンなカードUIに刷新され、カテゴリフィルター機能が追加されました。Generic Hostパターンの適用と品質管理ツールも新たに導入されました。"
cover:
  image: "images/posts/tablecloth-catalog-ui-refactoring.jpg"
  alt: "TableClothカタログUIアップデート"
---

## はじめに

韓国でインターネットバンキングを利用したことがあれば、各種セキュリティプログラムのインストール要求に頷くことでしょう。ActiveXは姿を消しましたが、その代わりとなった数多くのセキュリティプラグイン—AhnLab Safe Transaction、TouchEn nxKey、Veraportなど—は依然として私たちのPCへのインストールを要求しています。

[TableCloth（食卓布）](https://yourtablecloth.app)プロジェクトは、これらのセキュリティプログラムをWindows Sandboxという隔離された環境で実行できるようにするオープンソースツールです。[TableClothカタログ](https://github.com/yourtablecloth/TableClothCatalog)は、どの金融サイトでどのセキュリティプログラムが必要かを整理したデータベースの役割を果たしています。

## 今回のアップデート概要

TableClothカタログプロジェクトに5件のコミットが適用されました。今回のアップデートは**フロントエンド**、**バックエンド**、**DevOps**の3つの領域にわたる総合的な改善です。

| 領域 | 変更内容 | 主要技術 |
| ------ | ---------- | ---------- |
| **フロントエンド** | カタログWebページの全面再設計 | カードUI、カテゴリフィルター、レスポンシブレイアウト |
| **バックエンド** | ビルドツールアーキテクチャのリファクタリング | Generic Host、依存性注入、構造化ロギング |
| **DevOps** | 品質管理自動化ツールの追加 | 画像検証、未使用リソース整理、ファビコン収集改善 |

各領域で何が変わったのか、なぜそのような決定を下したのか、詳しく見ていきます。

---

## フロントエンド：テーブルからカードへ

### なぜUIを変更する必要があったのか？

既存のカタログページは典型的なHTMLテーブル形式でした。カテゴリ、サービス名、必要なパッケージリストが行と列で整列された構造です。機能的には問題ありませんでしたが、いくつかの限界がありました。

まず、100を超えるサービスをスクロールしながら探す必要がありました。モバイル環境では横スクロールが発生してユーザビリティが低下し、視覚的な階層構造がないため情報の把握が困難でした。何より、カテゴリ別のフィルタリングができず、目的のサービスを素早く見つけることが難しい状況でした。

これらの問題を解決するため、カードベースのUIへの全面改編を決定しました。

### XSLトランスフォームで実装したレスポンシブカードUI

TableClothカタログの興味深い点は、データがXML形式で保存され、Webページが**XSLT（XSL Transformations）**を通じてレンダリングされることです。サーバーサイドのロジックなしに、ブラウザが直接XMLをHTMLに変換します。

#### デザイントークンシステムの導入

モダンなCSS設計の核心は**デザイントークン**です。色、間隔、影などをCSS変数として定義することで、一貫性のあるデザインを維持しながらメンテナンスが容易になります。

```css
:root {
    /* カラーパレット */
    --primary-color: #2563eb;
    --primary-hover: #1d4ed8;
    --bg-color: #f8fafc;
    --card-bg: #ffffff;
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --border-color: #e2e8f0;
    
    /* シャドウ */
    --shadow: 0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
    
    /* レイアウト */
    --radius: 12px;
}
```

このカラースキームはTailwind CSSのデフォルトパレットからインスピレーションを得ています。スレート系のテキストカラーとブルー系のアクセントカラーを組み合わせることで、クリーンかつプロフェッショナルな印象を与えることができます。

### CSS Gridで実装したレスポンシブレイアウト

カードレイアウトの核心はCSS Gridの`auto-fill`と`minmax()`の組み合わせです：

```css
.services-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 1.25rem;
}
```

この1行のCSSで次のことを達成しています。画面幅に応じて列数が自動調整され、各カードは最小340pxを維持しながら利用可能なスペースで均等に配分されます。カード間の間隔は20pxで一貫して維持されます。

340pxという最小幅は、モバイル環境（約375px）でも単一列できれいに表示されるよう計算された値です。

### マイクロインタラクションで生動感を付与

静的なカードよりも、ユーザーのインタラクションに反応するカードの方が魅力的です：

```css
.service-card {
    transition: transform 0.2s, box-shadow 0.2s;
}

.service-card:hover {
    transform: translateY(-4px);
    box-shadow: var(--shadow-lg);
}
```

マウスをホバーするとカードが少し浮き上がるエフェクトです。0.2秒のトランジション時間はスムーズでありながら遅延なく反応する感覚を与えます。4pxの上昇距離は微妙ですが確実に認識できるレベルです。

## JavaScriptカテゴリフィルターの実装

100を超えるサービスの中から目的のものを見つけるには、フィルタリングが必須です。シンプルなバニラJavaScriptで実装しました：

```javascript
function filterCards(category) {
    const cards = document.querySelectorAll('.service-card');
    const buttons = document.querySelectorAll('.filter-btn');
    
    // ボタン状態の更新
    buttons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    // カードのフィルタリング
    cards.forEach(card => {
        if (category === 'all' || card.dataset.category === category) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}
```

核心は各カードに`data-category`属性を付与することです。XSLでは次のように生成されます：

```xml
<div class="service-card" data-category="{@Category}">
```

このアプローチにはいくつかの利点があります。クライアント側で即座にフィルタリングするため、サーバーリクエストが不要です。シンプルなトグル機能なので、複雑なURL状態管理も必要ありません。また、JavaScriptが無効な環境でもすべてのカードがそのまま表示され、プログレッシブエンハンスメント（Progressive Enhancement）の原則に従っています。

### カテゴリ別の視覚的区別

各カテゴリに固有の色バッジを付与しました：

```css
.category-Banking { background: #dbeafe; color: #1e40af; }
.category-CreditCard { background: #fce7f3; color: #9d174d; }
.category-Government { background: #d1fae5; color: #065f46; }
.category-Financing { background: #fef3c7; color: #92400e; }
.category-Insurance { background: #e0e7ff; color: #3730a3; }
.category-Education { background: #f3e8ff; color: #6b21a8; }
.category-Security { background: #fee2e2; color: #991b1b; }
.category-Other { background: #f1f5f9; color: #475569; }
```

色の選択には意味を込めています。銀行（Banking）には信頼と安定を象徴するブルーを、カード（CreditCard）には決済と関連したピンク/マゼンタを適用しました。公共機関（Government）には公共性を表すグリーンを、金融（Financing）にはお金を連想させるアンバーを使用しました。保険（Insurance）には保護を意味するインディゴを、セキュリティ（Security）には注意と警告を示すレッドを配置しました。

---

## バックエンド：Generic Hostパターンでリファクタリングしたビルドツール

UIの改善とともに、バックエンドツールである`catalogutil.cs`も大幅にリファクタリングされました。核心は.NETの**Generic Host**パターンの適用です。

### Generic Hostとは？

Generic Hostは.NETでアプリケーションのライフサイクル、依存性注入、構成、ロギングなどを管理するフレームワークです。元々ASP.NET Core Webアプリケーションで使用していたパターンですが、.NET Core 3.0からコンソールアプリやバックグラウンドサービスでも活用できるようになりました。

```csharp
// Generic Hostの設定
var builder = Host.CreateApplicationBuilder(args);

// 構成からタイムアウト値を読み取り
const double DefaultTimeoutSeconds = 15d;
const double MinTimeoutSeconds = 5d;
var configuredTimeout = builder.Configuration.GetValue("TimeoutSeconds", DefaultTimeoutSeconds);
var timeoutSeconds = Math.Max(configuredTimeout, MinTimeoutSeconds);

// サービス登録（依存性注入）
builder.Services.AddSingleton<CatalogLoader>();
builder.Services.AddSingleton<ImageConverter>();
```

### なぜコンソールアプリにGeneric Hostを？

「単純なビルドスクリプトにこのような複雑なパターンが必要なのか？」と問うことができます。しかし、Generic Hostが提供する利点は明確です：

#### **依存性注入（DI）**

```csharp
// コンストラクタ注入で依存性を明示
public class CatalogLoader
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<CatalogLoader> _logger;
    
    public CatalogLoader(HttpClient httpClient, ILogger<CatalogLoader> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
    }
}
```

DIを使用すると、クラス間の結合度が低くなり、テストが容易になり、依存性が明示的になります。

#### **構成管理**

```csharp
// appsettings.jsonまたは環境変数から設定を読み取り
var timeout = builder.Configuration.GetValue("TimeoutSeconds", 15d);
```

ハードコードされた値の代わりに外部構成を使用すると、環境ごとに異なる設定を適用できます。

#### **構造化ロギング**

```csharp
_logger.LogInformation("Processing service: {ServiceName}", service.Name);
```

構造化ロギングは、ログを単純な文字列ではなく検索可能なデータに変換します。

---

## DevOps：品質管理の自動化とファビコン収集の改善

### ファビコン収集機能の改善

カタログの各サービスにアイコンを表示するには、該当Webサイトのファビコンを収集する必要があります。今回のアップデートでファビコン収集ロジックが大幅に改善されました。

### Webアプリマニフェストのサポート

現代のWebサイトは`manifest.json`（または`manifest.webmanifest`）を通じてアプリアイコンを定義しています：

```json
{
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192" },
    { "src": "/icons/icon-512.png", "sizes": "512x512" }
  ]
}
```

新バージョンではHTMLの`<link rel="manifest">`タグをパースしてマニフェストファイルを見つけ、その中のアイコン情報を抽出します。

### フォールバック戦略

1つの方法でファビコンが見つからない場合、次の方法を試行します：

1. **Webアプリマニフェスト**：`manifest.json`のicons配列
2. **Linkタグ**：`<link rel="icon">`または`<link rel="shortcut icon">`
3. **デフォルト位置**：`/favicon.ico`
4. **外部サービス**：Google Faviconサービスなどへのフォールバック

このような多重フォールバック戦略により、ほとんどのWebサイトからアイコンを正常に取得できます。

### 画像品質管理の自動化

オープンソースプロジェクトでデータ品質管理は常に課題です。今回追加された品質管理ツールは、複数の検証作業を自動で実行します。

まず、画像整合性検証機能があります。カタログに登録されたすべてのサービスのアイコンファイルが実際に存在するか確認し、破損しているかロードできない画像を検出します。PNGフォーマットの有効性も併せて検査します。

次に、未使用リソース整理機能があります。

```text
⚠️  Orphan image found: images/Banking/OldBank.png
    → This image is not referenced by any service in the catalog
```

サービスが削除されたが画像が残っている場合を自動検出します。

---

## おわりに

今回のアップデートは単なる「きれいなUI」への変更ではありません。ユーザーが目的のサービスを素早く見つけられるようUXを改善し、開発者がプロジェクトをメンテナンスしやすいようコード品質を高め、データの整合性を自動で検証するシステムを構築しました。

オープンソースプロジェクトの価値は、コードの一行一行に込められた細やかな配慮から生まれます。TableClothプロジェクトに興味があれば、直接カタログページを訪問するか、GitHubでコードをご覧ください。

## 参考リンク

- [TableClothカタログ GitHub](https://github.com/yourtablecloth/TableClothCatalog)
- [TableClothプロジェクトホームページ](https://yourtablecloth.app)
- [TableClothカタログWebページ](https://yourtablecloth.app/TableClothCatalog/)
- [.NET Generic Host公式ドキュメント](https://learn.microsoft.com/dotnet/core/extensions/generic-host)

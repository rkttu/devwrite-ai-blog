---
title: "AIが見たことのない.NET UIフレームワークでIDEを作るとき、エージェントはどうやってAPIを把握するのか"
date: 2026-02-08T00:00:00+09:00
draft: false
slug: "why-i-use-handmirror-mcp"
tags:
  - .NET
  - MCP
  - AIエージェント
  - NuGet
  - IDE
  - オープンソース
categories:
  - AIツール活用
translationKey: "why-i-use-handmirror-mcp"
description: "AIの学習データにない新生.NET UIフレームワークでIDE開発時、HandMirror MCPでアセンブリを直接検査し、初回ビルドエラーを3個に押さえた経験を共有します。"
cover:
  image: "images/posts/why-i-use-handmirror-mcp.webp"
  alt: "虫眼鏡でコードを検査するコンセプトイメージ"
tldr: "HandMirror MCPでNuGetパッケージのコンパイル済みアセンブリを直接検査すれば、AIが学習したことのない新生フレームワークでも正確なAPIシグネチャを把握でき、初回ビルドエラーを3個まで削減できます。"
---

> 2026-02-08 — LibraStudio開発記 #1

---

## 背景

### なぜまた別の.NET IDEなのか

.NETエコシステムにおけるIDEの選択肢は、実はそれほど広くありません。Visual Studioは強力ですがWindows専用であり、Community Editionでさえ商用利用に制約があります。VS Code + C# Dev Kitの組み合わせも優れていますが、C# Dev Kitがプロプライエタリライセンスである点は変わりません。結局、重要な部分でベンダーロックインが発生し、その上に構築したツールチェーンとワークフロー全体が特定ベンダーの意思決定に依存してしまいます。

かつてはSharpDevelopがWindowsで、MonoDevelop（Xamarin Studio）がクロスプラットフォームでその役割を担っていました。しかしSharpDevelopは2017年に開発が停止し、MonoDevelopはXamarinに統合された後、事実上スタンドアロンIDEとしての役目を終えました。それ以降、最新の.NET（Core以降）開発環境を適切にサポートする**オープンソースでリベラルライセンスのクロスプラットフォームIDE**は登場していません。

この点がずっと惜しいと感じていました。そこでLibraStudioを始めました。ElectronやVS Codeベースではなく、純粋な.NETネイティブIDEを目指します。一人でVisual Studioレベルのものを作ろうというわけではありません。しかし2026年にはAIベースのコードエディタの力を借りることができます。AIエージェントにフレームワークAPIの探索、ボイラープレートの生成、繰り返しの実装を委任すれば、一人でカバーできる範囲は過去とはまったく異なります。

UIフレームワークには[Aprillz.MewUI](https://github.com/aprillz/MewUI)を使用しています。NativeAOTに対応し、XAMLなしでC#コードだけでUIを構築する軽量フレームワークです。このフレームワークは、私と同じく韓国の代表的な.NET開発者コミュニティであるDotNetDev（.NET Dev、<https://forum.dotnetdev.kr/>）で活動しているソン・ヨンジェ氏のオープンソースプロジェクトです。

### AIが知らない新生フレームワークという難関

MewUIはまったく新しいコンセプトの新生UIフレームワークです。XAMLベースのWPFやAvaloniaUIとは異なり、純粋なC# fluent APIでUIを構築する独自の設計を持っています。当然、公式ドキュメントが豊富ではなく、Stack Overflowに関連する質問が蓄積されてもいません。

これに.NETというプラットフォーム自体の問題も重なります。大規模言語モデルの学習データにおいて、.NET/C#はJavaScriptやPythonに比べて相対的に学習頻度が低いです。メジャーフレームワークであるWPFやWinFormsでさえ不正確なコードを生成することがあるのに、学習データにほとんど含まれていないMewUIのAPIを正確に当てる可能性は極めて低いです。

このような状況でAIコーディングエージェントに「最小限のタブベースのテキストエディタを作ってください」と依頼すると、何が起こるでしょうか。

---

## 一般的なアプローチ：推測と反復

通常のAIコーディングエージェントのワークフローは次のとおりです：

1. 学習データから類似のAPIを思い出してコードを書きます
2. ビルドします
3. エラーが出たらエラーメッセージを見て修正します
4. 2〜3を繰り返します

この方式は、学習データに豊富に含まれているメジャーフレームワーク（WPF、React、SwiftUIなど）ではうまく機能します。しかし、MewUIのようにまったく新しいコンセプトの新生フレームワーク――しかも相対的に学習頻度が低い.NETベース――では、**推測の精度が極めて低くなります**。メソッド名、パラメータの順序、オーバーロードの有無、イベントシグネチャ――すべてが外れる可能性があります。

---

## 別のアプローチ：アセンブリを直接覗く

今回の作業では[HandMirror MCP](https://github.com/pjmagee/handmirror-mcp)を使用しました。HandMirrorは、NuGetパッケージの**コンパイル済みアセンブリを直接検査する**MCP（Model Context Protocol）サーバーです。

Webドキュメントを検索する代わりに、実際の`.dll`を分析し、次の情報を返します。注目すべきは、HandMirrorが一般的な.NETリフレクション（`System.Reflection`）ではなく[Mono.Cecil](https://github.com/jbevain/cecil)を使用している点です。Cecilは.NETアセンブリのメタデータをランタイムロードなしに直接読み取るため、検査対象アセンブリの.NETランタイムバージョンに影響されません。.NET Framework 4.x用ライブラリでも.NET 10対象でも同様に分析できます：

- すべての名前空間と型の一覧
- 各型のコンストラクタ、プロパティ、メソッド、イベントのシグネチャ
- Extension methodがどの名前空間にあるか
- 継承階層構造

### 実際に得られた情報

`Aprillz.MewUI v0.9.1`を検査した結果：

- **178個のパブリック型**、14個の名前空間
- `MultiLineTextBox`が`TextBase`を継承し、`Text`、`Placeholder`、`AcceptTab`、`Wrap`、`IsReadOnly`などのプロパティを持つこと
- `TabControl.SelectionChanged`が`Action<int>`であること（ドキュメントがなければ`Action<TabItem>`と推測していたでしょう――実際そうでした）
- `FileDialog.OpenFile()`が`OpenFileDialogOptions`を受け取り、`Title`、`Filter`、`Owner`などのプロパティを持つこと
- `Menu.Item()`と`ContextMenu.Item()`のオーバーロードが異なること――`Menu.Item`にはショートカット文字列パラメータがない
- `ObservableValue<T>`が`Subscribe()`、`NotifyChanged()`、`Set()`メソッドを持つこと

この情報だけで、エディタのコアコードをほぼ正確に記述できました。

---

## 結果：初回ビルドでエラー3個

コード全体を書き上げた後、初回ビルドで発生したエラーはわずか3個でした：

| エラー | 原因 |
| ------ | ---- |
| `Menu.Item("text", "shortcut", action)` — オーバーロードなし | `ContextMenu.Item`にしかないショートカットパラメータを`Menu.Item`でも使用 |
| `BorderThickness(0, 1, 0, 0)` — 4パラメータのオーバーロードなし | 実際には`BorderThickness(double)`の単一パラメータのみ存在 |
| `SelectionChanged`の型不一致 | HandMirrorが`Action<int>`と教えてくれたが、コードで誤って`Action<TabItem>`を使用 |

3つ目は純粋に**読み取った情報をコードに誤って反映したミス**でした。HandMirrorが提供した情報自体は正確でした。

3つのエラーを修正した後、ビルド成功、アプリが正常に実行されました。

---

## HandMirrorなしだったら？

比較のため、HandMirrorなしで同じ作業を行った場合のシナリオを推定してみます：

1. `MultiLineTextBox`というコントロールが存在することはAGENTS.mdに明記されているので分かる
2. しかしfluent APIの正確なメソッド名は？`BindText`なのか`SetText`なのか`TextBinding`なのか？
3. `FileDialog` APIがあるのか、あるならどのような形か？
4. `TabControl`のイベントシグネチャは？
5. `ObservableValue<T>`のサブスクリプションメカニズムは？

これらすべてで**推測→ビルド→エラー→修正**の繰り返しが必要になっていたでしょう。178個の型にわたるAPI表面を試行錯誤で探索するのは非効率的です。

---

## まとめ

### 1. 「AIが学習したことのないフレームワーク」はAIエージェントの弱点であり、ツールで克服可能な弱点です

大規模言語モデルは学習データにあるものをよく記憶しています。学習頻度が高いJavaScript/Pythonエコシステムのフレームワークであれば、かなり正確なコードを生成します。しかし.NETのように相対的に学習頻度が低いプラットフォームの、それもまったく新しい新生フレームワークの場合は？推測するしかなく、推測は高い確率で誤ります。しかし**実際のバイナリを検査するツール**があれば、この弱点は相殺されます。

### 2. 正確な情報を得ても、ミスは発生します

HandMirrorが`SelectionChanged`の型が`Action<int>`であることを正確に教えてくれましたが、コーディング中に`Action<TabItem>`と誤って入力してしまいました。ツールが提供する情報の正確さと、その情報をコードに反映する正確さは別の問題です。

### 3. MCPエコシステムの力

HandMirrorはMCP（Model Context Protocol）サーバーとして実装されています。このプロトコルのおかげで、AIエージェントは**学習時点では存在しなかった知識**をランタイムに動的に取得できます。これは単なるツールではなく、AIエージェントの能力の境界を拡張するインフラです。

現在HandMirrorは.NETアセンブリに特化していますが、今後は必要に応じた拡張も検討中です。例えば[IKVM](https://github.com/ikvmnet/ikvm)を活用したJavaの`.class`/`.jar`ファイル検査や、ネイティブライブラリのシンボルテーブル分析など――.NETエコシステム外のAPI表面までAIエージェントが探索できるようになれば、多言語ランタイム上で動作するプロジェクトでも同じ方式で正確なコードを生成できるようになるでしょう。

### 4. AIエージェントとともにあれば、個人開発の限界が変わります

SharpDevelopやMonoDevelopのようなプロジェクトは、数十人のコントリビューターが数年かけて作り上げました。2026年にはAIエージェントがAPI探索、ボイラープレート生成、繰り返し実装を担当してくれます。アーキテクチャの決定と品質判断は依然として人間の役割ですが、コードを物理的にタイピングするボトルネックは大幅に減少しました。オープンソースIDEという夢が、一人のサイドプロジェクトとしても始められるようになったのです。

---

## 作ったもの

HandMirror MCPのアシストにより、MewUIベースの最小限のテキストエディタを構築でき、以下の画像のようなスケルトンが整いました。

![LibraStudio WIP - テキストエディタ](image.png)

LibraStudioはApache License 2.0の下で開発中です。© 2026 rkttu

```text
src/LibraStudio.Common/         # ファイル I/O ユーティリティ
src/LibraStudio.Editor/         # エディタ タブモデル + タブマネージャー
src/LibraStudio.Shell/          # メニューバー、ステータスバー、キーボードショートカット統合
```

機能：

- `MultiLineTextBox`ベースのタブエディタ（Consolas、等幅フォント）
- ファイルメニュー：New / Open / Save / Save As / Close Tab / Exit
- キーボードショートカット：`Ctrl+N`、`Ctrl+O`、`Ctrl+S`、`Ctrl+Shift+S`、`Ctrl+W`
- OSネイティブファイルダイアログ（Win32）
- 変更検知（dirtyステート）→ タブヘッダーに`•`表示
- タブを閉じる際の保存確認ダイアログ
- ステータスバーに現在のファイルパスを表示

構文ハイライトはまだなく、行番号もなく、検索・置換もありません。しかし、**ファイルを開き、編集し、保存できる**最小限のテキストエディタとして動作します。

---

## 技術スタック

| 項目 | 値 |
| ------ | ----- |
| 言語 | C# 13 / .NET 10 |
| UI | Aprillz.MewUI 0.9.1 |
| グラフィック | Direct2D (Windows) |
| テーマ | Dark + Blue accent |
| ビルド | NativeAOT対象 (`PublishAot=true`) |
| AIツール | GitHub Copilot (Claude) + HandMirror MCP |

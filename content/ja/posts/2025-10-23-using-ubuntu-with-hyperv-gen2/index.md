---
title: "Windows 10/11 ProでHyper-V第2世代VMからUbuntuを起動する方法"
date: 2025-10-23T00:00:00+09:00
draft: false
slug: "using-ubuntu-with-hyperv-gen2"
tags:
  - Hyper-V
  - Ubuntu
  - 仮想化
  - Windows
categories:
  - 開発環境
translationKey: "using-ubuntu-with-hyperv-gen2"
cover:
  image: "images/posts/using-ubuntu-with-hyperv-gen2.jpg"
  alt: "サーバー仮想化環境のイメージ"
description: "Hyper-V第2世代VMでUbuntuが起動しない場合は、セキュアブートテンプレートを「Microsoft UEFI証明機関」に変更してください。"
tldr: "Hyper-V第2世代VMでUbuntuが起動しない場合は、セキュアブートテンプレートを「Microsoft UEFI証明機関」に変更してください。"
---

## はじめに

Windows Proには標準でHyper-Vが含まれています。別途仮想化ソフトウェアをインストールしなくても、OS内で直接仮想マシンを作成・管理できます。この記事では、Hyper-Vの第2世代（Generation 2）仮想マシンを使用してUbuntuを起動する方法をご紹介します。

まず、管理者権限でPowerShellを開き、次のコマンドを入力してHyper-V機能を有効にします。

```powershell
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
```

インストールが完了したら、システムを再起動してください。

次に「Hyper-Vマネージャー」を起動し、新しい仮想マシンを作成します。世代は必ず「第2世代（Generation 2）」を選択し、メモリは4GB以上、ディスクは20GB以上を指定してください。

ネットワークアダプターは「既定のスイッチ（Default Switch）」を選択すれば、追加設定なしですぐにインターネット接続が可能です。

次に、[Ubuntu公式サイト](https://ubuntu.com/download/desktop)からISOイメージをダウンロードし、仮想マシンのDVDドライブ→「イメージファイル」に接続します。ファームウェア設定でDVDドライブを起動順序の一番上に移動させれば、ISOから直接起動できます。

## 重要なポイント

ここまでは一般的な手順です。しかし、実際にUbuntuをインストールしようとすると、「No bootable device」や「Start boot option」などのエラーが発生し、起動できないことがよくあります。

**その理由は簡単です。Hyper-Vの第2世代VMは、デフォルトでWindows専用のUEFIセキュアブートテンプレートを使用しているからです。**

この問題を解決するには、仮想マシンを作成した後、必ず「設定→セキュリティ」に移動してください。

ここで**「セキュアブートを有効にする（Enable Secure Boot）」**にチェックを入れ、下の「テンプレート」オプションを**「Microsoft UEFI証明機関（Microsoft UEFI Certificate Authority）」**に変更してください。
この設定が正しく行われていないと、Ubuntuのブートローダーが署名されていないイメージとして認識され、UEFIによって起動がブロックされます。
つまり、ISOファイルやディスク構成をいくら作り直しても、この設定がなければUbuntuは絶対に起動しません。

上記の手順を完了すると、Ubuntuのインストール画面が正常に表示され、案内に従ってインストールを進めることができます。

Ubuntu 20.04以降のバージョンには、Hyper-V統合サービスがデフォルトで含まれているため、追加のドライバーをインストールしなくても、クリップボード共有、画面解像度の自動調整、時刻同期などの機能がすぐに動作します。

結論として、Hyper-V第2世代VMでUbuntuを起動するには、「セキュアブートテンプレート」を必ずMicrosoft UEFI証明機関に設定する必要があります。

この1つの設定さえ忘れなければ、Windows Pro環境でも安定してUbuntuを実行し、開発環境を構築することができます。

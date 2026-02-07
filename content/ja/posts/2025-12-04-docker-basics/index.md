---
title: "Dockerコンテナの基礎"
date: 2025-12-05T12:00:00+09:00
draft: true
slug: "docker-basics"
tags:
  - Docker
  - コンテナ
  - DevOps
categories:
  - 開発環境
translationKey: "docker-basics"
description: "Dockerの基本概念を理解し、インストールから最初のコンテナ実行までをステップバイステップで学びます。"
tldr: "Dockerの基本概念を理解し、インストールから最初のコンテナ実行までをステップバイステップで学びます。"
cover:
  image: "images/posts/docker-basics.jpg"
  alt: "コンテナとサーバーインフラを象徴するイメージ"
---

Dockerは、アプリケーションをコンテナという隔離された環境で実行できるプラットフォームです。この記事では、Dockerの基本概念から最初のコンテナ実行までを解説します。

## Dockerとは？

Dockerはコンテナベースの仮想化プラットフォームです。従来の仮想マシン（VM）とは異なり、コンテナはホストOSのカーネルを共有するため、より軽量で高速です。

### コンテナ vs 仮想マシン

| 特性 | コンテナ | 仮想マシン |
|------|----------|------------|
| 起動時間 | 秒単位 | 分単位 |
| リソース使用量 | 少ない | 多い |
| 分離レベル | プロセスレベル | 完全なOSレベル |
| イメージサイズ | MB単位 | GB単位 |

## Dockerのインストール

### Windows

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/)をダウンロードします。
2. インストーラーを実行し、指示に従ってインストールします。
3. WSL 2バックエンドを有効にします。

### macOS

```bash
brew install --cask docker
```

### Linux (Ubuntu)

```bash
# リポジトリのセットアップ
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg

# DockerのGPGキーを追加
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Dockerをインストール
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io
```

## 最初のコンテナを実行

インストールが完了したら、最初のコンテナを実行してみましょう。

```bash
docker run hello-world
```

このコマンドは以下の処理を行います：

1. ローカルに`hello-world`イメージがあるか確認
2. なければDocker Hubからイメージをダウンロード
3. イメージからコンテナを作成して実行
4. メッセージを出力して終了

## よく使うDockerコマンド

```bash
# 実行中のコンテナ一覧
docker ps

# すべてのコンテナ一覧（停止中も含む）
docker ps -a

# イメージ一覧
docker images

# コンテナを停止
docker stop <container_id>

# コンテナを削除
docker rm <container_id>

# イメージを削除
docker rmi <image_id>
```

## 実践：Nginxウェブサーバーの実行

実用的なコンテナを実行してみましょう。Nginxウェブサーバーをコンテナで実行します。

```bash
docker run -d -p 8080:80 --name my-nginx nginx
```

- `-d`: バックグラウンドで実行（デタッチドモード）
- `-p 8080:80`: ホストの8080ポートをコンテナの80ポートにマッピング
- `--name my-nginx`: コンテナに名前を付ける

ブラウザで`http://localhost:8080`にアクセスすると、Nginxのウェルカムページが表示されます。

## 次のステップ

Dockerの基本を学んだら、次のトピックを学習してみてください：

- **Dockerfile**: カスタムイメージの作成
- **Docker Compose**: 複数コンテナの管理
- **Docker Volume**: データの永続化管理
- **Docker Network**: コンテナ間通信

Dockerを活用すれば、開発環境の構築とデプロイがより簡単になります。楽しいコンテナライフを！🐳

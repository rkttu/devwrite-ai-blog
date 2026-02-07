---
title: "Docker 컨테이너 기초"
date: 2025-12-05T12:00:00+09:00
draft: true
slug: "docker-basics"
tags:
  - Docker
  - 컨테이너
  - DevOps
categories:
  - 개발환경
translationKey: "docker-basics"
tldr: "Docker의 기본 개념을 이해하고, 설치부터 첫 번째 컨테이너 실행까지 단계별로 알아봅니다."
cover:
  image: "images/posts/docker-basics.jpg"
  alt: "컨테이너와 서버 인프라를 상징하는 이미지"
---

Docker는 애플리케이션을 컨테이너라는 격리된 환경에서 실행할 수 있게 해주는 플랫폼입니다. 이 글에서는 Docker의 기본 개념부터 첫 번째 컨테이너 실행까지 알아보겠습니다.

## Docker란?

Docker는 컨테이너 기반의 가상화 플랫폼입니다. 기존의 가상 머신(VM)과 달리, 컨테이너는 호스트 OS의 커널을 공유하므로 더 가볍고 빠릅니다.

### 컨테이너 vs 가상 머신

| 특성 | 컨테이너 | 가상 머신 |
|------|----------|-----------|
| 시작 시간 | 초 단위 | 분 단위 |
| 리소스 사용 | 적음 | 많음 |
| 격리 수준 | 프로세스 수준 | 완전한 OS 수준 |
| 이미지 크기 | MB 단위 | GB 단위 |

## Docker 설치

### Windows

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/)을 다운로드합니다.
2. 설치 파일을 실행하고 안내에 따라 설치합니다.
3. WSL 2 백엔드를 활성화합니다.

### macOS

```bash
brew install --cask docker
```

### Linux (Ubuntu)

```bash
# 저장소 설정
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg

# Docker GPG 키 추가
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Docker 설치
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io
```

## 첫 번째 컨테이너 실행

설치가 완료되었다면, 첫 번째 컨테이너를 실행해봅시다.

```bash
docker run hello-world
```

이 명령어는 다음 작업을 수행합니다:

1. 로컬에 `hello-world` 이미지가 있는지 확인
2. 없다면 Docker Hub에서 이미지 다운로드
3. 이미지로부터 컨테이너 생성 및 실행
4. 메시지 출력 후 종료

## 자주 사용하는 Docker 명령어

```bash
# 실행 중인 컨테이너 목록
docker ps

# 모든 컨테이너 목록 (중지된 것 포함)
docker ps -a

# 이미지 목록
docker images

# 컨테이너 중지
docker stop <container_id>

# 컨테이너 삭제
docker rm <container_id>

# 이미지 삭제
docker rmi <image_id>
```

## 실습: Nginx 웹 서버 실행

실제로 유용한 컨테이너를 실행해봅시다. Nginx 웹 서버를 컨테이너로 실행합니다.

```bash
docker run -d -p 8080:80 --name my-nginx nginx
```

- `-d`: 백그라운드에서 실행 (detached mode)
- `-p 8080:80`: 호스트의 8080 포트를 컨테이너의 80 포트에 연결
- `--name my-nginx`: 컨테이너 이름 지정

브라우저에서 `http://localhost:8080`에 접속하면 Nginx 환영 페이지가 표시됩니다.

## 다음 단계

Docker의 기본을 익혔다면, 다음 주제들을 학습해보세요:

- **Dockerfile**: 커스텀 이미지 만들기
- **Docker Compose**: 여러 컨테이너 관리하기
- **Docker Volume**: 데이터 영속성 관리
- **Docker Network**: 컨테이너 간 통신

Docker를 활용하면 개발 환경 구축과 배포가 훨씬 간편해집니다. 즐거운 컨테이너 라이프 되세요! 🐳

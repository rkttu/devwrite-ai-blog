---
title: "Edge0 연재 2: Microsoft Learn과 Apple Translation 실행 환경"
date: "2026-09-14T09:00:00+09:00"
draft: false
slug: "edge0-setup-microsoft-learn-translation"
translationKey: "edge0-setup-microsoft-learn-translation"
description: "Edge0 서버, Microsoft Learn CLI, Apple Translation을 연결할 실행 환경을 구성합니다. 가상 환경 재활성화, 번역 API 조건, 한국어 질문 정규화의 이유를 설명합니다."
tags: ["Edge0", "로컬 LLM", "RAG", "Apple Silicon", "Microsoft Learn"]
categories: ["인공지능"]
tldr: "Edge0-35B 서버와 Python 에이전트를 별도 터미널에서 실행하고 Microsoft Learn 검색과 온디바이스 번역을 연결합니다. 모델 경로, macOS 26.4 이상에서 사용하는 번역 API, 언어 리소스 설치와 한국어 간접 의문문 처리까지 준비합니다."
cover:
  image: "images/posts/edge0-setup-microsoft-learn-translation.webp"
  alt: "노트북 앞의 연산 장치, 문서 카드와 반투명 말풍선을 연결한 구성"
  caption: "글의 주제를 바탕으로 AI로 생성했습니다."
license: "CC BY-NC 4.0"
---

2026년 9월 13일 기준으로 이 연재의 샘플은 Edge0-35B, Microsoft Learn CLI, macOS Translation 프레임워크를 사용합니다. {{< series-link slug="edge0-16gb-mac-overview" text="1편" >}}에서 정한 역할 분담에 따라 추론 서버와 Python 에이전트 호스트를 별도 터미널에서 실행합니다.

이번 글은 Edge0와 모델 설치, 스트리밍 서버 실행, 공식 문서 검색, 한국어와 영어 번역, 질문 정규화를 다룹니다. 전체 파일은 [샘플 Gist](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)의 `README.md`, `apple_translate.swift`, `microsoft_expert_agent.py`에서 확인할 수 있습니다.

실행 조건과 설치 순서부터 살펴보겠습니다. 첫 번째 터미널에서 서버를 시작한 뒤 검색 도구와 번역 CLI를 준비하고, 두 번째 터미널에서 에이전트를 실행할 수 있는 상태까지 구성합니다.

아래 절차는 다음 공개 버전과 API 조건을 기준으로 설명합니다.

> 문서는 2026년 9월 13일에 확인했습니다. `Edge0-35B-A3B-preview`는 이후 구성이 달라질 수 있습니다. Swift 예제의 `TranslationSession(installedSource:target:preferredStrategy:)`는 macOS 26.4 이상과 해당 API를 포함한 SDK를 전제로 합니다.

## Edge0와 35B 모델의 설치 조건

실험에는 Apple Silicon Mac, Python 3.12, Node.js 22 이상, Xcode Command Line Tools를 사용합니다. 약 23GB의 모델 파일을 저장할 공간과 한국어 및 영어 번역 리소스도 준비합니다. Edge0의 지원 환경과 모델 파일 구성은 [공식 README](https://github.com/Edge0-AI/Edge0)에 나와 있습니다.

### 저장소와 Python 가상 환경

작업할 디렉터리에서 저장소를 내려받고 가상 환경을 활성화한 뒤 샘플 의존성을 설치합니다.

```bash
git clone https://github.com/Edge0-AI/Edge0.git
cd Edge0

python3.12 -m venv .venv
source .venv/bin/activate

pip install -e '.[dev,fetch]'
pip install flask requests
```

이후 명령은 Edge0 저장소 루트를 작업 디렉터리로 사용합니다. `flask`는 스트리밍 전송에, `requests`는 Python 호스트의 HTTP 요청에 사용합니다.

### 모델 다운로드와 경로 지정

공식 다운로드 스크립트로 35B 모델을 받은 뒤 현재 셸에 모델 경로를 등록합니다.

```bash
python scripts/fetch_models.py \
  --tier edge0-35b \
  --target-dir models

export EDGE0_35B_MODEL="$PWD/models/edge0-35b"
```

`models/edge0-35b/`에는 설정, 모델 가중치, 토크나이저와 LoRA 및 프리라우터 어댑터가 함께 들어갑니다. 어댑터를 포함한 디렉터리 전체를 모델 경로로 사용합니다.

## 첫 번째 터미널의 스트리밍 서버

첫 번째 터미널의 서버 실행 절차를 다루겠습니다. Edge0의 [35B 모델 문서](https://github.com/Edge0-AI/Edge0/blob/main/docs/models/edge0-35b.md)는 Flask 전송 계층을 통한 SSE 스트리밍과 `/healthz` 상태 확인 경로를 설명합니다. 이 샘플에서는 접속 주소를 `127.0.0.1:8083`으로 지정합니다.

### 가상 환경 재활성화와 서버 실행

새 터미널에서는 작업 경로와 가상 환경, 모델 환경 변수를 다시 설정합니다. `/path/to/Edge0`는 앞에서 저장소를 내려받은 실제 경로로 바꿉니다.

```bash
cd /path/to/Edge0
source .venv/bin/activate

export EDGE0_35B_MODEL="$PWD/models/edge0-35b"

edge0 serve edge0-35b \
  --host 127.0.0.1 \
  --port 8083 \
  --flask
```

첫 번째 터미널은 서버가 실행되는 동안 유지합니다. 가상 환경을 활성화했던 이전 터미널의 상태가 새 셸에 자동으로 적용되지는 않습니다.

### 별도 셸의 상태 확인

다른 터미널에서 다음 요청으로 서버의 응답을 확인합니다.

```bash
curl http://127.0.0.1:8083/healthz
```

이 요청이 성공하면 지정한 주소의 HTTP 서버에 접근할 수 있습니다. 실제 생성 동작은 에이전트 질문을 보내는 단계에서 확인합니다.

## Microsoft Learn 검색과 입력 자료 제한

Microsoft는 [Learn MCP 서버와 CLI](https://github.com/MicrosoftDocs/mcp#-microsoft-learn-cli)를 제공합니다. Python 호스트는 `mslearn`을 하위 프로세스로 실행하고 JSON 결과를 읽습니다. 샘플에서 MCP 전송 계층을 직접 구현하지 않아도 같은 문서 검색 기능을 사용할 수 있습니다.

### CLI 설치와 검색 확인

Node.js 환경에서 CLI를 설치한 뒤 Native AOT 관련 검색 결과를 확인합니다.

```bash
npm install -g @microsoft/learn-cli

mslearn search \
  ".NET NativeAOT Reflection.Emit" \
  --json
```

이 검색은 Microsoft Learn 외부 서비스에 질의를 전송합니다. Edge0 추론과 번역을 로컬에서 실행하더라도 검색 단계에는 네트워크 연결을 사용합니다.

### 관련 구절의 수와 길이 제한

샘플은 전체 페이지를 가져오는 대신 검색 결과가 반환한 관련 구절을 사용합니다. [전체 코드](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)는 다음 상수로 입력량을 제한합니다.

```python
MAX_SOURCES = 3
MAX_SOURCE_CHARS = 1800
```

최대 세 건을 선택하고 각 구절을 1,800자까지 전달합니다. 이 한도는 문자 수이며 KB나 모델 토큰 수와 같지 않습니다. 질문에 필요한 근거를 유지하면서 한도를 조절한 뒤 응답 품질과 대기 시간을 비교할 수 있습니다.

## Apple Translation을 호출하는 Swift CLI

번역 계층의 API 조건을 확인하겠습니다. 예제는 [Apple의 TranslationSession 초기화 API](https://developer.apple.com/documentation/translation/translationsession/init%28installedsource%3Atarget%3Apreferredstrategy%3A%29)를 사용하며 `preferredStrategy` 인자는 macOS 26.4 이상에서 사용할 수 있습니다. 운영체제와 컴파일 SDK가 이 API를 지원하는 환경에서 다음 코드를 빌드합니다.

### 번역 언어와 텍스트를 전달하는 진입점

다음 소스를 Edge0 저장소 루트의 `apple_translate.swift`에 저장합니다.

```swift
import Foundation
import Translation

@main
struct AppleTranslateCLI {
    static func main() async {
        guard CommandLine.arguments.count >= 4 else {
            fputs(
                "usage: apple_translate <source> <target> <text>\n",
                stderr
            )
            exit(2)
        }

        let source = Locale.Language(
            identifier: CommandLine.arguments[1]
        )

        let target = Locale.Language(
            identifier: CommandLine.arguments[2]
        )

        let text = CommandLine.arguments
            .dropFirst(3)
            .joined(separator: " ")

        do {
            let session = TranslationSession(
                installedSource: source,
                target: target,
                preferredStrategy: .lowLatency
            )

            let response = try await session.translate(text)

            print(response.targetText)
        }
        catch {
            fputs(
                "translation error: \(error)\n",
                stderr
            )
            exit(1)
        }
    }
}
```

CLI는 원본 언어, 대상 언어, 번역할 텍스트를 인자로 받고 번역 결과를 표준 출력으로 전달합니다. `installedSource` 방식은 이미 설치한 언어 리소스를 전제로 합니다.

### 컴파일과 첫 번역

단일 Swift 파일의 `@main` 진입점을 사용하도록 `-parse-as-library`를 지정하고 번역을 시험합니다.

```bash
xcrun swiftc \
  -parse-as-library \
  apple_translate.swift \
  -o apple_translate

./apple_translate ko en \
  "NativeAOT에서 Reflection.Emit을 사용할 수 있습니까?"
```

`-parse-as-library`를 생략하면 단일 파일의 `@main`과 최상위 코드에 관한 컴파일 오류가 발생할 수 있습니다. `TranslationError.Cause.notInstalled` 오류가 발생하면 한국어와 영어 번역 리소스의 설치 상태를 확인합니다. 언어 리소스를 설치한 뒤에는 번역을 온디바이스에서 처리합니다.

## 질문의 의미를 보존하는 한국어 정규화

번역 과정에서 발견한 간접 의문문 문제를 짚어보겠습니다. 제가 NLLB 600M, NLLB 1.3B와 Apple Translation을 시험했을 때 생성 여부를 묻는 질문을 생성 방법을 묻는 요청으로 번역하는 사례가 있었습니다. 이 연재에서는 [샘플의 정규화 함수](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)로 일부 문형을 처리합니다.

실험에 사용한 질문과 번역 사례, 정규화한 문장을 비교하면 다음과 같습니다.

| 구분 | 문장 | 질문의 의미 |
| --- | --- | --- |
| 원래 질문 | 런타임에 새로운 실행 코드를 생성하는지도 함께 설명해주세요. | 생성 여부 |
| 번역 오류 사례 | Explain how to generate new executable code at runtime. | 생성 방법 |
| 정규화 후 | 런타임에 새로운 실행 코드를 생성합니까? 그 여부도 함께 설명해주세요. | 생성 여부 |

정규화 함수는 `~할 수 있는지도`, `~되는지도`, `~하는지도`, `~필요한지도`와 같은 정해진 패턴을 직접 의문문으로 바꿉니다. 정규식에 맞지 않는 문장은 그대로 번역기에 전달합니다. 한국어 문장 전체를 이해하고 고치는 범용 교정 기능으로 사용하지는 않습니다.

## 두 번째 터미널의 에이전트 실행 준비

에이전트 실행에 필요한 파일과 확인 순서를 정리하겠습니다. [Gist](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)의 `microsoft_expert_agent.py`를 Edge0 저장소 루트에 저장하고 번역 실행 파일도 같은 위치에 둡니다.

두 번째 터미널에서는 서버를 실행한 터미널과 별도로 가상 환경을 활성화합니다.

```bash
cd /path/to/Edge0
source .venv/bin/activate

pip install requests
```

실행 전에 다음 순서로 구성 요소를 확인할 수 있습니다.

1. 첫 번째 터미널에서 Edge0 서버의 실행 상태를 확인합니다.
2. 두 번째 터미널에서 `/healthz` 응답을 확인합니다.
3. `mslearn search`의 JSON 검색 결과를 확인합니다.
4. `./apple_translate`로 한국어와 영어 번역을 확인합니다.
5. 저장소 루트에서 `python microsoft_expert_agent.py`를 실행합니다.

3편과 4편에서는 전체 에이전트의 코드 중 검색, 프롬프트 구성, 스트리밍과 측정 부분을 나누어 설명합니다.

## 독립적으로 확인할 수 있는 세 구성 요소

여기까지 정리하면 Edge0 서버, Microsoft Learn 검색, Apple Translation을 각각 실행하고 확인할 수 있습니다. Python 호스트는 이 세 구성 요소를 연결해 한국어 질문에 답하는 흐름을 제어합니다.

현재 실행에는 터미널별 가상 환경과 모델 경로, 번역 API의 운영체제 조건이 직접 영향을 줍니다. 검색 결과 재정렬과 더 짧은 그라운딩 자료는 이후 성능 비교 과제로 남깁니다. {{< series-link slug="edge0-local-rag-agent" text="3편" >}}에서는 질문 정규화부터 검색 결과 선택과 대화 문맥 구성까지 Python 코드로 연결합니다.

연재의 다른 글은 다음 순서로 읽을 수 있습니다.

1. {{< series-link slug="edge0-16gb-mac-overview" text="16GB Mac의 35B 로컬 LLM과 근거 기반 에이전트" >}}
2. {{< series-link slug="edge0-setup-microsoft-learn-translation" text="현재 글" >}}
3. {{< series-link slug="edge0-local-rag-agent" text="Microsoft Learn 검색을 연결한 로컬 RAG 에이전트" >}}
4. {{< series-link slug="edge0-streaming-ttft-metrics" text="스트리밍 응답의 TTFT와 출력 속도 계측" >}}
5. {{< series-link slug="edge0-real-benchmark-and-poc" text="M2 Air 16GB 실측 결과와 사내 PoC 확장 조건" >}}

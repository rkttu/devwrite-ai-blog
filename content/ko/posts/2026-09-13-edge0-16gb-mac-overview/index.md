---
title: "Edge0 연재 1: 16GB Mac의 35B 로컬 LLM과 근거 기반 에이전트"
date: "2026-09-13T09:00:00+09:00"
draft: false
slug: "edge0-16gb-mac-overview"
translationKey: "edge0-16gb-mac-overview"
description: "16GB M2 MacBook Air에서 Edge0-35B를 실행한 경험을 바탕으로 공식 문서 검색, 근거 기반 답변, 한국어 번역을 결합한 로컬 에이전트의 설계 방향을 정리합니다."
tags: ["Edge0", "로컬 LLM", "RAG", "Apple Silicon", "Microsoft Learn"]
categories: ["인공지능"]
tldr: "Edge0-35B를 M2 MacBook Air 16GB에서 실행하고 Microsoft Learn 자료를 제공해 기술 질문에 답하도록 구성했습니다. 실행 가능성, 근거에 따른 답변 변화, 입력 문서 길이에 따른 처리 시간을 구분해 로컬 RAG 에이전트의 역할 분담을 설명합니다."
cover:
  image: "images/posts/edge0-16gb-mac-overview.webp"
  alt: "은색 노트북 위의 유리 블록과 옆에 쌓인 저장 장치로 표현한 로컬 모델 추론"
  caption: "글의 주제를 바탕으로 AI로 생성했습니다."
license: "CC BY-NC 4.0"
---

2026년 9월 13일 기준으로 Edge0는 Apple Silicon용 MLX 백엔드와 `Edge0-35B-A3B-preview` 모델을 공개하고 있습니다. 저는 M2 MacBook Air 16GB에서 이 모델을 실행한 뒤 Microsoft Learn 자료를 근거로 답하는 기술 전문가 에이전트를 구성했습니다.

이 연재는 35B급 모델의 실행 조건, 검색 자료에 따른 답변 변화, 한국어 입출력 구성, 스트리밍 성능 측정, 사내 PoC로 확장할 때의 조건을 다룹니다. 전체 실행 코드는 [Edge0 Microsoft Technology Expert Agent Gist](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)에 정리했습니다.

첫 글에서는 모델을 실행한 경험부터 살펴보겠습니다. 외부 근거를 제공한 실험과 입력 자료의 길이를 줄인 결과를 비교한 뒤 나머지 연재에서 구현할 에이전트의 구조를 설명하겠습니다.

공개 상태와 측정 범위는 다음 기준으로 구분합니다.

> 공개 문서는 2026년 9월 13일에 확인했습니다. 모델은 preview 단계이며 구성과 성능은 이후 달라질 수 있습니다. 실행 시간과 답변 사례는 제가 수행한 개별 실험에서 기록했으며 모든 장비와 질문에 적용되는 성능을 뜻하지 않습니다.

## SSD에서 필요한 가중치를 읽는 35B 모델

Edge0의 메모리 사용 방식부터 짚어보겠습니다. [프로젝트 설명](https://github.com/Edge0-AI/Edge0)에 따르면 Edge0는 희소 MoE 모델의 전문가 가중치를 SSD에 두고 추론에 필요한 부분을 읽어 옵니다. 따라서 모델 파일 전체를 처음부터 RAM에 적재하는 구성과 메모리 사용 양상이 다릅니다.

공개 모델과 제가 사용한 환경을 비교하면 다음과 같습니다.

| 항목 | 값 | 해석 범위 |
| --- | --- | --- |
| 공개 모델 | `Edge0-35B-A3B-preview` | 4비트 양자화를 적용한 35B급 MoE 모델 |
| 모델 파일 크기 | 약 23GB | SSD에 저장하는 체크포인트 크기 |
| 공식 메모리 측정 | 약 2.9GiB | 짧은 문맥에서 측정한 MLX 할당기 최대 활성 메모리 |
| 개인 실험 장비 | M2 MacBook Air 16GB | 이 연재에서 사용한 노트북 |
| 첫 생성 실험 | 128토큰에 약 43.8초 | 특정 입력과 실행 조건에서 기록한 결과 |

공식 메모리 수치는 시스템 전체의 메모리 사용량을 나타내지 않습니다. 운영체제, 토크나이저, 캐시와 문맥 길이에 따른 추가 사용량을 함께 고려할 수 있습니다. 구체적인 가중치 로딩 경로는 [아키텍처 문서](https://github.com/Edge0-AI/Edge0/blob/main/docs/architecture.md)에서 설명합니다.

제 장비에서도 모델이 문장을 생성했습니다. 이 결과를 통해 16GB 노트북에서의 실행 가능성을 확인했지만 응답 속도와 답변의 정확성은 각각 평가했습니다.

## 외부 근거를 중심으로 바꾼 답변 구성

질문만 제공하는 zero-shot 실험에서는 C# Native AOT와 Rust의 컴파일 모델을 잘못 설명하는 답변을 확인했습니다. 영어 질문에서도 비슷한 오류가 반복됐습니다. 질문 수를 충분히 늘린 품질 평가를 수행한 결과는 아니므로 이 경험만으로 모델의 전체 성능을 판단하지는 않았습니다.

이에 따라 모델에 사실 지식을 맡기는 범위를 줄였습니다. 제가 답변을 판정할 수 있는 .NET Native AOT와 JIT 질문을 사용하고 [Microsoft Learn의 Native AOT 문서](https://learn.microsoft.com/dotnet/core/deploying/native-aot/)를 함께 제공했습니다.

이후 에이전트에서는 역할을 다음과 같이 나눴습니다.

```text
Edge0
    질문과 문서의 내용 파악
    관련 근거 선택
    근거에 따른 답변 생성

외부 시스템과 Python 호스트
    공식 문서 검색
    입력 자료 구성
    대화 상태 관리
    한국어 입출력 처리
```

모델이 제공받은 문서를 읽고 질문에 맞게 답을 구성하는지에 실험의 초점을 맞췄습니다.

## 근거 부족을 표현한 답변 사례

근거 제공 방식에 따른 답변 변화를 정리하겠습니다. 실험에서는 질문만 전달하는 방식, Microsoft Learn 자료를 함께 전달하는 방식, 제공한 자료의 범위 안에서 답하도록 더 강하게 제한하는 방식을 차례로 비교했습니다. 여기서는 모델에 전달하는 참고 자료를 그라운딩 자료라고 부르겠습니다.

자료를 제공한 뒤에는 모델이 게시 시점의 네이티브 코드 생성과 JIT 사용 여부를 설명했습니다. 런타임 코드 생성과 동적 로딩의 제약도 답변에 반영했습니다. 이 내용은 [Native AOT의 제한 사항](https://learn.microsoft.com/dotnet/core/deploying/native-aot/#limitations-of-native-aot-deployment)과 대조했습니다.

그라운딩 자료에 없는 CoreCLR의 Dynamic PGO 세부 사항을 질문했을 때에는 다음 응답을 받았습니다.

```text
The supplied reference does not provide enough information.
```

해당 응답에서는 근거가 부족하다는 경계를 표현했습니다. 한 번의 응답이 같은 동작을 항상 보장하지는 않지만 이후 프롬프트에 근거 부족을 알리는 규칙을 포함할 이유가 됐습니다.

## 잘못된 질문 전제를 판정한 실험

질문에 오류를 넣었을 때의 반응도 검토하겠습니다. Native AOT가 게시 과정에서 찾지 못한 코드를 런타임 JIT로 생성하고 `Reflection.Emit`이 이를 보완한다는 설명을 제시했습니다. 모델에는 Microsoft Learn 자료를 사용해 두 주장을 판정하도록 요청했습니다.

모델은 두 주장을 모두 거부했습니다. [공식 설명](https://learn.microsoft.com/dotnet/core/deploying/native-aot/)은 Native AOT 앱이 실행 중 JIT 컴파일러를 사용하지 않으며 `System.Reflection.Emit`과 같은 런타임 코드 생성을 지원하지 않는다고 명시합니다.

이 실험에서는 모델이 질문의 전제를 제공한 자료와 비교해 판정했습니다. 이후 에이전트에서도 출처를 함께 출력하고 답변을 원문과 대조할 수 있도록 구성했습니다.

## 입력 자료 길이에 따른 처리 시간 변화

같은 질문에 제공하는 그라운딩 자료의 양을 줄이면서 전체 처리 시간을 비교했습니다. [연재의 샘플 코드](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)에서도 검색 결과의 수와 길이를 제한하는 이유가 여기에 있습니다.

| 그라운딩 자료 크기 | 전체 처리 시간 | 답변 관찰 |
| --- | --- | --- |
| 약 6.7KB | 약 94초 | 비교 기준으로 사용한 답변 |
| 약 3.4KB | 약 78초 | 자료 축소 후 답변 비교 |
| 약 1.7KB | 약 48초 | 핵심 답변 유지 확인 |

다만 이 수치는 개별 실행 기록이며 반복 횟수와 캐시 상태를 통제한 벤치마크 결과는 아닙니다. 자료 크기는 바이트 단위이고 모델이 처리하는 입력 토큰 수와도 다릅니다. 이 결과만으로 처리 시간 감소분 전체를 프리필 단축으로 설명할 수는 없습니다.

검색 결과에서 질문과 관련된 구절을 좁히면 모델에 전달하는 입력량을 줄일 수 있습니다. 자료를 지나치게 줄여 핵심 근거를 잃지 않도록 답변 품질과 지연 시간을 함께 비교하는 방향으로 실험을 이어갔습니다.

## 검색과 번역을 연결한 에이전트 구조

최종 샘플의 질문 처리 흐름을 확인하겠습니다. 한국어 질문을 받아 영어로 검색하고 답변을 생성한 뒤 한국어로 번역합니다. [Gist의 전체 코드](https://gist.github.com/rkttu/805dd58e333b7e51b10326168a484c2d)는 이 흐름을 Python 호스트에서 제어합니다.

각 구성 요소의 호출 순서는 다음과 같습니다.

```text
한국어 질문
    ↓
질문 정규화와 Apple Translation
    ↓
Microsoft Learn 검색
    ↓
관련 구절을 그라운딩 자료로 구성
    ↓
Edge0-35B의 영어 응답 스트리밍
    ↓
문장 단위 Apple Translation
    ↓
한국어 답변과 출처 출력
```

Python 호스트가 검색과 상태를 관리하므로 모델의 자율적인 도구 선택 기능에 의존하지 않습니다. 모델에는 문서를 읽고 답을 합성하는 역할을 맡깁니다.

모델 추론과 번역은 Mac에서 처리하지만 Microsoft Learn 검색은 외부 서비스에 질의를 전송합니다. 따라서 이 연재의 로컬 RAG는 인터넷 검색을 포함하며 완전한 오프라인 구성을 뜻하지 않습니다.

## 실행 가능성을 바탕으로 좁힌 다음 실험

여기까지 정리하면 M2 MacBook Air 16GB에서 35B급 모델을 실행하고 공식 문서를 근거로 답을 구성하는 흐름을 확인했습니다. 질문만 제공했을 때의 오류와 자료를 제공한 뒤의 답변 변화를 함께 기록하면서 모델과 호스트의 역할을 나눴습니다.

현재 구성에는 입력 자료의 길이와 첫 응답 대기 시간이 직접 영향을 줍니다. 더 빠른 장비나 다른 백엔드로의 확장은 후속 비교 과제로 남깁니다. {{< series-link slug="edge0-setup-microsoft-learn-translation" text="2편" >}}에서는 Edge0 서버, Microsoft Learn CLI, Apple Translation을 준비하고 터미널별 가상 환경과 모델 경로를 설정합니다.

연재의 다른 글은 다음 순서로 읽을 수 있습니다.

1. {{< series-link slug="edge0-16gb-mac-overview" text="현재 글" >}}
2. {{< series-link slug="edge0-setup-microsoft-learn-translation" text="Microsoft Learn과 Apple Translation 실행 환경" >}}
3. {{< series-link slug="edge0-local-rag-agent" text="Microsoft Learn 검색을 연결한 로컬 RAG 에이전트" >}}
4. {{< series-link slug="edge0-streaming-ttft-metrics" text="스트리밍 응답의 TTFT와 출력 속도 계측" >}}
5. {{< series-link slug="edge0-real-benchmark-and-poc" text="M2 Air 16GB 실측 결과와 사내 PoC 확장 조건" >}}

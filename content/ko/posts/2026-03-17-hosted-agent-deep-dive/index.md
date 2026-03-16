---
title: "RoleEntryPoint에서 FoundryCBAgent까지 — .NET 개발자가 본 Microsoft Foundry Hosted Agent의 아키텍처"
date: 2026-03-17T00:00:00+09:00
draft: false
slug: "hosted-agent-deep-dive"
tags:
  - Azure
  - .NET
  - AI 에이전트
  - PaaS
  - Microsoft Foundry
categories:
  - 클라우드
translationKey: "hosted-agent-deep-dive"
description: "Microsoft Foundry Hosted Agent의 아키텍처를 Windows Azure Cloud Services부터 이어온 .NET PaaS 계보 속에서 분석합니다."
cover:
  image: "images/posts/hosted-agent-deep-dive.webp"
  alt: "클라우드 플랫폼 아키텍처 개념 이미지"
tldr: "Hosted Agent는 Cloud Services의 RoleEntryPoint와 동일한 설계 원칙으로, 어댑터가 HTTP/SSE/인증을 처리하고 개발자는 IAgentInvocation.InvokeAsync 하나만 구현합니다. 프리뷰 단계이지만, 이 계약 기반 아키텍처를 이해해두면 GA 이후 마이그레이션 경로를 확보할 수 있습니다."
---

> 이 글은 2026년 3월 기준, 퍼블릭 프리뷰 상태인 Microsoft Foundry Hosted Agent의 설계를 .NET 아키텍처의 계보 속에서 분석합니다. 현시점에서 프로덕션 사용을 권장하는 글이 아니며, 엔터프라이즈 AI 아키텍트가 주목해야 할 설계 방향성에 초점을 맞춥니다.

---

## 에이전트를 프로덕션에 올린다는 것

엔터프라이즈에서 AI 에이전트를 프로덕션에 배포하려 할 때, 현재 선택지는 두 가지입니다.

**선언적 에이전트.** Microsoft Foundry 포털에서 프롬프트와 도구를 조합해 만드는 no-code 방식입니다. 빠르게 만들 수 있지만, 복잡한 분기 로직이나 멀티스텝 워크플로우, 외부 시스템과의 정밀한 연동을 코드로 제어할 수 없습니다. 일정 수준을 넘어서는 순간 한계에 부딪힙니다.

**자체 컨테이너.** 에이전트 로직을 직접 코드로 작성하고, 컨테이너에 담아 배포하는 방식입니다. 자유도는 완전하지만, HTTP 서버 구성, 인증, 대화 상태 관리, 스케일링, 모니터링, 버전 관리를 전부 직접 구현해야 합니다. 그리고 결정적으로, 이 컨테이너 안에서 에이전트가 무엇을 하는지 **플랫폼이 전혀 알 수 없습니다.** LLM을 어떻게 호출했는지, 도구를 어떤 순서로 사용했는지, 왜 그런 응답을 생성했는지가 블랙박스입니다.

Hosted Agent는 이 사이의 공백을 메웁니다. 코드 수준의 자유도를 유지하면서, 에이전트의 동작이 플랫폼에 구조적으로 투명하게 노출되는 제3의 경로입니다.

---

## Windows Azure를 기억하는가

지금의 Microsoft Azure는 2010년 2월에 **Windows Azure**라는 이름으로 상용 출시되었습니다. 2014년 3월에 Microsoft Azure로 리브랜딩되기까지, 이 플랫폼의 정체성은 지금과는 상당히 달랐습니다.

Windows Azure는 태생적으로 **PaaS 플랫폼**이었습니다. VM을 직접 다루는 IaaS는 초기에 존재하지 않았고, 2012년에 가서야 Virtual Machines가 추가되었습니다. 출발점은 Cloud Services(Web Role, Worker Role), SQL Azure(지금의 Azure SQL Database), Storage Services 같은 관리형 서비스였습니다. 개발자가 인프라를 의식하지 않고 코드와 구성 파일만으로 배포하는 것이 핵심 약속이었고, 이것은 당시 AWS가 EC2 중심의 IaaS로 시장을 열어가던 것과는 근본적으로 다른 접근이었습니다.

2014년 리브랜딩 이후, Azure는 AWS를 강하게 의식하면서 IaaS 기능을 빠르게 확충했습니다. VM, VNET, Load Balancer, 그리고 이후의 AKS까지. 시장에서 "클라우드 = 가상 머신을 빌려 쓰는 것"이라는 인식이 지배적이었던 시기에 IaaS를 강화한 것은 상업적으로 옳은 판단이었지만, 그 과정에서 Windows Azure 시절의 PaaS 중심 철학은 다소 희석되었습니다.

그러나 Microsoft의 본래 강점은 언제나 PaaS와 SaaS에 있었습니다. .NET Framework, Visual Studio, SQL Server, Office 365, SharePoint — 이 회사는 개발자와 정보 근로자에게 **관리형 플랫폼** 위에서 일하도록 하는 데 30년 이상의 역사를 가지고 있습니다. Windows Azure 시절의 Cloud Services가 그 철학의 클라우드 확장이었고, 이후의 App Service, Azure Functions, Container Apps도 같은 맥락에 있습니다.

이 배경을 이해해야, Hosted Agent가 왜 이런 형태로 설계되었는지가 명확해집니다. Microsoft는 AI 에이전트라는 새로운 워크로드 앞에서, IaaS적 접근(자체 컨테이너를 직접 관리)이 아니라 PaaS적 접근(플랫폼이 호스팅하고 개발자는 로직에 집중)을 선택한 것입니다. 이것은 AWS가 Bedrock Agents에서 취하는 방향과도, Google이 Vertex AI Agent Builder에서 취하는 방향과도 다릅니다. Microsoft의 고유한 PaaS DNA가 AI 시대에 다시 발현된 것으로 볼 수 있습니다.

---

## 어디서 많이 본 패턴

.NET 개발자라면, 그리고 Azure의 역사를 함께 걸어온 개발자라면, Hosted Agent의 아키텍처에서 강한 기시감을 느낄 것입니다.

Windows Azure Cloud Services 시절을 떠올려 보겠습니다. 그때도 "개발자는 비즈니스 로직만 작성하고, 플랫폼이 제공하는 호스트 프로세스가 그 로직을 감싸서 인프라에 올린다"는 것이 핵심 약속이었습니다. `RoleEntryPoint`를 상속하고, `OnStart()`, `Run()`, `OnStop()`을 구현하면, `WaWorkerHost.exe`가 그 코드를 로딩해서 실행했고, Fabric Controller가 인스턴스의 프로비저닝과 헬스 모니터링을 담당했습니다.

Hosted Agent의 구조는 이 패턴을 AI 에이전트 도메인으로 재해석한 것입니다.

| Windows Azure Cloud Services | Microsoft Foundry Hosted Agent |
| --- | --- |
| `RoleEntryPoint` 추상 클래스 | `FoundryCBAgent` / `IAgentInvocation` 인터페이스 |
| `OnStart()`, `Run()`, `OnStop()` | `InvokeAsync()` + liveness/readiness 프로브 |
| `WaIISHost.exe` / `WaWorkerHost.exe` | AgentServer 어댑터 내장 Kestrel 서버 |
| `.csdef` + `.cscfg` | `agent.yaml` + 환경 변수 |
| Fabric Controller | Agent Service Runtime |
| DiagnosticMonitor (WAD) | OpenTelemetry 자동 계측 + Application Insights |
| Input/Internal Endpoint 선언 | Foundry Responses API 프로토콜 자동 노출 |

핵심 공통점은 세 가지입니다. 플랫폼의 호스트 프로세스가 개발자 코드를 로딩하는 구조, 플랫폼이 정의한 계약(contract)에 맞춰 코드를 작성해야 하는 규칙, 인프라 관심사가 플랫폼으로 이전되는 효과. 15년 전에 Cloud Services에서 작동했던 이 설계 원칙이, 이제 AI 에이전트라는 새로운 워크로드에 다시 적용되고 있습니다.

---

## Hosting Adapter의 실체: 사전 구성된 Kestrel

.NET 관점에서 Hosting Adapter의 실체를 정확히 파악하는 것이 중요합니다.

`Azure.AI.AgentServer.Core` 패키지는 ASP.NET Core의 Kestrel 서버, DI 컨테이너, 미들웨어 파이프라인을 공유합니다. 일반적인 ASP.NET Core 앱과 기술 스택의 근간이 같습니다. 차이는, `WebApplicationBuilder`를 직접 구성하는 대신, **어댑터 패키지가 제공하는 사전 구성된 호스트를 사용한다**는 점입니다.

일반적인 ASP.NET Core 앱에서 `Program.cs`에 `builder.Services.AddXxx()`, `app.MapPost()`, `app.UseMiddleware()`를 직접 조합하는 것과 달리, Hosted Agent에서는 이 조합이 이미 끝나 있는 상태에서 `IAgentInvocation.InvokeAsync` 하나만 구현합니다. 라우팅(`/responses`, `/liveness`, `/readiness`), SSE 스트리밍을 위한 chunked response 설정, OpenTelemetry 미들웨어 등록, 인증 처리 파이프라인이 전부 어댑터 내부에서 구성 완료된 채로 제공됩니다.

```text
기술 스택의 수직 단면:

┌─────────────────────────────────────────┐
│  IAgentInvocation.InvokeAsync           │  ← 개발자가 구현
│  (에이전트 비즈니스 로직)                    │
├─────────────────────────────────────────┤
│  Azure.AI.AgentServer 어댑터 계층          │  ← 패키지가 제공
│  - Foundry Responses API 프로토콜 변환      │
│  - SSE 스트리밍 이벤트 직렬화               │
│  - OpenTelemetry 자동 계측                 │
│  - OAuth consent 처리                     │
│  - Tool Client 프로비저닝                  │
├─────────────────────────────────────────┤
│  ASP.NET Core 미들웨어 파이프라인            │  ← 공유 스택
│  Kestrel HTTP 서버                        │
│  DI 컨테이너, 설정 시스템                    │
└─────────────────────────────────────────┘
```

Python 쪽은 Starlette(ASGI 프레임워크)를 내장 웹 서버로 사용합니다. "어댑터가 임베디드 웹 서버를 내장한다"는 아키텍처 패턴은 동일하되, 언어별로 해당 생태계에서 가장 자연스러운 웹 스택을 선택한 것입니다.

---

## 왜 어댑터를 우회할 수 없는가

"Foundry가 기대하는 엔드포인트 스펙을 직접 구현하면 되지 않느냐"는 질문이 나올 수 있습니다. `/responses`, `/liveness`, `/readiness` 세 개의 경로만 맞추면 되는 것 아닌가?

이것이 단순한 REST 엔드포인트 몇 개를 맞추는 문제가 아닌 이유는, **HTTP 프로토콜 수준의 재정의가 요구되기 때문**입니다.

에이전트의 응답은 일반적인 JSON 한 덩어리가 아닙니다. `ResponseTextDeltaEvent` → `ResponseTextDoneEvent` → `ResponseContentPartDoneEvent` → `ResponseOutputItemDoneEvent` → `ResponseCompletedEvent`로 이어지는 **순서가 정해진 이벤트 체인**입니다. 이것이 HTTP 응답으로 나갈 때는 chunked transfer encoding 기반의 SSE 스트림이 되어야 하고, 각 이벤트의 JSON 스키마, 시퀀스 넘버링, 종료 조건까지 프로토콜이 규정합니다.

.NET의 `IAgentInvocation` 구현 코드를 보면 이 구조가 명확해집니다. `InvokeAsync`가 `IAsyncEnumerable<ResponseStreamEvent>`를 반환하고, 어댑터가 이 스트림을 받아 SSE로 변환합니다. 각 이벤트에는 시퀀스 번호(`seq`)가 부여되고, `ResponseOutputItemDoneEvent`에는 완성된 콘텐츠가, `ResponseCompletedEvent`에는 전체 응답 객체가 포함되어야 합니다.

이것을 직접 구현한다는 것은, "이 경로에서 이 순서로 이 스키마의 이벤트를 청크 단위로 스트리밍하되, 비동기 제너레이터의 백프레셔 처리와 연결 중단 시의 정리까지 올바르게 수행한다"는 뜻이 됩니다. 여기에 OpenTelemetry span의 시작/종료 타이밍, OAuth consent가 필요한 상황에서의 특수 응답 포맷까지 더하면, 사실상 어댑터 패키지를 처음부터 다시 만드는 것과 같습니다.

그래서 정확한 표현은 이것입니다: **에이전트 로직은 무엇으로든 작성할 수 있지만, HTTP 서버 계층은 어댑터 패키지가 제공하는 것을 사용하는 것이 공식 경로.** "웹 서버를 자유롭게 선택한다"가 아니라, "어댑터가 제공하는 사전 구성된 웹 서버 위에서, 비즈니스 로직 구현의 자유도가 완전하다"는 것입니다.

Cloud Services 시절, IIS를 직접 설정해서 Web Role처럼 동작하게 만들 수는 있었겠지만, `RoleEntryPoint`를 상속하고 `.csdef`를 작성해야 Fabric Controller가 그 인스턴스를 관리할 수 있었던 것과 정확히 같은 맥락입니다.

---

## 엔터프라이즈 AI가 놓치고 있는 것: 계약 기반 투명성

Hosted Agent의 진짜 가치는 "구현이 단순해진다"가 아닙니다.

자체 컨테이너 방식의 근본적 문제는 **불투명성**입니다. 컨테이너 안에서 에이전트가 LLM을 어떻게 호출하고, 도구를 어떤 순서로 사용했는지, 왜 그 응답을 생성했는지를 플랫폼이 알 수 없습니다. 개발자가 로깅을 아무리 열심히 해도, 그것은 개발자의 자발적 노력이지 플랫폼이 보장하는 구조가 아닙니다.

Hosted Agent는 어댑터가 강제하는 프로토콜 계약 덕분에, 에이전트의 동작이 플랫폼에 구조적으로 노출됩니다.

**관측 가능성(Observability)이 계약 수준에서 보장됩니다.** 어댑터가 HTTP 요청, 모델 호출, 도구 사용을 자동으로 계측합니다. 개발자가 OpenTelemetry를 설정할 필요가 없습니다. Foundry 포털의 Traces 탭에서 에이전트가 어떤 판단을 거쳐 응답에 도달했는지를 확인할 수 있습니다.

**정량적 평가(Evaluation)가 플랫폼에 통합됩니다.** 어댑터가 강제하는 응답 프로토콜 덕분에, 플랫폼이 응답 구조를 이해할 수 있고, Intent Resolution, Task Adherence, Tool Call Accuracy 같은 빌트인 평가 메트릭을 직접 적용할 수 있습니다. 자체 컨테이너에서는 이 평가 파이프라인을 처음부터 별도로 구축해야 합니다.

**거버넌스가 아이덴티티 수준에서 적용됩니다.** 퍼블리시 전에는 프로젝트의 시스템 할당 관리 ID로 동작하다가, 퍼블리시 시 전용 에이전트 아이덴티티가 분리되고, Microsoft Entra 에이전트 레지스트리에 등록됩니다. 조직 차원에서 "어떤 에이전트가 어떤 리소스에 접근 가능한지"를 중앙에서 통제할 수 있습니다.

**대화 상태가 플랫폼 관리입니다.** 컨테이너 자체는 stateless한 HTTP 서버로 동작하고, "이 사용자와 이전에 어떤 대화를 했는지"는 Agent Service Runtime이 `CreateResponse` 요청 안에 컨텍스트로 주입합니다. 개발자가 대화 상태 저장소를 직접 구현할 필요가 없습니다.

이것이 PoC를 넘어 프로덕션으로 갈 때 결정적인 차이입니다. 보안 팀은 "에이전트가 무엇을 했는지 추적 가능한가?"를 묻고, 컴플라이언스 팀은 "에이전트의 접근 권한이 관리되는가?"를 묻고, 경영진은 "에이전트의 품질을 어떻게 측정하는가?"를 묻습니다. 자체 컨테이너 방식에서는 이 모든 질문에 "직접 구현했습니다"라고 답해야 하지만, Hosted Agent에서는 "플랫폼이 보장합니다"라고 답할 수 있습니다.

---

## 런타임 동작 모델

실제 운영 환경에서 Hosted Agent의 동작을 정확히 이해하는 것이 중요합니다.

에이전트 코드를 담은 어셈블리는 "세션별로 인스턴스화되는 에이전트"가 아니라, "요청이 올 때마다 주입된 컨텍스트에 기반해서 stateless하게 응답을 생성하는 서비스"로 동작합니다.

```text
[사용자 A 세션] ──┐
[사용자 B 세션] ──┤   Agent Service Runtime
[사용자 C 세션] ──┘   (대화 상태 관리 + 라우팅)
                          │
                 ┌────────┼────────┐
                 ▼        ▼        ▼
             [Replica 1] [Replica 2] [Replica 3]
             (동일한 컨테이너 이미지, stateless)
             (각 요청에 해당 세션의 대화 컨텍스트가 주입됨)
```

세션마다 별도 컨테이너가 뜨는 것이 아닙니다. 소수의 replica가 다수의 세션 요청을 처리하되, 각 요청에 해당 세션의 대화 컨텍스트가 플랫폼으로부터 주입됩니다. 에이전트 로직은 하나인데, 대화의 연속성은 플랫폼이 보장하는 구조입니다.

`min-replicas 0`으로 설정하면 scale-to-zero까지 가능하고, 첫 요청 시 cold start가 발생합니다. 지속적인 응답 지연이 허용되지 않는 환경에서는 `min-replicas 1` 이상을 유지하는 것이 권장됩니다.

---

## 코드로 보는 Hosted Agent: MCP 도구 통합 예제

아키텍처 논의를 코드 수준으로 구체화하겠습니다. Microsoft의 공식 샘플 중 Hosted Agent에서 MCP 서버를 도구로 사용하는 C# 예제를 중심으로, 앞서 설명한 개념들이 코드에서 어떻게 실현되는지 해설합니다.

### 환경 설정과 에이전트 정의

```csharp
var endpoint = Environment.GetEnvironmentVariable("AZURE_FOUNDRY_PROJECT_ENDPOINT")
    ?? throw new InvalidOperationException("AZURE_FOUNDRY_PROJECT_ENDPOINT is not set.");
var model = Environment.GetEnvironmentVariable("AZURE_FOUNDRY_PROJECT_MODEL_ID") ?? "gpt-4.1-mini";

const string AgentName = "MicrosoftLearnAgent";
const string AgentInstructions = "You answer questions by searching the Microsoft Learn content only.";
```

첫 번째로 주목할 것은, 에이전트 코드에 HTTP 서버 구성 코드가 **전혀 없다**는 점입니다. Kestrel 설정, 라우트 매핑, 미들웨어 파이프라인 — 일반적인 ASP.NET Core 앱이라면 반드시 있어야 할 이 코드들이 보이지 않습니다. 이것이 앞서 설명한 "어댑터가 사전 구성된 Kestrel을 제공한다"는 것의 실체입니다. 개발자는 에이전트의 이름, 지시문, 사용할 모델만 정의합니다.

### MCP 도구 선언

```csharp
var mcpTool = new MCPToolDefinition(
    serverLabel: "microsoft_learn",
    serverUrl: "https://learn.microsoft.com/api/mcp");
mcpTool.AllowedTools.Add("microsoft_docs_search");
```

`MCPToolDefinition`은 세 가지를 선언합니다. `serverLabel`은 이 MCP 서버의 고유 식별자이고, `serverUrl`은 원격 MCP 서버의 엔드포인트이며, `AllowedTools`는 해당 서버가 노출하는 도구 중 이 에이전트가 사용할 수 있는 도구의 허용 목록입니다.

여기서 중요한 것은, MCP 서버와의 실제 통신을 **에이전트 코드가 직접 수행하지 않는다**는 점입니다. 자체 컨테이너 방식이었다면 MCP 클라이언트를 초기화하고, 도구 목록을 열거하고, 호출 결과를 파싱하는 코드를 직접 작성해야 합니다. Hosted Agent에서는 도구 정의만 선언하면, Agent Service Runtime이 MCP 서버와의 통신을 플랫폼 수준에서 관리합니다. 이것이 "계약 기반 투명성"의 구체적 예시입니다 — 플랫폼이 도구 호출을 중개하기 때문에, 어떤 도구가 언제 호출되었는지를 자동으로 추적할 수 있습니다.

### Persistent Agent 생성

```csharp
var persistentAgentsClient = new PersistentAgentsClient(endpoint, new DefaultAzureCredential());

var agentMetadata = await persistentAgentsClient.Administration.CreateAgentAsync(
    model: model,
    name: AgentName,
    instructions: AgentInstructions,
    tools: [mcpTool]);
```

`PersistentAgentsClient`는 Foundry 서비스에 에이전트를 **서버 사이드로 등록**합니다. 이 호출 이후, 에이전트는 Foundry 포털에서 확인할 수 있는 관리 대상이 됩니다. `DefaultAzureCredential`은 개발 환경에서는 Azure CLI 인증을, 배포 환경에서는 Managed Identity를 자동으로 선택합니다 — 앞서 논의한 아이덴티티 전환 구조의 클라이언트 측 구현입니다.

### 도구 승인 정책과 실행

```csharp
var runOptions = new ChatClientAgentRunOptions()
{
    ChatOptions = new()
    {
        RawRepresentationFactory = (_) => new ThreadAndRunOptions()
        {
            ToolResources = new MCPToolResource(serverLabel: "microsoft_learn")
            {
                RequireApproval = new MCPApproval("never"),
            }.ToToolResources()
        }
    }
};
```

`RequireApproval`은 MCP 도구 호출에 대한 승인 정책입니다. `"never"`는 자동 실행, `"always"`는 매 호출마다 사용자 승인을 요구합니다. 이것은 자체 컨테이너에서는 직접 구현해야 할 Human-in-the-Loop 패턴을 플랫폼이 표준화한 것입니다. 엔터프라이즈 환경에서 "이 에이전트가 외부 도구를 호출할 때 반드시 사람의 승인을 거쳐야 한다"는 정책을 코드 한 줄로 적용할 수 있습니다.

```csharp
AIAgent agent = await persistentAgentsClient.GetAIAgentAsync(agentMetadata.Value.Id);
AgentSession session = await agent.CreateSessionAsync();

var response = await agent.RunAsync(
    "Please summarize the Azure AI Agent documentation related to MCP Tool calling?",
    session,
    runOptions);

Console.WriteLine(response);
```

`agent.RunAsync()`가 호출되면, 요청은 Foundry의 Agent Service Runtime으로 전달되고, Runtime이 MCP 서버에 도구 호출을 중개하고, LLM에 컨텍스트를 전달하며, 최종 응답을 스트리밍 이벤트로 반환합니다. 개발자 코드에서는 이 과정이 단일 `await` 호출로 추상화됩니다.

```csharp
await persistentAgentsClient.Administration.DeleteAgentAsync(agent.Id);
```

마지막의 정리 코드는, 에이전트가 Foundry의 관리 대상 리소스임을 보여줍니다. 자체 컨테이너라면 "컨테이너를 중지한다"이지만, Hosted Agent에서는 "에이전트를 삭제한다"입니다. 관리 단위가 인프라가 아니라 에이전트 자체입니다.

### 이 코드가 말해주는 것

전체 코드에서 HTTP, 스트리밍, 프로토콜, 인증, 상태 관리에 대한 코드는 **한 줄도 없습니다.** 개발자가 작성한 것은 "어떤 모델을 쓸 것인가, 어떤 도구를 쓸 것인가, 어떤 지시문을 줄 것인가, 승인 정책은 무엇인가"뿐입니다. 나머지는 전부 플랫폼이 처리합니다.

이것이 `RoleEntryPoint`에서 `OnStart()`와 `Run()`만 구현하면 나머지를 Fabric Controller가 처리했던 것과 같은 패턴입니다. 15년의 시차를 두고, 동일한 설계 철학이 AI 에이전트 도메인에서 반복되고 있습니다.

---

## 현실 점검: 아직 청사진이다

솔직하게 말해야 할 것이 있습니다.

2026년 3월 현재, Hosted Agent는 퍼블릭 프리뷰입니다. 그리고 Hosted Agent 이전에, no-code 에이전트에서 MCP 서버를 연결해 두 턴 이상 대화를 시도하면 에이전트가 크래시되는 수준입니다. 대화 상태에 도구 호출 이력이 누적되면서 직렬화/역직렬화 과정에서 문제가 생기거나, MCP 세션의 수명 관리가 대화 턴 경계에서 제대로 처리되지 않는 것으로 보입니다.

MCP 서버 통합의 제약 사항조차 아직 규정되지 않은 상태입니다. 어떤 transport를 지원해야 하는지(SSE인지, Streamable HTTP인지), 어떤 MCP 프로토콜 버전을 요구하는지, 도구 스키마에 제약이 있는지 같은 기본적인 사양이 공개 문서에 없습니다. MCP 프로토콜 자체도 진화 중이고, Foundry가 이 중 어떤 버전과 transport를 공식 지원할 것인지 확정되지 않았습니다.

프리뷰 단계의 명시적 제약도 있습니다. Azure 구독당 Hosted Agent를 포함한 Foundry 리소스 100개, 리소스당 최대 200개의 Hosted Agent, replica는 최소 2개, 최대 5개까지. 프라이빗 네트워킹도 아직 지원되지 않습니다. 빌링은 2026년 4월 1일 이후 시작 예정입니다.

이 모든 것을 종합하면, 현 시점에서 Hosted Agent까지 도입하는 것은 시기상조입니다. PoC를 진행한다면 자체 컨테이너에서 LLM API를 직접 호출하는 방식이 더 예측 가능합니다. 플랫폼 투명성을 포기하는 대신, 크래시 원인을 직접 제어할 수 있기 때문입니다.

---

## 그럼에도 지금 알아야 하는 이유

Hosted Agent의 아키텍처를 지금 이해해두는 것은, GA 이후의 마이그레이션 경로를 확보하기 위해서입니다.

자체 컨테이너로 PoC를 진행하더라도, 에이전트의 비즈니스 로직을 `CreateResponse` → `Response | Stream[ResponseStreamEvent]` 계약에 가깝게 설계해두면, 나중에 어댑터로 감싸는 것은 비교적 단순한 작업이 됩니다. .NET에서는 `IAgentInvocation.InvokeAsync(CreateResponseRequest, AgentInvocationContext, CancellationToken)` 시그니처를 염두에 두고 로직을 구성하면 됩니다.

그리고 이 아키텍처가 안정화되었을 때 가장 큰 혜택을 받는 것은, 복잡한 에이전트 로직을 코드로 정밀하게 제어하면서도 엔터프라이즈 거버넌스 요구사항을 충족해야 하는 조직입니다. 바로 지금 "선언적 에이전트로는 부족하고, 자체 컨테이너로는 감당이 안 되는" 사이에 끼어 있는 팀들입니다.

Microsoft는 Cloud Services에서 App Service로, App Service에서 Azure Functions로, Functions에서 Container Apps로 이어지는 관리형 컴퓨트의 추상화 수준을 꾸준히 높여왔습니다. Hosted Agent는 그 계보의 최신 지점에서, AI 에이전트라는 특정 워크로드에 맞춘 도메인 특화 PaaS를 시도하고 있습니다. `RoleEntryPoint`에서 `FoundryCBAgent`까지, 15년에 걸친 "플랫폼이 호스트 프로세스를 제공하고 개발자는 비즈니스 로직에 집중한다"는 약속이 AI 시대에도 유효한지 검증하는 실험이 지금 진행 중입니다.

---

*이 글은 [/dev/write](https://devwrite.ai) 뉴스레터에서 발행되었습니다.*

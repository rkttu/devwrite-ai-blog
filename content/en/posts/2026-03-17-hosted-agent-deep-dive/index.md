---
title: "From RoleEntryPoint to FoundryCBAgent — A .NET Developer's View of Microsoft Foundry Hosted Agent Architecture"
date: 2026-03-17T00:00:00+09:00
draft: false
slug: "hosted-agent-deep-dive"
tags:
  - Azure
  - .NET
  - AI Agent
  - PaaS
  - Microsoft Foundry
categories:
  - Cloud
translationKey: "hosted-agent-deep-dive"
description: "Analyzing Microsoft Foundry Hosted Agent's architecture through the lineage of .NET PaaS, from Windows Azure Cloud Services to today."
cover:
  image: "images/posts/hosted-agent-deep-dive.webp"
  alt: "Cloud platform architecture concept image"
tldr: "Hosted Agent follows the same design principles as Cloud Services' RoleEntryPoint — the adapter handles HTTP/SSE/authentication while developers implement just IAgentInvocation.InvokeAsync. Though still in preview, understanding this contract-based architecture now secures your migration path after GA."
---

> This article analyzes the design of Microsoft Foundry Hosted Agent, currently in public preview as of March 2026, within the lineage of .NET architecture. This is not a recommendation for production use at this point, but focuses on the design direction that enterprise AI architects should pay attention to.

---

## What It Means to Put an Agent in Production

When deploying AI agents to production in an enterprise, there are currently two options.

**Declarative agents.** A no-code approach where you combine prompts and tools in the Microsoft Foundry portal. Quick to build, but you cannot control complex branching logic, multi-step workflows, or precise integration with external systems through code. You hit a wall the moment you go beyond a certain level.

**Self-hosted containers.** You write the agent logic directly in code and deploy it in a container. Complete freedom, but you must implement HTTP server configuration, authentication, conversation state management, scaling, monitoring, and version management all by yourself. And critically, **the platform has no visibility** into what the agent does inside that container. How it called the LLM, in what order it used tools, and why it generated that response — all of it is a black box.

Hosted Agent fills this gap. It is the third path that maintains code-level freedom while structurally exposing agent behavior to the platform.

---

## Do You Remember Windows Azure?

Today's Microsoft Azure was commercially launched in February 2010 under the name **Windows Azure**. Until it was rebranded to Microsoft Azure in March 2014, the platform's identity was quite different from what it is now.

Windows Azure was inherently a **PaaS platform**. IaaS for directly managing VMs didn't exist initially — Virtual Machines weren't added until 2012. The starting point was managed services like Cloud Services (Web Role, Worker Role), SQL Azure (now Azure SQL Database), and Storage Services. The core promise was that developers could deploy using only code and configuration files without worrying about infrastructure, and this was a fundamentally different approach from AWS, which was opening the market with EC2-centric IaaS.

After the 2014 rebranding, Azure rapidly expanded IaaS capabilities with a keen eye on AWS. VMs, VNETs, Load Balancers, and later AKS. Strengthening IaaS during a period when the market perception was "cloud = renting virtual machines" was commercially sound, but the PaaS-centric philosophy of the Windows Azure era became somewhat diluted in the process.

However, Microsoft's inherent strength has always been in PaaS and SaaS. .NET Framework, Visual Studio, SQL Server, Office 365, SharePoint — this company has over 30 years of history in making developers and information workers operate on **managed platforms**. Cloud Services from the Windows Azure era was the cloud extension of that philosophy, and the subsequent App Service, Azure Functions, and Container Apps are in the same lineage.

Understanding this background makes it clear why Hosted Agent is designed this way. Facing the new workload of AI agents, Microsoft chose a PaaS approach (the platform hosts, developers focus on logic) rather than an IaaS approach (managing your own containers). This differs from the direction AWS takes with Bedrock Agents and from Google's approach with Vertex AI Agent Builder. Microsoft's unique PaaS DNA is manifesting again in the AI era.

---

## A Pattern You've Seen Before

If you're a .NET developer — and especially if you've walked alongside Azure's history — you'll feel strong déjà vu in Hosted Agent's architecture.

Think back to the Windows Azure Cloud Services era. Back then too, the core promise was "developers write only business logic, and the host process provided by the platform wraps that logic and puts it on infrastructure." You inherited `RoleEntryPoint`, implemented `OnStart()`, `Run()`, `OnStop()`, and `WaWorkerHost.exe` loaded and executed that code while Fabric Controller handled instance provisioning and health monitoring.

Hosted Agent's structure is a reinterpretation of this pattern for the AI agent domain.

| Windows Azure Cloud Services | Microsoft Foundry Hosted Agent |
| --- | --- |
| `RoleEntryPoint` abstract class | `FoundryCBAgent` / `IAgentInvocation` interface |
| `OnStart()`, `Run()`, `OnStop()` | `InvokeAsync()` + liveness/readiness probes |
| `WaIISHost.exe` / `WaWorkerHost.exe` | AgentServer adapter with embedded Kestrel server |
| `.csdef` + `.cscfg` | `agent.yaml` + environment variables |
| Fabric Controller | Agent Service Runtime |
| DiagnosticMonitor (WAD) | OpenTelemetry auto-instrumentation + Application Insights |
| Input/Internal Endpoint declaration | Foundry Responses API protocol auto-exposure |

There are three core commonalities: the structure where the platform's host process loads developer code, the rule that code must be written to match contracts defined by the platform, and the effect of infrastructure concerns being transferred to the platform. These design principles that worked in Cloud Services 15 years ago are now being applied again to the new workload of AI agents.

---

## The Reality of the Hosting Adapter: Pre-configured Kestrel

From a .NET perspective, it's important to understand exactly what the Hosting Adapter is.

The `Azure.AI.AgentServer.Core` package shares ASP.NET Core's Kestrel server, DI container, and middleware pipeline. The foundational tech stack is the same as a typical ASP.NET Core app. The difference is that instead of configuring `WebApplicationBuilder` directly, **you use the pre-configured host provided by the adapter package**.

Unlike a typical ASP.NET Core app where you compose `builder.Services.AddXxx()`, `app.MapPost()`, and `app.UseMiddleware()` directly in `Program.cs`, in Hosted Agent you just implement `IAgentInvocation.InvokeAsync` with all that composition already done. Routing (`/responses`, `/liveness`, `/readiness`), chunked response configuration for SSE streaming, OpenTelemetry middleware registration, and the authentication processing pipeline are all pre-configured inside the adapter.

```text
Vertical cross-section of the tech stack:

┌─────────────────────────────────────────┐
│  IAgentInvocation.InvokeAsync           │  ← Developer implements
│  (Agent business logic)                 │
├─────────────────────────────────────────┤
│  Azure.AI.AgentServer adapter layer     │  ← Package provides
│  - Foundry Responses API protocol       │
│  - SSE streaming event serialization    │
│  - OpenTelemetry auto-instrumentation   │
│  - OAuth consent handling               │
│  - Tool Client provisioning             │
├─────────────────────────────────────────┤
│  ASP.NET Core middleware pipeline       │  ← Shared stack
│  Kestrel HTTP server                    │
│  DI container, configuration system     │
└─────────────────────────────────────────┘
```

On the Python side, Starlette (an ASGI framework) is used as the embedded web server. The architectural pattern of "the adapter embeds a web server" is the same, with each language choosing the most natural web stack in its ecosystem.

---

## Why You Can't Bypass the Adapter

The question may arise: "Can't I just implement the endpoint spec that Foundry expects directly?" Just match three paths — `/responses`, `/liveness`, `/readiness` — and we're done, right?

The reason this isn't simply a matter of matching a few REST endpoints is that **redefinition at the HTTP protocol level is required**.

An agent's response is not a single JSON blob. It's an **ordered event chain** of `ResponseTextDeltaEvent` → `ResponseTextDoneEvent` → `ResponseContentPartDoneEvent` → `ResponseOutputItemDoneEvent` → `ResponseCompletedEvent`. When this goes out as an HTTP response, it must be an SSE stream based on chunked transfer encoding, and the protocol specifies each event's JSON schema, sequence numbering, and termination conditions.

Looking at .NET's `IAgentInvocation` implementation code, this structure becomes clear. `InvokeAsync` returns `IAsyncEnumerable<ResponseStreamEvent>`, and the adapter receives this stream and converts it to SSE. Each event is assigned a sequence number (`seq`), `ResponseOutputItemDoneEvent` must contain the completed content, and `ResponseCompletedEvent` must include the complete response object.

Implementing this directly means "streaming events of this schema in this order at this path in chunk units, while correctly handling backpressure from the async generator and cleanup on connection disconnection." Add the timing of OpenTelemetry span start/end and the special response format for situations requiring OAuth consent, and you're essentially rebuilding the adapter package from scratch.

So the precise statement is this: **Agent logic can be written in anything, but using what the adapter package provides for the HTTP server layer is the official path.** It's not "freely choose your web server," but rather "on the pre-configured web server provided by the adapter, there is complete freedom in business logic implementation."

In the Cloud Services era, you could have configured IIS directly to behave like a Web Role, but you had to inherit `RoleEntryPoint` and write `.csdef` for Fabric Controller to manage that instance — exactly the same context.

---

## What Enterprise AI Is Missing: Contract-Based Transparency

The real value of Hosted Agent is not "simplification of implementation."

The fundamental problem with self-hosted containers is **opacity**. The platform cannot know how the agent called the LLM inside the container, in what order it used tools, or why it generated that response. No matter how diligently developers implement logging, that's voluntary effort, not a structure guaranteed by the platform.

With Hosted Agent, agent behavior is structurally exposed to the platform thanks to the protocol contract enforced by the adapter.

**Observability is guaranteed at the contract level.** The adapter automatically instruments HTTP requests, model calls, and tool usage. Developers don't need to set up OpenTelemetry. In the Traces tab of the Foundry portal, you can see what decisions the agent made to arrive at its response.

**Quantitative evaluation is integrated into the platform.** Thanks to the response protocol enforced by the adapter, the platform can understand the response structure and directly apply built-in evaluation metrics like Intent Resolution, Task Adherence, and Tool Call Accuracy. With self-hosted containers, you'd have to build this evaluation pipeline from scratch.

**Governance is applied at the identity level.** Before publishing, the agent operates with the project's system-assigned managed identity. At publish time, a dedicated agent identity is separated and registered in the Microsoft Entra Agent Registry. Organizations can centrally control "which agent can access which resources."

**Conversation state is platform-managed.** The container itself operates as a stateless HTTP server, and "what conversations this user had previously" is injected as context by the Agent Service Runtime within the `CreateResponse` request. Developers don't need to implement a conversation state store.

This is the decisive difference when moving beyond PoC to production. The security team asks "Can we track what the agent did?", the compliance team asks "Are the agent's access rights managed?", and executives ask "How do we measure agent quality?" With self-hosted containers, you have to answer all these questions with "We built it ourselves," but with Hosted Agent, you can answer "The platform guarantees it."

---

## Runtime Behavior Model

It's important to precisely understand how Hosted Agent behaves in actual production environments.

The assembly containing agent code operates not as "an agent instantiated per session" but as "a service that statelessly generates responses based on context injected with each request."

```text
[User A session] ──┐
[User B session] ──┤   Agent Service Runtime
[User C session] ──┘   (Conversation state management + routing)
                          │
                 ┌────────┼────────┐
                 ▼        ▼        ▼
             [Replica 1] [Replica 2] [Replica 3]
             (Same container image, stateless)
             (Each request receives that session's conversation context)
```

A separate container doesn't spin up for each session. A small number of replicas handle requests from many sessions, with each request receiving the relevant session's conversation context from the platform. Agent logic is singular, but conversation continuity is guaranteed by the platform.

With `min-replicas 0`, scale-to-zero is possible, and cold start occurs on the first request. For environments where persistent response latency is not acceptable, maintaining `min-replicas 1` or higher is recommended.

---

## Hosted Agent in Code: MCP Tool Integration Example

Let's concretize the architectural discussion at the code level. Focusing on a C# example from Microsoft's official samples that uses an MCP server as a tool in a Hosted Agent, we'll explain how the concepts discussed above are realized in code.

### Environment Setup and Agent Definition

```csharp
var endpoint = Environment.GetEnvironmentVariable("AZURE_FOUNDRY_PROJECT_ENDPOINT")
    ?? throw new InvalidOperationException("AZURE_FOUNDRY_PROJECT_ENDPOINT is not set.");
var model = Environment.GetEnvironmentVariable("AZURE_FOUNDRY_PROJECT_MODEL_ID") ?? "gpt-4.1-mini";

const string AgentName = "MicrosoftLearnAgent";
const string AgentInstructions = "You answer questions by searching the Microsoft Learn content only.";
```

The first thing to notice is that there is **no HTTP server configuration code** in the agent code. Kestrel settings, route mapping, middleware pipeline — code that would be essential in a typical ASP.NET Core app is nowhere to be found. This is the reality of the "adapter provides pre-configured Kestrel" discussed earlier. Developers define only the agent's name, instructions, and model to use.

### MCP Tool Declaration

```csharp
var mcpTool = new MCPToolDefinition(
    serverLabel: "microsoft_learn",
    serverUrl: "https://learn.microsoft.com/api/mcp");
mcpTool.AllowedTools.Add("microsoft_docs_search");
```

`MCPToolDefinition` declares three things: `serverLabel` is the unique identifier for this MCP server, `serverUrl` is the remote MCP server's endpoint, and `AllowedTools` is the allowlist of tools this agent can use from those exposed by the server.

What's important here is that the **agent code does not directly perform the actual communication** with the MCP server. With a self-hosted container approach, you'd have to initialize the MCP client, enumerate the tool list, and parse call results yourself. With Hosted Agent, you just declare the tool definition, and the Agent Service Runtime manages communication with the MCP server at the platform level. This is a concrete example of "contract-based transparency" — because the platform mediates tool calls, it can automatically track which tool was called and when.

### Persistent Agent Creation

```csharp
var persistentAgentsClient = new PersistentAgentsClient(endpoint, new DefaultAzureCredential());

var agentMetadata = await persistentAgentsClient.Administration.CreateAgentAsync(
    model: model,
    name: AgentName,
    instructions: AgentInstructions,
    tools: [mcpTool]);
```

`PersistentAgentsClient` **registers the agent server-side** with the Foundry service. After this call, the agent becomes a managed resource visible in the Foundry portal. `DefaultAzureCredential` automatically selects Azure CLI authentication in development environments and Managed Identity in deployment environments — the client-side implementation of the identity transition structure discussed earlier.

### Tool Approval Policy and Execution

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

`RequireApproval` is the approval policy for MCP tool calls. `"never"` means automatic execution, `"always"` requires user approval for every call. This is the platform standardizing the Human-in-the-Loop pattern that you'd have to implement yourself with self-hosted containers. In enterprise environments, the policy of "this agent must get human approval when calling external tools" can be applied with a single line of code.

```csharp
AIAgent agent = await persistentAgentsClient.GetAIAgentAsync(agentMetadata.Value.Id);
AgentSession session = await agent.CreateSessionAsync();

var response = await agent.RunAsync(
    "Please summarize the Azure AI Agent documentation related to MCP Tool calling?",
    session,
    runOptions);

Console.WriteLine(response);
```

When `agent.RunAsync()` is called, the request is forwarded to the Foundry Agent Service Runtime, which mediates tool calls to the MCP server, passes context to the LLM, and returns the final response as streaming events. In the developer's code, this entire process is abstracted into a single `await` call.

```csharp
await persistentAgentsClient.Administration.DeleteAgentAsync(agent.Id);
```

The cleanup code at the end shows that the agent is a managed resource within Foundry. With a self-hosted container you'd "stop the container," but with Hosted Agent you "delete the agent." The unit of management is the agent itself, not the infrastructure.

### What This Code Tells Us

In the entire codebase, there is **not a single line** about HTTP, streaming, protocol, authentication, or state management. What the developer wrote is only "what model to use, what tools to use, what instructions to give, what the approval policy is." Everything else is handled by the platform.

This is the same pattern where implementing only `OnStart()` and `Run()` in `RoleEntryPoint` let Fabric Controller handle the rest. With a 15-year gap, the same design philosophy is repeating in the AI agent domain.

---

## Reality Check: It's Still a Blueprint

Let's be honest about what needs to be said.

As of March 2026, Hosted Agent is in public preview. And even before Hosted Agent, when connecting an MCP server to a no-code agent and attempting conversations beyond two turns, the agent crashes. It appears that issues arise in serialization/deserialization as tool call history accumulates in conversation state, or that MCP session lifecycle management isn't properly handled at conversation turn boundaries.

Even the constraints of MCP server integration haven't been defined yet. Basic specifications like which transport should be supported (SSE or Streamable HTTP), which MCP protocol version is required, and whether there are constraints on tool schemas are absent from public documentation. The MCP protocol itself is still evolving, and which version and transport Foundry will officially support hasn't been finalized.

There are also explicit preview-stage constraints. 100 Foundry resources including Hosted Agents per Azure subscription, up to 200 Hosted Agents per resource, replicas between 2 and 5. Private networking isn't supported yet either. Billing is scheduled to begin after April 1, 2026.

Putting all of this together, adopting Hosted Agent at this point is premature. If you're running a PoC, calling LLM APIs directly in self-hosted containers is more predictable. You sacrifice platform transparency, but gain the ability to directly control crash causes.

---

## Why You Should Understand This Now Anyway

Understanding Hosted Agent's architecture now is about securing your migration path after GA.

Even when running a PoC with self-hosted containers, if you design the agent's business logic close to the `CreateResponse` → `Response | Stream[ResponseStreamEvent]` contract, wrapping it with the adapter later becomes a relatively simple task. In .NET, structure your logic with the `IAgentInvocation.InvokeAsync(CreateResponseRequest, AgentInvocationContext, CancellationToken)` signature in mind.

And when this architecture stabilizes, the organizations that benefit most are those that need to precisely control complex agent logic through code while meeting enterprise governance requirements. Exactly the teams currently stuck between "declarative agents aren't enough" and "self-hosted containers are too much to handle."

Microsoft has steadily raised the abstraction level of managed compute from Cloud Services to App Service, from App Service to Azure Functions, from Functions to Container Apps. Hosted Agent is attempting a domain-specific PaaS tailored for the AI agent workload, at the latest point in that lineage. From `RoleEntryPoint` to `FoundryCBAgent`, the 15-year-old promise of "the platform provides the host process and developers focus on business logic" is now being tested for validity in the AI era.

---

*This article was published in the [/dev/write](https://devwrite.ai) newsletter.*

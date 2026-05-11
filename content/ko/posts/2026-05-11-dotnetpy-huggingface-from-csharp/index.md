---
title: "C#에서 허깅페이스 모델 호출하기: DotNetPy 0.6.0으로 Whisper · sentence-transformers · Stable Diffusion 돌려보기"
date: 2026-05-11T00:00:00+09:00
draft: false
slug: "dotnetpy-huggingface-from-csharp"
tags:
  - .NET
  - C#
  - Python
  - HuggingFace
  - AI
  - 머신러닝
  - Native AOT
categories:
  - .NET 개발
translationKey: "dotnetpy-huggingface-from-csharp"
description: "DotNetPy 0.6.0으로 C# 앱 안에서 CPython C API를 직접 호출해 Whisper, sentence-transformers, Stable Diffusion을 실행한 경험과, PEP 703 free-threaded 빌드까지 검증한 설계 과정을 정리합니다."
cover:
  image: "images/posts/dotnetpy-huggingface-from-csharp.webp"
  alt: "C#과 Python이 만나는 머신러닝 인터롭 개념 이미지"
tldr: "DotNetPy 0.6.0은 CPython C API를 직접 호출해 .NET 앱에서 Python을 실행하는 라이브러리로, Whisper · sentence-transformers · Stable Diffusion Turbo 샘플이 Native AOT와 PEP 703 free-threaded CPython 빌드 모두에서 동작합니다. 동시 ML 워커는 `Python.CreateIsolated()` 한 줄로 격리된 실행기를 만드는 것으로 충분합니다."
---

<!--
크로스 포스팅 메모:
- 영문 원문(canonical): https://dev.to/rkttu/speech-search-and-stable-diffusion-calling-huggingface-from-c-2bkk
- Velog/Tistory에 옮길 때 SEO 설정의 canonical URL 필드에 위 주소를 지정하면,
  두 글이 검색 결과에서 서로 경쟁하지 않고 dev.to의 점수가 한국어 글의 backlink로 잡힙니다.
-->

> 주말에 작은 C# 라이브러리 [DotNetPy](https://github.com/rkttu/dotnetpy) 의 0.6.0을 출시했습니다. CPython C API를 직접 호출해 .NET 앱 안에서 Python을 실행하는 인터롭 라이브러리입니다. 이 글은 0.6.0에 포함된 세 가지 머신러닝 샘플 — `sentence-transformers` 의미 검색, Whisper 음성 인식, Stable Diffusion Turbo 이미지 생성 — 을 어떻게 묶었고, 그 과정에서 PEP 703 free-threaded CPython까지 어떻게 검증했는지에 대한 기록입니다.

---

## 시작점: C#만 손에 잡혔는데 모델은 허깅페이스에 있을 때

몇 달에 한 번씩 같은 패턴이 반복됩니다. 자막용 Whisper가 필요하거나, 검색용 sentence-transformer가 필요하거나, 가끔은 Stable Diffusion 같은 모델을 써야 하는데 정작 손에 잡은 도구는 C# 한 가지입니다. 이럴 때 흔히 쓰는 우회로는 하나씩 다 결정적인 단점이 있습니다.

- **ONNX로 변환.** 비전이나 인코더 모델에는 잘 맞지만, 새 아키텍처나 diffusion 파이프라인에서는 변환 자체가 별도 프로젝트가 됩니다.
- **Python 마이크로서비스로 띄우기.** 프로세스가 두 개, 배포 시나리오가 두 개, 그리고 핫 패스에 네트워크 홉 하나가 더 붙습니다.
- **외부 API 호출.** 비용이 들고, 인터넷이 필요하고, 데이터가 박스 밖으로 나갑니다.
- **[pythonnet](https://github.com/pythonnet/pythonnet) 이나 [CSnakes](https://github.com/tonybaloney/csnakes) 사용.** 견실한 선택지지만, pythonnet은 아직 Native AOT를 지원하지 않고, CSnakes는 Source Generator 기반 워크플로를 강제합니다. 그리고 두 라이브러리 모두 free-threaded CPython 빌드에 대한 공개된 검증을 아직 내놓지 않았습니다.

저는 좀 더 얇은 선택지를 원했습니다. **C# 코드 안에 Python 스니펫을 문자열로 인라인 작성하고, 배열을 그대로 넘기고, JSON 형태로 결과를 돌려받고, 전체가 AOT 컴파일되어 단일 바이너리로 나오는** 형태입니다. 그것이 DotNetPy의 목표였고, 아래 세 샘플은 모두 GPU 없는 평범한 Windows 11 노트북에서 처음부터 끝까지 동작합니다.

---

## 샘플 1 — `sentence-transformers` 로 의미 검색

첫 번째 샘플은 작은 코퍼스를 임베딩한 뒤, 쿼리를 인코딩해서 가장 비슷한 top-K 문장을 받아옵니다. 반환 값은 `DotNetPyValue` 인데, 내부적으로는 JSON 문서를 감싼 래퍼이고 `GetString()`, `GetInt32()`, `GetDouble()`, 경로 기반 프로퍼티 접근으로 .NET 세계로 되돌아옵니다.

```csharp
using DotNetPy;
using DotNetPy.Uv;

using var project = PythonProject.CreateBuilder()
    .WithProjectName("dotnetpy-ml-embeddings")
    .WithPythonVersion("==3.12.*")
    .AddDependencies(
        "sentence-transformers==2.7.0",
        "transformers==4.40.2",
        "torch>=2.2,<2.5")
    .Build();

await project.InitializeAsync();
var executor = project.GetExecutor();

executor.Execute(@"
import numpy as np
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('all-MiniLM-L6-v2')
");

var corpus = new[]
{
    "Python is a popular programming language for data science.",
    "C# and .NET are great for building enterprise applications.",
    "Rust offers memory safety without garbage collection.",
    "Pizza is delicious with various toppings.",
    // …
};
var query = "Tell me about programming languages";

using var hits = executor.ExecuteAndCapture(@"
corpus_emb = model.encode(corpus, normalize_embeddings=True)
query_emb = model.encode([query], normalize_embeddings=True)[0]
sims = corpus_emb @ query_emb
top_idx = np.argsort(-sims)[:3]
result = [
    {'rank': int(rank + 1), 'score': float(sims[i]), 'text': corpus[int(i)]}
    for rank, i in enumerate(top_idx)
]
", new Dictionary<string, object?> { { "corpus", corpus }, { "query", query } });

foreach (var hit in hits!.RootElement.EnumerateArray())
{
    Console.WriteLine($"  {hit.GetProperty("rank").GetInt32()}. " +
                      $"[{hit.GetProperty("score").GetDouble():F3}] " +
                      $"{hit.GetProperty("text").GetString()}");
}
```

실제 출력은 이렇게 나옵니다.

```text
  1. [0.578] Python is a popular programming language for data science.
  2. [0.370] C# and .NET are great for building enterprise applications.
  3. [0.203] Rust offers memory safety without garbage collection.
```

여기서 흥미로운 지점은 **두 세계의 경계**입니다. `corpus` 는 .NET 의 `string[]` 이고 `query` 는 .NET 의 `string` 인데, Python 쪽에서는 네이티브 list 와 str 로 자연스럽게 도착합니다. 점수가 매겨진 결과는 JSON 문서 한 덩어리로 되돌아오고, .NET 에서는 평소처럼 `JsonElement` API 로 읽으면 끝입니다.

---

## 샘플 2 — Whisper 로 음성-텍스트 변환

모양은 거의 같습니다. 모달리티만 바뀐 셈입니다. `.wav` 나 `.flac` 파일 경로를 넘기면 텍스트와 chunk 단위 타임스탬프가 돌아옵니다. 한 가지 핵심은 **오디오 바이트가 .NET ↔ Python 경계를 절대 건너지 않는다**는 것입니다. Python 이 파일을 직접 열고, 경계로는 구조화된 transcript 만 흐릅니다.

```csharp
var executor = project.GetExecutor();
executor.Execute(@"
from transformers import pipeline
import torch
asr = pipeline(
    'automatic-speech-recognition',
    model='openai/whisper-base.en',
    chunk_length_s=30,
    return_timestamps=True,
    torch_dtype=torch.float32,
)
");

using var transcript = executor.ExecuteAndCapture(@"
out = asr(audio_path)
chunks = [
    {'start': float(c['timestamp'][0]), 'end': float(c['timestamp'][1]),
     'text': c['text'].strip()}
    for c in out.get('chunks', [])
    if c['timestamp'][0] is not None and c['timestamp'][1] is not None
]
result = {'text': out['text'].strip(), 'chunks': chunks}
", new Dictionary<string, object?> { { "audio_path", audioPath } });

Console.WriteLine($"\"{transcript!.GetString("text")}\"");
foreach (var c in transcript.RootElement.GetProperty("chunks").EnumerateArray())
    Console.WriteLine($"  [{c.GetProperty("start").GetDouble():F2}s → " +
                      $"{c.GetProperty("end").GetDouble():F2}s] " +
                      $"{c.GetProperty("text").GetString()}");
```

샘플에 함께 들어있는 퍼블릭 도메인 JFK 클립을 돌리면 이런 결과가 나옵니다.

```text
"And so my fellow Americans, ask not what your country can do for you,
 ask what you can do for your country."

  [0.00s → 11.00s] And so my fellow Americans, ask not what your country can
                   do for you, ask what you can do for your country.
```

`whisper-base.en` 은 290 MB 짜리 모델이고, 11초 클립을 제 노트북 CPU에서 transcribe 하는 데 7초쯤 걸립니다. 두 번째 실행부터는 모델과 가상환경이 캐시되어 첫 실행의 다운로드 비용이 사라집니다.

---

## 샘플 3 — Stable Diffusion Turbo 로 텍스트-이미지

`stabilityai/sd-turbo` 는 1-step diffusion 모델입니다. CPU 에서 512×512 한 장을 만드는 데 약 30초, 요즘 GPU 에서는 2초 안팎입니다. 여기서도 .NET 쪽은 이미지 바이트를 보지 않습니다. Python 이 PNG 를 디스크에 저장하고, 메타데이터만 돌려줍니다.

```csharp
executor.Execute(@"
import torch
from diffusers import AutoPipelineForText2Image
pipe = AutoPipelineForText2Image.from_pretrained(
    'stabilityai/sd-turbo',
    torch_dtype=torch.float32,
    safety_checker=None, requires_safety_checker=False,
)
pipe.set_progress_bar_config(disable=True)
");

using var meta = executor.ExecuteAndCapture(@"
import time, os
t0 = time.time()
img = pipe(prompt=prompt, num_inference_steps=1, guidance_scale=0.0).images[0]
elapsed = time.time() - t0
out_path = os.path.join(out_dir, 'generated.png')
img.save(out_path)
result = {
    'path': out_path,
    'width': img.size[0],
    'height': img.size[1],
    'size_bytes': os.path.getsize(out_path),
    'elapsed_seconds': elapsed,
}
", new Dictionary<string, object?>
{
    { "prompt", "a serene mountain lake at sunset, oil painting style" },
    { "out_dir", outDir },
});

Console.WriteLine($"  Saved:   {meta!.GetString("path")}");
Console.WriteLine($"  Size:    {meta.GetInt32("width")}×{meta.GetInt32("height")} px, " +
                  $"{meta.GetInt32("size_bytes"):N0} bytes");
Console.WriteLine($"  Inference: {meta.GetDouble("elapsed_seconds"):F2}s");
```

출력은 다음과 같습니다.

```text
  Saved:   .../samples/ml-image-gen/output/generated.png
  Size:    512×512 px, 434,242 bytes
  Inference: 31.19s
```

세 샘플을 거치면서 강조하고 싶은 패턴이 하나 있습니다. **경계를 건너는 것은 구조화된 데이터뿐**이라는 것입니다. PNG 바이트 (~400KB), 임베딩 행렬, float32 텐서는 모두 Python 쪽에 머무릅니다. .NET 쪽에서는 작은 프롬프트 한 줄이 들어가고 작은 JSON 객체 하나가 돌아오는 것만 보면 됩니다. 이 분리가 Native AOT 호환을 가능하게 해주는 가장 중요한 설계 결정입니다.

---

## 설치와 첫 실행

라이브러리 자체는 평범한 NuGet 패키지입니다.

```bash
dotnet add package DotNetPy --version 0.6.0
```

위 샘플을 그대로 따라하고 싶다면, 저장소의 [`samples/`](https://github.com/rkttu/dotnetpy/tree/main/samples) 디렉터리에 위 세 가지에 더해 AOT 로 빌드한 네이티브 DLL을 C export 로 호출하는 [`native-aot`](https://github.com/rkttu/dotnetpy/tree/main/samples/native-aot) 컨슈머가 같이 들어있습니다. DotNetPy를 C / C++ / Rust 호스트에 임베드하는 경로입니다.

ML 샘플들은 [uv](https://docs.astral.sh/uv/) 를 사용해서 C# 안에서 선언적으로 Python + 허깅페이스 스택을 프로비저닝합니다.

```csharp
using var project = PythonProject.CreateBuilder()
    .WithProjectName("my-app")
    .WithPythonVersion("==3.12.*")
    .AddDependencies("transformers==4.40.2", "torch>=2.2,<2.5")
    .Build();

await project.InitializeAsync();
```

이것이 전부입니다. 별도의 Python 설치도 필요 없고, venv 를 직접 만들 일도 없습니다.

---

## 진짜 신경 쓴 부분 — PEP 703 free-threaded Python

인터롭 라이브러리 관점에서 흥미로운 변곡점이 2025–26년에 도착했습니다. CPython 3.13 에 **free-threaded 빌드** (`t` 접미사가 붙은 `python3.13t`) 가 도입되면서, GIL 이 사라지고 동시에 실행되는 스레드들이 *진짜로* 병렬로 Python 코드를 실행할 수 있게 됩니다. ML 서빙에는 환상적인 변화입니다. 한 프로세스 안에 추론 워커를 여러 개 두고 싶을 테니까요. 동시에, 기존 GIL 가정 위에 쓰여 있던 수많은 라이브러리의 암묵적 불변 조건이 깨지는 시점이기도 합니다.

특히 pythonnet 도 이 작업을 진행 중인데, [PR #2721](https://github.com/pythonnet/pythonnet/pull/2721) 이 필요한 작업을 다섯 가지 범주로 정리해 두었습니다.

1. Refcount 레이아웃 변경 (`ob_refcnt` 가 split 구조로 바뀜)
2. 동시 타입 / 객체 캐시 경합
3. `Reflection.Emit` 스레드 안전성
4. `GCHandle` 슬롯 소유권 원자성
5. Finalizer / `Py_Finalize` 경합

DotNetPy 0.6.0 을 만들 때 저는 pythonnet의 PR 을 일종의 **감사용 체크리스트** 처럼 활용했습니다. 다섯 가지 범주를 하나하나 적용해 보면서 DotNetPy 가 같은 함정에 빠지는지 점검한 것입니다. 결과적으로, **다섯 항목 중 네 가지는 DotNetPy 의 설계 자체가 해당 사항을 비껴갑니다.** .NET 과 Python 의 타입 시스템을 다리 놓지 않고, CLR 타입을 Python 서브클래스로 만들지도 않으며, `Reflection.Emit` 을 사용하지 않고, Python 에 `GCHandle` 슬롯을 노출하지도 않고, `Py_Finalize` 를 호출하지도 않기 때문입니다. 다섯 번째 항목(finalizer / shutdown)은 `SafeHandle.ReleaseHandle` 의 `Py_DecRef` 호출 주변에 명시적인 `PyGILState_Ensure` 가드를 두어 해결했습니다.

감사 과정에서 실제로 발견되어 0.6.0 에서 수정한 문제는 다음과 같습니다.

- **공유 `__main__` globals 안의 내부 임시 변수 이름 충돌.** 모든 헬퍼 변수(`_json_result`, `_is_valid`, …)를 `Interlocked.Increment` 로 호출마다 고유하게 발급하도록 바꿔서, 동시에 실행되는 두 호출자가 같은 슬롯을 두고 경합하지 않도록 했습니다.
- **`Evaluate` 가 공유 `result` 전역을 흘려보내던 문제.** 같은 패턴으로 해결했습니다. 호출마다 고유한 싱크 이름을 발급하고, `finally` 에서 깔끔하게 정리합니다.
- 위 두 수정이 미묘하게 맞물리는데, 출시 시점에도 사용자 변수 주입(`Execute` / `ExecuteAndCapture` 의 `variables:` 파라미터) 은 여전히 공유 `__main__` globals 로 들어갑니다. 동시 호출자가 같은 사용자 변수 이름을 쓰면 충돌이 그대로 남아 있습니다.

세 번째 문제에 대한 해법이 0.6.0 의 가장 눈에 띄는 추가 기능, 격리된 실행기 팩토리 메서드입니다.

```csharp
using var iso = Python.CreateIsolated();
iso.Execute("import json");
iso.Execute("data = {'k': 1}");   // `data` 는 이 실행기만 봅니다
```

`CreateIsolated()` 는 자체 Python dict (사전 채워진 `__builtins__` 포함) 을 소유한 실행기를 만듭니다. 격리된 실행기들은 공유 싱글톤, 그리고 다른 격리 실행기들과 같은 프로세스에서 공존하지만, 서로 사이로 변수가 새지 않습니다.

이 덕분에 동시 ML 패턴이 굉장히 간결해집니다.

```csharp
Parallel.For(0, Environment.ProcessorCount, threadId =>
{
    using var iso = Python.CreateIsolated();
    iso.Execute("import torch; from transformers import pipeline");
    iso.Execute(@"
asr = pipeline('automatic-speech-recognition',
               model='openai/whisper-base.en')
");
    using var r = iso.ExecuteAndCapture(@"
out = asr(audio_path)
result = {'text': out['text']}
", new Dictionary<string, object?> { { "audio_path", path } });

    Console.WriteLine(r?.GetString("text"));
});
```

free-threaded CPython 빌드 위에서 이 루프는 **진짜로 병렬로 돕니다.** 모든 워커가 자기만의 `asr` 파이프라인과 자기만의 Python 네임스페이스를 가집니다. 기존 GIL 빌드에서는 같은 코드가 정확하게 동작하긴 해도 인터프리터에서 직렬화됩니다. 어차피 이건 어떤 인터롭 라이브러리를 써도 부딪히는 벽이라서 DotNetPy 가 해결할 수 있는 문제는 아닙니다.

세 가지 빌드 조합으로 매트릭스 검증을 마쳤습니다.

| Python 빌드 | 단위 테스트 | Native AOT 컨슈머 |
| --- | --- | --- |
| CPython 3.13 (GIL, auto-discovered) | 209 / 1 / **0** | 8 / 8 ✅ |
| CPython 3.13.13t (free-threaded) | 205 / 5 / **0** | 8 / 8 ✅ |
| CPython 3.14.4t (free-threaded) | 205 / 5 / **0** | 8 / 8 ✅ |

전체 감사 결과는 [`docs/FREETHREADED-AUDIT.md`](https://github.com/rkttu/dotnetpy/blob/main/docs/FREETHREADED-AUDIT.md) 에 정리해 두었습니다. 의도적으로 공개 문서로 두었습니다. "검증했습니다" 라고 말할 때 그 말이 정확히 무슨 의미인지를 독자가 직접 읽어볼 수 있도록 하기 위해서입니다.

---

## 솔직하게 짚어둘 한계

몇 가지는 분명하게 짚고 가야 합니다.

- **DotNetPy 는 아직 0.6.0.** 실험 단계이며, 프로덕션 안정 단계가 아닙니다. 적지 않은 패턴이 아직 정리되는 중입니다.
- **Python ML 스택 자체가 완전히 free-threaded 가 아닙니다.** PyTorch 의 FT 지원은 활발히 마이그레이션 중이고, NumPy 2.1+ 가 PEP 703 을 지원합니다. `transformers` 와 `diffusers` 는 동작은 하지만, 내부 C 확장 모듈들의 상태는 제각각입니다. 업스트림 스택이 따라잡기 전까지는 DotNetPy 인터롭 계층에서는 free-threaded 환경의 정합성을 얻지만, Python 쪽 ML 성능 자체는 여전히 라이브러리 내부 락을 통해 직렬화될 수 있습니다.
- **Native AOT 퍼블리시는 플랫폼별 C 툴체인을 요구합니다.** Windows 는 Visual Studio C++ build tools, Linux 는 `clang` / `lld` 가 필요합니다. AOT 컴파일하는 일반 .NET 앱과 동일한 제약입니다.
- **JSON 마샬링이 데이터 평면.** 모든 결과 변수는 Python 쪽에서 직렬화되고 .NET 쪽에서 `System.Text.Json` 으로 역직렬화됩니다. Native AOT 호환을 얻기 위한 의도된 트레이드오프입니다. 결과 객체가 매우 큰 워크로드라면, 여러 값을 한 번의 capture 호출 안에서 묶고 작은 구조화 요약만 반환하는 패턴을 권장합니다.

---

## 더 알아보려면

- **코드**: <https://github.com/rkttu/dotnetpy>
- **NuGet**: `dotnet add package DotNetPy --version 0.6.0`
- **샘플**: [`samples/ml-embeddings`](https://github.com/rkttu/dotnetpy/tree/main/samples/ml-embeddings), [`samples/ml-whisper`](https://github.com/rkttu/dotnetpy/tree/main/samples/ml-whisper), [`samples/ml-image-gen`](https://github.com/rkttu/dotnetpy/tree/main/samples/ml-image-gen) — 각각 `dotnet run sample.cs` 한 번으로 끝납니다.
- **Free-threaded 감사 문서**: [`docs/FREETHREADED-AUDIT.md`](https://github.com/rkttu/dotnetpy/blob/main/docs/FREETHREADED-AUDIT.md)
- **pythonnet / CSnakes / IronPython 과의 비교 (의사 결정 트리 포함)**: [`docs/COMPARISON.md`](https://github.com/rkttu/dotnetpy/blob/main/docs/COMPARISON.md)
- **영문 원문**: [dev.to](https://dev.to/rkttu/speech-search-and-stable-diffusion-calling-huggingface-from-c-2bkk)

"C# 으로 지금 막 발표된 허깅페이스 모델을 어떻게 돌리지" 라는 질문에 한 가지 답이 될 수 있었으면 좋겠습니다. 이슈, PR, 댓글 모두 환영합니다. 한국 닷넷 커뮤니티에서 같은 고민을 하고 계신 분들이 있다면 한 번 시도해 보시고 피드백 주세요.

---

*이 글은 [/dev/write](https://devwrite.ai) 뉴스레터에서 발행되었습니다.*

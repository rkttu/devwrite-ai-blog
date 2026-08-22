---
title: "Calling Hugging Face Models from C#: Running Whisper, sentence-transformers, and Stable Diffusion with DotNetPy 0.6.0"
date: 2026-05-11T00:00:00+09:00
draft: false
slug: "dotnetpy-huggingface-from-csharp"
tags:
  - .NET
  - C#
  - Python
  - HuggingFace
  - AI
  - Machine Learning
  - Native AOT
categories:
  - .NET Development
translationKey: "dotnetpy-huggingface-from-csharp"
description: "How DotNetPy 0.6.0 calls CPython's C API directly from .NET to run Whisper, sentence-transformers, and Stable Diffusion — plus what it took to validate the design on PEP 703 free-threaded builds."
cover:
  image: "images/posts/dotnetpy-huggingface-from-csharp.webp"
  alt: "Conceptual image of C# and Python meeting for machine learning interop"
tldr: "DotNetPy 0.6.0 calls CPython's C API directly from .NET, and its Whisper · sentence-transformers · Stable Diffusion Turbo samples all run on both Native AOT and PEP 703 free-threaded CPython builds. Concurrent ML workers boil down to a single `Python.CreateIsolated()` call that hands you an isolated executor."
---

<!--
Cross-posting note:
- Canonical English version: https://dev.to/rkttu/speech-search-and-stable-diffusion-calling-huggingface-from-c-2bkk
- This blog hosts an authored variant for the /dev/write audience.
-->

> Over the weekend I shipped 0.6.0 of [DotNetPy](https://github.com/rkttu/dotnetpy), a small C# library that calls CPython's C API directly to run Python inside a .NET app. This post walks through the three machine learning samples bundled with 0.6.0 — semantic search with `sentence-transformers`, speech recognition with Whisper, and text-to-image with Stable Diffusion Turbo — and explains how the same release was also validated on PEP 703 free-threaded CPython.

---

## Starting Point: You Only Have C#, but the Model Lives on Hugging Face

Every few months the same pattern repeats. I need Whisper for subtitles, or a sentence-transformer for search, or occasionally something like Stable Diffusion — but the only tool in hand is C#. The usual workarounds all come with a decisive downside.

- **Convert to ONNX.** Works well for vision and encoder models, but for newer architectures or diffusion pipelines, the conversion itself becomes a separate project.
- **Stand up a Python microservice.** That doubles your processes, doubles your deployment story, and adds a network hop to the hot path.
- **Call a hosted API.** Costs money, requires the internet, and pushes data outside the box.
- **Use [pythonnet](https://github.com/pythonnet/pythonnet) or [CSnakes](https://github.com/tonybaloney/csnakes).** Both are solid choices, but pythonnet does not yet support Native AOT, and CSnakes forces a Source Generator–based workflow. Neither has published a validation pass on free-threaded CPython builds yet.

I wanted something thinner: **write Python snippets inline as strings inside C#, hand arrays straight across, get JSON-shaped results back, and have the whole thing AOT-compile into a single binary.** That's the goal of DotNetPy, and all three samples below run end-to-end on an ordinary Windows 11 laptop with no GPU.

---

## Sample 1 — Semantic Search with `sentence-transformers`

The first sample embeds a small corpus, encodes a query, and returns the top-K most similar sentences. The return value is a `DotNetPyValue` — a wrapper around a JSON document — that comes back to the .NET side through `GetString()`, `GetInt32()`, `GetDouble()`, and path-based property access.

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

Running this prints:

```text
  1. [0.578] Python is a popular programming language for data science.
  2. [0.370] C# and .NET are great for building enterprise applications.
  3. [0.203] Rust offers memory safety without garbage collection.
```

The interesting part here is **the boundary between the two worlds**. `corpus` is a .NET `string[]` and `query` is a .NET `string`, but they arrive on the Python side as a native list and `str`. The scored results come back as a single JSON document, and the .NET side reads them with the same `JsonElement` API you'd use anywhere else.

---

## Sample 2 — Speech-to-Text with Whisper

The shape is almost identical — only the modality changes. You hand it a path to a `.wav` or `.flac` file, and you get back text plus chunk-level timestamps. The one thing worth highlighting: **the audio bytes never cross the .NET ↔ Python boundary.** Python opens the file directly; only a structured transcript flows back across the boundary.

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

Running it on the public-domain JFK clip that ships with the sample produces:

```text
"And so my fellow Americans, ask not what your country can do for you,
 ask what you can do for your country."

  [0.00s → 11.00s] And so my fellow Americans, ask not what your country can
                   do for you, ask what you can do for your country.
```

`whisper-base.en` is a 290 MB model, and transcribing the 11-second clip takes about 7 seconds on my laptop's CPU. From the second run onward, the model and virtualenv are cached, so the first-run download cost disappears.

---

## Sample 3 — Text-to-Image with Stable Diffusion Turbo

`stabilityai/sd-turbo` is a 1-step diffusion model. Generating a single 512×512 image takes about 30 seconds on CPU, and roughly 2 seconds on a modern GPU. Once again, the .NET side never sees the image bytes — Python writes the PNG to disk and only metadata flows back.

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

Which prints:

```text
  Saved:   .../samples/ml-image-gen/output/generated.png
  Size:    512×512 px, 434,242 bytes
  Inference: 31.19s
```

There's one pattern I want to call out across all three samples. **Only structured data crosses the boundary.** PNG bytes (~400 KB), embedding matrices, float32 tensors — all of those stay on the Python side. The .NET side only sees a short prompt going in and a small JSON object coming back. That separation is the single most important design decision that makes Native AOT compatibility possible.

---

## Installation and a First Run

The library itself is an ordinary NuGet package.

```bash
dotnet add package DotNetPy --version 0.6.0
```

If you want to follow the samples above, the repository's [`samples/`](https://github.com/rkttu/dotnetpy/tree/main/samples) directory contains those three plus a [`native-aot`](https://github.com/rkttu/dotnetpy/tree/main/samples/native-aot) consumer that calls an AOT-built native DLL via C exports — the path for embedding DotNetPy in C / C++ / Rust hosts.

The ML samples use [uv](https://docs.astral.sh/uv/) to declaratively provision Python plus the Hugging Face stack from inside C#.

```csharp
using var project = PythonProject.CreateBuilder()
    .WithProjectName("my-app")
    .WithPythonVersion("==3.12.*")
    .AddDependencies("transformers==4.40.2", "torch>=2.2,<2.5")
    .Build();

await project.InitializeAsync();
```

That's it. No separate Python install, no manual venv setup.

---

## What I Actually Sweated Over — PEP 703 Free-Threaded Python

From an interop library's point of view, an interesting inflection point arrived in 2025–26. CPython 3.13 introduced a **free-threaded build** (`python3.13t`, with a `t` suffix) that removes the GIL so concurrently scheduled threads can *actually* execute Python code in parallel. For ML serving that's a fantastic shift — you genuinely want multiple inference workers in a single process. At the same time, it's the moment when implicit invariants in countless libraries that were written against the GIL start to break.

pythonnet is working through the same transition, and [PR #2721](https://github.com/pythonnet/pythonnet/pull/2721) organizes the required work into five categories.

1. Refcount layout changes (`ob_refcnt` becomes a split structure)
2. Concurrent type / object cache contention
3. `Reflection.Emit` thread safety
4. Atomic ownership of `GCHandle` slots
5. Finalizer / `Py_Finalize` races

While building DotNetPy 0.6.0, I used the pythonnet PR as **an audit checklist** — going through the five categories one by one to check whether DotNetPy fell into the same traps. The result: **four of the five categories don't apply to DotNetPy by design.** DotNetPy doesn't bridge .NET and Python type systems, doesn't subclass CLR types into Python, doesn't use `Reflection.Emit`, doesn't expose `GCHandle` slots to Python, and doesn't call `Py_Finalize`. The fifth (finalizer / shutdown) was resolved by placing an explicit `PyGILState_Ensure` guard around the `Py_DecRef` call inside `SafeHandle.ReleaseHandle`.

What the audit *did* surface, and what 0.6.0 fixes:

- **Name collisions for internal temporary variables inside the shared `__main__` globals.** Every helper variable (`_json_result`, `_is_valid`, …) is now issued uniquely per call with `Interlocked.Increment`, so two concurrent callers no longer race over the same slot.
- **`Evaluate` leaking a shared `result` global.** Same fix — issue a unique sink name per call, and clean it up in `finally`.
- The two fixes interact subtly with a third issue that's still present in this release: user variable injection (the `variables:` parameter on `Execute` / `ExecuteAndCapture`) still lands in the shared `__main__` globals. Concurrent callers using the same user variable name will still collide.

The fix for that third issue is the headline addition of 0.6.0: an isolated executor factory method.

```csharp
using var iso = Python.CreateIsolated();
iso.Execute("import json");
iso.Execute("data = {'k': 1}");   // `data` is only visible to this executor
```

`CreateIsolated()` builds an executor that owns its own Python dict (pre-populated with `__builtins__`). Isolated executors coexist in the same process with the shared singleton and with each other, but no variables leak between them.

This makes the concurrent ML pattern remarkably concise.

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

On a free-threaded CPython build this loop **actually runs in parallel.** Every worker has its own `asr` pipeline and its own Python namespace. On a stock GIL build the same code runs correctly, but the interpreter serializes execution. That's a wall every interop library hits — it isn't something DotNetPy can solve.

I ran the matrix across three build combinations.

| Python build | Unit tests | Native AOT consumer |
| --- | --- | --- |
| CPython 3.13 (GIL, auto-discovered) | 209 / 1 / **0** | 8 / 8 ✅ |
| CPython 3.13.13t (free-threaded) | 205 / 5 / **0** | 8 / 8 ✅ |
| CPython 3.14.4t (free-threaded) | 205 / 5 / **0** | 8 / 8 ✅ |

The full audit lives at [`docs/FREETHREADED-AUDIT.md`](https://github.com/rkttu/dotnetpy/blob/main/docs/FREETHREADED-AUDIT.md). I left it as a public document on purpose — when someone says "we validated this," I want readers to be able to see exactly what that means.

---

## Limitations, Stated Plainly

A few things are worth calling out explicitly.

- **DotNetPy is still 0.6.0.** It's experimental, not production-stable. Plenty of patterns are still being shaken out.
- **The Python ML stack itself isn't fully free-threaded yet.** PyTorch's FT support is actively migrating, and NumPy 2.1+ supports PEP 703. `transformers` and `diffusers` work, but the state of their internal C extension modules varies. Until the upstream stack catches up, you get free-threaded coherence at the DotNetPy interop layer, but Python-side ML throughput can still serialize through library-internal locks.
- **Native AOT publishing requires a platform-specific C toolchain.** Windows needs Visual Studio C++ build tools; Linux needs `clang` / `lld`. Same constraint as any AOT-compiled .NET app.
- **JSON marshalling is the data plane.** All result variables are serialized on the Python side and deserialized with `System.Text.Json` on the .NET side. It's a deliberate trade-off to get Native AOT compatibility. If your workload returns very large result objects, the recommended pattern is to bundle multiple values into a single capture call and return only a small structured summary.

---

## Further Reading

- **Code**: <https://github.com/rkttu/dotnetpy>
- **NuGet**: `dotnet add package DotNetPy --version 0.6.0`
- **Samples**: [`samples/ml-embeddings`](https://github.com/rkttu/dotnetpy/tree/main/samples/ml-embeddings), [`samples/ml-whisper`](https://github.com/rkttu/dotnetpy/tree/main/samples/ml-whisper), [`samples/ml-image-gen`](https://github.com/rkttu/dotnetpy/tree/main/samples/ml-image-gen) — each runs end-to-end with a single `dotnet run sample.cs`.
- **Free-threaded audit**: [`docs/FREETHREADED-AUDIT.md`](https://github.com/rkttu/dotnetpy/blob/main/docs/FREETHREADED-AUDIT.md)
- **Comparison with pythonnet / CSnakes / IronPython (with a decision tree)**: [`docs/COMPARISON.md`](https://github.com/rkttu/dotnetpy/blob/main/docs/COMPARISON.md)
- **Original English version on dev.to**: [dev.to](https://dev.to/rkttu/speech-search-and-stable-diffusion-calling-huggingface-from-c-2bkk)

I'd be happy if this turns into one possible answer to "how do I actually run a just-released Hugging Face model from C#?" Issues, PRs, and comments are all welcome. If you're in the .NET community and have been wrestling with the same problem, please give it a try and let me know how it goes.

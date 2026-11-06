# Local model inventory and official candidate catalog

Checked: 2026-10-19 Asia/Kolkata. Inference and model inventory are local-only. No candidate was downloaded.

## Hardware and installed inventory

- Hardware summary: Apple M5 MacBook Air, 10 CPU cores (4 performance / 6 efficiency), 16 GB unified memory. Serial and device identifiers omitted.
- Provider: Ollama 0.34.2.
- `llama3:latest`: digest `365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1`; GGUF, 8.0B parameters, Q4_0, model metadata context length 8,192, installed size 4,661,224,676 bytes.
- `gemma3:12b-it-q4_K_M`: digest `b92b218582c521ba287f38f1d6057dcd3c6cbff036f13cac97b5d861f5e58ec3`; GGUF, 11.8B parameters, Q4_K_M, model metadata context length 131,072, installed size 8,164,039,732 bytes, with completion and vision capabilities. The user selected and authorized this artifact on 2026-10-19. Local inference screening began at context 4,096; metadata context is not an active allocation or quality claim.
- `nomic-embed-text:latest`: digest `0a109f422b47e3a30ba2b10eca18548e944e8a23073ee3f3e947efcf3c45e59f`; F16, 137M, installed size 274,302,450 bytes, embedding-only capability. Not a chat candidate.
- During warm shadow runs the active `llama3:latest` allocation reported 5,003,804,671 bytes in `size` / `size_vram` and runtime context length 4,096. This differs from the model metadata maximum of 8,192 and was the reason the first run set was quarantined. The evaluation runner now reads `/api/ps` and requires the observed active context to match the declared run context.

Source: local read-only `ollama list`, `ollama show llama3:latest --verbose`, `ollama --version`, and `GET http://127.0.0.1:11434/api/tags` / `/api/ps`. Commands required elevated local endpoint access; no request generated text. Installed Llama digest matches the pinned historical tag digest in the baseline replay metadata.

## Official Ollama catalog information

The selected Gemma artifact is locally installed and digest-verified. Qwen3 remains an unselected catalog candidate. Catalog size is the artifact download size, not required runtime memory. Advertised context is family capability, not the active context allocated on this 16 GB device.

| Candidate | Official listing | Initial compatibility note |
|---|---|---|
| `gemma3:12b-it-q4_K_M` | 8.2 GB, 11.8B parameters, Q4_K_M, 128K family context; catalog short digest `b92b218582c5` | Downloaded with user authorization and locally verified. Runtime memory and comparative quality remain measurement questions. |
| `qwen3:14b-q4_K_M` | 9.3 GB, 14B family, 40K family context; catalog short digest `bdbd181c33f2` | Larger than baseline, with a 9.3 GB artifact. Full digest and actual Ollama format/quantization must be verified after any authorized download. |

Catalog references checked on 2026-10-19:

- Ollama's [Gemma 3 tags](https://ollama.com/library/gemma3/tags) list the 12B Q4_K_M artifact at 8.2 GB and a 128K family context.
- Ollama's [Qwen3 tags](https://ollama.com/library/qwen3/tags) list the 14B Q4_K_M artifact at 9.3 GB and a 40K family context.
- Ollama's [Llama 3 tags](https://ollama.com/library/llama3/tags) list the installed baseline family and its 8K context.
- Ollama's [OpenAI compatibility documentation](https://github.com/ollama/ollama/blob/main/docs/api/openai-compatibility.mdx) says the OpenAI API does not configure model context size; its documented route is a Modelfile `PARAMETER num_ctx` setting. This checkout's runner therefore records and checks the active context from `/api/ps` instead of treating the CLI argument as proof.

No quality claim is derived from model size, family descriptions, or catalog benchmarks. The selected artifact's exact full digest and quantization are verified locally. Active context, memory, latency, format support, and paired response quality are measured separately in the run manifest/ledger.

User decision update (2026-10-20 Asia/Kolkata): Gemma's local resource cost is too high for this computer; continue with the existing `llama3:latest` only. Gemma inference was stopped, and the latest Ollama `/api/ps` readback showed no model loaded. The Gemma artifact remains installed; no removal was requested.

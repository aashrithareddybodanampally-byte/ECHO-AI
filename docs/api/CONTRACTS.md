# ECHO-AI — API & Service Contracts (Phase 2.5)

> **Status:** Contracts defined. **No implementations exist.** Every endpoint below
> authenticates the caller, validates input, and then returns
> `501 Not Implemented` until a later phase registers a real service.
>
> These are versioned contracts (`/api/v1`). Do not rename fields or paths
> without updating this document, the schemas, the tests, and all consumers.

All emotion, sentiment and fusion outputs are **model predictions, not
clinical or psychological diagnoses**, and must never be presented as such.

---

## Conventions

| Topic | Rule |
|---|---|
| Base path | `/api/v1` |
| Auth | Every endpoint in this document requires `Authorization: Bearer <JWT>` (from `POST /api/v1/auth/login`). |
| Ownership | The user is always taken from the token, never from the request body. A resource owned by another user is treated exactly like a nonexistent one (`404`). |
| Confidence format | Every score, confidence and probability is a float in `[0.0, 1.0]`. |
| Labels | Emotion, sentiment and state labels are strings. The label set comes from the dataset/model selected in a later phase and is **not** fixed by this contract. |
| Model versioning | Every ML result carries `model_version` so the deployed model is identifiable. |
| Errors | JSON body `{"detail": ...}` (FastAPI default). |

### Status codes

| Code | When |
|---|---|
| `401` | Missing, malformed, invalid or expired token. Checked before anything else. |
| `404` | Referenced conversation/message does not exist **or** belongs to another user. Body is always `{"detail": "Not found"}`. |
| `413` | `POST /emotion/analyze` body larger than `MAX_AUDIO_UPLOAD_BYTES` (25 MB). |
| `415` | `POST /emotion/analyze` with a non-`audio/*` `Content-Type`. |
| `422` | Request fails schema validation, or a service rejects well-formed but unusable input (e.g. no speech detected). |
| `501` | The service behind the endpoint is not implemented yet (current state for all endpoints below). |

### Latency

Not measured yet. No latency targets have been set; they must be defined and
measured in the phase that implements each service.

---

## Endpoints

### `POST /api/v1/emotion/analyze` — voice emotion

Request: raw audio bytes as the request body, `Content-Type: audio/*`
(e.g. `audio/wav`). Empty body → `422`.

Maximum upload size: **25 MB** (26,214,400 bytes), configured by the
`MAX_AUDIO_UPLOAD_BYTES` setting (`backend/app/config.py`, overridable via
environment). A larger `Content-Length`, or a streamed body that exceeds the
limit, is rejected with `413` without passing the audio to the service.

Check order: authentication (`401`) → service availability (`501`) →
`Content-Type` (`415`) → size (`413`) → empty body (`422`). The body is not
read until authentication has succeeded.

Response `200` — `VoiceEmotionResult`:

```json
{
  "emotion": "sad",
  "confidence": 0.74,
  "probabilities": {"sad": 0.74, "neutral": 0.16, "angry": 0.06, "happy": 0.04},
  "model_version": "emotion_model_v1"
}
```

Rules: `emotion` must be a key of `probabilities`; `probabilities` must sum to
1.0 (±0.001); `confidence` must equal `probabilities[emotion]`.
Unusable audio (no speech, too noisy, empty recording) → `422` rather than a
low-quality prediction.

### `POST /api/v1/emotion/fusion` — multimodal fusion

Request — `FusionRequest` (at least one of `voice` / `text` required):

```json
{
  "voice": { "...VoiceEmotionResult..." },
  "text": {"sentiment": "negative", "emotion": "frustration", "confidence": 0.81, "model_version": "text_model_v1"},
  "context": {"label": "exam-related stress", "score": 0.65}
}
```

Response `200` — `FusionResult`:

```json
{"state": "stressed", "confidence": 0.79, "signals": {"voice": 0.72, "text": 0.81, "context": 0.65}}
```

The fusion method (weights, learned model) is **not** part of the contract.

### `POST /api/v1/rag/retrieve` — retrieval

Request: `{"query": "study breaks", "top_k": 5}`. `query` must not be blank (whitespace-only is rejected); `top_k`
is `1–20`, default `5`.

Response `200`:

```json
{"query": "study breaks", "chunks": [{"source": "Study Resource A", "content": "...", "score": 0.9}]}
```

`score` range depends on the similarity metric chosen in the RAG phase.

### `POST /api/v1/chat` — conversation turn

Request: `{"message": "I'm really tired.", "conversation_id": 12}`. `message`
must not be blank. Omit `conversation_id` to start a new conversation.

Response `200` — `ChatResponse`:

```json
{
  "conversation_id": 12,
  "reply": {"id": 34, "conversation_id": 12, "role": "assistant", "content": "...", "created_at": "2026-01-01T00:00:00Z"},
  "sources": [],
  "emotion": null
}
```

`sources` lists the chunks that supported the reply (empty if retrieval was
not used). `emotion` is present only when emotion signals were available.

### `POST /api/v1/feedback` — "Was this helpful?"

Request: `{"message_id": 34, "helpful": true}`. Response `201`:
`{"message_id": 34, "helpful": true}`. A message outside the user's
conversations → `404`.

### `GET /api/v1/history` — conversation history

Query: `limit` (`1–100`, default `20`), `offset` (`≥0`, default `0`).

Response `200`: `{"conversations": [{"id", "title", "created_at", "updated_at", "messages": [...]}]}`.
Messages are in chronological order (oldest first). Only the caller's
conversations are returned.

### `GET /api/v1/analytics` — per-user summary

Response `200`:

```json
{"emotion_distribution": {"neutral": 3, "sad": 1}, "feedback": {"helpful": 2, "not_helpful": 1}}
```

---

## Service interfaces

Defined in `backend/app/services/interfaces.py` as `typing.Protocol`s, so
implementations in `ml/`, `rag/` and `safety/` satisfy them structurally
without importing backend modules. Routes receive services through the
dependencies in `backend/app/services/providers.py`, which currently raise
`501`.

| Interface | Method | Returns | Exposed via |
|---|---|---|---|
| `VoiceEmotionService` | `analyze(audio: bytes, content_type: str)` | `VoiceEmotionResult` | `/emotion/analyze` |
| `SpeechToTextService` | `transcribe(audio: bytes, content_type: str)` | `TranscriptionResult` (`text`, `language?`, `confidence?`) | internal |
| `TextAnalysisService` | `analyze(text: str)` | `TextAnalysisResult` | internal |
| `FusionService` | `fuse(request: FusionRequest)` | `FusionResult` | `/emotion/fusion` |
| `RetrievalService` | `retrieve(query: str, top_k: int)` | `list[RetrievedChunk]` | `/rag/retrieve` |
| `LLMService` | `generate(request: LLMRequest)` | `LLMResponse` (`content`, `model`) | internal |
| `SafetyService` | `check_input(text)` / `check_output(text)` | `InputSafetyAssessment` (`level`: `normal` \| `distress` \| `high_risk`) / `OutputSafetyAssessment` (`approved`, `flags`) | internal |
| `ChatService` | `respond(user, request)` | `ChatResponse` | `/chat` |
| `FeedbackService` | `submit(user, request)` | `FeedbackResponse` | `/feedback` |
| `HistoryService` | `list_conversations(user, limit, offset)` | `HistoryResponse` | `/history` |
| `AnalyticsService` | `summarize(user)` | `AnalyticsResponse` | `/analytics` |

`LLMRequest` carries: current `message`, chronological `history`, optional
`emotion` (`FusionResult`), `retrieved` chunks, and `safety_level`.

### Error behavior

| Raise from a service | HTTP result |
|---|---|
| `InvalidInputError(message)` | `422`, `{"detail": message}` |
| `ResourceNotFoundError` | `404`, `{"detail": "Not found"}` (message is never exposed) |
| Any other exception | `500`, `{"message": "Internal server error"}` (existing global handler) |

---

## Open questions (to be decided by the phase that implements each service)

- Supported audio formats/codecs for `/emotion/analyze` (to be decided in Phase 2.6 — see [`docs/phases/PHASE-2.6-AUDIO-PREPROCESSING.md`](../phases/PHASE-2.6-AUDIO-PREPROCESSING.md)).
- Emotion label set (depends on the chosen dataset).
- Text sentiment/emotion label sets and model.
- Speech-to-text model/provider and language handling.
- Fusion method and weights.
- Embedding model, vector store and similarity metric.
- LLM provider.
- How feedback and emotion predictions are persisted (no `Feedback` or `AnalysisResult` table exists yet; any new table needs a non-destructive migration).
- Memory endpoints and user preferences in `LLMRequest` (memory contracts are not defined yet).
- Latency targets.

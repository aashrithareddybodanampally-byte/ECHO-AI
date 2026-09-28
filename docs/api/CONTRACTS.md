# ECHO-AI — API & Service Contracts

> **Status:** Implemented. Defined in Phase 2.5, implemented on
> `feature/echo-ai-completion`. Versioned under `/api/v1`: do not rename
> fields or paths without updating this document, the schemas, the tests,
> and the frontend (`frontend/src/api.ts`, `frontend/src/types.ts`).

All emotion, sentiment and fusion outputs are **model predictions, not
clinical or psychological diagnoses**, and must never be presented as such.

Interactive OpenAPI docs: `http://localhost:8000/docs` when the backend runs.

---

## Conventions

| Topic | Rule |
|---|---|
| Base path | `/api/v1` |
| Auth | Everything except `/health*`, `/auth/register` and `/auth/login` requires `Authorization: Bearer <JWT>`. |
| Ownership | The user always comes from the token, never from the request body. Another user's conversation or message is treated exactly like a nonexistent one (`404`, body `{"detail": "Not found"}`). |
| Confidence format | Every score, confidence and probability is a float in `[0.0, 1.0]`. |
| Labels | Voice emotion labels come from the trained model (RAVDESS: `angry, calm, disgust, fearful, happy, neutral, sad, surprised`). Text emotion uses the same vocabulary. |
| Model versioning | Every ML result carries `model_version`. |
| Errors | JSON body `{"detail": ...}`. |

### Status codes

| Code | When |
|---|---|
| `401` | Missing, malformed, invalid or expired token. Checked before anything else. |
| `404` | Referenced conversation/message/memory does not exist **or** belongs to another user. |
| `409` | Conflicts with the user's settings (adding memory while memory is disabled; memory limit of 50 reached). |
| `413` | Audio body larger than `MAX_AUDIO_UPLOAD_BYTES` (default 25 MB). |
| `415` | Audio `Content-Type` not `audio/*`, or not WAV/FLAC. |
| `422` | Schema validation failure, or unusable input (empty/undecodable/silent/too short/too long audio, no speech transcribed, feedback on a non-assistant message). |
| `503` | A required model is unavailable (voice emotion model not trained; speech-to-text disabled or failed to load). |

### Audio uploads (`/emotion/analyze`, `/chat/voice`)

Raw request body, `Content-Type: audio/wav` (or `audio/x-wav`, `audio/flac`, ...).
Maximum 25 MB (`MAX_AUDIO_UPLOAD_BYTES`). The body is read only after
authentication succeeds and is rejected with `413` as soon as it exceeds the
limit. Audio is processed in memory and never stored.

Preprocessing: mono, resampled to 16 kHz, DC removal, 80 Hz high-pass, peak
normalization to 0.95, leading/trailing silence trimmed (−40 dB). Accepted
duration after trimming: 0.5–60 s.

---

## Endpoints

### Auth & health (Phases 2.1–2.4)
`POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `GET /health`, `GET /health/db`.

### `POST /emotion/analyze` — voice emotion

Response `200` — `VoiceEmotionResult`:
```json
{"emotion": "sad", "confidence": 0.74,
 "probabilities": {"sad": 0.74, "neutral": 0.16, "...": 0.10},
 "model_version": "emotion_model_v1"}
```
`emotion` is a key of `probabilities`; `probabilities` sum to 1 (±0.001);
`confidence == probabilities[emotion]`. `503` if the model is not trained.

### `POST /emotion/fusion` — multimodal fusion
Request: `{"voice": VoiceEmotionResult?, "text": TextAnalysisResult?, "context": {"label", "score"}?}` (voice or text required).
Response: `{"state": "sad", "confidence": 0.733, "signals": {"voice": 0.72, "text": 0.81, "context": 0.65}}`.
Method: weighted late fusion 0.5 voice / 0.3 text / 0.2 context, re-normalized over present signals (`ml/models/fusion.py`).

### `POST /rag/retrieve`
Request `{"query": "...", "top_k": 1-20 (default 5)}` → `{"query", "chunks": [{"source", "content", "score"}]}`.
TF-IDF cosine similarity over `rag/knowledge_base/`; chunks scoring below 0.05 are dropped.

### `POST /chat` — text turn
Request `{"message": "...", "conversation_id": 12?}` (omit the id to start a conversation).

Response `200`:
```json
{
  "conversation_id": 12,
  "reply": {"id": 34, "conversation_id": 12, "role": "assistant", "content": "...", "created_at": "..."},
  "sources": [{"source": "Study Techniques — Study breaks and focus intervals", "content": "...", "score": 0.41}],
  "emotion": {"state": "fearful", "confidence": 0.65, "signals": {"voice": null, "text": 0.65, "context": null}},
  "safety_level": "normal",
  "transcript": null,
  "llm_model": "claude-opus-5-5",
  "timings_ms": {"context_ms": 3.1, "text_analysis_ms": 1.2, "fusion_ms": 0.4, "retrieval_ms": 1.0,
                 "llm_ms": 2100.5, "output_safety_ms": 0.2, "total_ms": 2107.9}
}
```
- `safety_level`: `normal` | `distress` | `high_risk`. On `high_risk` the LLM is **not** called; the reply is the fixed crisis protocol and `llm_model` is `"safety-protocol"`.
- `llm_model`: the Claude model that answered, `"offline-template-v1"` when no API key is configured or the provider failed, or `"safety-protocol"`.
- `timings_ms`: measured per request (no targets are claimed).

### `POST /chat/voice?conversation_id=12` — voice turn
Raw audio body → preprocessing → speech-to-text (faster-whisper `base`) and voice emotion → same pipeline as `/chat`.
Response is a `ChatResponse` with `transcript` set and `timings_ms.audio_ms`. If the voice model is not trained the turn still works with text-only emotion.

### `GET /history?limit=20&offset=0`, `DELETE /history/{conversation_id}`
Caller's conversations (most recently updated first), messages oldest first. Delete is permanent (`204`).

### `POST /feedback`
`{"message_id": 34, "helpful": true}` → `201`. Assistant messages only; re-submitting updates the rating.

### `GET /analytics`
`{"emotion_distribution": {"neutral": 3, "sad": 1}, "feedback": {"helpful": 2, "not_helpful": 1}}`.
The distribution only includes turns saved while the user had `save_emotion_stats` on.

### Memory & settings
| Method | Path | Behavior |
|---|---|---|
| `GET` | `/memory` | `{"enabled": bool, "items": [{"id", "content", "created_at"}]}` |
| `POST` | `/memory` | `{"content": "..."}` (1–500 chars) → `201`; `409` if disabled or 50 items reached |
| `DELETE` | `/memory/{id}` | `204` |
| `POST` | `/memory/disable`, `/memory/enable` | Toggle use of memory in replies (items are kept) |
| `GET` / `PATCH` | `/settings` | `{"memory_enabled", "save_emotion_stats", "response_style": "concise" \| "balanced" \| "detailed"}` |

Defaults: memory on, emotion statistics **off**, style `balanced`. Memories are
only ever created by the user; nothing is extracted automatically.

---

## Service interfaces

`backend/app/services/interfaces.py` (Protocols). Implementations:

| Interface | Implementation |
|---|---|
| `VoiceEmotionService` | `components.VoiceEmotionAdapter` → `ml/inference/voice_emotion.py` |
| `SpeechToTextService` | `components.SpeechToTextAdapter` → `ml/audio/speech_to_text.py` |
| `TextAnalysisService` | `components.TextAnalysisAdapter` → `ml/nlp/text_emotion.py` |
| `FusionService` | `components.FusionAdapter` → `ml/models/fusion.py` |
| `RetrievalService` | `components.RetrievalAdapter` → `rag/retrieval/retriever.py` |
| `SafetyService` | `components.SafetyAdapter` → `safety/guardrails.py` |
| `LLMService` | `llm.AnthropicLLMService` / `llm.OfflineLLMService` |
| `ChatService` | `chat_service.ChatPipeline` |
| `HistoryService`, `FeedbackService`, `AnalyticsService` | `chat_service.Database*Service` |

Service errors → HTTP: `InvalidInputError` 422, `ResourceNotFoundError` 404,
`UnsupportedMediaError` 415, `ServiceUnavailableError` 503, `ConflictError` 409.

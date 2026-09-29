# Counseling Style: How ECHO-AI Talks

ECHO-AI's reply style is based on established counseling practice. This page
records the sources and how each principle is implemented. ECHO-AI is not a
therapist: it does not diagnose, treat or give medication advice, and crisis
messages bypass the LLM (see `safety/guardrails.py`).

## Principles and where they live

| Principle | Source | Implementation |
|---|---|---|
| Use OARS skills (Open questions, Affirmations, Reflections, Summaries), with about **two reflections per question** | Motivational interviewing: [NIDA OARS guide](https://nida.nih.gov/sites/default/files/oarsessentialcommunicationtechniques.pdf), [Relias](https://www.relias.com/blog/oars-motivational-interviewing) | System prompt (`backend/app/services/llm.py`): mostly reflections, one small question per reply, affirmations when genuine, brief summaries in the *deepen* stage |
| Simple vs complex reflections (say it back vs name what sits underneath) | NIDA OARS guide | Prompt examples of both |
| **Keep counselor turns brief**; avoid the **righting reflex** (fixing or advising before understanding) | NIDA OARS guide | `policy.py`: default length `short` (1–3 sentences); stage *explore* for the first 2 user turns forbids advice; knowledge-base tips are retrieved only in the *support* stage |
| Validation levels: attention, accurate reflection, articulating the unspoken, understanding through history, normalizing, genuineness | Linehan (DBT): [Psych Central](https://psychcentral.com/blog/emotionally-sensitive/2012/02/understanding-the-levels-of-validation), [Counseling Center Group](https://counselingcentergroup.com/6-levels-of-validation-dbt-skill/) | Prompt: validate by showing why the reaction makes sense; use past sessions/memories for "history" |
| Validation needs a dialectical counterpoint; AI tends to validate only | [AI & Psychotherapy](https://ia-et-psychotherapie.com/en/resources/concepts/emotional-validation-linehan/) | Prompt, *deepen* stage: gently get curious about absolutes ("no one ever…") |
| Empathy, unconditional positive regard, genuineness (congruence) | Rogers: [Simply Psychology](https://www.simplypsychology.org/client-centred-therapy.html) | Prompt: plain human language, no jargon or stock phrases, never invent details, no judgment |

## Conversation stages (`backend/app/services/policy.py`)

| Stage | When | Reply shape |
|---|---|---|
| `explore` | First 2 user turns in a conversation | Reflect + one small, easy question. No advice, tips or techniques |
| `deepen` | Later turns | Reflect, occasionally summarize, notice patterns and links to earlier sessions, gently question absolutes; may ask whether they want to think about what could help |
| `support` | The user explicitly asks for help ("what should I do", "any tips", …) | One line showing understanding, then **one** concrete idea that fits what they said, and a check-in on how it sounds |

Referral to a trusted person or counselor is suggested once, gently, only for
hopelessness/worthlessness language or when asked; high-risk messages always
get the crisis protocol.

## Observed example (live, `openai/gpt-oss-120b` via Groq, 2026-09-29)

| User | ECHO-AI (abridged) | Stage |
|---|---|---|
| "no one cares what i need or talk about, always im the one excluded from the group" | "That feels like being invisible when you're trying to be heard… What's the most recent time you felt that?" | explore |
| "i found out from instagram. i just act like its fine" | "…Acting like it's fine might be a way to keep things calm, even if it still hurts. What does 'fine' look like for you right now?" | deepen |
| "honestly it always happens, what should i do?" | One suggestion (a low-key message asking to be included next time) + "How does trying that feel?" | support |

Replies were 37–47 words. This is a qualitative check on one conversation,
not an evaluation; no formal quality metric has been measured.

## Known limitations

- The text emotion analyzer is a keyword heuristic: masked feelings ("I act like it's fine") read as *calm*. The LLM still sees the full conversation.
- Explicit references to previous sessions are inconsistent at `GROQ_REASONING_EFFORT=low`.
- An AI cannot offer the genuineness of a human relationship (validation level 6); ECHO-AI says so when relevant and does not replace professional care.

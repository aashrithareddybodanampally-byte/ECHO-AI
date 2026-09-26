# AGENTS.md — ECHO-AI

> **Read this file before modifying any code in this repository.**

---

## Project

**ECHO-AI** — A multimodal AI conversational system.

## Current Phase

**Phase 1** — Development Environment & Repository Foundation

Phase 1 establishes the engineering foundation only. No AI/ML functionality, no application logic, no deployment infrastructure has been implemented yet.

---

## Architecture Principles

1. **Modular architecture** — Each domain (backend, ML, RAG, safety, frontend) lives in its own top-level directory with clear boundaries.
2. **Separation of concerns** — ML models do not contain API logic; the backend does not contain training code; RAG is isolated from core NLP.
3. **API-first backend** — The backend exposes a well-defined REST/WebSocket API. Frontend and other consumers interact only through this API.
4. **ML isolated from application logic** — ML components expose prediction interfaces consumed by the backend; they never import backend modules directly.
5. **Configuration through environment variables** — All secrets, connection strings, and tunable parameters come from `.env` (never committed). See `.env.example` for the template.
6. **No secrets in source code** — API keys, passwords, tokens, and certificates must never appear in committed files.
7. **Testable components** — Every module should be independently testable. Tests live under `tests/` mirroring the source structure.
8. **Documentation alongside implementation** — When you build a feature, update the relevant docs in `docs/`.

---

## Agent Rules

### Code Modification

1. **Read `AGENTS.md`** before modifying code.
2. **Read `PROJECT-CONTEXT.md`** before major architectural changes.
3. **Inspect existing code** before creating new files — do not duplicate functionality.
4. **Do not rewrite working code** unnecessarily.
5. **Do not introduce dependencies** without justification documented in a commit message or PR description.
6. **Do not hardcode secrets** — use environment variables.
7. **Do not modify unrelated modules** — keep changes scoped.
8. **Add tests** for meaningful functionality.
9. **Run relevant tests** after changes and report results honestly.
10. **Report failures honestly** — never claim a command succeeded unless it actually did.
11. **Never fabricate metrics** — benchmarks, test counts, coverage numbers must come from real execution.
12. **Preserve API contracts** — do not change existing public interfaces without updating all consumers and documentation.
13. **Follow existing project conventions** — match the style, naming, and patterns already in use.
14. **Prefer simple solutions** before introducing complexity.
15. **Do not implement future phases** unless explicitly instructed.

### Git Rules

1. **Phase 1 Foundation** — Phase 1 begins by establishing the `develop` integration branch.
2. **Branch Roles** — `main` remains the stable branch, while `develop` is the integration branch for ongoing feature development.
3. Use **feature branches** created from `develop`.
4. **Do not force push** to `main` or `develop`.
5. **Do not reset** shared branches.
6. Keep commits **focused** — one logical change per commit.
7. **Do not commit secrets**, generated datasets, trained models, virtual environments, or `node_modules`.
8. Write clear, conventional commit messages (e.g., `feat:`, `fix:`, `docs:`, `chore:`, `test:`).

### Phase Rule

> Agents must **not** implement functionality belonging to future phases unless the human operator explicitly instructs them to do so. When in doubt, ask.

---

## Repository Structure

```
ECHO-AI/
├── frontend/           # React + Vite frontend (Phase 3+)
├── backend/            # Python FastAPI backend (Phase 2+)
├── ml/                 # Machine learning pipelines
│   ├── audio/          # Audio/speech processing
│   ├── nlp/            # NLP models and processing
│   ├── models/         # Model definitions
│   ├── training/       # Training scripts
│   ├── inference/      # Inference/serving
│   └── evaluation/     # Model evaluation
├── rag/                # Retrieval-Augmented Generation
│   ├── ingestion/      # Document ingestion
│   ├── embeddings/     # Embedding generation
│   ├── retrieval/      # Vector search & retrieval
│   └── evaluation/     # RAG evaluation
├── safety/             # Safety & guardrails
├── database/           # Database schemas & migrations
├── tests/              # All tests
├── docs/               # Documentation
├── scripts/            # Utility & automation scripts
├── infrastructure/     # Docker, CI/CD, deployment
├── data/               # Datasets (git-ignored, except READMEs)
├── models/             # Trained model artifacts (git-ignored, except README)
├── logs/               # Log output (git-ignored)
└── .github/workflows/  # GitHub Actions CI/CD
```

---

## Key Files

| File | Purpose |
|---|---|
| `AGENTS.md` | This file — rules for AI coding agents |
| `PROJECT-CONTEXT.md` | High-level project description & architecture |
| `README.md` | Public-facing project README |
| `.env.example` | Environment variable template |
| `.gitignore` | Git ignore rules |
| `docs/` | All project documentation |
| `scripts/check_environment.ps1` | Development environment validation |

# ECHO-AI — Development Guide

---

## Prerequisites

Ensure the following tools are installed on your development machine:

| Tool | Minimum Version | Required for Phase 1? |
|---|---|---|
| Git | 2.30+ | ✅ Yes |
| Python | 3.10+ | ✅ Yes |
| Node.js | 18+ | ✅ Yes |
| npm | 9+ | ✅ Yes |
| Docker | 20+ | ❌ Not yet |
| Docker Compose | 2.0+ | ❌ Not yet |

### Verify Your Environment

Run the validation script:

```powershell
# Windows (PowerShell)
.\scripts\check_environment.ps1
```

```bash
# Linux / macOS
bash scripts/check_environment.sh
```

---

## Repository Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd ECHO-AI

# 2. Copy environment variables
cp .env.example .env

# 3. (When backend work begins) Create Python virtual environment
python -m venv .venv

# Activate — Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Activate — Linux / macOS:
source .venv/bin/activate

# 4. (When frontend work begins) Install Node dependencies
cd frontend
npm install
cd ..
```

---

## Git Workflow

### Branches

| Branch | Purpose | Protected |
|---|---|---|
| `main` | Production-ready releases | Yes |
| `develop` | Active development integration | Yes |
| `feat/*` | Feature branches | No |
| `fix/*` | Bug fix branches | No |
| `docs/*` | Documentation branches | No |
| `chore/*` | Maintenance branches | No |

### Creating a Feature Branch

```bash
# Always branch from develop
git checkout develop
git pull origin develop
git checkout -b feat/my-feature

# Work on your feature...
git add .
git commit -m "feat: add my feature"

# Push and create PR
git push -u origin feat/my-feature
```

### Commit Conventions

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <description>

[optional body]

[optional footer]
```

**Types**: `feat`, `fix`, `docs`, `chore`, `test`, `refactor`, `style`, `perf`, `ci`, `build`

**Examples**:
```
feat: add user authentication endpoint
fix: resolve audio sample rate mismatch
docs: update RAG architecture documentation
chore: update Python dependencies
test: add unit tests for emotion classifier
refactor: extract audio preprocessing into utility module
```

---

## Environment Setup

### Environment Variables

1. Copy `.env.example` to `.env`
2. Fill in actual values for the services you're working with
3. **Never commit `.env`** — it is git-ignored

### Python Virtual Environment

```bash
# Create
python -m venv .venv

# Activate (PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate (Bash)
source .venv/bin/activate

# Install dependencies (when requirements.txt exists)
pip install -r requirements.txt

# Deactivate
deactivate
```

The virtual environment directory `.venv/` is git-ignored.

---

## Using AI Coding Agents

ECHO-AI is developed with AI coding agent assistance. All agents **must**:

1. Read `AGENTS.md` before starting work
2. Read `PROJECT-CONTEXT.md` before architectural changes
3. Inspect existing code before creating new files
4. Follow the project conventions documented in this guide
5. Not implement functionality beyond the current phase
6. Run tests after changes and report results honestly

See [`AGENT-WORKFLOW.md`](AGENT-WORKFLOW.md) for the detailed agent development workflow.

---

## Running Validation

```powershell
# Check development environment
.\scripts\check_environment.ps1
```

---

## Pull Request Expectations

1. **Branch** from `develop`, target `develop`
2. **Title** follows commit convention: `feat: ...`, `fix: ...`, etc.
3. **Description** explains what changed and why
4. **Tests** pass — include new tests for new functionality
5. **Documentation** updated if behavior changed
6. **No secrets** in committed code
7. **Focused scope** — one logical change per PR

---

## Testing Expectations

- Write tests for all meaningful functionality
- Tests live in `tests/` mirroring the source structure
- Backend tests use `pytest`
- Frontend tests use Vitest or Jest
- Integration tests verify cross-module behavior
- Run `pytest` from the project root to execute all Python tests

---

## Directory Conventions

| Directory | Contents |
|---|---|
| `frontend/` | All frontend source code |
| `backend/` | All backend source code |
| `ml/` | ML model code — not application logic |
| `rag/` | RAG-specific code — separate from ML |
| `safety/` | Safety/guardrail modules |
| `database/` | Schema definitions, migrations, seed data |
| `tests/` | All test files |
| `docs/` | All documentation |
| `scripts/` | Utility and automation scripts |
| `infrastructure/` | Docker, CI/CD, deployment configs |
| `data/` | Datasets (git-ignored except READMEs) |
| `models/` | Trained models (git-ignored except README) |
| `logs/` | Runtime logs (git-ignored) |

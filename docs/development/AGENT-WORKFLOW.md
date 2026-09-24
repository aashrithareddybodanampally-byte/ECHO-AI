# ECHO-AI — Agent Development Workflow

> This document defines the standard workflow when AI coding agents contribute to ECHO-AI.

---

## Workflow Diagram

```
┌────────────────────────┐
│   Human Requirement    │
│  (Task / Issue / PR)   │
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│  Agent Reads Context   │
│  • AGENTS.md           │
│  • PROJECT-CONTEXT.md  │
│  • Relevant docs/      │
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│  Agent Inspects Code   │
│  • Existing structure  │
│  • Related modules     │
│  • Current tests       │
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│  Agent Proposes Plan   │
│  • Files to create     │
│  • Files to modify     │
│  • Dependencies        │
│  • Test strategy       │
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│  Agent Implements      │
│  • Write code          │
│  • Follow conventions  │
│  • Update docs         │
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│  Agent Runs Tests      │
│  • Unit tests          │
│  • Integration tests   │
│  • Linting             │
│  • Report results      │
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│   Human Reviews        │
│  • Code review         │
│  • Test verification   │
│  • Architecture check  │
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│   Commit & Push        │
│  • Conventional commit │
│  • Feature branch      │
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│   Pull Request         │
│  • Description         │
│  • CI passes           │
│  • Review approved     │
└───────────┬────────────┘
            ▼
┌────────────────────────┐
│   Merge to develop     │
└────────────────────────┘
```

---

## Step-by-Step

### 1. Receive Requirement

The human provides a task description, issue, or feature request. The agent must understand:
- **What** needs to be built
- **Why** it is needed
- **Which phase** it belongs to (do not implement out-of-phase work)

### 2. Read Project Context

Before writing any code, the agent **must** read:
- `AGENTS.md` — Coding rules, architecture principles, phase restrictions
- `PROJECT-CONTEXT.md` — Project purpose, current status, module overview
- Relevant `docs/` files for the affected subsystem

### 3. Inspect Existing Code

The agent **must** examine:
- The directory structure of affected modules
- Existing implementations that might overlap
- Existing tests for the affected area
- Current API contracts and interfaces

**Rule**: Do not create duplicates. Do not rewrite working code.

### 4. Propose Implementation

Before making changes, the agent should outline:
- Files to be created or modified
- New dependencies (with justification)
- Test approach
- Documentation updates

For significant changes, present the plan to the human before implementing.

### 5. Implement

- Follow existing project conventions (naming, structure, style)
- Use environment variables for configuration
- Do not hardcode secrets
- Write clear, documented code
- Update relevant documentation alongside code changes

### 6. Run Tests

- Execute all relevant tests
- Add new tests for new functionality
- Report results **honestly** — do not fabricate passing tests
- If tests fail, diagnose and fix before proceeding

### 7. Human Review

The human reviews:
- Code quality and correctness
- Adherence to architecture principles
- Test coverage
- Documentation accuracy

### 8. Commit

- Use conventional commit messages
- Keep commits focused (one logical change per commit)
- Ensure no secrets, generated files, or large binaries are committed

### 9. Pull Request

- Create PR from feature branch to `develop`
- Include a clear description of changes
- Ensure CI checks pass
- Request review

### 10. Merge

- After approval, merge to `develop`
- Delete the feature branch after merging

---

## Agent Checklist

Before submitting work, the agent should verify:

- [ ] Read `AGENTS.md` and `PROJECT-CONTEXT.md`
- [ ] Inspected existing code in affected areas
- [ ] No duplicate functionality created
- [ ] No hardcoded secrets
- [ ] No unnecessary dependencies added
- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] Commit message follows conventions
- [ ] Only current-phase work implemented
- [ ] Changes are focused and scoped appropriately

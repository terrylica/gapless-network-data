---
status: proposed
date: 2025-12-01
decision-maker: Terry Li
consulted: [Alpha Forge Integration Team]
research-method: single-agent
clarification-iterations: 0
perspectives: [SDK Consumer, Security, Backward Compatibility]
---

# Add Auto .env File Loading for Credential Resolution

**Design Spec**: [Implementation Spec](/docs/design/2025-12-01-dotenv-credential-loading/spec.md)

## Context and Problem Statement

The gapless-network-data SDK currently supports two credential resolution methods:

1. **Doppler CLI** (recommended) - requires Doppler setup and service token
2. **Environment variables** - requires manual `export` commands

For small teams integrating with platforms like Alpha Forge, neither option provides zero-friction onboarding. Team members must either set up Doppler or remember to export environment variables before each session.

The industry-standard solution is `.env` file support via `python-dotenv`, which allows teams to:

1. Create a `.env` file with credentials
2. Share via secure channels (Signal, etc.)
3. Drop in project root - everything just works

### Before/After

```
┌─────────────────────────────────────────────────────────────────┐
│ BEFORE: Credential Resolution                                   │
│                                                                 │
│ ┌─────────────┐     ┌──────────────┐     ┌───────────────────┐ │
│ │ Doppler CLI │ ──▶ │ os.environ   │ ──▶ │ CredentialError   │ │
│ │ (10s timeout│     │ .get()       │     │ (setup instructions│ │
│ │   subprocess│     │              │     │                    │ │
│ └─────────────┘     └──────────────┘     └───────────────────┘ │
│                                                                 │
│ User must: Set up Doppler OR manually export vars              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ AFTER: Credential Resolution                                    │
│                                                                 │
│ ┌─────────────┐     ┌─────────────┐     ┌──────────────┐       │
│ │ load_dotenv │ ──▶ │ Doppler CLI │ ──▶ │ os.environ   │ ──▶ … │
│ │ (if .env    │     │ (10s timeout│     │ .get()       │       │
│ │  exists)    │     │   subprocess│     │              │       │
│ └─────────────┘     └─────────────┘     └──────────────┘       │
│                                                                 │
│ User can: Drop .env file → everything works automatically      │
└─────────────────────────────────────────────────────────────────┘
```

## Decision Drivers

- **Zero-friction onboarding**: New team members should just drop a `.env` file and go
- **Industry standard**: `python-dotenv` is the Python equivalent of Node.js `dotenv`
- **Backward compatible**: Existing Doppler and env var users must be unaffected
- **Security**: `.env` files must be excluded from git

## Considered Options

1. **Add python-dotenv with load_dotenv() at credential resolution start**
2. Keep current Doppler + env var approach only
3. Add custom .env parser (avoid dependency)

## Decision Outcome

**Chosen option**: Option 1 - Add python-dotenv with load_dotenv()

### Rationale

- `python-dotenv` is battle-tested (100M+ downloads/month)
- `load_dotenv()` is non-invasive - only populates `os.environ` if `.env` exists
- No changes needed to existing Doppler or env var reading logic
- Single line addition at function start achieves the goal

### Consequences

**Good**:

- Zero-friction onboarding for small teams
- Works immediately after dropping `.env` file
- Existing users unaffected

**Bad**:

- New dependency (though lightweight: ~10KB)

**Neutral**:

- `.env.example` template needed for discoverability
- `.gitignore` update required

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Credential Resolution Chain (api.py)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  _get_clickhouse_credentials()                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                                                             ││
│  │  ┌───────────────┐                                          ││
│  │  │ load_dotenv() │ ◀── NEW: Loads .env → os.environ         ││
│  │  └───────┬───────┘                                          ││
│  │          │                                                  ││
│  │          ▼                                                  ││
│  │  ┌───────────────┐                                          ││
│  │  │ Doppler CLI   │ ◀── Try subprocess (10s timeout)         ││
│  │  │ subprocess    │                                          ││
│  │  └───────┬───────┘                                          ││
│  │          │ (on failure)                                     ││
│  │          ▼                                                  ││
│  │  ┌───────────────┐                                          ││
│  │  │ os.environ    │ ◀── Now includes .env values!            ││
│  │  │ .get()        │                                          ││
│  │  └───────┬───────┘                                          ││
│  │          │ (if missing)                                     ││
│  │          ▼                                                  ││
│  │  ┌───────────────┐                                          ││
│  │  │ Credential    │ ◀── Raise with setup instructions        ││
│  │  │ Exception     │     (now includes .env option)           ││
│  │  └───────────────┘                                          ││
│  │                                                             ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation

See [Design Spec](/docs/design/2025-12-01-dotenv-credential-loading/spec.md) for detailed implementation plan.

### Summary

| File                                | Change                               |
| ----------------------------------- | ------------------------------------ |
| `pyproject.toml`                    | Add `python-dotenv>=1.0.0`           |
| `api.py`                            | Import + `load_dotenv()` + error msg |
| `.env.example`                      | NEW template file                    |
| `.gitignore`                        | Add `.env` patterns                  |
| `llms.txt`, `README.md`, `probe.py` | Update setup docs                    |

## Decision Log

| Date       | Decision                             | Rationale                                     |
| ---------- | ------------------------------------ | --------------------------------------------- |
| 2025-12-01 | Use python-dotenv                    | Industry standard, battle-tested, lightweight |
| 2025-12-01 | Call load_dotenv() at function start | Non-invasive, works with existing flow        |

## Links

- [python-dotenv PyPI](https://pypi.org/project/python-dotenv/)
- [Alpha Forge Integration Request](#) (internal)

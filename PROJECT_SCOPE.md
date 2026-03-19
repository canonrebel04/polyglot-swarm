# PolyglotSwarm — Project Scope & Best Practices

> **Project Codename:** PolyglotSwarm  
> **Inspired by:** [Overstory](https://github.com/jayminwest/overstory)  
> **Goal:** A provider-agnostic multi-agent orchestration TUI with first-class support for the most popular coding-agent CLIs, including Claude Code, Codex CLI, Gemini CLI, Aider, OpenHands CLI, OpenCode, Goose, Cline CLI, Qodo Gen CLI, Mistral Vibe (`vibe`), Hermes-based local agents, and OpenClaw.

---

## Implementation Progress

> Last updated: 2026-03-19

### Overall Status: Foundation Complete — Moving to TUI + Runtime Adapters

| Component | Status | Notes |
|-----------|--------|-------|
| Core Architecture | ✅ 100% | Runtime system, role system, messaging, worktree all operational |
| Agent Roles | 🔄 70% | Scout, Builder, Developer, Tester complete. Reviewer, Merger, Monitor, Lead, Supervisor, Coordinator, Orchestrator pending |
| Runtime Adapters | 🔄 10% | Echo runtime complete. 11 Tier-1/2 adapters pending |
| Orchestrator | 🔄 70% | Coordinator, AgentManager, Watchdog, workflow management done. Overseer loop, merge manager pending |
| CLI Commands | ✅ 90% | `init`, `run`, `status`, `stop`, `doctor`, `cleanup`, `roles`, `runtimes` working |
| TUI | ⬜ 0% | Not started. Next major phase |
| Tests | ✅ 100% | 46 tests passing in 1.58s |

### Completed Items

- `AgentRuntime` base interface
- Role registry + YAML contracts + permission system
- SQLite messaging database
- Git worktree manager
- Fleet status model
- Coordinator (task decomposition + assignment)
- AgentManager (spawn/monitor/message/kill)
- Watchdog (stall detection)
- Workflow management (scout → developer → tester pipeline)
- Echo runtime (testing stub)
- All core CLI commands
- 46-test suite with unit + integration + e2e coverage

### Active Next Steps (Priority Order)

1. **TUI** — Textual split-pane overseer chat + fleet status + agent output panels
2. **Runtime Adapters** — Claude Code, Codex CLI, Gemini CLI, Aider, OpenHands, OpenCode, Vibe, Hermes
3. **Remaining Roles** — Reviewer, Merger, Monitor, Lead, Supervisor, Orchestrator
4. **Role Safety** — Tool policy enforcement, filesystem policy, drift detection, structured output validation
5. **Overseer Loop** — Task decomposition via LLM, auto-nudge, dynamic agent dispatch
6. **Merge Manager** — FIFO merge queue, conflict resolution tiers

---

## 1. Problem Statement

Overstory is one of the strongest references for multi-agent orchestration, but its implementation and defaults are still centered around its own supported runtime stack and workflow assumptions.

Key gaps that PolyglotSwarm addresses:

- I want support for **all major coding-agent CLIs**, not only one or two.
- I want a visible **overseer + worker fleet interface**, not only a command-driven orchestration flow.
- I want **role-stable agents** that stay inside their assigned role instead of drifting into other jobs.
- I want **provider/runtime portability**, including cloud and local models.
- I want an architecture where **new agent runtimes can be added without rewriting orchestration logic**.
- I want a clean path for both **interactive terminal agents** and **headless CI/task agents**.

---

## 2. Core Vision

A **terminal-first multi-agent orchestration system** where:

1. An **Overseer** maintains the top-level conversation and project objective.
2. The Overseer **decomposes work into role-bound sub-tasks**.
3. The Overseer **spawns sub-agents** using different runtimes depending on task fit.
4. The TUI shows **both layers simultaneously** — Overseer chat, active agents, current task, status, runtime, and recent output.
5. The Overseer can **nudge, pause, retry, replace, or terminate** stalled agents.
6. Every agent runs with a **locked role contract** so it cannot silently become a different type of agent.
7. The system supports both **single-project swarms** and eventually **multi-project orchestration**.

---

## 3. Build vs Fork Decision

**Decision: Built from Scratch ✅** — This decision is finalized. The foundation is complete.

The build-from-scratch approach was correct. The role system, adapter interface, and orchestration logic are all cleanly designed without inherited coupling from Overstory's TypeScript/Bun stack or Claude-specific hooks. Overstory's role hierarchy, worktree isolation, coordinator pattern, and watchdog ideas were used as reference only.

---

## 4. Tech Stack

| Layer | Choice | Status |
|-------|--------|--------|
| **Language** | Python 3.12+ | ✅ In use |
| **TUI Framework** | [Textual](https://github.com/Textualize/textual) | ⬜ Next phase |
| **CLI Entry Point** | [Typer](https://typer.tiangolo.com/) | ✅ In use |
| **Process Management** | `asyncio` + `asyncio.subprocess` | ✅ In use |
| **Optional Session Control** | `tmux` via `libtmux` | 🔄 Planned |
| **Messaging / State** | SQLite (WAL mode) via `aiosqlite` | ✅ In use |
| **Validation / Config** | Pydantic + YAML | ✅ In use |
| **Worktree Isolation** | `git worktree` | ✅ In use |
| **Logs / Events** | NDJSON | 🔄 Planned |
| **Policy Engine** | Internal rules layer | 🔄 Phase 4 |

> **SpacetimeDB note:** Evaluated and not adopted for v1. SQLite WAL is the right fit for local single-machine coordination. SpacetimeDB's Python SDK is unmaintained (2023) and the tool is designed for multi-client networked state, not local orchestration. Revisit if PolyglotSwarm ever becomes multi-node.

---

## 5. Architecture Design

```text
┌────────────────────────────────────────────────────────────────────┐
│                        PolyglotSwarm TUI                          │
├──────────────────────────────┬─────────────────────────────────────┤
│        OVERSEER CHAT         │          AGENT FLEET                │
│  [User] build feature X      │  lead-1       running   claude      │
│  [Overseer] spawning lead    │  builder-1    running   aider       │
│  [Overseer] scout first      │  tester-1     queued    gemini      │
│  [Overseer] nudging builder  │  reviewer-1   stalled   codex       │
│                              │  merger-1     waiting   opencode    │
├──────────────────────────────┴─────────────────────────────────────┤
│                  SELECTED AGENT OUTPUT / EVENTS                    │
│  builder-1: reading files...                                       │
│  builder-1: edited auth.py                                         │
│  builder-1: ready for tests                                        │
└────────────────────────────────────────────────────────────────────┘
```

### Core Components

```text
polyglot-swarm/
  src/
    main.py
    config.py
    cli/
      app.py
      commands/
        init.py          ✅
        run.py           ✅
        status.py        ✅
        inspect.py
        nudge.py
        stop.py          ✅
        doctor.py        ✅
        roles.py         ✅
        runtimes.py      ✅
        cleanup.py       ✅
    tui/                 ⬜ next phase
      app.py
      panels/
        overseer_chat.py
        agent_fleet.py
        agent_output.py
        event_log.py
        role_view.py
    orchestrator/
      overseer.py        🔄 partial
      coordinator.py     ✅
      dispatcher.py
      agent_manager.py   ✅
      watchdog.py        ✅
      merge_manager.py   ⬜
      completion.py
    runtimes/
      base.py            ✅
      echo.py            ✅  (testing stub)
      claude_code.py     ⬜
      codex.py           ⬜
      gemini_cli.py      ⬜
      aider.py           ⬜
      openhands.py       ⬜
      opencode.py        ⬜
      goose.py           ⬜
      cline.py           ⬜
      qodo.py            ⬜
      mistral_vibe.py    ⬜
      hermes.py          ⬜
      openclaw.py        ⬜
      registry.py        ✅
      capabilities.py    ✅
    roles/
      registry.py        ✅
      contracts.py       ✅
      guards.py          ⬜  phase 4
      prompts.py         ✅
      policies.py        ⬜  phase 4
    messaging/
      db.py              ✅
      protocol.py        ✅
      bus.py             ✅
      events.py
    worktree/
      manager.py         ✅
    logging/
      logger.py
      replay.py
    agents/
      definitions/
        orchestrator.md   ⬜
        coordinator.md    ✅
        supervisor.md     ⬜
        lead.md           ⬜
        scout.md          ✅
        developer.md      ✅
        builder.md        ✅
        tester.md         ✅
        reviewer.md       ⬜
        merger.md         ⬜
        monitor.md        ⬜
  config.yaml
  pyproject.toml
  README.md
  AGENTS.md
```

---

## 6. Supported Runtime Strategy

PolyglotSwarm supports runtimes in **tiers**.

### Tier 1 — Must Support in v1

| Runtime | Why it matters | Mode | Status |
|--------|----------------|------|--------|
| **Claude Code** | One of the leading coding agents | Interactive + task | ⬜ |
| **Codex CLI** | Core target runtime | Interactive + task | ⬜ |
| **Gemini CLI** | Core target runtime | Interactive + task | ⬜ |
| **Aider** | Popular terminal-native coding tool with repo awareness | Task-first | ⬜ |
| **OpenHands CLI** | Strong agentic coding workflow and headless fit | Task-first | ⬜ |
| **OpenCode** | Built as a terminal coding agent with agent concepts | Interactive + task | ⬜ |
| **Mistral Vibe (`vibe`)** | Important for Mistral-based workflows | Task-first / resumable | ⬜ |
| **Hermes (Ollama / llama.cpp)** | Local/private model support | Task-first | ⬜ |

### Tier 2 — High-Value After v1

| Runtime | Why it matters | Mode | Status |
|--------|----------------|------|--------|
| **Goose** | Strong CLI agent story and tool integrations | Task-first | ⬜ |
| **Cline CLI** | Terminal-native coding agent, promising for orchestration | Interactive + task | ⬜ |
| **Qodo Gen CLI** | Agent framework orientation and CI angle | Task-first | ⬜ |
| **OpenClaw** | Interesting agent/gateway system, not primarily a coding CLI | Task-first | ⬜ |

### Tier 3 — Experimental

- Cursor CLI
- Copilot CLI-style interfaces
- Local wrappers around custom MCP-capable agents
- Custom shell-based or API-backed internal agents

### Runtime Support Levels

| Level | Meaning |
|------|---------|
| **Level 1** | Run task, stream output, capture completion/failure |
| **Level 2** | Resume, nudge, interrupt, retry |
| **Level 3** | Full role-safe integration with structured status, isolation, and tool policy |

---

## 7. AgentRuntime Interface

Designed and implemented. ✅

```python
# src/runtimes/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator

@dataclass
class AgentConfig:
    name: str
    role: str
    task: str
    worktree_path: str
    model: str
    runtime: str
    system_prompt_path: str
    allowed_tools: list[str] = field(default_factory=list)
    blocked_tools: list[str] = field(default_factory=list)
    read_only: bool = False
    can_spawn_children: bool = False
    extra_env: dict[str, str] = field(default_factory=dict)

@dataclass
class AgentStatus:
    name: str
    role: str
    state: str          # queued | running | stalled | done | error | blocked
    current_task: str
    runtime: str
    last_output: str
    pid: int | None

@dataclass
class RuntimeCapabilities:
    interactive_chat: bool
    headless_run: bool
    resume_session: bool
    streaming_output: bool
    tool_allowlist: bool
    sandbox_support: bool
    agent_profiles: bool
    parallel_safe: bool

class AgentRuntime(ABC):
    @property
    @abstractmethod
    def runtime_name(self) -> str: ...

    @property
    @abstractmethod
    def capabilities(self) -> RuntimeCapabilities: ...

    @abstractmethod
    async def spawn(self, config: AgentConfig) -> str: ...

    @abstractmethod
    async def send_message(self, session_id: str, message: str) -> None: ...

    @abstractmethod
    async def get_status(self, session_id: str) -> AgentStatus: ...

    @abstractmethod
    async def stream_output(self, session_id: str) -> AsyncIterator[str]: ...

    @abstractmethod
    async def kill(self, session_id: str) -> None: ...
```

---

## 8. Agent Role System

Role registry and contracts are complete. ✅  
Remaining roles (Reviewer, Merger, Monitor, Lead, Supervisor, Orchestrator) are next.

### Full Role Set

| Role | Purpose | Access | Can Spawn? | Status |
|------|---------|--------|------------|--------|
| **Orchestrator** | Multi-project meta-coordinator | Read-only | Yes | ⬜ |
| **Coordinator** | Break goals into work, assign agents | Read-only | Yes | ✅ |
| **Supervisor** | Fleet oversight, escalation handling | Read-only | Limited | ⬜ |
| **Lead** | Team-level coordinator for a workstream | Read-mostly | Yes | ⬜ |
| **Scout** | Explore code, read docs, gather facts | Read-only | No | ✅ |
| **Developer** | Complex implementation, reasoning-intensive | Read-write | No | ✅ |
| **Builder** | Fast execution-oriented code editing | Read-write | No | ✅ |
| **Tester** | Run/write tests, validate behavior, repro bugs | Read-write (tests) | No | ✅ |
| **Reviewer** | Review code, detect issues, reject bad outputs | Read-only | No | ⬜ |
| **Merger** | Merge approved work, resolve safe conflicts | Read-write | No | ⬜ |
| **Monitor** | Detect stalls, failures, drift, unhealthy sessions | Read-only | No | ⬜ |

### Role Hierarchy

```text
Orchestrator
  -> Coordinator
      -> Supervisor
          -> Lead
              -> Scout
              -> Developer
              -> Builder
              -> Tester
              -> Reviewer
              -> Merger
      -> Monitor
```

### Why Both Developer and Builder?

| Role | Best Use |
|------|----------|
| **Developer** | Complex implementation requiring planning, reasoning, architecture-sensitive edits |
| **Builder** | Faster execution on bounded code tasks, refactors, small feature slices |
| **Tester** | Verification, regression checks, test writing, repro scripts |

---

## 9. Role Locking and Anti-Drift

**Status: Architecture defined. Guards and policies implementation is Phase 4.**

Role contracts are designed and loaded. Full enforcement (tool policy, filesystem policy, output validation, drift detection) is the next major safety milestone.

### Best Practice: Role = Prompt + Policy + Access + Validation

Each spawned agent must receive:

1. A **role ID**
2. A **role contract**
3. A **system prompt template**
4. A **tool allowlist**
5. A **filesystem policy**
6. A **spawn policy**
7. A **completion schema**
8. A **drift detector**

### Role Contract Example

```yaml
# roles/contracts/builder.yaml
role: builder
identity: "You are Builder, an implementation agent."
mission: "Make scoped code changes only for the assigned task."
may:
  - read_repo
  - edit_code
  - run_local_tests
  - write_small_docs
may_not:
  - redefine_requirements
  - review_own_work_as_final_authority
  - merge_branches
  - spawn_agents
  - modify_global_policy
required_outputs:
  - summary
  - files_changed
  - risks
  - test_status
handoff_to:
  - tester
  - reviewer
```

### Enforcement Layers (Phase 4)

1. **Prompt-Level Role Anchoring** — identity, permissions, forbidden actions, handoff targets embedded in every role prompt
2. **Runtime-Level Tool Restrictions** — tool allowlists enforced via runtime adapter where supported
3. **Filesystem Policy** — read-only mounts for Scout/Reviewer; test-scoped writes for Tester; full worktree access for Developer/Builder
4. **Task-Type Validation** — coordinator tags every task with the required role; mismatches are rejected
5. **Output Schema Validation** — each role returns structured output that is validated before handoff
6. **Drift Detection** — Monitor/Supervisor scan for wrong tool usage, forbidden writes, self-reassignment language, unexpected spawns

### Hard Rule

**Agents never self-upgrade roles.**  
Scout requests a Builder if code must change. Builder hands off to Reviewer when done. Reviewer sends work back if it finds gaps instead of fixing them directly.

---

## 10. Agent Definitions

```text
src/agents/definitions/
  coordinator.md    ✅
  scout.md          ✅
  developer.md      ✅
  builder.md        ✅
  tester.md         ✅
  orchestrator.md   ⬜
  supervisor.md     ⬜
  lead.md           ⬜
  reviewer.md       ⬜
  merger.md         ⬜
  monitor.md        ⬜
```

### Definition Template

```markdown
# Role: Builder

## Identity
You are Builder, an implementation-focused coding agent.

## Primary Goal
Make the assigned code changes cleanly and minimally.

## Allowed Actions
- Read repository files
- Edit source code
- Run local validation commands approved for this task
- Produce a structured handoff for tester/reviewer

## Forbidden Actions
- Do not merge branches
- Do not redefine the task
- Do not spawn new agents
- Do not claim review is complete
- Do not modify unrelated files

## Success Criteria
- Task scope satisfied
- Changes remain minimal
- Output includes files changed, validation run, risks, and handoff notes

## Handoff
Send work to Tester or Reviewer when implementation is complete.
```

---

## 11. Overseer and Delegation Rules

**Status: Coordinator working. Full Overseer LLM loop is next.**

### Task Packet

```python
@dataclass
class TaskPacket:
    id: str
    title: str
    description: str
    role_required: str
    runtime_preference: list[str]
    priority: str
    files_in_scope: list[str]
    acceptance_criteria: list[str]
    parent_agent: str | None
```

### Delegation Rules

- **Scout** first when facts are missing.
- **Lead** when one issue needs multiple workers.
- **Developer** for architecture-sensitive or multi-file changes.
- **Builder** for bounded implementation tasks.
- **Tester** after implementation or for bug reproduction.
- **Reviewer** before merge on non-trivial changes.
- **Merger** only after approval conditions are met.
- **Monitor** runs continuously or on interval.

### Default Workflow

```text
User request
  -> Coordinator
      -> Scout (map code + risks)
      -> Lead (split work)
          -> Developer (complex change)
          -> Builder (small subtask)
          -> Tester (run validations)
          -> Reviewer (judge quality)
      -> Merger
      -> Monitor (watching continuously)
```

---

## 12. Runtime Adapters

### Runtime Capability Matrix

| Runtime | Category | Support Level | Status |
|--------|----------|:---:|--------|
| **Claude Code** | Premium coding agent | 3 | ⬜ |
| **Codex CLI** | Premium coding agent | 3 | ⬜ |
| **Gemini CLI** | Premium coding agent | 3 | ⬜ |
| **Aider** | Terminal coding tool | 3 | ⬜ |
| **OpenHands CLI** | Autonomous coding agent | 2 | ⬜ |
| **OpenCode** | Terminal coding agent | 2 | ⬜ |
| **Mistral Vibe (`vibe`)** | Programmatic CLI | 2 | ⬜ |
| **Hermes (Ollama)** | Local model runtime | 1 | ⬜ |
| **Goose** | Open-source CLI agent | 2 | ⬜ |
| **Cline CLI** | Terminal coding agent | 2 | ⬜ |
| **Qodo Gen CLI** | Agent framework CLI | 2 | ⬜ |
| **OpenClaw** | Agent gateway platform | 1 | ⬜ |
| **Echo** | Internal test runtime | — | ✅ |

### Core Adapter Requirement

Every adapter must implement:

- spawn task
- stream output
- capture structured completion
- detect stall/error
- send follow-up or resume when supported
- expose `RuntimeCapabilities`
- respect role/tool restrictions as much as the runtime allows

---

## 13. Mistral Vibe (`vibe`) Notes

**Confirmed flags from `vibe --help`:**

| Flag | Purpose |
|------|--------|
| `-p TEXT` | Programmatic headless mode — auto-approves tools, outputs and exits |
| `--max-turns N` | Limit assistant turns |
| `--max-price DOLLARS` | Cost cap |
| `--enabled-tools TOOL` | Tool allowlist (disables all others in `-p` mode) |
| `--output streaming` | NDJSON per message — best for live TUI streaming |
| `--agent NAME` | Use builtin or custom agent profile (`auto-approve` recommended) |
| `--workdir DIR` | Run from this directory |
| `--resume SESSION_ID` | Resume prior session for nudge/continuation |

**Best practices:**
- Use `-p` + `--output streaming` for headless agent runs
- Use `--enabled-tools` to align with role tool policy
- Capture vibe SESSION_ID from first run; use `--resume` for nudges
- Good role fits: Scout, Builder, Developer, Tester, Reviewer (tool-restricted)

---

## 14. OpenClaw Notes

**Confirmed flags from `openclaw --help`:**

OpenClaw is a WhatsApp/Telegram gateway with a built-in agent system. It is **not** a general-purpose coding agent CLI. Treat as an experimental runtime.

**Key commands:** `openclaw agent` (single turn), `openclaw acp` (Agent Control Protocol), `openclaw agents` (isolated workspaces), `--profile <name>` (per-agent isolation).

**Multi-agent strategy:** Each sub-agent maps to an isolated `--profile swarm-<name>` with its own gateway instance.

**Good role fits:** Monitor, Supervisor, notification bridges, experimental task routing.

---

## 15. TUI Layout

**Status: ⬜ Not started. This is the next major phase.**

```python
# src/tui/app.py
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer
from .panels.overseer_chat import OverseerChat
from .panels.agent_fleet import AgentFleet
from .panels.agent_output import AgentOutput

class PolyglotSwarmApp(App):
    CSS = """
    Screen { layout: vertical; }
    #main { height: 70%; }
    OverseerChat { width: 45%; border: solid green; }
    AgentFleet { width: 55%; border: solid cyan; }
    AgentOutput { height: 30%; border: solid yellow; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main"):
            yield OverseerChat()
            yield AgentFleet()
        yield AgentOutput()
        yield Footer()
```

### Required TUI Panels

- Overseer conversation (live LLM chat)
- Fleet status table (name, role, state, runtime, task)
- Selected agent live output
- Event log
- Role contract viewer
- Drift / stall / forbidden action alerts
- Nudge / retry / kill actions via keyboard shortcuts

---

## 16. Config File Design

```yaml
# config.yaml

overseer:
  runtime: claude-code
  model: sonnet
  system_prompt: src/agents/definitions/coordinator.md

agents:
  max_concurrent: 8
  stall_timeout_seconds: 120
  drift_check_seconds: 20
  require_role_contract: true
  require_structured_output: true
  default_handoff: reviewer

roles:
  enabled:
    - orchestrator
    - coordinator
    - supervisor
    - lead
    - scout
    - developer
    - builder
    - tester
    - reviewer
    - merger
    - monitor
  prompts_dir: src/agents/definitions
  contracts_dir: src/roles/contracts
  strict_locking: true
  forbid_self_reassignment: true

runtimes:
  claude-code:
    binary: claude
    support_level: 3
  codex:
    binary: codex
    support_level: 3
  gemini-cli:
    binary: gemini
    support_level: 3
  aider:
    binary: aider
    support_level: 3
  openhands:
    binary: openhands
    support_level: 2
  opencode:
    binary: opencode
    support_level: 2
  goose:
    binary: goose
    support_level: 2
  cline:
    binary: cline
    support_level: 2
  qodo:
    binary: qodo
    support_level: 2
  mistral-vibe:
    binary: vibe
    support_level: 2
    programmatic_flag: "-p"
    output_format: streaming
  hermes:
    binary: ollama
    model: nous-hermes-3
    support_level: 1
  openclaw:
    binary: openclaw
    support_level: 1
    profile_prefix: swarm-

messaging:
  db_path: .swarm/messages.db

worktree:
  base_path: .swarm/worktrees
  one_worktree_per_agent: true
```

---

## 17. Milestone Roadmap

### Phase 1 — Foundation ✅ Complete
- [x] Project scaffolding
- [x] `AgentRuntime` base interface
- [x] Role registry + role contracts
- [x] SQLite event/message bus
- [x] Git worktree manager
- [x] Fleet status model
- [x] Echo runtime (test stub)
- [x] 46 tests passing

### Phase 2 — Core Roles 🔄 70% Complete
- [x] coordinator
- [x] scout
- [x] builder
- [x] developer
- [x] tester
- [ ] reviewer
- [ ] merger
- [ ] monitor
- [ ] lead
- [ ] supervisor
- [ ] orchestrator

### Phase 3 — Runtime Adapters v1 ⬜ Not Started
- [ ] Claude Code adapter
- [ ] Codex CLI adapter
- [ ] Gemini CLI adapter
- [ ] Aider adapter
- [ ] OpenHands CLI adapter
- [ ] OpenCode adapter
- [ ] Vibe adapter
- [ ] Hermes adapter

### Phase 4 — Role Safety ⬜ Not Started
- [ ] Tool policy enforcement (`guards.py`)
- [ ] Filesystem policy enforcement (`policies.py`)
- [ ] Structured output validation per role
- [ ] Drift detection
- [ ] Supervisor escalation flow

### Phase 5 — TUI ⬜ Not Started
- [ ] Textual app skeleton
- [ ] Overseer chat panel
- [ ] Fleet panel
- [ ] Selected agent output panel
- [ ] Event log panel
- [ ] Role contract viewer
- [ ] Drift/stall warnings
- [ ] Nudge / retry / kill actions

### Phase 6 — Overseer LLM Loop ⬜ Not Started
- [ ] LLM-driven task decomposition
- [ ] Dynamic runtime selection per sub-task
- [ ] Auto-nudge generation
- [ ] Merge conflict resolution (FIFO queue)

### Phase 7 — Extended Adapters ⬜ Not Started
- [ ] Goose adapter
- [ ] Cline CLI adapter
- [ ] Qodo Gen CLI adapter
- [ ] OpenClaw experimental adapter

### Phase 8 — Polish ⬜ Not Started
- [ ] `swarm doctor` improvements
- [ ] Replay logs
- [ ] Merge queue
- [ ] README
- [ ] Demo GIF / asciinema

---

## 18. Key Differences from Overstory

| Feature | Overstory | PolyglotSwarm |
|---------|-----------|---------------|
| Runtime scope | Focused supported runtime set | Broad coding-agent CLI support |
| Primary UX | CLI + dashboard | Overseer-first orchestration TUI |
| Role model | Strong hierarchy | Strong hierarchy + strict role locking |
| Developer role | Not central in exposed role list | First-class role ✅ |
| Tester role | Validation/review patterns exist | First-class dedicated role ✅ |
| Runtime adapters | Pluggable | Pluggable with capability matrix |
| Drift enforcement | Guard-centric | Guard + contract + schema + policy |
| Language | TypeScript/Bun | Python 3.12+ |
| TUI | Chalk ANSI (basic) | Textual (reactive, mouse-aware) |

---

## 19. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Runtime fragmentation across many CLIs | Capability flags + support levels |
| Some tools are interactive-first, not orchestration-first | Adapter policies; define partial support honestly |
| Agents drift out of role | Contracts, tool restrictions, structured outputs, drift detection |
| Reviewer or Scout starts editing code | Block with runtime/tool/filesystem policy (Phase 4) |
| Builder tries to self-review or self-merge | Force handoff chain |
| Too many adapters delay shipping | Tier 1 first; Echo runtime enables development in the meantime |
| Overseer context becomes too large | Summarize agent state into compact packets before injecting |
| Merge conflicts multiply with concurrency | One worktree per agent + FIFO merge queue |
| Local-model runtimes act inconsistently | Mark Level 1 until stabilized; tune stall timeout per runtime |
| vibe `-p` exits after max-turns | Store SESSION_ID; use `--resume` for nudges |
| OpenClaw gateway port collisions | `--profile` isolates each agent's gateway port automatically |

---

## 20. Non-Negotiable Rules

- Every agent has exactly **one role** per session.
- Roles are assigned by the coordinator and cannot be self-changed.
- Every task declares the required role.
- Every agent writes structured output for its role.
- Every handoff is explicit.
- Non-implementation agents do not edit code.
- Non-merge agents do not merge.
- Only spawn-capable roles can create child agents.
- Monitor and Supervisor can intervene, but not silently replace role policy.

---

## 21. References

- [Overstory GitHub](https://github.com/jayminwest/overstory)
- [Textual Docs](https://textual.textualize.io/)
- [Typer Docs](https://typer.tiangolo.com/)
- [aiosqlite](https://github.com/omnilib/aiosqlite)
- [libtmux](https://libtmux.git-pull.com/)
- [Pydantic v2](https://docs.pydantic.dev/)
- `vibe --help` — confirmed `-p`, `streaming`, `--enabled-tools`, `--resume`
- `openclaw --help` — confirmed `--profile`, `agent`, `acp`, gateway management
- Aider docs / OpenHands CLI docs / OpenCode docs / Goose docs / Cline CLI docs / Qodo Gen CLI
- SpacetimeDB evaluated and deferred — Python SDK unmaintained, wrong fit for local single-machine coordination

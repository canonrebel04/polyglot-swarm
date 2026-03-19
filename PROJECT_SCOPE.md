# PolyglotSwarm — Project Scope & Best Practices

> **Project Codename:** PolyglotSwarm  
> **Inspired by:** [Overstory](https://github.com/jayminwest/overstory)  
> **Goal:** A provider-agnostic multi-agent orchestration TUI with first-class support for Mistral (via `mistral-vibe-cli`), Hermes agents, OpenClaw, and any other CLI-based agent runtime.

---

## 1. Problem Statement

Overstory is a solid multi-agent orchestration framework, but it is tightly coupled to Claude Code and its ecosystem. Key gaps that PolyglotSwarm addresses:

- No support for **Mistral Vibe CLI** (`mistral-vibe` or `mvibe`)
- No support for **Hermes-based agents** (e.g., Nous Hermes via Ollama or llama.cpp)
- No support for **OpenClaw** or other privacy-first/self-hosted agent runtimes
- Dashboard/TUI is tmux-based with limited UI polish
- Provider coupling makes swapping models per-agent difficult at runtime

---

## 2. Core Vision

A **terminal-first multi-agent orchestration system** where:

1. An **Overseer model** (your choice of provider) maintains a top-level chat interface
2. The Overseer **spawns sub-agents** dynamically, each with a visible current task
3. The TUI shows **both layers simultaneously** — Overseer chat on top, agent fleet status below
4. The Overseer can **nudge, respawn, or kill** stalled agents autonomously
5. **Any CLI-based agent runtime** can be plugged in via an adapter interface

---

## 3. Build vs Fork Decision

### Option A — Fork Overstory

| Pros | Cons |
|------|------|
| Mature SQLite mail system already built | Deeply Claude-coupled in agent definitions |
| FIFO merge queue and worktree isolation ready | TypeScript/Bun stack (may conflict with your tooling preferences) |
| 36 CLI commands already implemented | Lots of dead weight to untangle (hooks, Anthropic env vars wired everywhere) |
| Tiered watchdog system is battle-tested | Dashboard is basic ANSI via Chalk — hard to extend cleanly |

### Option B — Build from Scratch ✅ (Recommended)

| Pros | Cons |
|------|------|
| Full control over runtime adapter interface from day one | More upfront work |
| Can choose your preferred language (Python, Rust, Node.js) | No battle-tested internals to lean on |
| TUI can be designed around your exact layout vision | SQLite messaging, worktree isolation must be implemented |
| No legacy Claude Code coupling to rip out | |

**Verdict:** Build from scratch. Overstory's most reusable ideas are its *concepts* (runtime adapter pattern, SQLite mail, watchdog tiers), not its code. Starting fresh lets you design the `AgentRuntime` interface with Mistral/Hermes/OpenClaw as first-class citizens rather than afterthoughts.

---

## 4. Recommended Tech Stack

| Layer | Recommendation | Reason |
|-------|---------------|--------|
| **Language** | Python 3.12+ | Fastest iteration, best AI/subprocess tooling, you already know it |
| **TUI Framework** | [Textual](https://github.com/Textualize/textual) | Rich reactive TUI, panels, live updates — ideal for split overseer/agent view |
| **Subprocess/Agent spawning** | `asyncio` + `asyncio.subprocess` | Non-blocking agent process management |
| **Messaging/State** | SQLite (WAL mode) via `aiosqlite` | Same approach as Overstory, proven ~1-5ms per query |
| **Worktree isolation** | `git worktree` via subprocess | Each agent gets its own branch/directory |
| **Config** | YAML via `PyYAML` + Pydantic validation | Structured, strict config with runtime overrides |
| **CLI entry point** | [Typer](https://typer.tiangolo.com/) | Clean CLI with subcommands, auto-help |
| **Session/process mgmt** | `tmux` via `libtmux` | Spawn agent sessions, read output, send input |

---

## 5. Architecture Design

```
┌─────────────────────────────────────────────────────────┐
│                  PolyglotSwarm TUI                      │
├───────────────────────────┬─────────────────────────────┤
│    OVERSEER CHAT PANEL    │    AGENT FLEET STATUS       │
│  > [Overseer]: Spawning   │  [agent-1] builder  ✅ done │
│    3 agents for task X    │  [agent-2] scout    🔄 work │
│  > [User]: status?        │  [agent-3] review   ⏸ stall│
│  > [Overseer]: agent-3    │                             │
│    appears stalled,       │  ┌─ agent-2 output ───────┐ │
│    nudging now...         │  │ reading src/main.py... │ │
│                           │  └────────────────────────┘ │
└───────────────────────────┴─────────────────────────────┘
```

### Core Components

```
polyglot-swarm/
  src/
    main.py                    # CLI entry point (Typer)
    config.py                  # Config loader + Pydantic models
    tui/
      app.py                   # Textual App root
      panels/
        overseer_chat.py       # Overseer conversation panel
        agent_fleet.py         # Sub-agent status grid
        agent_output.py        # Selected agent live output
    orchestrator/
      overseer.py              # Overseer loop: task decomp, dispatch, nudge
      agent_manager.py         # Spawn / kill / track agents
      watchdog.py              # Stall detection + auto-nudge
    runtimes/
      base.py                  # AgentRuntime abstract base class
      mistral.py               # Mistral Vibe CLI adapter
      hermes.py                # Hermes (Ollama/llama.cpp) adapter
      openclaw.py              # OpenClaw adapter
      claude.py                # Claude Code adapter (optional compat)
      gemini.py                # Gemini CLI adapter (optional compat)
    messaging/
      db.py                    # SQLite WAL message store
      protocol.py              # Typed message schema (Pydantic)
      bus.py                   # Async publish/subscribe layer
    worktree/
      manager.py               # git worktree create/cleanup
    agents/
      definitions/             # Per-role system prompt templates
        overseer.md
        builder.md
        scout.md
        reviewer.md
  config.yaml                  # Default config
  pyproject.toml
```

---

## 6. AgentRuntime Interface (Best Practice)

The most important architectural decision is the **runtime adapter interface**. Design this first, before any other code.

```python
# src/runtimes/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncIterator

@dataclass
class AgentConfig:
    name: str
    role: str          # builder, scout, reviewer, etc.
    task: str
    worktree_path: str
    model: str         # e.g. "mistral-large", "hermes-3", "openclaw-base"
    extra_env: dict[str, str] = None

@dataclass
class AgentStatus:
    name: str
    state: str         # idle | running | stalled | done | error
    current_task: str
    last_output: str
    pid: int | None

class AgentRuntime(ABC):
    """All agent runtimes must implement this interface."""

    @abstractmethod
    async def spawn(self, config: AgentConfig) -> str:
        """Spawn an agent session. Returns agent session ID."""
        ...

    @abstractmethod
    async def send_message(self, session_id: str, message: str) -> None:
        """Send a message/nudge to a running agent."""
        ...

    @abstractmethod
    async def get_status(self, session_id: str) -> AgentStatus:
        """Get current agent status."""
        ...

    @abstractmethod
    async def stream_output(self, session_id: str) -> AsyncIterator[str]:
        """Stream live output from agent."""
        ...

    @abstractmethod
    async def kill(self, session_id: str) -> None:
        """Terminate agent session."""
        ...

    @property
    @abstractmethod
    def runtime_name(self) -> str:
        """Unique identifier for this runtime."""
        ...
```

---

## 7. Mistral Vibe CLI Adapter Pattern

```python
# src/runtimes/mistral.py
import asyncio
from .base import AgentRuntime, AgentConfig, AgentStatus

class MistralVibeRuntime(AgentRuntime):
    runtime_name = "mistral-vibe"

    async def spawn(self, config: AgentConfig) -> str:
        # Spawn mistral-vibe in a new tmux window or subprocess
        cmd = [
            "mistral-vibe",           # or 'mvibe' depending on install
            "--model", config.model,
            "--system", self._load_system_prompt(config.role),
            "--workdir", config.worktree_path,
            "--non-interactive",      # headless mode flag (confirm with mistral-vibe docs)
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=config.worktree_path,
            env={**os.environ, **(config.extra_env or {})}
        )
        session_id = f"mistral-{config.name}-{proc.pid}"
        self._sessions[session_id] = proc
        return session_id

    def _load_system_prompt(self, role: str) -> str:
        prompt_path = Path(f"agents/definitions/{role}.md")
        return prompt_path.read_text() if prompt_path.exists() else ""
```

> **Note:** The exact flags for `mistral-vibe` (headless/non-interactive mode) need to be confirmed against the actual CLI's `--help`. Adapt the `spawn()` method accordingly.

---

## 8. Overseer Loop (Core Logic)

The Overseer is not just a model — it's a **control loop**:

```python
# src/orchestrator/overseer.py
async def overseer_loop(
    task: str,
    runtime_registry: dict[str, AgentRuntime],
    agent_manager: AgentManager,
    watchdog: Watchdog,
):
    # 1. Send task to Overseer model → decompose into sub-tasks
    sub_tasks = await overseer_model.decompose(task)

    # 2. Spawn agents per sub-task
    for sub_task in sub_tasks:
        runtime = runtime_registry[sub_task.preferred_runtime]
        await agent_manager.spawn_agent(runtime, sub_task)

    # 3. Monitor loop
    while not agent_manager.all_done():
        stalled = await watchdog.check_for_stalls()
        for agent in stalled:
            nudge_msg = await overseer_model.generate_nudge(agent)
            await agent_manager.nudge(agent.session_id, nudge_msg)
        await asyncio.sleep(5)

    # 4. Collect results, merge
    results = await agent_manager.collect_results()
    await merge_results(results)
```

---

## 9. TUI Layout Best Practices (Textual)

```python
# src/tui/app.py
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual.containers import Horizontal
from .panels.overseer_chat import OverseerChat
from .panels.agent_fleet import AgentFleet

class PolyglotSwarmApp(App):
    CSS = """
    Horizontal { height: 100%; }
    OverseerChat { width: 50%; border: solid green; }
    AgentFleet { width: 50%; border: solid cyan; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield OverseerChat()
            yield AgentFleet()
        yield Footer()
```

Textual supports **reactive data binding** — agent status updates push to the TUI automatically without polling hacks.

---

## 10. Config File Design

```yaml
# config.yaml
overseer:
  runtime: mistral-vibe
  model: mistral-large-latest
  system_prompt: agents/definitions/overseer.md

agents:
  default_runtime: hermes       # fallback for spawned agents
  max_concurrent: 5
  stall_timeout_seconds: 120    # trigger nudge after this many seconds of no output

runtimes:
  mistral-vibe:
    binary: mistral-vibe        # or absolute path
    extra_flags: []
  hermes:
    binary: ollama
    model: nous-hermes-3
    extra_flags: ["run"]
  openclaw:
    binary: openclaw
    extra_flags: ["--headless"]
  claude:
    binary: claude
    extra_flags: []

messaging:
  db_path: .swarm/messages.db

worktree:
  base_path: .swarm/worktrees
```

---

## 11. Milestone Roadmap

### Phase 1 — Foundation
- [ ] Project scaffolding (pyproject.toml, Typer CLI, config loader)
- [ ] `AgentRuntime` abstract base class
- [ ] Hermes/Ollama runtime adapter (easiest to test locally)
- [ ] SQLite message bus (`aiosqlite`, WAL mode)
- [ ] Git worktree manager

### Phase 2 — Orchestration Core
- [ ] `AgentManager` — spawn, track, kill agents
- [ ] `Watchdog` — stall detection (no output > N seconds)
- [ ] Overseer control loop (decompose → dispatch → monitor → nudge)
- [ ] Mistral Vibe CLI adapter
- [ ] OpenClaw adapter

### Phase 3 — TUI
- [ ] Textual app skeleton (split panels)
- [ ] Overseer chat panel (live conversation stream)
- [ ] Agent fleet panel (status grid with task labels)
- [ ] Agent output panel (selected agent live output)
- [ ] Nudge button / keyboard shortcut

### Phase 4 — Polish
- [ ] `swarm init` command
- [ ] `swarm doctor` health checks
- [ ] Config validation (Pydantic)
- [ ] Logging (NDJSON structured logs per agent)
- [ ] README + demo GIF

---

## 12. Key Differences from Overstory

| Feature | Overstory | PolyglotSwarm |
|---------|-----------|---------------|
| Primary runtime | Claude Code | **Any** (Mistral, Hermes, OpenClaw, Claude, Gemini) |
| Language | TypeScript/Bun | Python 3.12+ |
| TUI | Chalk ANSI (basic) | **Textual** (reactive, mouse-aware) |
| Overseer chat panel | ❌ Not visible in TUI | ✅ First-class panel |
| Agent spawn mechanism | tmux worktrees | tmux + asyncio subprocess (both) |
| Messaging | SQLite mail (typed) | SQLite pub/sub (Pydantic typed) |
| Mistral Vibe CLI | ❌ | ✅ |
| Hermes (Ollama) | ❌ | ✅ |
| OpenClaw | ❌ | ✅ |
| License compatibility | MIT (can reference) | MIT (new project) |

---

## 13. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Mistral Vibe CLI may lack headless/non-interactive mode | Wrap in tmux pane; send input via `tmux send-keys` instead |
| Hermes models via Ollama may be slower — agent stalls look like crashes | Tune `stall_timeout_seconds` per runtime in config |
| OpenClaw API/CLI surface unknown | Abstract via `AgentRuntime`; stub adapter first, fill in details |
| Overseer LLM context gets huge with many agents | Summarize agent status before injecting into overseer context; keep fleet updates compact |
| Merge conflicts between agent worktrees | Borrow Overstory's 4-tier conflict resolution approach; FIFO merge queue |

---

## 14. References

- [Overstory GitHub](https://github.com/jayminwest/overstory) — inspiration and architectural reference
- [Textual Docs](https://textual.textualize.io/) — TUI framework
- [Typer Docs](https://typer.tiangolo.com/) — CLI framework
- [aiosqlite](https://github.com/omnilib/aiosqlite) — async SQLite
- [libtmux](https://libtmux.git-pull.com/) — programmatic tmux control
- [Pydantic v2](https://docs.pydantic.dev/) — config and message schema validation
- [Overstory STEELMAN.md](https://github.com/jayminwest/overstory/blob/main/STEELMAN.md) — risk analysis for multi-agent systems (read before going to production)

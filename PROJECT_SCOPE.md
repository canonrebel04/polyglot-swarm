# PolyglotSwarm — Project Scope & Best Practices

> **Project Codename:** PolyglotSwarm  
> **Inspired by:** [Overstory](https://github.com/jayminwest/overstory)  
> **Goal:** A provider-agnostic multi-agent orchestration TUI with first-class support for Mistral (via `vibe`), Hermes agents, OpenClaw, and any other CLI-based agent runtime.

---

## 1. Problem Statement

Overstory is a solid multi-agent orchestration framework, but it is tightly coupled to Claude Code and its ecosystem. Key gaps that PolyglotSwarm addresses:

- No support for **Mistral Vibe CLI** (`vibe`)
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
      mistral.py               # Mistral Vibe CLI adapter  (binary: vibe)
      hermes.py                # Hermes (Ollama/llama.cpp) adapter
      openclaw.py              # OpenClaw adapter          (binary: openclaw)
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
from dataclasses import dataclass, field
from typing import AsyncIterator

@dataclass
class AgentConfig:
    name: str
    role: str          # builder, scout, reviewer, etc.
    task: str
    worktree_path: str
    model: str         # e.g. "mistral-large-latest", "hermes-3", "openclaw-base"
    extra_env: dict[str, str] = field(default_factory=dict)

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

## 7. Mistral Vibe CLI Adapter

> **Binary:** `vibe`  
> **Programmatic mode flag:** `-p` / `--prompt` — sends prompt, auto-approves all tools, outputs response, then exits.  
> **Key flags confirmed from `vibe --help`:**

| Flag | Purpose |
|------|---------|
| `-p TEXT` / `--prompt TEXT` | Programmatic (headless) mode. Runs non-interactively, auto-approves tools. |
| `--max-turns N` | Limit assistant turns (programmatic mode only) |
| `--max-price DOLLARS` | Cost cap before interrupt (programmatic mode only) |
| `--enabled-tools TOOL` | Allowlist specific tools; disables all others in `-p` mode. Supports glob + regex. |
| `--output {text,json,streaming}` | Output format. Use `streaming` for live NDJSON per message. |
| `--agent NAME` | Use a custom agent from `~/.vibe/agents/NAME.toml` or builtins: `default`, `plan`, `accept-edits`, `auto-approve` |
| `--workdir DIR` | Change to this directory before running |
| `--resume SESSION_ID` | Resume a specific session (supports partial match) |
| `-c` / `--continue` | Continue from most recent session |

### Spawn Strategy

Use `-p` (programmatic mode) with `--output streaming` for non-interactive agent runs. The streaming NDJSON output lets you read each message as it arrives without waiting for the agent to finish. For multi-turn agents that need to stay alive and receive nudges, use `--resume SESSION_ID` to re-enter a session.

```python
# src/runtimes/mistral.py
import asyncio, os, json
from pathlib import Path
from .base import AgentRuntime, AgentConfig, AgentStatus

class MistralVibeRuntime(AgentRuntime):
    runtime_name = "mistral-vibe"

    def __init__(self):
        self._sessions: dict[str, asyncio.subprocess.Process] = {}
        self._session_ids: dict[str, str] = {}  # session_id -> vibe SESSION_ID for resume

    async def spawn(self, config: AgentConfig) -> str:
        system_prompt = self._load_system_prompt(config.role)
        # Write system prompt into a custom agent toml if needed, or prepend to prompt
        initial_prompt = f"{system_prompt}\n\nYour task:\n{config.task}"

        cmd = [
            "vibe",
            "-p", initial_prompt,
            "--output", "streaming",        # NDJSON stream per message
            "--max-turns", "50",
            "--workdir", config.worktree_path,
            "--agent", "auto-approve",       # auto-approve all tool calls
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=config.worktree_path,
            env={**os.environ, **(config.extra_env or {})},
        )
        session_id = f"vibe-{config.name}-{proc.pid}"
        self._sessions[session_id] = proc
        return session_id

    async def send_message(self, session_id: str, message: str) -> None:
        # For nudges: resume the last session with a new -p prompt
        vibe_session = self._session_ids.get(session_id)
        cmd = ["vibe", "-p", message, "--output", "streaming"]
        if vibe_session:
            cmd += ["--resume", vibe_session]
        proc = await asyncio.create_subprocess_exec(*cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        self._sessions[session_id] = proc

    async def stream_output(self, session_id: str):
        proc = self._sessions.get(session_id)
        if not proc or not proc.stdout:
            return
        async for line in proc.stdout:
            decoded = line.decode().strip()
            if decoded:
                try:
                    msg = json.loads(decoded)  # NDJSON streaming
                    yield msg.get("content", decoded)
                except json.JSONDecodeError:
                    yield decoded

    async def kill(self, session_id: str) -> None:
        proc = self._sessions.pop(session_id, None)
        if proc:
            proc.terminate()
            await proc.wait()

    async def get_status(self, session_id: str) -> AgentStatus:
        proc = self._sessions.get(session_id)
        if not proc:
            state = "error"
        elif proc.returncode is None:
            state = "running"
        elif proc.returncode == 0:
            state = "done"
        else:
            state = "error"
        return AgentStatus(
            name=session_id, state=state,
            current_task="", last_output="", pid=proc.pid if proc else None
        )

    def _load_system_prompt(self, role: str) -> str:
        p = Path(f"agents/definitions/{role}.md")
        return p.read_text() if p.exists() else ""
```

---

## 8. OpenClaw Adapter

> **Binary:** `openclaw`  
> **OpenClaw is a WhatsApp/Telegram automation gateway with a built-in agent system**, not a general-purpose coding agent. Its agent interface is accessed via the running Gateway.
> **Key commands confirmed from `openclaw --help`:**

| Command/Flag | Purpose |
|--------------|--------|
| `openclaw agent` | Run **one agent turn** via the Gateway |
| `openclaw agents *` | Manage isolated agent workspaces, auth, routing |
| `openclaw gateway *` | Start/stop/query the WebSocket Gateway (agents run through this) |
| `openclaw tui` | Open a terminal UI connected to the Gateway |
| `openclaw acp *` | Agent Control Protocol tools |
| `openclaw sandbox *` | Manage sandbox containers for agent isolation |
| `openclaw sessions *` | List stored conversation sessions |
| `--profile <name>` | Isolate state under `~/.openclaw-<name>` (critical for multi-agent) |
| `--dev` | Dev profile: isolated state, shifts ports (gateway port 19001) |

### Key Insight: Multi-Agent with OpenClaw

OpenClaw was designed for a **single gateway with isolated agents via `--profile`**. Each sub-agent in PolyglotSwarm maps to its own OpenClaw profile (isolated workspace). Communication between agents goes through PolyglotSwarm's SQLite bus, NOT through WhatsApp/Telegram channels.

```python
# src/runtimes/openclaw.py
import asyncio, os
from .base import AgentRuntime, AgentConfig, AgentStatus

class OpenClawRuntime(AgentRuntime):
    runtime_name = "openclaw"

    def __init__(self):
        self._sessions: dict[str, asyncio.subprocess.Process] = {}
        self._profiles: dict[str, str] = {}  # session_id -> profile name

    async def spawn(self, config: AgentConfig) -> str:
        profile = f"swarm-{config.name}"  # isolated profile per agent
        self._profiles[f"openclaw-{config.name}"] = profile

        # First ensure the gateway is running for this profile
        # openclaw --profile <name> gateway --background
        gw_cmd = [
            "openclaw",
            "--profile", profile,
            "gateway", "--background",   # start gateway in background
        ]
        gw_proc = await asyncio.create_subprocess_exec(
            *gw_cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await gw_proc.wait()
        await asyncio.sleep(2)  # allow gateway to initialize

        # Now run one agent turn with the initial task
        cmd = [
            "openclaw",
            "--profile", profile,
            "agent",
            "--message", config.task,
            "--deliver",                 # deliver response back
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, **(config.extra_env or {})},
        )
        session_id = f"openclaw-{config.name}-{proc.pid}"
        self._sessions[session_id] = proc
        return session_id

    async def send_message(self, session_id: str, message: str) -> None:
        # Nudge: run another agent turn against the same profile
        name = session_id.split("-")[1]  # extract agent name
        profile = self._profiles.get(f"openclaw-{name}")
        if not profile:
            return
        cmd = ["openclaw", "--profile", profile, "agent", "--message", message, "--deliver"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        self._sessions[session_id] = proc

    async def stream_output(self, session_id: str):
        proc = self._sessions.get(session_id)
        if not proc or not proc.stdout:
            return
        async for line in proc.stdout:
            decoded = line.decode().strip()
            if decoded:
                yield decoded

    async def kill(self, session_id: str) -> None:
        name = session_id.split("-")[1]
        profile = self._profiles.get(f"openclaw-{name}")
        proc = self._sessions.pop(session_id, None)
        if proc:
            proc.terminate()
            await proc.wait()
        # Stop gateway for this profile
        if profile:
            stop_cmd = ["openclaw", "--profile", profile, "gateway", "stop"]
            stop = await asyncio.create_subprocess_exec(*stop_cmd,
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            await stop.wait()

    async def get_status(self, session_id: str) -> AgentStatus:
        proc = self._sessions.get(session_id)
        if not proc:
            state = "error"
        elif proc.returncode is None:
            state = "running"
        elif proc.returncode == 0:
            state = "done"
        else:
            state = "error"
        return AgentStatus(
            name=session_id, state=state,
            current_task="", last_output="", pid=proc.pid if proc else None
        )

    @property
    def runtime_name(self) -> str:
        return "openclaw"
```

> **⚠️ OpenClaw Note:** OpenClaw's primary design is WhatsApp/Telegram automation. Using it as a coding agent runtime means you're driving it through its `agent` single-turn command or its ACP (Agent Control Protocol). Check `openclaw acp --help` and `openclaw agents --help` for richer multi-turn agent workspace management that may be better suited for persistent sub-agents.

---

## 9. Overseer Loop (Core Logic)

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

## 10. TUI Layout Best Practices (Textual)

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

## 11. Config File Design

```yaml
# config.yaml
overseer:
  runtime: mistral-vibe
  model: mistral-large-latest
  system_prompt: agents/definitions/overseer.md

agents:
  default_runtime: mistral-vibe
  max_concurrent: 5
  stall_timeout_seconds: 120    # trigger nudge after N seconds of no output

runtimes:
  mistral-vibe:
    binary: vibe                # confirmed binary name
    programmatic_flag: "-p"     # headless mode flag
    output_format: streaming    # NDJSON per message
    default_agent: auto-approve # builtin agent profile
  hermes:
    binary: ollama
    model: nous-hermes-3
    extra_flags: ["run"]
  openclaw:
    binary: openclaw
    profile_prefix: swarm-      # isolate each agent under swarm-<name> profile
    gateway_background: true
  claude:
    binary: claude
    extra_flags: []

messaging:
  db_path: .swarm/messages.db

worktree:
  base_path: .swarm/worktrees
```

---

## 12. Milestone Roadmap

### Phase 1 — Foundation
- [ ] Project scaffolding (pyproject.toml, Typer CLI, config loader)
- [ ] `AgentRuntime` abstract base class
- [ ] Hermes/Ollama runtime adapter (easiest to test locally offline)
- [ ] SQLite message bus (`aiosqlite`, WAL mode)
- [ ] Git worktree manager

### Phase 2 — Orchestration Core
- [ ] `AgentManager` — spawn, track, kill agents
- [ ] `Watchdog` — stall detection (no output > N seconds)
- [ ] Overseer control loop (decompose → dispatch → monitor → nudge)
- [ ] Mistral Vibe CLI adapter (`vibe -p`, streaming NDJSON output)
- [ ] OpenClaw adapter (profile-isolated, `openclaw agent` single-turn + ACP)

### Phase 3 — TUI
- [ ] Textual app skeleton (split panels)
- [ ] Overseer chat panel (live conversation stream)
- [ ] Agent fleet panel (status grid with task labels)
- [ ] Agent output panel (selected agent live output)
- [ ] Nudge button / keyboard shortcut

### Phase 4 — Polish
- [ ] `swarm init` command
- [ ] `swarm doctor` health checks (verify `vibe`, `openclaw`, `ollama` binaries)
- [ ] Config validation (Pydantic)
- [ ] Logging (NDJSON structured logs per agent)
- [ ] README + demo GIF

---

## 13. Key Differences from Overstory

| Feature | Overstory | PolyglotSwarm |
|---------|-----------|---------------|
| Primary runtime | Claude Code | **Any** (Mistral Vibe, Hermes, OpenClaw, Claude, Gemini) |
| Language | TypeScript/Bun | Python 3.12+ |
| TUI | Chalk ANSI (basic) | **Textual** (reactive, mouse-aware) |
| Overseer chat panel | ❌ Not visible in TUI | ✅ First-class panel |
| Agent spawn mechanism | tmux worktrees | asyncio subprocess + optional tmux |
| Messaging | SQLite mail (typed) | SQLite pub/sub (Pydantic typed) |
| Mistral Vibe (`vibe`) | ❌ | ✅ (`-p` programmatic + streaming NDJSON) |
| Hermes (Ollama) | ❌ | ✅ |
| OpenClaw | ❌ | ✅ (profile-isolated, ACP gateway) |
| License compatibility | MIT (can reference) | MIT (new project) |

---

## 14. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| `vibe -p` exits after `--max-turns` — multi-turn agents need session resume | Store vibe SESSION_ID after first run; use `--resume SESSION_ID` for nudges |
| `vibe --output streaming` NDJSON schema may change between versions | Pin vibe version in pyproject.toml; version-check on startup |
| OpenClaw gateway port collisions when running many agent profiles | Use `--profile` to isolate; each profile shifts derived ports automatically |
| OpenClaw `agent` is single-turn by design — may not suit long-running tasks | Use `openclaw acp` for multi-turn ACP-based agents; investigate `openclaw agents` workspaces |
| Hermes models via Ollama may be slower — stalls look like crashes | Tune `stall_timeout_seconds` per runtime in config |
| Overseer LLM context grows large with many agents | Summarize agent status before injecting into overseer context |
| Merge conflicts between agent worktrees | FIFO merge queue; borrow 4-tier conflict resolution pattern from Overstory |

---

## 15. References

- [Overstory GitHub](https://github.com/jayminwest/overstory) — inspiration and architectural reference
- [Textual Docs](https://textual.textualize.io/) — TUI framework
- [Typer Docs](https://typer.tiangolo.com/) — CLI framework
- [aiosqlite](https://github.com/omnilib/aiosqlite) — async SQLite
- [libtmux](https://libtmux.git-pull.com/) — programmatic tmux control
- [Pydantic v2](https://docs.pydantic.dev/) — config and message schema validation
- [Overstory STEELMAN.md](https://github.com/jayminwest/overstory/blob/main/STEELMAN.md) — risk analysis for multi-agent systems
- `vibe --help` — confirmed programmatic mode via `-p`, streaming NDJSON output, `--resume` for session continuation
- `openclaw --help` — confirmed profile isolation, `agent` single-turn command, ACP tools, gateway management

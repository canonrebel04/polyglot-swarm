"""
Test runtime system components.
"""

import pytest
from src.runtimes.base import AgentConfig, AgentStatus, RuntimeCapabilities
from src.runtimes.registry import RuntimeRegistry


def test_agent_config():
    """Test AgentConfig dataclass."""
    config = AgentConfig(
        name="test-agent",
        role="builder",
        task="implement feature",
        worktree_path="/tmp/worktree",
        model="gpt-4",
        runtime="codex",
        system_prompt_path="prompts/builder.md"
    )
    
    assert config.name == "test-agent"
    assert config.role == "builder"
    assert config.task == "implement feature"
    assert config.worktree_path == "/tmp/worktree"
    assert config.model == "gpt-4"
    assert config.runtime == "codex"
    assert config.system_prompt_path == "prompts/builder.md"
    assert config.allowed_tools == []
    assert config.blocked_tools == []
    assert config.read_only == False
    assert config.can_spawn_children == False


def test_agent_status():
    """Test AgentStatus dataclass."""
    status = AgentStatus(
        name="test-agent",
        role="builder",
        state="running",
        current_task="implementing feature",
        runtime="codex",
        last_output="working...",
        pid=12345
    )
    
    assert status.name == "test-agent"
    assert status.role == "builder"
    assert status.state == "running"
    assert status.current_task == "implementing feature"
    assert status.runtime == "codex"
    assert status.last_output == "working..."
    assert status.pid == 12345


def test_runtime_capabilities():
    """Test RuntimeCapabilities dataclass."""
    caps = RuntimeCapabilities(
        interactive_chat=True,
        headless_run=True,
        streaming_output=True
    )
    
    assert caps.interactive_chat == True
    assert caps.headless_run == True
    assert caps.streaming_output == True
    assert caps.resume_session == False
    assert caps.tool_allowlist == False


def test_runtime_registry():
    """Test RuntimeRegistry functionality."""
    registry = RuntimeRegistry()
    
    # Test empty registry
    assert registry.list_available() == []
    assert registry.has_runtime("test") == False
    assert registry.get("test") is None
    
    # Test registration (we can't test with abstract class, but we can test the registry logic)
    # This would normally be tested with a concrete implementation


def test_runtime_registry_global():
    """Test global registry instance."""
    from src.runtimes.registry import registry
    
    assert hasattr(registry, 'register')
    assert hasattr(registry, 'get')
    assert hasattr(registry, 'list_available')
    assert hasattr(registry, 'has_runtime')
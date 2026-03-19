"""
Test the echo runtime implementation.
"""

import pytest
import asyncio
from src.runtimes.echo import EchoRuntime
from src.runtimes.base import AgentConfig


@pytest.mark.asyncio
async def test_echo_runtime_basic():
    """Test basic echo runtime functionality."""
    runtime = EchoRuntime()
    
    # Test runtime properties
    assert runtime.runtime_name == "echo"
    assert runtime.capabilities.interactive_chat == True
    assert runtime.capabilities.headless_run == True


@pytest.mark.asyncio
async def test_echo_runtime_spawn():
    """Test spawning an echo agent."""
    runtime = EchoRuntime()
    
    config = AgentConfig(
        name="test-agent",
        role="builder",
        task="test task",
        worktree_path="/tmp/test",
        model="echo-model",
        runtime="echo",
        system_prompt_path="test.md"
    )
    
    session_id = await runtime.spawn(config)
    assert session_id is not None
    assert isinstance(session_id, str)
    
    # Test getting status
    status = await runtime.get_status(session_id)
    assert status.name == "test-agent"
    assert status.role == "builder"
    assert status.state == "running"
    assert status.current_task == "test task"
    assert status.runtime == "echo"


@pytest.mark.asyncio
async def test_echo_runtime_messages():
    """Test sending and receiving messages."""
    runtime = EchoRuntime()
    
    config = AgentConfig(
        name="test-agent",
        role="scout",
        task="explore codebase",
        worktree_path="/tmp/test",
        model="echo-model",
        runtime="echo",
        system_prompt_path="test.md"
    )
    
    session_id = await runtime.spawn(config)
    
    # Send a message
    await runtime.send_message(session_id, "Hello echo agent!")
    
    # Get status to see the echo response
    status = await runtime.get_status(session_id)
    assert "Echo: Hello echo agent!" in status.last_output


@pytest.mark.asyncio
async def test_echo_runtime_streaming():
    """Test streaming output from echo agent."""
    runtime = EchoRuntime()
    
    config = AgentConfig(
        name="test-agent",
        role="builder",
        task="build feature",
        worktree_path="/tmp/test",
        model="echo-model",
        runtime="echo",
        system_prompt_path="test.md"
    )
    
    session_id = await runtime.spawn(config)
    
    # Collect some output
    messages = []
    async for message in runtime.stream_output(session_id):
        messages.append(message)
        if len(messages) >= 3:  # Get initial messages
            break
    
    assert len(messages) >= 3
    assert any("started" in msg for msg in messages)
    assert any("Task:" in msg for msg in messages)
    assert any("Role:" in msg for msg in messages)


@pytest.mark.asyncio
async def test_echo_runtime_kill():
    """Test killing an echo agent."""
    runtime = EchoRuntime()
    
    config = AgentConfig(
        name="test-agent",
        role="tester",
        task="test task",
        worktree_path="/tmp/test",
        model="echo-model",
        runtime="echo",
        system_prompt_path="test.md"
    )
    
    session_id = await runtime.spawn(config)
    
    # Kill the agent
    await runtime.kill(session_id)
    
    # Verify it's gone
    with pytest.raises(ValueError):
        await runtime.get_status(session_id)


@pytest.mark.asyncio
async def test_echo_runtime_registration():
    """Test that echo runtime is properly registered."""
    from src.runtimes.registry import registry
    
    # The echo runtime should be auto-registered when imported
    assert registry.has_runtime("echo") == True
    
    echo_class = registry.get("echo")
    assert echo_class is not None
    assert echo_class().runtime_name == "echo"
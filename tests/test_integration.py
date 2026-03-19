"""
Integration tests for PolyglotSwarm components working together.
"""

import pytest
import asyncio
import tempfile
import os
from src.runtimes.echo import EchoRuntime
from src.runtimes.base import AgentConfig
from src.roles.registry import role_registry
from src.messaging.db import SwarmDB


@pytest.mark.asyncio
async def test_full_system_integration():
    """Test the full system working together."""
    # Test role registry
    roles = role_registry.list_roles()
    assert "scout" in roles
    assert "builder" in roles
    
    # Test that scout cannot edit code
    assert role_registry.can_perform_action("scout", "edit_code") == False
    
    # Test that builder can edit code
    assert role_registry.can_perform_action("builder", "edit_code") == True
    
    # Test runtime
    runtime = EchoRuntime()
    config = AgentConfig(
        name="integration-test-agent",
        role="builder",
        task="integration test task",
        worktree_path="/tmp/integration",
        model="test-model",
        runtime="echo",
        system_prompt_path="test.md"
    )
    
    session_id = await runtime.spawn(config)
    
    # Test sending a message
    await runtime.send_message(session_id, "Hello from integration test!")
    
    # Test getting status
    status = await runtime.get_status(session_id)
    assert status.name == "integration-test-agent"
    assert status.role == "builder"
    assert "Echo: Hello from integration test!" in status.last_output
    
    # Test streaming some output
    messages = []
    async for message in runtime.stream_output(session_id):
        messages.append(message)
        if len(messages) >= 2:
            break
    
    assert len(messages) >= 2
    
    # Test database
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "integration.db")
        db = SwarmDB(db_path)
        await db.connect()
        
        # Add a message
        await db.add_message(
            session_id=session_id,
            sender="integration-test",
            content="Integration test message",
            message_type="test"
        )
        
        # Create agent session
        await db.create_agent_session(
            session_id=session_id,
            agent_name=config.name,
            role=config.role,
            runtime=runtime.runtime_name,
            state="running"
        )
        
        # Get messages
        messages = await db.get_messages(session_id)
        assert len(messages) == 1
        assert messages[0][1] == "Integration test message"
        
        # Get agent sessions
        sessions = await db.get_agent_sessions()
        assert len(sessions) == 1
        assert sessions[0][1] == config.name
        
        # Add an event
        await db.add_event(
            event_type="integration_test",
            session_id=session_id,
            agent_name=config.name,
            data='{"test": "passed"}'
        )
        
        # Get events
        events = await db.get_recent_events()
        assert len(events) == 1
        assert events[0][0] == "integration_test"
        
        await db.close()
    
    # Clean up runtime
    await runtime.kill(session_id)


@pytest.mark.asyncio
async def test_role_runtime_integration():
    """Test role system integration with runtime system."""
    runtime = EchoRuntime()
    
    # Test spawning agents with different roles
    scout_config = AgentConfig(
        name="scout-agent",
        role="scout",
        task="explore codebase",
        worktree_path="/tmp/test",
        model="scout-model",
        runtime="echo",
        system_prompt_path="scout.md"
    )
    
    builder_config = AgentConfig(
        name="builder-agent",
        role="builder",
        task="implement feature",
        worktree_path="/tmp/test",
        model="builder-model",
        runtime="echo",
        system_prompt_path="builder.md"
    )
    
    scout_session = await runtime.spawn(scout_config)
    builder_session = await runtime.spawn(builder_config)
    
    # Verify roles are correctly set
    scout_status = await runtime.get_status(scout_session)
    builder_status = await runtime.get_status(builder_session)
    
    assert scout_status.role == "scout"
    assert builder_status.role == "builder"
    
    # Verify role permissions
    assert role_registry.can_perform_action("scout", "edit_code") == False
    assert role_registry.can_perform_action("builder", "edit_code") == True
    
    # Clean up
    await runtime.kill(scout_session)
    await runtime.kill(builder_session)


@pytest.mark.asyncio
async def test_end_to_end_flow():
    """Test a complete end-to-end flow."""
    # 1. Initialize components
    runtime = EchoRuntime()
    
    # 2. Create agent configuration
    config = AgentConfig(
        name="e2e-agent",
        role="developer",
        task="end-to-end test task",
        worktree_path="/tmp/e2e",
        model="e2e-model",
        runtime="echo",
        system_prompt_path="developer.md"
    )
    
    # 3. Spawn agent
    session_id = await runtime.spawn(config)
    
    # 4. Send task message
    await runtime.send_message(session_id, "Please implement the feature")
    
    # 5. Check status
    status = await runtime.get_status(session_id)
    assert status.state == "running"
    assert "Echo: Please implement the feature" in status.last_output
    
    # 6. Stream some output
    output_lines = []
    async for line in runtime.stream_output(session_id):
        output_lines.append(line)
        if len(output_lines) >= 3:
            break
    
    assert len(output_lines) >= 3
    
    # 7. Database integration
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "e2e.db")
        db = SwarmDB(db_path)
        await db.connect()
        
        # Log the agent session
        await db.create_agent_session(
            session_id=session_id,
            agent_name=config.name,
            role=config.role,
            runtime=runtime.runtime_name,
            state="completed"
        )
        
        # Log completion event
        await db.add_event(
            event_type="agent_completed",
            session_id=session_id,
            agent_name=config.name,
            data='{"status": "success"}'
        )
        
        # Verify data was stored
        sessions = await db.get_agent_sessions()
        events = await db.get_recent_events()
        
        assert len(sessions) == 1
        assert len(events) == 1
        
        await db.close()
    
    # 8. Clean up
    await runtime.kill(session_id)
    
    # Verify agent is terminated
    with pytest.raises(ValueError):
        await runtime.get_status(session_id)
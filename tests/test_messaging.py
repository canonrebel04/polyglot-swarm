"""
Test messaging system components.
"""

import pytest
import asyncio
import tempfile
import os
from src.messaging.db import SwarmDB


@pytest.mark.asyncio
async def test_db_initialization():
    """Test database initialization."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.db")
        db = SwarmDB(db_path)
        
        await db.connect()
        
        # Test that tables were created
        cursor = await db._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = await cursor.fetchall()
        table_names = [table[0] for table in tables]
        
        assert "messages" in table_names
        assert "agent_sessions" in table_names
        assert "events" in table_names
        
        await db.close()


@pytest.mark.asyncio
async def test_message_operations():
    """Test message CRUD operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.db")
        db = SwarmDB(db_path)
        await db.connect()
        
        # Add a message
        await db.add_message(
            session_id="test-session",
            sender="user",
            content="Hello world",
            message_type="text"
        )
        
        # Get messages
        messages = await db.get_messages("test-session")
        assert len(messages) == 1
        assert messages[0][0] == "user"  # sender
        assert messages[0][1] == "Hello world"  # content
        assert messages[0][3] == "text"  # message_type
        
        await db.close()


@pytest.mark.asyncio
async def test_agent_session_operations():
    """Test agent session operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.db")
        db = SwarmDB(db_path)
        await db.connect()
        
        # Create agent session
        await db.create_agent_session(
            session_id="test-session",
            agent_name="test-agent",
            role="builder",
            runtime="test-runtime",
            state="running"
        )
        
        # Update agent state
        await db.update_agent_state("test-session", "completed")
        
        # Get agent sessions
        sessions = await db.get_agent_sessions()
        assert len(sessions) == 1
        assert sessions[0][0] == "test-session"  # session_id
        assert sessions[0][1] == "test-agent"  # agent_name
        assert sessions[0][2] == "builder"  # role
        assert sessions[0][3] == "test-runtime"  # runtime
        assert sessions[0][4] == "completed"  # state
        
        await db.close()


@pytest.mark.asyncio
async def test_event_operations():
    """Test event logging operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test.db")
        db = SwarmDB(db_path)
        await db.connect()
        
        # Add events
        await db.add_event(
            event_type="agent_started",
            session_id="test-session",
            agent_name="test-agent",
            data='{"status": "running"}'
        )
        
        await db.add_event(
            event_type="agent_completed",
            session_id="test-session",
            agent_name="test-agent"
        )
        
        # Get recent events
        events = await db.get_recent_events()
        assert len(events) == 2
        
        # Check that both event types are present (order may vary)
        event_types = [event[0] for event in events]
        assert "agent_started" in event_types
        assert "agent_completed" in event_types
        
        await db.close()


@pytest.mark.asyncio
async def test_global_db_instance():
    """Test global database instance."""
    from src.messaging.db import db, init_db, close_db
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Change db path temporarily
        original_path = db.db_path
        db.db_path = os.path.join(temp_dir, "test.db")
        
        try:
            await init_db()
            
            # Test that we can use the global instance
            await db.add_message(
                session_id="test",
                sender="test",
                content="test"
            )
            
            messages = await db.get_messages("test")
            assert len(messages) == 1
            
            await close_db()
        finally:
            db.db_path = original_path
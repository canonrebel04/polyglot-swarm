"""
Test worktree manager functionality.
"""

import pytest
import tempfile
import os
from src.worktree.manager import WorktreeManager


def test_worktree_manager_initialization():
    """Test worktree manager initialization."""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = WorktreeManager(base_path=temp_dir)
        assert manager.base_path == temp_dir
        assert os.path.exists(temp_dir)


def test_worktree_manager_no_git():
    """Test worktree manager behavior when not in a git repository."""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = WorktreeManager(base_path=temp_dir)
        
        # Should raise an error when not in a git repo
        with pytest.raises(RuntimeError):  # Any RuntimeError is acceptable
            manager.create_worktree()


def test_worktree_manager_list_empty():
    """Test listing worktrees when none exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = WorktreeManager(base_path=temp_dir)
        worktrees = manager.list_worktrees()
        assert worktrees == []


def test_worktree_manager_cleanup():
    """Test cleanup functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = WorktreeManager(base_path=temp_dir)
        
        # Cleanup should work even when no worktrees exist
        manager.cleanup_all()  # Should not raise an error
        
        assert manager.list_worktrees() == []


def test_global_worktree_manager():
    """Test global worktree manager instance."""
    from src.worktree.manager import worktree_manager
    
    assert hasattr(worktree_manager, 'create_worktree')
    assert hasattr(worktree_manager, 'remove_worktree')
    assert hasattr(worktree_manager, 'list_worktrees')
    assert hasattr(worktree_manager, 'cleanup_all')
    
    # Should have default base path
    assert worktree_manager.base_path == ".swarm/worktrees"
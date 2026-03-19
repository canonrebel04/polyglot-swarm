"""
Git worktree manager for agent isolation.
"""

import os
import subprocess
import shutil
from typing import Optional, List
import uuid


class WorktreeManager:
    """Manage git worktrees for agent isolation."""

    def __init__(self, base_path: str = ".swarm/worktrees"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def create_worktree(self, branch_name: Optional[str] = None) -> str:
        """
        Create a new worktree for an agent.
        
        Args:
            branch_name: Optional branch name. If None, generates a unique name.
            
        Returns:
            Path to the new worktree
        """
        if branch_name is None:
            branch_name = f"swarm-agent-{uuid.uuid4().hex[:8]}"

        worktree_path = os.path.join(self.base_path, branch_name)
        
        # Check if we're in a git repository
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout.strip() != "true":
                raise RuntimeError("Not in a git repository")
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise RuntimeError("Not in a git repository or git not found")

        # Create the worktree
        try:
            subprocess.run(
                ["git", "worktree", "add", "--no-checkout", worktree_path, branch_name],
                check=True
            )
            
            # Initialize the worktree (checkout files)
            subprocess.run(
                ["git", "checkout", "--force"],
                cwd=worktree_path,
                check=True
            )
            
            return worktree_path
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to create worktree: {e}")

    def remove_worktree(self, worktree_path: str) -> None:
        """
        Remove a worktree.
        
        Args:
            worktree_path: Path to the worktree to remove
        """
        if not os.path.exists(worktree_path):
            return

        # Get the branch name from the path
        branch_name = os.path.basename(worktree_path)

        try:
            # Remove the worktree
            subprocess.run(
                ["git", "worktree", "remove", worktree_path],
                check=True
            )
            
            # Delete the branch
            subprocess.run(
                ["git", "branch", "-D", branch_name],
                check=True
            )
            
        except subprocess.CalledProcessError as e:
            # Fallback to direct deletion if git commands fail
            shutil.rmtree(worktree_path, ignore_errors=True)

    def list_worktrees(self) -> List[str]:
        """
        List all active worktrees.
        
        Returns:
            List of worktree paths
        """
        worktrees = []
        
        if os.path.exists(self.base_path):
            for item in os.listdir(self.base_path):
                item_path = os.path.join(self.base_path, item)
                if os.path.isdir(item_path):
                    worktrees.append(item_path)
        
        return worktrees

    def cleanup_all(self) -> None:
        """Remove all worktrees."""
        for worktree_path in self.list_worktrees():
            self.remove_worktree(worktree_path)


# Global worktree manager instance
worktree_manager = WorktreeManager()
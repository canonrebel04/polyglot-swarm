"""
Role registry for managing available agent roles.
"""

from typing import Dict, Optional
from dataclasses import dataclass
import yaml
import os


@dataclass
class RoleDefinition:
    """Definition of an agent role."""
    role: str
    identity: str
    mission: str
    allowed_actions: list[str]
    forbidden_actions: list[str]
    handoff_to: list[str]


class RoleRegistry:
    """Registry for managing agent roles and their contracts."""

    def __init__(self, contracts_dir: str = "src/roles/contracts"):
        self.contracts_dir = contracts_dir
        self._roles: Dict[str, RoleDefinition] = {}
        self._load_contracts()

    def _load_contracts(self) -> None:
        """Load role contracts from YAML files."""
        if not os.path.exists(self.contracts_dir):
            os.makedirs(self.contracts_dir, exist_ok=True)
            return

        for filename in os.listdir(self.contracts_dir):
            if filename.endswith(".yaml"):
                filepath = os.path.join(self.contracts_dir, filename)
                with open(filepath, 'r') as f:
                    contract_data = yaml.safe_load(f)
                    
                role_def = RoleDefinition(
                    role=contract_data['role'],
                    identity=contract_data.get('identity', ''),
                    mission=contract_data.get('mission', ''),
                    allowed_actions=contract_data.get('may', []),
                    forbidden_actions=contract_data.get('may_not', []),
                    handoff_to=contract_data.get('handoff_to', [])
                )
                
                self._roles[role_def.role] = role_def

    def register_role(self, role_def: RoleDefinition) -> None:
        """Register a new role definition."""
        self._roles[role_def.role] = role_def

    def get_role(self, role_name: str) -> Optional[RoleDefinition]:
        """Get a role definition by name."""
        return self._roles.get(role_name)

    def list_roles(self) -> list[str]:
        """List all available role names."""
        return list(self._roles.keys())

    def has_role(self, role_name: str) -> bool:
        """Check if a role is available."""
        return role_name in self._roles

    def can_perform_action(self, role_name: str, action: str) -> bool:
        """Check if a role is allowed to perform an action."""
        role_def = self.get_role(role_name)
        if not role_def:
            return False
        
        # Check if action is explicitly allowed
        if action in role_def.allowed_actions:
            return True
        
        # Check if action is explicitly forbidden
        if action in role_def.forbidden_actions:
            return False
        
        # Default to False for safety
        return False


# Global registry instance
role_registry = RoleRegistry()
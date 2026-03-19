"""
Test role system components.
"""

import pytest
import os
import tempfile
import yaml
from src.roles.registry import RoleRegistry, RoleDefinition


def test_role_definition():
    """Test RoleDefinition dataclass."""
    role_def = RoleDefinition(
        role="test-role",
        identity="test identity",
        mission="test mission",
        allowed_actions=["action1", "action2"],
        forbidden_actions=["action3"],
        handoff_to=["next-role"]
    )
    
    assert role_def.role == "test-role"
    assert role_def.identity == "test identity"
    assert role_def.mission == "test mission"
    assert role_def.allowed_actions == ["action1", "action2"]
    assert role_def.forbidden_actions == ["action3"]
    assert role_def.handoff_to == ["next-role"]


def test_role_registry_empty():
    """Test RoleRegistry with no contracts."""
    with tempfile.TemporaryDirectory() as temp_dir:
        registry = RoleRegistry(contracts_dir=temp_dir)
        
        assert registry.list_roles() == []
        assert registry.has_role("test") == False
        assert registry.get_role("test") is None


def test_role_registry_with_contracts():
    """Test RoleRegistry with contract files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test contract file
        contract_file = os.path.join(temp_dir, "test.yaml")
        contract_data = {
            'role': 'test-role',
            'identity': 'test identity',
            'mission': 'test mission',
            'may': ['action1', 'action2'],
            'may_not': ['action3'],
            'handoff_to': ['next-role']
        }
        
        with open(contract_file, 'w') as f:
            yaml.dump(contract_data, f)
        
        # Create registry and test
        registry = RoleRegistry(contracts_dir=temp_dir)
        
        assert registry.list_roles() == ['test-role']
        assert registry.has_role('test-role') == True
        
        role_def = registry.get_role('test-role')
        assert role_def is not None
        assert role_def.role == 'test-role'
        assert role_def.identity == 'test identity'
        assert role_def.mission == 'test mission'
        assert role_def.allowed_actions == ['action1', 'action2']
        assert role_def.forbidden_actions == ['action3']
        assert role_def.handoff_to == ['next-role']


def test_role_registry_permissions():
    """Test role permission checking."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test contract file
        contract_file = os.path.join(temp_dir, "test.yaml")
        contract_data = {
            'role': 'test-role',
            'may': ['allowed_action'],
            'may_not': ['forbidden_action']
        }
        
        with open(contract_file, 'w') as f:
            yaml.dump(contract_data, f)
        
        registry = RoleRegistry(contracts_dir=temp_dir)
        
        # Test allowed action
        assert registry.can_perform_action('test-role', 'allowed_action') == True
        
        # Test forbidden action
        assert registry.can_perform_action('test-role', 'forbidden_action') == False
        
        # Test undefined action (should be False by default for safety)
        assert registry.can_perform_action('test-role', 'undefined_action') == False
        
        # Test non-existent role
        assert registry.can_perform_action('non-existent', 'any_action') == False


def test_role_registry_global():
    """Test global role registry instance."""
    from src.roles.registry import role_registry
    
    assert hasattr(role_registry, 'register_role')
    assert hasattr(role_registry, 'get_role')
    assert hasattr(role_registry, 'list_roles')
    assert hasattr(role_registry, 'has_role')
    assert hasattr(role_registry, 'can_perform_action')
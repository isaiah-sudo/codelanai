"""
Environment and scope management for CodeLan.
"""

from typing import Dict, Any, Optional

class Environment:
    def __init__(self, parent: Optional['Environment'] = None):
        self.values: Dict[str, Any] = {}
        self.parent = parent

    def define(self, name: str, value: Any):
        self.values[name] = value

    def assign(self, name: str, value: Any) -> bool:
        if name in self.values:
            self.values[name] = value
            return True
        if self.parent is not None:
            return self.parent.assign(name, value)
        # If not found anywhere, define in current scope (friendly for beginners)
        self.values[name] = value
        return True

    def get(self, name: str) -> Any:
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise NameError(f"Undefined variable '{name}'")

    def has(self, name: str) -> bool:
        if name in self.values:
            return True
        if self.parent is not None:
            return self.parent.has(name)
        return False

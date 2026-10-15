"""
Abstract Syntax Tree nodes for CodeLan.
"""

from dataclasses import dataclass
from typing import Any, List, Optional, Dict

class ASTNode:
    line: int = 0
    column: int = 0

# Literals and basic expressions
@dataclass
class NumberLiteral(ASTNode):
    value: float | int

@dataclass
class StringLiteral(ASTNode):
    value: str

@dataclass
class BooleanLiteral(ASTNode):
    value: bool

@dataclass
class NullLiteral(ASTNode):
    pass

@dataclass
class Identifier(ASTNode):
    name: str

@dataclass
class ListLiteral(ASTNode):
    elements: List[Any]

@dataclass
class DictLiteral(ASTNode):
    pairs: List[tuple[Any, Any]]

# Expressions
@dataclass
class BinaryOp(ASTNode):
    left: Any
    op: str
    right: Any

@dataclass
class UnaryOp(ASTNode):
    op: str
    operand: Any

@dataclass
class Assignment(ASTNode):
    target: Any  # Identifier, MemberAccess, or IndexAccess
    value: Any
    op: str = "="  # =, +=, -=, *=, /=

@dataclass
class FunctionCall(ASTNode):
    callee: Any
    arguments: List[Any]

@dataclass
class MemberAccess(ASTNode):
    object: Any
    member: str

@dataclass
class IndexAccess(ASTNode):
    object: Any
    index: Any

# Statements
@dataclass
class ExpressionStatement(ASTNode):
    expression: Any

@dataclass
class VarDeclaration(ASTNode):
    name: str
    initializer: Any

@dataclass
class BlockStatement(ASTNode):
    statements: List[Any]

@dataclass
class IfStatement(ASTNode):
    condition: Any
    then_branch: Any
    else_branch: Optional[Any] = None

@dataclass
class WhileStatement(ASTNode):
    condition: Any
    body: Any

@dataclass
class ForInStatement(ASTNode):
    variable: str
    iterable: Any
    body: Any

@dataclass
class ForCStyleStatement(ASTNode):
    init: Optional[Any]
    condition: Optional[Any]
    update: Optional[Any]
    body: Any

@dataclass
class RepeatStatement(ASTNode):
    count: Any
    body: Any

@dataclass
class FunctionDeclaration(ASTNode):
    name: str
    parameters: List[str]
    body: BlockStatement

@dataclass
class ReturnStatement(ASTNode):
    value: Optional[Any] = None

@dataclass
class BreakStatement(ASTNode):
    pass

@dataclass
class ContinueStatement(ASTNode):
    pass

# Game lifecycle hooks
@dataclass
class GameHook(ASTNode):
    hook_type: str  # "setup", "update", "draw"
    body: BlockStatement

@dataclass
class EventHandler(ASTNode):
    event_type: str  # "key_down", "key_up", "mouse_down", "mouse_up"
    param: Optional[str]
    body: BlockStatement

@dataclass
class Program(ASTNode):
    statements: List[Any]

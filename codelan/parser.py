"""
Parser for CodeLan.
Transforms a list of tokens into an Abstract Syntax Tree (AST).
"""

from typing import List, Optional, Any
from .lexer import Token, TokenType
from .ast_nodes import (
    ASTNode, NumberLiteral, StringLiteral, BooleanLiteral, NullLiteral,
    Identifier, ListLiteral, DictLiteral, BinaryOp, UnaryOp, Assignment,
    FunctionCall, MemberAccess, IndexAccess, ExpressionStatement,
    VarDeclaration, BlockStatement, IfStatement, WhileStatement,
    ForInStatement, ForCStyleStatement, RepeatStatement, FunctionDeclaration,
    ReturnStatement, BreakStatement, ContinueStatement, GameHook,
    EventHandler, Program
)

class ParserError(Exception):
    def __init__(self, message: str, token: Token):
        super().__init__(f"Parse Error at {token.line}:{token.column}: {message}")
        self.token = token
        self.line = token.line
        self.column = token.column

class Parser:
    def __init__(self, tokens: List[Token], filename: str = "<stdin>"):
        self.tokens = tokens
        self.pos = 0
        self.filename = filename

    def current_token(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return self.tokens[-1]

    def peek(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return self.tokens[-1]

    def check(self, token_type: TokenType) -> bool:
        return self.current_token().type == token_type

    def advance(self) -> Token:
        token = self.current_token()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token

    def match(self, *token_types: TokenType) -> bool:
        for t in token_types:
            if self.check(t):
                self.advance()
                return True
        return False

    def consume(self, token_type: TokenType, message: str) -> Token:
        if self.check(token_type):
            return self.advance()
        tok = self.current_token()
        raise ParserError(f"{message} (got '{tok.value}' [{tok.type.name}])", tok)

    def optional_semicolon(self):
        while self.check(TokenType.SEMICOLON):
            self.advance()

    def parse(self) -> Program:
        statements = []
        while not self.check(TokenType.EOF):
            stmt = self.statement()
            if stmt is not None:
                statements.append(stmt)
            self.optional_semicolon()
        prog = Program(statements=statements)
        if self.tokens:
            prog.line = self.tokens[0].line
            prog.column = self.tokens[0].column
        return prog

    def statement(self) -> ASTNode:
        tok = self.current_token()

        # Game hooks: setup, update, draw
        if tok.type in (TokenType.SETUP, TokenType.UPDATE, TokenType.DRAW):
            hook_type = self.advance().value
            body = self.block_statement()
            node = GameHook(hook_type=hook_type, body=body)
            node.line = tok.line
            node.column = tok.column
            return node

        # Event handlers: on key_down(...) { ... }
        if tok.type == TokenType.ON:
            self.advance()
            event_name_tok = self.consume(TokenType.IDENTIFIER, "Expected event name after 'on' (e.g. key_down, mouse_down)")
            event_type = event_name_tok.value
            param = None
            if self.match(TokenType.LPAREN):
                if self.check(TokenType.IDENTIFIER):
                    param = self.advance().value
                self.consume(TokenType.RPAREN, "Expected ')' after event parameter")
            body = self.block_statement()
            node = EventHandler(event_type=event_type, param=param, body=body)
            node.line = tok.line
            node.column = tok.column
            return node

        # Function declaration
        if tok.type == TokenType.FN:
            return self.function_declaration()

        # Variable declaration: let / var
        if tok.type in (TokenType.LET, TokenType.VAR):
            return self.var_declaration()

        # If statement
        if tok.type == TokenType.IF:
            return self.if_statement()

        # While statement
        if tok.type == TokenType.WHILE:
            return self.while_statement()

        # For statement
        if tok.type == TokenType.FOR:
            return self.for_statement()

        # Repeat statement: repeat (n) { ... }
        if tok.type == TokenType.REPEAT:
            return self.repeat_statement()

        # Return statement
        if tok.type == TokenType.RETURN:
            self.advance()
            val = None
            if not self.check(TokenType.SEMICOLON) and not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
                val = self.expression()
            self.optional_semicolon()
            node = ReturnStatement(value=val)
            node.line = tok.line
            node.column = tok.column
            return node

        # Break
        if tok.type == TokenType.BREAK:
            self.advance()
            self.optional_semicolon()
            node = BreakStatement()
            node.line = tok.line
            node.column = tok.column
            return node

        # Continue
        if tok.type == TokenType.CONTINUE:
            self.advance()
            self.optional_semicolon()
            node = ContinueStatement()
            node.line = tok.line
            node.column = tok.column
            return node

        # Block
        if tok.type == TokenType.LBRACE:
            return self.block_statement()

        # Otherwise expression statement
        expr = self.expression()
        self.optional_semicolon()
        node = ExpressionStatement(expression=expr)
        node.line = tok.line
        node.column = tok.column
        return node

    def block_statement(self) -> BlockStatement:
        start_tok = self.consume(TokenType.LBRACE, "Expected '{'")
        stmts = []
        while not self.check(TokenType.RBRACE) and not self.check(TokenType.EOF):
            s = self.statement()
            if s is not None:
                stmts.append(s)
            self.optional_semicolon()
        self.consume(TokenType.RBRACE, "Expected '}' at end of block")
        node = BlockStatement(statements=stmts)
        node.line = start_tok.line
        node.column = start_tok.column
        return node

    def function_declaration(self) -> FunctionDeclaration:
        fn_tok = self.advance()
        name_tok = self.consume(TokenType.IDENTIFIER, "Expected function name")
        self.consume(TokenType.LPAREN, "Expected '(' after function name")
        params = []
        if not self.check(TokenType.RPAREN):
            while True:
                p_tok = self.consume(TokenType.IDENTIFIER, "Expected parameter name")
                params.append(p_tok.value)
                if not self.match(TokenType.COMMA):
                    break
        self.consume(TokenType.RPAREN, "Expected ')' after parameters")
        body = self.block_statement()
        node = FunctionDeclaration(name=name_tok.value, parameters=params, body=body)
        node.line = fn_tok.line
        node.column = fn_tok.column
        return node

    def var_declaration(self) -> VarDeclaration:
        let_tok = self.advance()
        name_tok = self.consume(TokenType.IDENTIFIER, "Expected variable name")
        initializer = None
        if self.match(TokenType.ASSIGN):
            initializer = self.expression()
        self.optional_semicolon()
        node = VarDeclaration(name=name_tok.value, initializer=initializer)
        node.line = let_tok.line
        node.column = let_tok.column
        return node

    def if_statement(self) -> IfStatement:
        if_tok = self.advance()
        has_paren = self.match(TokenType.LPAREN)
        cond = self.expression()
        if has_paren:
            self.consume(TokenType.RPAREN, "Expected ')' after if condition")

        then_branch = self.block_statement() if self.check(TokenType.LBRACE) else self.statement()
        else_branch = None

        if self.match(TokenType.ELSE):
            if self.check(TokenType.IF):
                else_branch = self.if_statement()
            elif self.check(TokenType.LBRACE):
                else_branch = self.block_statement()
            else:
                else_branch = self.statement()

        node = IfStatement(condition=cond, then_branch=then_branch, else_branch=else_branch)
        node.line = if_tok.line
        node.column = if_tok.column
        return node

    def while_statement(self) -> WhileStatement:
        while_tok = self.advance()
        has_paren = self.match(TokenType.LPAREN)
        cond = self.expression()
        if has_paren:
            self.consume(TokenType.RPAREN, "Expected ')' after while condition")

        body = self.block_statement() if self.check(TokenType.LBRACE) else self.statement()
        node = WhileStatement(condition=cond, body=body)
        node.line = while_tok.line
        node.column = while_tok.column
        return node

    def for_statement(self) -> ASTNode:
        for_tok = self.advance()
        has_paren = self.match(TokenType.LPAREN)

        # Check if C-style: for (let i = 0; i < 10; i += 1)
        # or for-in: for (item in list) or for item in list
        if self.check(TokenType.IDENTIFIER) and self.peek(1).type == TokenType.IN:
            var_name = self.advance().value
            self.advance()  # consume 'in'
            iterable = self.expression()
            if has_paren:
                self.consume(TokenType.RPAREN, "Expected ')' after for-in expression")
            body = self.block_statement() if self.check(TokenType.LBRACE) else self.statement()
            node = ForInStatement(variable=var_name, iterable=iterable, body=body)
            node.line = for_tok.line
            node.column = for_tok.column
            return node

        # If C-style:
        init = None
        if self.match(TokenType.LET, TokenType.VAR):
            name_tok = self.consume(TokenType.IDENTIFIER, "Expected variable name in for loop")
            self.consume(TokenType.ASSIGN, "Expected '=' in for variable init")
            val = self.expression()
            init = VarDeclaration(name=name_tok.value, initializer=val)
        elif not self.check(TokenType.SEMICOLON):
            init = self.expression()

        self.consume(TokenType.SEMICOLON, "Expected ';' after for initialization")

        condition = None
        if not self.check(TokenType.SEMICOLON):
            condition = self.expression()
        self.consume(TokenType.SEMICOLON, "Expected ';' after for condition")

        update = None
        if not self.check(TokenType.RPAREN):
            update = self.expression()

        if has_paren:
            self.consume(TokenType.RPAREN, "Expected ')' after for clauses")

        body = self.block_statement() if self.check(TokenType.LBRACE) else self.statement()
        node = ForCStyleStatement(init=init, condition=condition, update=update, body=body)
        node.line = for_tok.line
        node.column = for_tok.column
        return node

    def repeat_statement(self) -> RepeatStatement:
        rep_tok = self.advance()
        has_paren = self.match(TokenType.LPAREN)
        count_expr = self.expression()
        if has_paren:
            self.consume(TokenType.RPAREN, "Expected ')' after repeat count")
        body = self.block_statement() if self.check(TokenType.LBRACE) else self.statement()
        node = RepeatStatement(count=count_expr, body=body)
        node.line = rep_tok.line
        node.column = rep_tok.column
        return node

    # Expression parsing with Pratt / Precedence climbing
    def expression(self) -> ASTNode:
        return self.assignment()

    def assignment(self) -> ASTNode:
        expr = self.logical_or()

        if self.check(TokenType.ASSIGN) or self.check(TokenType.PLUS_ASSIGN) or \
           self.check(TokenType.MINUS_ASSIGN) or self.check(TokenType.STAR_ASSIGN) or \
           self.check(TokenType.SLASH_ASSIGN):
            op_tok = self.advance()
            val = self.assignment()

            # Target must be valid: Identifier, MemberAccess, IndexAccess
            if isinstance(expr, (Identifier, MemberAccess, IndexAccess)):
                node = Assignment(target=expr, value=val, op=op_tok.value)
                node.line = op_tok.line
                node.column = op_tok.column
                return node
            raise ParserError("Invalid assignment target", op_tok)

        return expr

    def logical_or(self) -> ASTNode:
        expr = self.logical_and()
        while self.check(TokenType.OR) or self.check(TokenType.PIPE_PIPE):
            op_tok = self.advance()
            right = self.logical_and()
            node = BinaryOp(left=expr, op="or", right=right)
            node.line = op_tok.line
            node.column = op_tok.column
            expr = node
        return expr

    def logical_and(self) -> ASTNode:
        expr = self.equality()
        while self.check(TokenType.AND) or self.check(TokenType.AMP_AMP):
            op_tok = self.advance()
            right = self.equality()
            node = BinaryOp(left=expr, op="and", right=right)
            node.line = op_tok.line
            node.column = op_tok.column
            expr = node
        return expr

    def equality(self) -> ASTNode:
        expr = self.comparison()
        while self.check(TokenType.EQUAL_EQUAL) or self.check(TokenType.BANG_EQUAL):
            op_tok = self.advance()
            right = self.comparison()
            node = BinaryOp(left=expr, op=op_tok.value, right=right)
            node.line = op_tok.line
            node.column = op_tok.column
            expr = node
        return expr

    def comparison(self) -> ASTNode:
        expr = self.term()
        while self.check(TokenType.LESS) or self.check(TokenType.LESS_EQUAL) or \
              self.check(TokenType.GREATER) or self.check(TokenType.GREATER_EQUAL):
            op_tok = self.advance()
            right = self.term()
            node = BinaryOp(left=expr, op=op_tok.value, right=right)
            node.line = op_tok.line
            node.column = op_tok.column
            expr = node
        return expr

    def term(self) -> ASTNode:
        expr = self.factor()
        while self.check(TokenType.PLUS) or self.check(TokenType.MINUS):
            op_tok = self.advance()
            right = self.factor()
            node = BinaryOp(left=expr, op=op_tok.value, right=right)
            node.line = op_tok.line
            node.column = op_tok.column
            expr = node
        return expr

    def factor(self) -> ASTNode:
        expr = self.unary()
        while self.check(TokenType.STAR) or self.check(TokenType.SLASH) or self.check(TokenType.PERCENT):
            op_tok = self.advance()
            right = self.unary()
            node = BinaryOp(left=expr, op=op_tok.value, right=right)
            node.line = op_tok.line
            node.column = op_tok.column
            expr = node
        return expr

    def unary(self) -> ASTNode:
        if self.check(TokenType.MINUS) or self.check(TokenType.BANG) or self.check(TokenType.NOT):
            op_tok = self.advance()
            op_str = "not" if op_tok.type in (TokenType.NOT, TokenType.BANG) else op_tok.value
            operand = self.unary()
            node = UnaryOp(op=op_str, operand=operand)
            node.line = op_tok.line
            node.column = op_tok.column
            return node
        return self.call_or_member()

    def call_or_member(self) -> ASTNode:
        expr = self.primary()

        while True:
            # Function call: expr(arg1, arg2)
            if self.match(TokenType.LPAREN):
                args = []
                if not self.check(TokenType.RPAREN):
                    while True:
                        args.append(self.expression())
                        if not self.match(TokenType.COMMA):
                            break
                rparen = self.consume(TokenType.RPAREN, "Expected ')' after arguments")
                node = FunctionCall(callee=expr, arguments=args)
                node.line = expr.line
                node.column = expr.column
                expr = node
            # Member access: expr.prop
            elif self.match(TokenType.DOT):
                member_tok = self.consume(TokenType.IDENTIFIER, "Expected property name after '.'")
                node = MemberAccess(object=expr, member=member_tok.value)
                node.line = member_tok.line
                node.column = member_tok.column
                expr = node
            # Index access: expr[idx]
            elif self.match(TokenType.LBRACKET):
                idx = self.expression()
                rbrack = self.consume(TokenType.RBRACKET, "Expected ']' after index")
                node = IndexAccess(object=expr, index=idx)
                node.line = expr.line
                node.column = expr.column
                expr = node
            else:
                break

        return expr

    def primary(self) -> ASTNode:
        tok = self.current_token()

        if self.match(TokenType.NUMBER):
            node = NumberLiteral(value=tok.value)
            node.line = tok.line
            node.column = tok.column
            return node

        if self.match(TokenType.STRING):
            node = StringLiteral(value=tok.value)
            node.line = tok.line
            node.column = tok.column
            return node

        if self.match(TokenType.TRUE):
            node = BooleanLiteral(value=True)
            node.line = tok.line
            node.column = tok.column
            return node

        if self.match(TokenType.FALSE):
            node = BooleanLiteral(value=False)
            node.line = tok.line
            node.column = tok.column
            return node

        if self.match(TokenType.NULL):
            node = NullLiteral()
            node.line = tok.line
            node.column = tok.column
            return node

        if self.match(TokenType.IDENTIFIER):
            node = Identifier(name=tok.value)
            node.line = tok.line
            node.column = tok.column
            return node

        # Grouping (expr)
        if self.match(TokenType.LPAREN):
            expr = self.expression()
            self.consume(TokenType.RPAREN, "Expected ')' after expression")
            return expr

        # List literal [elem1, elem2, ...]
        if self.match(TokenType.LBRACKET):
            elements = []
            if not self.check(TokenType.RBRACKET):
                while True:
                    elements.append(self.expression())
                    if not self.match(TokenType.COMMA):
                        break
            self.consume(TokenType.RBRACKET, "Expected ']' after list elements")
            node = ListLiteral(elements=elements)
            node.line = tok.line
            node.column = tok.column
            return node

        # Dict literal { key: val, ... }
        if self.match(TokenType.LBRACE):
            pairs = []
            if not self.check(TokenType.RBRACE):
                while True:
                    key_tok = self.current_token()
                    if key_tok.type in (TokenType.IDENTIFIER, TokenType.STRING):
                        self.advance()
                        key = key_tok.value
                    else:
                        raise ParserError("Expected identifier or string key in dictionary", key_tok)
                    self.consume(TokenType.COLON, "Expected ':' after dictionary key")
                    val = self.expression()
                    pairs.append((key, val))
                    if not self.match(TokenType.COMMA):
                        break
            self.consume(TokenType.RBRACE, "Expected '}' after dictionary pairs")
            node = DictLiteral(pairs=pairs)
            node.line = tok.line
            node.column = tok.column
            return node

        raise ParserError(f"Unexpected token: '{tok.value}' ({tok.type.name})", tok)

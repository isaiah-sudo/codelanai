"""
Lexer / Tokenizer for CodeLan.
Converts source code text into a stream of tokens.
"""

from enum import Enum, auto
from typing import List, Optional, Any

class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    IDENTIFIER = auto()

    # Keywords
    LET = auto()
    VAR = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    REPEAT = auto()
    FN = auto()
    RETURN = auto()
    BREAK = auto()
    CONTINUE = auto()
    TRUE = auto()
    FALSE = auto()
    NULL = auto()
    AND = auto()
    OR = auto()
    NOT = auto()

    # Game lifecycle keywords
    SETUP = auto()
    UPDATE = auto()
    DRAW = auto()
    ON = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()

    ASSIGN = auto()
    PLUS_ASSIGN = auto()
    MINUS_ASSIGN = auto()
    STAR_ASSIGN = auto()
    SLASH_ASSIGN = auto()

    EQUAL_EQUAL = auto()
    BANG_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()

    AMP_AMP = auto()
    PIPE_PIPE = auto()
    BANG = auto()

    # Punctuation
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    COLON = auto()
    SEMICOLON = auto()
    DOT = auto()

    EOF = auto()

class Token:
    def __init__(self, token_type: TokenType, value: Any, line: int, column: int):
        self.type = token_type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {repr(self.value)}, L{self.line}:C{self.column})"

KEYWORDS = {
    "let": TokenType.LET,
    "var": TokenType.VAR,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "repeat": TokenType.REPEAT,
    "fn": TokenType.FN,
    "fun": TokenType.FN,
    "function": TokenType.FN,
    "def": TokenType.FN,
    "return": TokenType.RETURN,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "null": TokenType.NULL,
    "nil": TokenType.NULL,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "setup": TokenType.SETUP,
    "update": TokenType.UPDATE,
    "draw": TokenType.DRAW,
    "on": TokenType.ON,
}

class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"Lexer Error at {line}:{column}: {message}")
        self.line = line
        self.column = column

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.length = len(source)
        self.pos = 0
        self.line = 1
        self.column = 1

    def peek(self, offset: int = 0) -> Optional[str]:
        idx = self.pos + offset
        if idx < self.length:
            return self.source[idx]
        return None

    def advance(self) -> Optional[str]:
        if self.pos >= self.length:
            return None
        char = self.source[self.pos]
        self.pos += 1
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return char

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        while self.pos < self.length:
            char = self.peek()

            # Whitespace
            if char in ' \t\r\n':
                self.advance()
                continue

            # Comments
            if char == '/' and self.peek(1) == '/':
                self.advance()
                self.advance()
                while self.pos < self.length and self.peek() != '\n':
                    self.advance()
                continue

            if char == '#':
                self.advance()
                while self.pos < self.length and self.peek() != '\n':
                    self.advance()
                continue

            if char == '/' and self.peek(1) == '*':
                start_line = self.line
                start_col = self.column
                self.advance()
                self.advance()
                while self.pos < self.length:
                    if self.peek() == '*' and self.peek(1) == '/':
                        self.advance()
                        self.advance()
                        break
                    self.advance()
                else:
                    raise LexerError("Unterminated block comment", start_line, start_col)
                continue

            start_line = self.line
            start_col = self.column

            # Numbers
            if char.isdigit():
                num_str = ""
                has_dot = False
                while self.pos < self.length and (self.peek().isdigit() or (self.peek() == '.' and not has_dot and self.peek(1) is not None and self.peek(1).isdigit())):
                    if self.peek() == '.':
                        has_dot = True
                    num_str += self.advance()
                value = float(num_str) if has_dot else int(num_str)
                tokens.append(Token(TokenType.NUMBER, value, start_line, start_col))
                continue

            # Strings
            if char in ('"', "'"):
                quote_type = self.advance()
                string_chars = []
                while self.pos < self.length and self.peek() != quote_type:
                    c = self.advance()
                    if c == '\\':
                        esc = self.advance()
                        if esc == 'n':
                            string_chars.append('\n')
                        elif esc == 't':
                            string_chars.append('\t')
                        elif esc == 'r':
                            string_chars.append('\r')
                        elif esc == '\\':
                            string_chars.append('\\')
                        elif esc == quote_type:
                            string_chars.append(quote_type)
                        else:
                            string_chars.append(esc)
                    else:
                        string_chars.append(c)
                if self.pos >= self.length or self.peek() != quote_type:
                    raise LexerError("Unterminated string literal", start_line, start_col)
                self.advance()  # consume closing quote
                tokens.append(Token(TokenType.STRING, "".join(string_chars), start_line, start_col))
                continue

            # Identifiers and keywords
            if char.isalpha() or char == '_':
                ident = ""
                while self.pos < self.length and (self.peek().isalnum() or self.peek() == '_'):
                    ident += self.advance()
                token_type = KEYWORDS.get(ident, TokenType.IDENTIFIER)
                tokens.append(Token(token_type, ident, start_line, start_col))
                continue

            # Two-character operators
            two_chars = self.source[self.pos:self.pos + 2]
            if two_chars == '==':
                self.advance(); self.advance()
                tokens.append(Token(TokenType.EQUAL_EQUAL, '==', start_line, start_col))
                continue
            if two_chars == '!=':
                self.advance(); self.advance()
                tokens.append(Token(TokenType.BANG_EQUAL, '!=', start_line, start_col))
                continue
            if two_chars == '<=':
                self.advance(); self.advance()
                tokens.append(Token(TokenType.LESS_EQUAL, '<=', start_line, start_col))
                continue
            if two_chars == '>=':
                self.advance(); self.advance()
                tokens.append(Token(TokenType.GREATER_EQUAL, '>=', start_line, start_col))
                continue
            if two_chars == '+=':
                self.advance(); self.advance()
                tokens.append(Token(TokenType.PLUS_ASSIGN, '+=', start_line, start_col))
                continue
            if two_chars == '-=':
                self.advance(); self.advance()
                tokens.append(Token(TokenType.MINUS_ASSIGN, '-=', start_line, start_col))
                continue
            if two_chars == '*=':
                self.advance(); self.advance()
                tokens.append(Token(TokenType.STAR_ASSIGN, '*=', start_line, start_col))
                continue
            if two_chars == '/=':
                self.advance(); self.advance()
                tokens.append(Token(TokenType.SLASH_ASSIGN, '/=', start_line, start_col))
                continue
            if two_chars == '&&':
                self.advance(); self.advance()
                tokens.append(Token(TokenType.AMP_AMP, '&&', start_line, start_col))
                continue
            if two_chars == '||':
                self.advance(); self.advance()
                tokens.append(Token(TokenType.PIPE_PIPE, '||', start_line, start_col))
                continue

            # Single character operators and punctuation
            c = self.advance()
            simple_tokens = {
                '+': TokenType.PLUS,
                '-': TokenType.MINUS,
                '*': TokenType.STAR,
                '/': TokenType.SLASH,
                '%': TokenType.PERCENT,
                '=': TokenType.ASSIGN,
                '<': TokenType.LESS,
                '>': TokenType.GREATER,
                '!': TokenType.BANG,
                '(': TokenType.LPAREN,
                ')': TokenType.RPAREN,
                '{': TokenType.LBRACE,
                '}': TokenType.RBRACE,
                '[': TokenType.LBRACKET,
                ']': TokenType.RBRACKET,
                ',': TokenType.COMMA,
                ':': TokenType.COLON,
                ';': TokenType.SEMICOLON,
                '.': TokenType.DOT,
            }

            if c in simple_tokens:
                tokens.append(Token(simple_tokens[c], c, start_line, start_col))
            else:
                raise LexerError(f"Unexpected character: {repr(c)}", start_line, start_col)

        tokens.append(Token(TokenType.EOF, None, self.line, self.column))
        return tokens

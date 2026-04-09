"""LeekScript tokenizer.

Scans .leek source into a stream of typed tokens.
Subset scoped to v14 AI: 14 keywords, 20 operators, literals, identifiers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class TokenType(Enum):
    # Literals
    NUMBER = auto()
    STRING = auto()
    TRUE = auto()
    FALSE = auto()
    NULL = auto()
    IDENTIFIER = auto()

    # Keywords
    VAR = auto()
    GLOBAL = auto()
    FUNCTION = auto()
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    RETURN = auto()
    BREAK = auto()
    CONTINUE = auto()
    NOT_KEYWORD = auto()  # 'not' as keyword (LeekScript supports both ! and not)

    # OOP Keywords (v2+)
    CLASS = auto()
    EXTENDS = auto()
    NEW = auto()
    THIS = auto()
    SUPER = auto()
    CONSTRUCTOR = auto()
    STATIC = auto()
    INSTANCEOF = auto()
    PRIVATE = auto()
    PROTECTED = auto()
    PUBLIC = auto()
    FINAL = auto()

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
    INCREMENT = auto()
    DECREMENT = auto()
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    POWER = auto()
    POWER_ASSIGN = auto()
    STRICT_EQ = auto()
    STRICT_NEQ = auto()
    PERCENT_ASSIGN = auto()
    INTDIV = auto()        # \ (integer division)
    INTDIV_ASSIGN = auto() # \=
    QUESTION = auto()
    COLON = auto()

    # Bitwise operators
    BITWISE_OR = auto()   # |
    BITWISE_AND = auto()  # &
    BITWISE_XOR = auto()  # ^
    BITWISE_NOT = auto()  # ~

    # Arrow operators
    ARROW = auto()       # ->
    FAT_ARROW = auto()   # =>

    # Keyword-based operators
    XOR = auto()
    IS = auto()
    AT = auto()  # @ reference operator

    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    COMMA = auto()
    SEMICOLON = auto()
    DOT = auto()

    EOF = auto()


KEYWORDS = {
    "var": TokenType.VAR,
    "global": TokenType.GLOBAL,
    "function": TokenType.FUNCTION,
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "return": TokenType.RETURN,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "null": TokenType.NULL,
    "not": TokenType.NOT_KEYWORD,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "xor": TokenType.XOR,
    "is": TokenType.IS,
    # OOP keywords (v2+)
    "class": TokenType.CLASS,
    "extends": TokenType.EXTENDS,
    "new": TokenType.NEW,
    "this": TokenType.THIS,
    "super": TokenType.SUPER,
    "constructor": TokenType.CONSTRUCTOR,
    "static": TokenType.STATIC,
    "instanceof": TokenType.INSTANCEOF,
    "private": TokenType.PRIVATE,
    "protected": TokenType.PROTECTED,
    "public": TokenType.PUBLIC,
    "final": TokenType.FINAL,
}


@dataclass
class Token:
    type: TokenType
    value: Any
    line: int
    col: int

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:{self.col})"


class LexError(Exception):
    def __init__(self, msg: str, line: int, col: int):
        super().__init__(f"Lex error at L{line}:{col}: {msg}")
        self.line = line
        self.col = col


def tokenize(source: str) -> list[Token]:
    """Tokenize LeekScript source into a list of tokens."""
    tokens: list[Token] = []
    i = 0
    line = 1
    col = 1
    length = len(source)

    while i < length:
        ch = source[i]

        # Whitespace
        if ch in " \t\r":
            i += 1
            col += 1
            continue

        # Newline
        if ch == "\n":
            i += 1
            line += 1
            col = 1
            continue

        # Line comment
        if ch == "/" and i + 1 < length and source[i + 1] == "/":
            i += 2
            while i < length and source[i] != "\n":
                i += 1
            continue

        # Block comment
        if ch == "/" and i + 1 < length and source[i + 1] == "*":
            start_line, start_col = line, col
            i += 2
            col += 2
            while i + 1 < length:
                if source[i] == "*" and source[i + 1] == "/":
                    i += 2
                    col += 2
                    break
                if source[i] == "\n":
                    line += 1
                    col = 1
                else:
                    col += 1
                i += 1
            else:
                raise LexError("Unterminated block comment", start_line, start_col)
            continue

        start_col = col

        # String literals (double or single quotes)
        if ch in ('"', "'"):
            quote = ch
            i += 1
            col += 1
            s = []
            while i < length and source[i] != quote:
                if source[i] == "\\":
                    i += 1
                    col += 1
                    if i < length:
                        esc = source[i]
                        if esc == "n":
                            s.append("\n")
                        elif esc == "t":
                            s.append("\t")
                        elif esc == "\\":
                            s.append("\\")
                        elif esc == quote:
                            s.append(quote)
                        else:
                            s.append(esc)
                elif source[i] == "\n":
                    line += 1
                    col = 0
                    s.append("\n")
                else:
                    s.append(source[i])
                i += 1
                col += 1
            if i >= length:
                raise LexError("Unterminated string", line, start_col)
            i += 1  # closing quote
            col += 1
            tokens.append(Token(TokenType.STRING, "".join(s), line, start_col))
            continue

        # Number literals
        if ch.isdigit() or (ch == "." and i + 1 < length and source[i + 1].isdigit()):
            num_start = i
            has_dot = False
            while i < length and (source[i].isdigit() or source[i] == "."):
                if source[i] == ".":
                    if has_dot:
                        break
                    # Check it's not .. (range operator, not used in v14 but safe)
                    if i + 1 < length and source[i + 1] == ".":
                        break
                    has_dot = True
                i += 1
            num_str = source[num_start:i]
            col += len(num_str)
            value = float(num_str) if has_dot else int(num_str)
            tokens.append(Token(TokenType.NUMBER, value, line, start_col))
            continue

        # Identifiers and keywords
        if ch.isalpha() or ch == "_":
            id_start = i
            while i < length and (source[i].isalnum() or source[i] == "_"):
                i += 1
            word = source[id_start:i]
            col += len(word)
            tt = KEYWORDS.get(word, TokenType.IDENTIFIER)
            if tt == TokenType.TRUE:
                tokens.append(Token(tt, True, line, start_col))
            elif tt == TokenType.FALSE:
                tokens.append(Token(tt, False, line, start_col))
            elif tt == TokenType.NULL:
                tokens.append(Token(tt, None, line, start_col))
            elif tt == TokenType.NOT_KEYWORD:
                tokens.append(Token(TokenType.NOT, "not", line, start_col))
            else:
                tokens.append(Token(tt, word, line, start_col))
            continue

        # Three-character operators (check BEFORE two-char)
        if i + 2 < length:
            three = source[i : i + 3]
            if three == "**=":
                tokens.append(Token(TokenType.POWER_ASSIGN, three, line, start_col))
                i += 3; col += 3; continue
            if three == "===":
                tokens.append(Token(TokenType.STRICT_EQ, three, line, start_col))
                i += 3; col += 3; continue
            if three == "!==":
                tokens.append(Token(TokenType.STRICT_NEQ, three, line, start_col))
                i += 3; col += 3; continue

        # Two-character operators (check BEFORE single-character)
        if i + 1 < length:
            two = source[i : i + 2]
            tt2 = {
                "++": TokenType.INCREMENT,
                "--": TokenType.DECREMENT,
                "+=": TokenType.PLUS_ASSIGN,
                "-=": TokenType.MINUS_ASSIGN,
                "*=": TokenType.STAR_ASSIGN,
                "/=": TokenType.SLASH_ASSIGN,
                "%=": TokenType.PERCENT_ASSIGN,
                "**": TokenType.POWER,
                "==": TokenType.EQ,
                "!=": TokenType.NEQ,
                "<=": TokenType.LTE,
                ">=": TokenType.GTE,
                "&&": TokenType.AND,
                "||": TokenType.OR,
                "->": TokenType.ARROW,
                "=>": TokenType.FAT_ARROW,
                "\\=": TokenType.INTDIV_ASSIGN,
            }.get(two)
            if tt2 is not None:
                tokens.append(Token(tt2, two, line, start_col))
                i += 2
                col += 2
                continue

        # Single-character operators and delimiters
        tt1 = {
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "/": TokenType.SLASH,
            "%": TokenType.PERCENT,
            "=": TokenType.ASSIGN,
            "<": TokenType.LT,
            ">": TokenType.GT,
            "!": TokenType.NOT,
            "?": TokenType.QUESTION,
            ":": TokenType.COLON,
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            "{": TokenType.LBRACE,
            "}": TokenType.RBRACE,
            "[": TokenType.LBRACKET,
            "]": TokenType.RBRACKET,
            ",": TokenType.COMMA,
            ";": TokenType.SEMICOLON,
            ".": TokenType.DOT,
            "@": TokenType.AT,
            "|": TokenType.BITWISE_OR,
            "&": TokenType.BITWISE_AND,
            "^": TokenType.BITWISE_XOR,
            "~": TokenType.BITWISE_NOT,
            "\\": TokenType.INTDIV,
        }.get(ch)

        if tt1 is not None:
            tokens.append(Token(tt1, ch, line, start_col))
            i += 1
            col += 1
            continue

        raise LexError(f"Unexpected character: {ch!r}", line, col)

    tokens.append(Token(TokenType.EOF, None, line, col))
    return tokens

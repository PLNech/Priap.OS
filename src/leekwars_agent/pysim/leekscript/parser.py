"""LeekScript recursive descent parser with Pratt precedence climbing.

Produces an AST from token stream. Two-pass: collect function declarations
first (hoisting), then parse bodies + main block.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .lexer import Token, TokenType


# ── AST Node Types ──────────────────────────────────────────────────────

# Statements
@dataclass
class Program:
    stmts: list


@dataclass
class FunctionDecl:
    name: str
    params: list[str]
    body: list
    line: int = 0


@dataclass
class VarDecl:
    name: str
    init: Any  # Expr | None
    is_global: bool


@dataclass
class Assignment:
    target: Any  # Expr
    op: str
    value: Any  # Expr


@dataclass
class IfStmt:
    condition: Any
    then_body: list
    else_body: list | None


@dataclass
class WhileStmt:
    condition: Any
    body: list


@dataclass
class ForIn:
    var_name: str
    iterable: Any
    body: list


@dataclass
class ForKeyValue:
    key_name: str
    val_name: str
    iterable: Any
    body: list


@dataclass
class ForClassic:
    init: Any  # VarDecl or Assignment or ExprStmt or None
    condition: Any  # Expr or None
    update: Any  # Expr or None (usually increment)
    body: list


@dataclass
class DoWhileStmt:
    condition: Any
    body: list


@dataclass
class ReturnStmt:
    value: Any  # Expr | None


@dataclass
class BreakStmt:
    pass


@dataclass
class ContinueStmt:
    pass


@dataclass
class ExprStmt:
    expr: Any


# Expressions
@dataclass
class BinaryOp:
    left: Any
    op: str
    right: Any


@dataclass
class UnaryOp:
    op: str
    operand: Any


@dataclass
class Ternary:
    condition: Any
    true_val: Any
    false_val: Any


@dataclass
class FunctionCall:
    callee: Any  # Identifier or expression
    args: list


@dataclass
class MethodCall:
    obj: Any
    method: str
    args: list


@dataclass
class Subscript:
    obj: Any
    index: Any


@dataclass
class PropertyAccess:
    obj: Any
    prop: str


@dataclass
class Identifier:
    name: str


@dataclass
class NumberLit:
    value: int | float


@dataclass
class StringLit:
    value: str


@dataclass
class BoolLit:
    value: bool


@dataclass
class NullLit:
    pass


@dataclass
class ArrayLit:
    elements: list


@dataclass
class MapLit:
    pairs: list  # list of (key_expr, value_expr) tuples


@dataclass
class Increment:
    target: Any
    prefix: bool
    op: str  # '++' or '--'


@dataclass
class AnonFunction:
    params: list[str]
    body: list


# ── Parser ──────────────────────────────────────────────────────────────

class ParseError(Exception):
    def __init__(self, msg: str, token: Token | None = None):
        loc = f" at L{token.line}:{token.col}" if token else ""
        super().__init__(f"Parse error{loc}: {msg}")
        self.token = token


# Operator precedence (Pratt) — lower number = lower precedence = binds looser
PRECEDENCE = {
    # Assignment (right-assoc)
    "=": 0, "+=": 0, "-=": 0, "*=": 0, "/=": 0, "%=": 0, "**=": 0,
    # Logical
    "||": 2,
    "xor": 2,
    "&&": 3,
    # Bitwise
    "|": 4, "^": 5, "&": 6,
    # Equality
    "==": 7, "!=": 7, "===": 7, "!==": 7, "is": 7, "is not": 7,
    # Relational + membership
    "in": 8, "<": 8, ">": 8, "<=": 8, ">=": 8,
    # Arithmetic
    "+": 10, "-": 10,
    "*": 11, "/": 11, "%": 11,
    "**": 12,
}

BINARY_OPS = {
    # Assignment
    TokenType.ASSIGN: "=",
    TokenType.PLUS_ASSIGN: "+=",
    TokenType.MINUS_ASSIGN: "-=",
    TokenType.STAR_ASSIGN: "*=",
    TokenType.SLASH_ASSIGN: "/=",
    TokenType.PERCENT_ASSIGN: "%=",
    TokenType.POWER_ASSIGN: "**=",
    # Arithmetic
    TokenType.PLUS: "+",
    TokenType.MINUS: "-",
    TokenType.STAR: "*",
    TokenType.SLASH: "/",
    TokenType.PERCENT: "%",
    TokenType.POWER: "**",
    # Comparison
    TokenType.EQ: "==",
    TokenType.NEQ: "!=",
    TokenType.STRICT_EQ: "===",
    TokenType.STRICT_NEQ: "!==",
    TokenType.LT: "<",
    TokenType.GT: ">",
    TokenType.LTE: "<=",
    TokenType.GTE: ">=",
    # Logical
    TokenType.AND: "&&",
    TokenType.OR: "||",
    TokenType.XOR: "xor",
    # Bitwise
    TokenType.BITWISE_OR: "|",
    TokenType.BITWISE_AND: "&",
    TokenType.BITWISE_XOR: "^",
    # Identity + membership
    TokenType.IS: "is",
    TokenType.IN: "in",
}

# Right-associative operators
RIGHT_ASSOC = {"**", "=", "+=", "-=", "*=", "/=", "%=", "**="}

# Assignment operators (produce Assignment node, not BinaryOp)
ASSIGN_OPS = {"=", "+=", "-=", "*=", "/=", "%=", "**="}


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Program:
        stmts = []
        while not self._at_end():
            stmt = self._parse_statement()
            if stmt is not None:
                if isinstance(stmt, list):
                    stmts.extend(stmt)
                else:
                    stmts.append(stmt)
        return Program(stmts)

    # ── Token helpers ───────────────────────────────────────────────

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _check(self, *types: TokenType) -> bool:
        return self._peek().type in types

    def _match(self, *types: TokenType) -> Token | None:
        if self._peek().type in types:
            return self._advance()
        return None

    def _expect(self, tt: TokenType, msg: str = "") -> Token:
        if self._peek().type == tt:
            return self._advance()
        raise ParseError(
            msg or f"Expected {tt.name}, got {self._peek().type.name} ({self._peek().value!r})",
            self._peek(),
        )

    def _skip_semis(self):
        while self._match(TokenType.SEMICOLON):
            pass

    # ── Statements ──────────────────────────────────────────────────

    def _parse_statement(self) -> Any:
        self._skip_semis()
        if self._at_end():
            return None

        tok = self._peek()

        if tok.type == TokenType.FUNCTION:
            # Named function decl: function NAME(...) { }
            # Anonymous: function(...) { } — handled as expression below
            next_tok = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
            if next_tok and next_tok.type == TokenType.IDENTIFIER:
                return self._parse_function_decl()
            # Fall through to expression statement (anonymous function)
        if tok.type in (TokenType.VAR, TokenType.GLOBAL):
            return self._parse_var_decl()
        if tok.type == TokenType.IF:
            return self._parse_if()
        if tok.type == TokenType.WHILE:
            return self._parse_while()
        if tok.type == TokenType.FOR:
            return self._parse_for()
        if tok.type == TokenType.IDENTIFIER and tok.value == "do":
            return self._parse_do_while()
        if tok.type == TokenType.RETURN:
            return self._parse_return()
        if tok.type == TokenType.BREAK:
            self._advance()
            self._match(TokenType.SEMICOLON)
            return BreakStmt()
        if tok.type == TokenType.CONTINUE:
            self._advance()
            self._match(TokenType.SEMICOLON)
            return ContinueStmt()
        if tok.type == TokenType.LBRACE:
            return self._parse_block_as_stmts()

        # Expression statement (function call, assignment, increment)
        # Assignment is now handled inside _parse_expression as an operator
        expr = self._parse_expression(0)
        self._match(TokenType.SEMICOLON)
        # Unwrap: if expression is an Assignment, return it directly as a statement
        if isinstance(expr, Assignment):
            return expr
        return ExprStmt(expr)

    def _parse_param_name(self) -> str:
        """Parse a parameter name, skipping optional @ prefix (pass-by-reference no-op)."""
        self._match(TokenType.AT)  # skip @ if present
        return self._expect(TokenType.IDENTIFIER, "Expected parameter name").value

    def _parse_function_decl(self) -> FunctionDecl:
        tok = self._advance()  # 'function'
        name_tok = self._expect(TokenType.IDENTIFIER, "Expected function name")
        self._expect(TokenType.LPAREN, "Expected '(' after function name")

        params = []
        if not self._check(TokenType.RPAREN):
            params.append(self._parse_param_name())
            while self._match(TokenType.COMMA):
                params.append(self._parse_param_name())

        self._expect(TokenType.RPAREN, "Expected ')' after parameters")
        body = self._parse_block()
        return FunctionDecl(name_tok.value, params, body, line=tok.line)

    def _parse_anon_function(self) -> AnonFunction:
        """Parse anonymous function expression: function(params) { body }"""
        self._advance()  # 'function'
        self._expect(TokenType.LPAREN, "Expected '(' after 'function'")

        params = []
        if not self._check(TokenType.RPAREN):
            params.append(self._parse_param_name())
            while self._match(TokenType.COMMA):
                params.append(self._parse_param_name())

        self._expect(TokenType.RPAREN, "Expected ')' after parameters")
        body = self._parse_block()
        return AnonFunction(params, body)

    def _parse_var_decl(self) -> VarDecl | list:
        """Parse var/global declaration. Returns single VarDecl or list for multi-var."""
        tok = self._advance()  # 'var' or 'global'
        is_global = tok.type == TokenType.GLOBAL

        decls = []
        while True:
            name = self._expect(TokenType.IDENTIFIER, "Expected variable name").value
            init = None
            if self._match(TokenType.ASSIGN):
                init = self._parse_expression(0)
            decls.append(VarDecl(name, init, is_global))
            if not self._match(TokenType.COMMA):
                break

        self._match(TokenType.SEMICOLON)
        return decls[0] if len(decls) == 1 else decls

    def _parse_if(self) -> IfStmt:
        self._advance()  # 'if'
        self._expect(TokenType.LPAREN, "Expected '(' after 'if'")
        condition = self._parse_expression(0)
        self._expect(TokenType.RPAREN, "Expected ')' after if condition")

        then_body = self._parse_body()
        else_body = None

        if self._match(TokenType.ELSE):
            if self._check(TokenType.IF):
                else_body = [self._parse_if()]
            else:
                else_body = self._parse_body()

        return IfStmt(condition, then_body, else_body)

    def _parse_while(self) -> WhileStmt:
        self._advance()  # 'while'
        self._expect(TokenType.LPAREN, "Expected '(' after 'while'")
        condition = self._parse_expression(0)
        self._expect(TokenType.RPAREN, "Expected ')' after while condition")
        body = self._parse_body()
        return WhileStmt(condition, body)

    def _parse_do_while(self) -> DoWhileStmt:
        self._advance()  # 'do'
        body = self._parse_body()
        self._expect(TokenType.WHILE, "Expected 'while' after do block")
        self._expect(TokenType.LPAREN, "Expected '(' after 'while'")
        condition = self._parse_expression(0)
        self._expect(TokenType.RPAREN, "Expected ')' after do-while condition")
        self._match(TokenType.SEMICOLON)
        return DoWhileStmt(condition, body)

    def _parse_for(self) -> ForIn | ForKeyValue | ForClassic:
        self._advance()  # 'for'
        self._expect(TokenType.LPAREN, "Expected '(' after 'for'")

        # Detect: C-style for (init; cond; update) vs for-in / for-kv
        if self._check(TokenType.VAR):
            # Could be: for (var x in ...) OR for (var x = 0; ...)
            saved_pos = self.pos
            self._advance()  # consume 'var'
            name1 = self._expect(TokenType.IDENTIFIER, "Expected variable name").value

            # for (var k : var v in map)
            if self._check(TokenType.COLON):
                self._advance()
                self._expect(TokenType.VAR, "Expected 'var' for value variable")
                name2 = self._expect(TokenType.IDENTIFIER, "Expected value variable name").value
                self._expect(TokenType.IN, "Expected 'in' in for loop")
                iterable = self._parse_expression(0)
                self._expect(TokenType.RPAREN, "Expected ')' after for clause")
                body = self._parse_body()
                return ForKeyValue(name1, name2, iterable, body)

            # for (var x in arr)
            if self._check(TokenType.IN):
                self._advance()
                iterable = self._parse_expression(0)
                self._expect(TokenType.RPAREN, "Expected ')' after for clause")
                body = self._parse_body()
                return ForIn(name1, iterable, body)

            # C-style: for (var x = 0; cond; update)
            init_expr = None
            if self._match(TokenType.ASSIGN):
                init_expr = self._parse_expression(0)
            init = VarDecl(name1, init_expr, False)
            self._expect(TokenType.SEMICOLON, "Expected ';' after for init")
            cond = self._parse_expression(0) if not self._check(TokenType.SEMICOLON) else BoolLit(True)
            self._expect(TokenType.SEMICOLON, "Expected ';' after for condition")
            update = self._parse_expression(0) if not self._check(TokenType.RPAREN) else None
            # Handle assignment in update: i++, i += 1, etc.
            if update and self._check(TokenType.ASSIGN, TokenType.PLUS_ASSIGN,
                                       TokenType.MINUS_ASSIGN, TokenType.STAR_ASSIGN,
                                       TokenType.SLASH_ASSIGN):
                op_tok = self._advance()
                value = self._parse_expression(0)
                update = Assignment(update, op_tok.value, value)
            self._expect(TokenType.RPAREN, "Expected ')' after for clause")
            body = self._parse_body()
            return ForClassic(init, cond, update, body)

        # C-style without var: for (; cond; update) or for (expr; ...)
        init = None
        if not self._check(TokenType.SEMICOLON):
            expr = self._parse_expression(0)
            if self._check(TokenType.ASSIGN, TokenType.PLUS_ASSIGN):
                op = self._advance()
                val = self._parse_expression(0)
                init = Assignment(expr, op.value, val)
            else:
                init = ExprStmt(expr)
        self._expect(TokenType.SEMICOLON, "Expected ';' in for loop")
        cond = self._parse_expression(0) if not self._check(TokenType.SEMICOLON) else BoolLit(True)
        self._expect(TokenType.SEMICOLON, "Expected ';' in for loop")
        update = None
        if not self._check(TokenType.RPAREN):
            update = self._parse_expression(0)
            if self._check(TokenType.ASSIGN, TokenType.PLUS_ASSIGN,
                           TokenType.MINUS_ASSIGN, TokenType.STAR_ASSIGN):
                op_tok = self._advance()
                value = self._parse_expression(0)
                update = Assignment(update, op_tok.value, value)
        self._expect(TokenType.RPAREN, "Expected ')' after for clause")
        body = self._parse_body()
        return ForClassic(init, cond, update, body)

    def _parse_return(self) -> ReturnStmt:
        self._advance()  # 'return'
        value = None
        if not self._check(TokenType.SEMICOLON, TokenType.RBRACE, TokenType.EOF):
            # Check if next token could start an expression
            if not self._at_end() and self._peek().type not in (
                TokenType.SEMICOLON, TokenType.RBRACE, TokenType.EOF,
                TokenType.ELSE,
            ):
                value = self._parse_expression(0)
        self._match(TokenType.SEMICOLON)
        return ReturnStmt(value)

    def _parse_block(self) -> list:
        """Parse { ... } block, returning list of statements."""
        self._expect(TokenType.LBRACE, "Expected '{'")
        stmts = []
        while not self._check(TokenType.RBRACE) and not self._at_end():
            stmt = self._parse_statement()
            if stmt is not None:
                if isinstance(stmt, list):
                    stmts.extend(stmt)
                else:
                    stmts.append(stmt)
        self._expect(TokenType.RBRACE, "Expected '}'")
        return stmts

    def _parse_block_as_stmts(self) -> Any:
        """Parse a { ... } block occurring as a statement. Returns stmts inline."""
        stmts = self._parse_block()
        # Wrap in a dummy if-true to keep block scoping behavior
        return IfStmt(BoolLit(True), stmts, None)

    def _parse_body(self) -> list:
        """Parse either a block or a single statement."""
        if self._check(TokenType.LBRACE):
            return self._parse_block()
        # Empty body: while(cond); or for(...);
        if self._match(TokenType.SEMICOLON):
            return []
        stmt = self._parse_statement()
        if isinstance(stmt, list):
            return stmt
        return [stmt] if stmt else []

    # ── Expressions (Pratt precedence climbing) ─────────────────────

    def _parse_expression(self, min_prec: int) -> Any:
        left = self._parse_unary()

        while True:
            tok = self._peek()

            # Ternary (right-associative, low precedence)
            if tok.type == TokenType.QUESTION and min_prec <= 1:
                self._advance()
                true_val = self._parse_expression(0)
                self._expect(TokenType.COLON, "Expected ':' in ternary")
                false_val = self._parse_expression(1)  # right-assoc
                left = Ternary(left, true_val, false_val)
                continue

            # Binary operators
            op_str = BINARY_OPS.get(tok.type)
            if op_str is not None:
                prec = PRECEDENCE[op_str]
                if prec < min_prec:
                    break
                self._advance()

                # Handle "is not" compound operator
                if op_str == "is" and self._check(TokenType.NOT, TokenType.NOT_KEYWORD):
                    self._advance()
                    op_str = "is not"

                # Right-associative vs left-associative
                if op_str in RIGHT_ASSOC:
                    right = self._parse_expression(prec)
                else:
                    right = self._parse_expression(prec + 1)

                # Assignment ops produce Assignment node
                if op_str in ASSIGN_OPS:
                    left = Assignment(left, op_str, right)
                else:
                    left = BinaryOp(left, op_str, right)
                continue

            break

        return left

    def _parse_unary(self) -> Any:
        tok = self._peek()

        # Unary minus
        if tok.type == TokenType.MINUS:
            self._advance()
            operand = self._parse_unary()
            # Optimize: -literal → negative literal
            if isinstance(operand, NumberLit):
                return NumberLit(-operand.value)
            return UnaryOp("-", operand)

        # Logical NOT (! or 'not')
        if tok.type == TokenType.NOT:
            self._advance()
            operand = self._parse_unary()
            return UnaryOp("!", operand)

        # Prefix increment/decrement
        if tok.type in (TokenType.INCREMENT, TokenType.DECREMENT):
            self._advance()
            operand = self._parse_postfix()
            return Increment(operand, prefix=True, op=tok.value)

        return self._parse_postfix()

    def _parse_postfix(self) -> Any:
        expr = self._parse_primary()

        while True:
            # Function call
            if self._check(TokenType.LPAREN):
                self._advance()
                args = []
                if not self._check(TokenType.RPAREN):
                    args.append(self._parse_expression(0))
                    while self._match(TokenType.COMMA):
                        args.append(self._parse_expression(0))
                self._expect(TokenType.RPAREN, "Expected ')' after arguments")
                expr = FunctionCall(expr, args)
                continue

            # Subscript
            if self._check(TokenType.LBRACKET):
                self._advance()
                index = self._parse_expression(0)
                self._expect(TokenType.RBRACKET, "Expected ']' after subscript")
                expr = Subscript(expr, index)
                continue

            # Property access / method call
            if self._check(TokenType.DOT):
                self._advance()
                prop = self._expect(TokenType.IDENTIFIER, "Expected property name after '.'").value
                if self._check(TokenType.LPAREN):
                    self._advance()
                    args = []
                    if not self._check(TokenType.RPAREN):
                        args.append(self._parse_expression(0))
                        while self._match(TokenType.COMMA):
                            args.append(self._parse_expression(0))
                    self._expect(TokenType.RPAREN, "Expected ')' after method args")
                    expr = MethodCall(expr, prop, args)
                else:
                    expr = PropertyAccess(expr, prop)
                continue

            # Postfix increment/decrement
            if self._check(TokenType.INCREMENT, TokenType.DECREMENT):
                tok = self._advance()
                expr = Increment(expr, prefix=False, op=tok.value)
                continue

            break

        return expr

    def _parse_primary(self) -> Any:
        tok = self._peek()

        # Number
        if tok.type == TokenType.NUMBER:
            self._advance()
            return NumberLit(tok.value)

        # String
        if tok.type == TokenType.STRING:
            self._advance()
            return StringLit(tok.value)

        # Bool
        if tok.type in (TokenType.TRUE, TokenType.FALSE):
            self._advance()
            return BoolLit(tok.value)

        # Null
        if tok.type == TokenType.NULL:
            self._advance()
            return NullLit()

        # @ reference operator — no-op in Python (lists/dicts already pass by ref)
        if tok.type == TokenType.AT:
            self._advance()
            return self._parse_primary()

        # Anonymous function: function(params) { body }
        if tok.type == TokenType.FUNCTION:
            return self._parse_anon_function()

        # Identifier (variable or function name — call handled in postfix)
        if tok.type == TokenType.IDENTIFIER:
            self._advance()
            return Identifier(tok.value)

        # Parenthesized expression
        if tok.type == TokenType.LPAREN:
            self._advance()
            expr = self._parse_expression(0)
            self._expect(TokenType.RPAREN, "Expected ')'")
            return expr

        # Array literal or map literal
        if tok.type == TokenType.LBRACKET:
            return self._parse_array_or_map()

        raise ParseError(f"Unexpected token: {tok.type.name} ({tok.value!r})", tok)

    def _parse_array_or_map(self) -> ArrayLit | MapLit:
        self._advance()  # '['

        # Empty map: [:]
        if self._check(TokenType.COLON) and self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].type == TokenType.RBRACKET:
            self._advance()  # ':'
            self._advance()  # ']'
            return MapLit([])

        # Empty array: []
        if self._check(TokenType.RBRACKET):
            self._advance()
            return ArrayLit([])

        # Parse first element
        first = self._parse_expression(0)

        # Check if it's a map: [key: value, ...]
        if self._check(TokenType.COLON):
            self._advance()
            val = self._parse_expression(0)
            pairs = [(first, val)]
            while self._match(TokenType.COMMA):
                if self._check(TokenType.RBRACKET):
                    break
                k = self._parse_expression(0)
                self._expect(TokenType.COLON, "Expected ':' in map literal")
                v = self._parse_expression(0)
                pairs.append((k, v))
            self._expect(TokenType.RBRACKET, "Expected ']'")
            return MapLit(pairs)

        # It's an array: [a, b, c, ...]
        elements = [first]
        while self._match(TokenType.COMMA):
            if self._check(TokenType.RBRACKET):
                break
            elements.append(self._parse_expression(0))
        self._expect(TokenType.RBRACKET, "Expected ']'")
        return ArrayLit(elements)

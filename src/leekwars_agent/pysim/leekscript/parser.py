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


# OOP AST nodes
@dataclass
class ClassDecl:
    name: str
    parent: str | None  # extends ClassName
    members: list  # ClassField | ClassMethod | ClassConstructor


@dataclass
class ClassField:
    name: str
    init: Any  # Expr | None
    access: str  # 'public', 'private', 'protected'
    is_static: bool
    is_final: bool


@dataclass
class ClassMethod:
    name: str
    params: list[str]
    defaults: list  # parallel to params, None = no default
    body: list
    access: str
    is_static: bool


@dataclass
class ClassConstructor:
    params: list[str]
    defaults: list
    body: list
    access: str


@dataclass
class NewExpr:
    class_expr: Any  # Identifier or expression
    args: list


@dataclass
class ThisExpr:
    pass


@dataclass
class SuperExpr:
    pass


# ── Parser ──────────────────────────────────────────────────────────────

class ParseError(Exception):
    def __init__(self, msg: str, token: Token | None = None):
        loc = f" at L{token.line}:{token.col}" if token else ""
        super().__init__(f"Parse error{loc}: {msg}")
        self.token = token


# Operator precedence (Pratt) — lower number = lower precedence = binds looser
PRECEDENCE = {
    # Assignment (right-assoc)
    "=": 0, "+=": 0, "-=": 0, "*=": 0, "/=": 0, "\\=": 0, "%=": 0, "**=": 0,
    # Logical
    "||": 2,
    "xor": 2,
    "&&": 3,
    # Bitwise
    "|": 4, "^": 5, "&": 6,
    # Equality
    "==": 7, "!=": 7, "===": 7, "!==": 7, "is": 7, "is not": 7,
    # Relational + membership
    "in": 8, "<": 8, ">": 8, "<=": 8, ">=": 8, "instanceof": 8,
    # Arithmetic
    "+": 10, "-": 10,
    "*": 11, "/": 11, "\\": 11, "%": 11,
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
    TokenType.INTDIV: "\\",
    TokenType.INTDIV_ASSIGN: "\\=",
    # Identity + membership
    TokenType.IS: "is",
    TokenType.IN: "in",
    TokenType.INSTANCEOF: "instanceof",
}

# Right-associative operators
RIGHT_ASSOC = {"**", "=", "+=", "-=", "*=", "/=", "\\=", "%=", "**="}

# Assignment operators (produce Assignment node, not BinaryOp)
ASSIGN_OPS = {"=", "+=", "-=", "*=", "/=", "\\=", "%=", "**="}


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

        # Class declaration
        if tok.type == TokenType.CLASS:
            return self._parse_class_decl()

        # Typed declaration without 'var': `TypeName varName = expr` or `Type<G> name = expr`
        # Also handles union types: `Type|Other name = expr` and nullable: `Type? name = expr`
        # Detect: IDENTIFIER IDENTIFIER or IDENTIFIER < ... > IDENTIFIER or IDENTIFIER | ...
        if tok.type == TokenType.IDENTIFIER and self.pos + 1 < len(self.tokens):
            next_tok = self.tokens[self.pos + 1]
            if next_tok.type in (TokenType.LT, TokenType.BITWISE_OR, TokenType.QUESTION):
                # Could be generic/union/nullable type or comparison/bitwise op
                # But `ident ? expr : expr` is a ternary, not a nullable type decl.
                # Try typed decl, but validate: after parsing, next token must look like
                # a declaration continuation (=, ;, ,) not a call/expr continuation ((, .)
                saved = self.pos
                try:
                    result = self._parse_typed_var_decl()
                    # Sanity check: if the next token is something unexpected for a decl,
                    # we probably misparsed a ternary or expression as a typed decl
                    nxt = self._peek().type
                    if nxt in (TokenType.LPAREN, TokenType.COLON, TokenType.QUESTION):
                        # This looks like an expression, not a declaration
                        self.pos = saved
                        raise ParseError("false typed decl", self._peek())
                    return result
                except ParseError:
                    self.pos = saved
            elif next_tok.type == TokenType.IDENTIFIER:
                # Simple typed decl: `Type name = expr`
                # But NOT function calls: `foo(bar)` or `foo bar` in expression context
                # Heuristic: only if the next-next is `=`, `,`, `;`, or EOF
                if self.pos + 2 < len(self.tokens):
                    after_name = self.tokens[self.pos + 2]
                    if after_name.type in (TokenType.ASSIGN, TokenType.COMMA, TokenType.SEMICOLON,
                                           TokenType.RPAREN, TokenType.EOF, TokenType.LBRACKET):
                        return self._parse_typed_var_decl()
                    # Also allow `Type name = ...` where name is followed by expression
                    if after_name.type not in (TokenType.LPAREN, TokenType.DOT, TokenType.LBRACKET,
                                               TokenType.PLUS, TokenType.MINUS, TokenType.STAR):
                        saved = self.pos
                        try:
                            return self._parse_typed_var_decl()
                        except ParseError:
                            self.pos = saved

        # Expression statement (function call, assignment, increment)
        # Assignment is now handled inside _parse_expression as an operator
        expr = self._parse_expression(0)
        self._match(TokenType.SEMICOLON)
        # Unwrap: if expression is an Assignment, return it directly as a statement
        if isinstance(expr, Assignment):
            return expr
        return ExprStmt(expr)

    def _parse_param_name(self) -> str:
        """Parse a parameter name, skipping optional @ prefix and type annotation."""
        self._match(TokenType.AT)  # skip @ if present
        # Skip optional type annotation before param name (including union/generic/nullable)
        if self._check(TokenType.IDENTIFIER) and self.pos + 1 < len(self.tokens):
            next_tok = self.tokens[self.pos + 1]
            if next_tok.type in (TokenType.IDENTIFIER, TokenType.LT,
                                 TokenType.BITWISE_OR, TokenType.QUESTION):
                saved = self.pos
                self._skip_type_annotation()
                if self._check(TokenType.IDENTIFIER):
                    pass  # Successfully skipped type, now at name
                else:
                    self.pos = saved  # Wasn't a type, restore
        return self._expect(TokenType.IDENTIFIER, "Expected parameter name").value

    def _skip_return_type(self):
        """Skip optional return type annotation: `=> Type` or `-> Type` or `: Type` after params.
        Also handles inline return types when IDENTIFIER follows `)` directly."""
        if self._match(TokenType.FAT_ARROW) or self._match(TokenType.ARROW):
            self._skip_type_annotation()
        elif self._check(TokenType.COLON) and self.pos + 1 < len(self.tokens):
            # : ReturnType { ... } — only if next-next is {
            # Don't consume colon if it's not a return type
            pass

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
        # Skip optional return type annotation
        self._skip_return_type()
        body = self._parse_block()
        return FunctionDecl(name_tok.value, params, body, line=tok.line)

    def _parse_arrow_lambda(self) -> AnonFunction:
        """Parse typed arrow lambda: (Type name, Type name) => Type { body }.
        Raises ParseError if this doesn't look like a lambda (caller uses try/except)."""
        self._advance()  # consume '('
        params = []
        if not self._check(TokenType.RPAREN):
            # Each param: [Type] name
            # Must have at least one `Type name` pair to distinguish from (expr)
            self._match(TokenType.AT)  # optional @
            if self._check(TokenType.IDENTIFIER) and self.pos + 1 < len(self.tokens):
                next_tok = self.tokens[self.pos + 1]
                if next_tok.type not in (TokenType.COMMA, TokenType.RPAREN, TokenType.ASSIGN):
                    self._skip_type_annotation()
            params.append(self._expect(TokenType.IDENTIFIER, "Expected parameter name").value)
            while self._match(TokenType.COMMA):
                self._match(TokenType.AT)
                if self._check(TokenType.IDENTIFIER) and self.pos + 1 < len(self.tokens):
                    next_tok = self.tokens[self.pos + 1]
                    if next_tok.type not in (TokenType.COMMA, TokenType.RPAREN, TokenType.ASSIGN):
                        self._skip_type_annotation()
                params.append(self._expect(TokenType.IDENTIFIER, "Expected parameter name").value)
        self._expect(TokenType.RPAREN, "Expected ')' after lambda parameters")
        # Must have => (arrow) to confirm this is a lambda
        if not self._check(TokenType.FAT_ARROW) and not self._check(TokenType.ARROW):
            raise ParseError("Expected '=>' for arrow lambda", self._peek())
        self._advance()  # consume => or ->
        # Skip optional return type
        if self._check(TokenType.IDENTIFIER):
            saved = self.pos
            self._skip_type_annotation()
            # Only consume type if followed by { (block body)
            if not self._check(TokenType.LBRACE):
                self.pos = saved
        body = self._parse_block()
        return AnonFunction(params, body)

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
        # Skip optional return type annotation
        self._skip_return_type()
        body = self._parse_block()
        return AnonFunction(params, body)

    def _parse_var_decl(self) -> VarDecl | list:
        """Parse var/global declaration. Returns single VarDecl or list for multi-var.
        Handles optional type annotations: `var Type<Gen> name = expr`."""
        tok = self._advance()  # 'var' or 'global'
        is_global = tok.type == TokenType.GLOBAL

        # Skip optional type annotation after var/global
        if self._check(TokenType.IDENTIFIER) and self.pos + 1 < len(self.tokens):
            next_tok = self.tokens[self.pos + 1]
            if next_tok.type == TokenType.LT:
                # var Array<string> name — generic type
                saved = self.pos
                self._skip_type_annotation()
                if not self._check(TokenType.IDENTIFIER):
                    self.pos = saved  # Wasn't a type
            elif next_tok.type == TokenType.IDENTIFIER:
                # var Type name — but only if the second identifier is followed by = or , or ;
                if self.pos + 2 < len(self.tokens):
                    after = self.tokens[self.pos + 2]
                    if after.type in (TokenType.ASSIGN, TokenType.COMMA, TokenType.SEMICOLON):
                        saved = self.pos
                        self._skip_type_annotation()
                        if not self._check(TokenType.IDENTIFIER):
                            self.pos = saved

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
        # Also handle typed for-in: for (Type name in ...)
        if self._check(TokenType.VAR):
            # Could be: for (var x in ...) OR for (var x = 0; ...)
            saved_pos = self.pos
            self._advance()  # consume 'var'
            # Skip optional type annotation after 'var'
            if self._check(TokenType.IDENTIFIER) and self.pos + 1 < len(self.tokens):
                next_t = self.tokens[self.pos + 1]
                if next_t.type == TokenType.IDENTIFIER:
                    # var Type name — skip Type
                    self._skip_type_annotation()
                elif next_t.type == TokenType.LT:
                    saved_type = self.pos
                    self._skip_type_annotation()
                    if not self._check(TokenType.IDENTIFIER):
                        self.pos = saved_type
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

        # Typed for-in/kv/c-style without 'var': for (Type name in ...) or for (Type k : Type v in ...)
        # or for (Type name = expr; cond; update)
        if self._check(TokenType.IDENTIFIER) and self.pos + 1 < len(self.tokens):
            next_t = self.tokens[self.pos + 1]
            # Check for `Type name` or `Type<Gen> name` pattern
            if next_t.type == TokenType.IDENTIFIER or next_t.type == TokenType.LT:
                saved_pos = self.pos
                self._skip_type_annotation()
                if self._check(TokenType.IDENTIFIER):
                    name1 = self._advance().value
                    # for (Type k : Type v in map)
                    if self._check(TokenType.COLON):
                        self._advance()
                        self._match(TokenType.VAR)  # optional var before value
                        # Skip optional type on value
                        if self._check(TokenType.IDENTIFIER) and self.pos + 1 < len(self.tokens):
                            next_t2 = self.tokens[self.pos + 1]
                            if next_t2.type == TokenType.IDENTIFIER:
                                self._skip_type_annotation()
                            elif next_t2.type == TokenType.LT:
                                sav = self.pos
                                self._skip_type_annotation()
                                if not self._check(TokenType.IDENTIFIER):
                                    self.pos = sav
                        name2 = self._expect(TokenType.IDENTIFIER, "Expected value variable name").value
                        self._expect(TokenType.IN, "Expected 'in'")
                        iterable = self._parse_expression(0)
                        self._expect(TokenType.RPAREN, "Expected ')'")
                        body = self._parse_body()
                        return ForKeyValue(name1, name2, iterable, body)
                    # for (Type name in arr)
                    if self._check(TokenType.IN):
                        self._advance()
                        iterable = self._parse_expression(0)
                        self._expect(TokenType.RPAREN, "Expected ')'")
                        body = self._parse_body()
                        return ForIn(name1, iterable, body)
                    # Typed C-style: for (Type name = expr; cond; update)
                    if self._check(TokenType.ASSIGN):
                        self._advance()  # consume '='
                        init_expr = self._parse_expression(0)
                        init = VarDecl(name1, init_expr, False)
                        self._expect(TokenType.SEMICOLON, "Expected ';' after for init")
                        cond = self._parse_expression(0) if not self._check(TokenType.SEMICOLON) else BoolLit(True)
                        self._expect(TokenType.SEMICOLON, "Expected ';' after for condition")
                        update = self._parse_expression(0) if not self._check(TokenType.RPAREN) else None
                        self._expect(TokenType.RPAREN, "Expected ')' after for clause")
                        body = self._parse_body()
                        return ForClassic(init, cond, update, body)
                    # Was actually `for (expr; ...` — restore
                    self.pos = saved_pos
                else:
                    self.pos = saved_pos

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

    # ── Type annotations (skip) ──────────────────────────────────────

    def _skip_type_annotation(self) -> bool:
        """Try to consume a type annotation (e.g., `integer`, `Array<Enemy>`, `Map<int, Leek>`,
        `Type|OtherType`, `Type?`, `Function<A, B => void>`).
        Returns True if a type was consumed, False if nothing was consumed."""
        if not self._check(TokenType.IDENTIFIER):
            return False
        self._advance()  # consume type name
        # Handle generics: Type<A, B> — count depth, allowing => and | inside
        if self._check(TokenType.LT):
            depth = 1
            self._advance()  # consume <
            while depth > 0 and not self._at_end():
                if self._check(TokenType.LT):
                    depth += 1
                elif self._check(TokenType.GT):
                    depth -= 1
                elif self._check(TokenType.GTE):
                    # >> can be two closing brackets in nested generics
                    depth -= 1
                self._advance()
        # Handle union types: Type|OtherType|AnotherType
        while self._check(TokenType.BITWISE_OR):
            self._advance()  # consume |
            if self._check(TokenType.IDENTIFIER):
                self._skip_type_annotation()  # recurse for the next type in union
            elif self._check(TokenType.NULL):
                self._advance()  # Type|null
        # Handle nullable: Type?
        if self._check(TokenType.QUESTION):
            self._advance()
        return True

    def _parse_typed_var_decl(self) -> VarDecl | list:
        """Parse typed declaration: `Type name [= expr]` → treat as var decl."""
        # Skip the type annotation
        self._skip_type_annotation()
        # Now parse like a var declaration
        decls = []
        while True:
            name = self._expect(TokenType.IDENTIFIER, "Expected variable name").value
            init = None
            if self._match(TokenType.ASSIGN):
                init = self._parse_expression(0)
            decls.append(VarDecl(name, init, is_global=False))
            if not self._match(TokenType.COMMA):
                break
        self._match(TokenType.SEMICOLON)
        return decls[0] if len(decls) == 1 else decls

    # ── Class declarations ─────────────────────────────────────────────

    def _parse_class_decl(self) -> ClassDecl:
        """Parse: class Name [extends Parent] { members... }"""
        self._advance()  # 'class'
        name = self._expect(TokenType.IDENTIFIER, "Expected class name").value

        parent = None
        if self._match(TokenType.EXTENDS):
            parent = self._expect(TokenType.IDENTIFIER, "Expected parent class name").value

        self._expect(TokenType.LBRACE, "Expected '{' after class declaration")

        members = []
        while not self._check(TokenType.RBRACE) and not self._at_end():
            self._skip_semis()
            if self._check(TokenType.RBRACE):
                break
            member = self._parse_class_member()
            if member is not None:
                members.append(member)

        self._expect(TokenType.RBRACE, "Expected '}' to close class")
        return ClassDecl(name, parent, members)

    def _parse_class_member(self) -> Any:
        """Parse a single class member (field, method, or constructor)."""
        access = "public"
        is_static = False
        is_final = False

        # Consume access modifiers
        if self._check(TokenType.PUBLIC, TokenType.PRIVATE, TokenType.PROTECTED):
            access = self._advance().value

        # Consume static
        if self._match(TokenType.STATIC):
            is_static = True

        # Consume final (context-sensitive keyword — lexed as IDENTIFIER)
        if self._check(TokenType.IDENTIFIER) and self._peek().value == "final":
            self._advance()
            is_final = True

        # Constructor
        if self._check(TokenType.CONSTRUCTOR):
            self._advance()
            params, defaults = self._parse_method_params()
            body = self._parse_block()
            self._match(TokenType.SEMICOLON)
            return ClassConstructor(params, defaults, body, access)

        # Skip optional type annotation before name
        # We need to be careful: if it's `string()` that's the toString method, not a type
        saved = self.pos
        has_type = False

        # Check for `string(` — special toString method (no type annotation, method named "string")
        if self._check(TokenType.IDENTIFIER) and self._peek().value == "string":
            if self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].type == TokenType.LPAREN:
                # It's the string() method
                pass  # Don't skip type
            else:
                has_type = self._skip_type_annotation()
                # After type, check if next is identifier (member name)
                if not self._check(TokenType.IDENTIFIER):
                    self.pos = saved
                    has_type = False
        elif self._check(TokenType.IDENTIFIER):
            # Look ahead: if IDENTIFIER IDENTIFIER, first is type
            if self.pos + 1 < len(self.tokens):
                next_tok = self.tokens[self.pos + 1]
                if next_tok.type in (TokenType.IDENTIFIER, TokenType.LT,
                                     TokenType.BITWISE_OR, TokenType.QUESTION):
                    # Type annotation with possible generics/union/nullable
                    has_type = self._skip_type_annotation()
                    # After type, check if next is identifier (member name)
                    if not self._check(TokenType.IDENTIFIER):
                        # Wasn't a type after all, restore
                        self.pos = saved
                        has_type = False

        # Now we should be at the member name
        if not self._check(TokenType.IDENTIFIER):
            # Skip unknown token
            self._advance()
            self._match(TokenType.SEMICOLON)
            return None

        name_tok = self._advance()
        name = name_tok.value

        # Method: name(params) { body }
        if self._check(TokenType.LPAREN):
            params, defaults = self._parse_method_params()
            body = self._parse_block()
            self._match(TokenType.SEMICOLON)
            return ClassMethod(name, params, defaults, body, access, is_static)

        # Field: name [= expr]
        init = None
        if self._match(TokenType.ASSIGN):
            init = self._parse_expression(0)
        self._match(TokenType.SEMICOLON)
        return ClassField(name, init, access, is_static, is_final)

    def _parse_method_params(self) -> tuple[list[str], list]:
        """Parse (param1, param2 = default, ...) returning (names, defaults).
        Handles type annotations including union types (Type|Type) and generics."""
        self._expect(TokenType.LPAREN, "Expected '(' for method parameters")
        params = []
        defaults = []
        while not self._check(TokenType.RPAREN) and not self._at_end():
            # Skip @ reference prefix
            self._match(TokenType.AT)
            # Skip optional type annotation (including union types and generics)
            if self._check(TokenType.IDENTIFIER) and self.pos + 1 < len(self.tokens):
                next_tok = self.tokens[self.pos + 1]
                if next_tok.type == TokenType.IDENTIFIER:
                    # Could be `Type name` — check that after skipping type we land on IDENTIFIER
                    saved = self.pos
                    self._skip_type_annotation()
                    if self._check(TokenType.IDENTIFIER):
                        pass  # Successfully skipped type
                    else:
                        self.pos = saved  # Wasn't a type
                elif next_tok.type == TokenType.LT:
                    saved = self.pos
                    self._skip_type_annotation()
                    if self._check(TokenType.IDENTIFIER):
                        pass
                    else:
                        self.pos = saved
                elif next_tok.type == TokenType.BITWISE_OR:
                    # Union type: Type|OtherType name
                    saved = self.pos
                    self._skip_type_annotation()
                    if self._check(TokenType.IDENTIFIER):
                        pass
                    else:
                        self.pos = saved
                elif next_tok.type == TokenType.QUESTION:
                    # Nullable type: Type? name
                    saved = self.pos
                    self._skip_type_annotation()
                    if self._check(TokenType.IDENTIFIER):
                        pass
                    else:
                        self.pos = saved
            name = self._expect(TokenType.IDENTIFIER, "Expected parameter name").value
            params.append(name)
            # Default value
            if self._match(TokenType.ASSIGN):
                defaults.append(self._parse_expression(0))
            else:
                defaults.append(None)
            self._match(TokenType.COMMA)
        self._expect(TokenType.RPAREN, "Expected ')' after parameters")
        # Skip optional return type annotation on method
        self._skip_return_type()
        return params, defaults

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
                false_val = self._parse_expression(0)  # allow assignments in false branch too
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
                # Allow keywords as property names (this.class.name, super.method, etc.)
                prop_tok = self._peek()
                if prop_tok.type == TokenType.IDENTIFIER or prop_tok.type in (
                    TokenType.CLASS, TokenType.SUPER, TokenType.THIS, TokenType.NEW,
                    TokenType.CONSTRUCTOR, TokenType.STATIC,
                    TokenType.PUBLIC, TokenType.PRIVATE, TokenType.PROTECTED,
                    TokenType.RETURN, TokenType.FUNCTION, TokenType.IN,
                ):
                    prop = self._advance().value
                else:
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

            # Non-null assertion: expr!  (skip — treat as identity)
            if self._check(TokenType.NOT):
                # Distinguish postfix `!` from binary `!=` / `!==`
                # Postfix `!` is followed by `.`, `;`, `)`, `[`, `,`, `}`, `!`, EOF, or operator
                # NOT followed by `=` (which would be `!=`)
                next_idx = self.pos + 1
                if next_idx < len(self.tokens):
                    after_bang = self.tokens[next_idx]
                    if after_bang.type != TokenType.ASSIGN and after_bang.value != "=":
                        self._advance()  # consume `!`
                        continue

            # `as` type cast: expr as Type — skip the cast (Python is dynamically typed)
            if self._check(TokenType.IDENTIFIER) and self._peek().value == "as":
                self._advance()  # consume 'as'
                self._skip_type_annotation()
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

        # `new ClassName(args)` expression
        if tok.type == TokenType.NEW:
            self._advance()
            class_expr = Identifier(self._expect(TokenType.IDENTIFIER, "Expected class name after 'new'").value)
            args = []
            if self._check(TokenType.LPAREN):
                self._advance()
                if not self._check(TokenType.RPAREN):
                    args.append(self._parse_expression(0))
                    while self._match(TokenType.COMMA):
                        args.append(self._parse_expression(0))
                self._expect(TokenType.RPAREN, "Expected ')' after constructor args")
            return NewExpr(class_expr, args)

        # `this` keyword
        if tok.type == TokenType.THIS:
            self._advance()
            return ThisExpr()

        # `super` keyword
        if tok.type == TokenType.SUPER:
            self._advance()
            return SuperExpr()

        # `class` as expression (inside methods: returns current class)
        if tok.type == TokenType.CLASS:
            self._advance()
            return Identifier("__class__")

        # Anonymous function: function(params) { body }
        if tok.type == TokenType.FUNCTION:
            return self._parse_anon_function()

        # Identifier (variable or function name — call handled in postfix)
        if tok.type == TokenType.IDENTIFIER:
            self._advance()
            return Identifier(tok.value)

        # Parenthesized expression OR typed arrow lambda: (Type name, ...) => Type { body }
        if tok.type == TokenType.LPAREN:
            # Try typed arrow lambda first
            saved = self.pos
            try:
                return self._parse_arrow_lambda()
            except ParseError:
                self.pos = saved
            # Fall back to normal parenthesized expression
            self._advance()
            expr = self._parse_expression(0)
            self._expect(TokenType.RPAREN, "Expected ')'")
            return expr

        # Array literal or map literal
        if tok.type == TokenType.LBRACKET:
            return self._parse_array_or_map()

        # Object literal: { key: val, ... }
        if tok.type == TokenType.LBRACE:
            return self._parse_object_literal()

        # Set literal: <> (empty), <elem, elem, ...>
        if tok.type == TokenType.LT:
            return self._parse_set_literal()

        # Bitwise NOT: ~expr
        if tok.type == TokenType.BITWISE_NOT:
            self._advance()
            operand = self._parse_unary()
            return UnaryOp("~", operand)

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

        # Check if it's a range: [start..end]
        if self._check(TokenType.DOTDOT):
            self._advance()  # consume '..'
            end = self._parse_expression(0)
            self._expect(TokenType.RBRACKET, "Expected ']' after range")
            # Represent range as FunctionCall to 'range' builtin
            return FunctionCall(Identifier("__range__"), [first, end])

        # Check if it's a map: [key: value, ...]
        if self._check(TokenType.COLON):
            self._advance()
            val = self._parse_expression(0)
            pairs = [(first, val)]
            while not self._check(TokenType.RBRACKET) and not self._at_end():
                self._match(TokenType.COMMA)  # comma is optional between map entries
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

    def _parse_object_literal(self) -> MapLit:
        """Parse object literal: { key: val, key: val, ... } → treated as MapLit."""
        self._advance()  # '{'

        # Empty object: {}
        if self._check(TokenType.RBRACE):
            self._advance()
            return MapLit([])

        pairs = []
        while not self._check(TokenType.RBRACE) and not self._at_end():
            # Key: identifier or string or expression
            if self._check(TokenType.IDENTIFIER):
                key = StringLit(self._advance().value)
            elif self._check(TokenType.STRING):
                key = StringLit(self._advance().value)
            else:
                key = self._parse_expression(0)
            self._expect(TokenType.COLON, "Expected ':' in object literal")
            val = self._parse_expression(0)
            pairs.append((key, val))
            if not self._match(TokenType.COMMA):
                # LS allows commas to be optional
                if self._check(TokenType.RBRACE):
                    break
        self._expect(TokenType.RBRACE, "Expected '}' to close object literal")
        return MapLit(pairs)

    def _parse_set_literal(self) -> ArrayLit:
        """Parse Set literal: <> (empty), <elem, elem, ...>.
        Sets are represented as ArrayLit at runtime (Python set semantics added in interpreter).
        Elements are parsed at precedence 9 (above comparison) so `>` isn't consumed as binary op."""
        self._advance()  # consume '<'
        # Empty set: <> or < > (with space)
        if self._check(TokenType.GT):
            self._advance()
            return ArrayLit([])
        # Non-empty set: <elem, elem, ...>
        # Parse at prec 9 to stop before < > <= >= comparisons (prec 8)
        elements = [self._parse_expression(9)]
        while self._match(TokenType.COMMA):
            if self._check(TokenType.GT):
                break
            elements.append(self._parse_expression(9))
        self._expect(TokenType.GT, "Expected '>' to close set literal")
        return ArrayLit(elements)

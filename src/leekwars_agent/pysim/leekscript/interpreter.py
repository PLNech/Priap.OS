"""LeekScript tree-walking interpreter.

Evaluates AST nodes produced by the parser. Manages variable scoping
(global persists across turns, local is per-function-call). Game API
functions are injected as a dict by the fight engine.
"""

from __future__ import annotations

import math
from typing import Any, Callable

from .parser import (
    Program, FunctionDecl, VarDecl, Assignment, IfStmt, WhileStmt,
    ForIn, ForKeyValue, ForClassic, DoWhileStmt,
    ReturnStmt, BreakStmt, ContinueStmt, ExprStmt,
    BinaryOp, UnaryOp, Ternary, FunctionCall, MethodCall, Subscript,
    PropertyAccess, Identifier, NumberLit, StringLit, BoolLit, NullLit,
    ArrayLit, MapLit, Increment,
)


class Environment:
    """Variable scope. Chained: local -> parent -> ... -> global."""

    __slots__ = ("vars", "parent")

    def __init__(self, parent: Environment | None = None):
        self.vars: dict[str, Any] = {}
        self.parent = parent

    def get(self, name: str) -> Any:
        if name in self.vars:
            return self.vars[name]
        if self.parent is not None:
            return self.parent.get(name)
        return None  # undefined -> null in LeekScript

    def set(self, name: str, value: Any) -> bool:
        """Set existing variable. Walk up scope chain."""
        if name in self.vars:
            self.vars[name] = value
            return True
        if self.parent is not None:
            return self.parent.set(name, value)
        return False

    def define(self, name: str, value: Any):
        """Define new variable in current scope."""
        self.vars[name] = value


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


class ReturnSignal(Exception):
    __slots__ = ("value",)

    def __init__(self, value: Any = None):
        self.value = value


class LSRuntimeError(Exception):
    """LeekScript runtime error."""
    pass


# Max iterations to prevent infinite loops
MAX_LOOP_ITERATIONS = 100_000
MAX_OPS = 1_000_000


class Interpreter:
    """Tree-walking LeekScript evaluator.

    Each entity gets its own Interpreter. The global_env persists across
    run() calls (turns), matching LeekScript's `global` keyword semantics.
    """

    def __init__(self, game_api: dict[str, Any] | None = None):
        self.global_env = Environment()
        self.functions: dict[str, FunctionDecl] = {}
        self.game_api: dict[str, Any] = game_api or {}
        self.debug_log: list[str] = []
        self.ops = 0
        self._initialized = False
        self._setup_builtins()

    def _setup_builtins(self):
        def _push(arr, val):
            if isinstance(arr, list):
                arr.append(val)
            return None

        def _count(x):
            if x is None:
                return 0
            if isinstance(x, (list, dict, str)):
                return len(x)
            return 0

        def _floor(x):
            if x is None:
                return 0
            return int(math.floor(float(x)))

        def _ceil(x):
            if x is None:
                return 0
            return int(math.ceil(float(x)))

        def _max(a, b):
            a = _to_num(a)
            b = _to_num(b)
            return a if a > b else b

        def _min(a, b):
            a = _to_num(a)
            b = _to_num(b)
            return a if a < b else b

        def _abs(x):
            return abs(_to_num(x))

        def _debug(*args):
            msg = " ".join(_to_str(a) for a in args)
            self.debug_log.append(msg)
            return None

        def _number(x):
            return _to_num(x)

        def _string(x):
            return _to_str(x)

        def _type_of(x):
            if x is None:
                return 0  # NULL type
            if isinstance(x, bool):
                return 1  # BOOLEAN
            if isinstance(x, int):
                return 2  # NUMBER
            if isinstance(x, float):
                return 3  # NUMBER
            if isinstance(x, str):
                return 4  # STRING
            if isinstance(x, list):
                return 5  # ARRAY
            if isinstance(x, dict):
                return 6  # MAP
            return 0

        def _sort(arr, key_fn=None):
            if not isinstance(arr, list):
                return arr
            if key_fn is not None:
                arr.sort(key=lambda x: key_fn(x))
            else:
                arr.sort(key=lambda x: (_to_num(x) if isinstance(x, (int, float)) else 0))
            return arr

        def _reverse(arr):
            if isinstance(arr, list):
                arr.reverse()
            return arr

        def _indexOf(arr, val):
            if isinstance(arr, list):
                try:
                    return arr.index(val)
                except ValueError:
                    return -1
            return -1

        def _remove(arr, idx):
            if isinstance(arr, list) and 0 <= idx < len(arr):
                return arr.pop(idx)
            return None

        def _replace(s, old, new):
            if isinstance(s, str):
                return s.replace(str(old), str(new))
            return s

        def _length(s):
            if isinstance(s, str):
                return len(s)
            return 0

        def _substring(s, start, end=None):
            if isinstance(s, str):
                if end is None:
                    return s[int(start):]
                return s[int(start):int(end)]
            return ""

        def _sqrt(x):
            return math.sqrt(_to_num(x))

        def _pow(x, y):
            return _to_num(x) ** _to_num(y)

        def _round(x):
            return round(_to_num(x))

        def _arrayMap(arr, fn):
            if not isinstance(arr, list):
                return []
            return [fn(v) for v in arr]

        def _arrayFilter(arr, fn):
            if not isinstance(arr, list):
                return []
            return [v for v in arr if fn(v)]

        def _inArray(arr, val):
            if isinstance(arr, list):
                return val in arr
            return False

        self._builtins: dict[str, Callable] = {
            "push": _push,
            "count": _count,
            "floor": _floor,
            "ceil": _ceil,
            "max": _max,
            "min": _min,
            "abs": _abs,
            "debug": _debug,
            "debugW": _debug,
            "debugE": _debug,
            "debugC": _debug,
            "number": _number,
            "string": _string,
            "typeOf": _type_of,
            "sort": _sort,
            "reverse": _reverse,
            "indexOf": _indexOf,
            "remove": _remove,
            "replace": _replace,
            "length": _length,
            "substring": _substring,
            "sqrt": _sqrt,
            "pow": _pow,
            "round": _round,
            "arrayMap": _arrayMap,
            "arrayFilter": _arrayFilter,
            "inArray": _inArray,
        }

    def run(self, program: Program) -> Any:
        """Execute a parsed program. Called once per turn.

        First call: register functions + init globals + run main block.
        Subsequent calls: re-run the entire program (functions re-register,
        globals already exist so re-assignment updates them).
        """
        self.ops = 0
        result = None

        for stmt in program.stmts:
            try:
                # First pass on first run: register function signatures
                if isinstance(stmt, FunctionDecl):
                    self.functions[stmt.name] = stmt
                    continue
                result = self._exec_stmt(stmt, self.global_env)
            except ReturnSignal as r:
                return r.value
            except (BreakSignal, ContinueSignal):
                pass  # stray break/continue at top level — ignore

        self._initialized = True
        return result

    # ── Statement execution ─────────────────────────────────────────

    def _exec_stmt(self, stmt: Any, env: Environment) -> Any:
        self.ops += 1
        if self.ops > MAX_OPS:
            raise LSRuntimeError("Operation limit exceeded")

        if isinstance(stmt, VarDecl):
            return self._exec_var_decl(stmt, env)
        if isinstance(stmt, Assignment):
            return self._exec_assignment(stmt, env)
        if isinstance(stmt, IfStmt):
            return self._exec_if(stmt, env)
        if isinstance(stmt, WhileStmt):
            return self._exec_while(stmt, env)
        if isinstance(stmt, ForIn):
            return self._exec_for_in(stmt, env)
        if isinstance(stmt, ForKeyValue):
            return self._exec_for_kv(stmt, env)
        if isinstance(stmt, ForClassic):
            return self._exec_for_classic(stmt, env)
        if isinstance(stmt, DoWhileStmt):
            return self._exec_do_while(stmt, env)
        if isinstance(stmt, ReturnStmt):
            val = self._eval_expr(stmt.value, env) if stmt.value else None
            raise ReturnSignal(val)
        if isinstance(stmt, BreakStmt):
            raise BreakSignal()
        if isinstance(stmt, ContinueStmt):
            raise ContinueSignal()
        if isinstance(stmt, ExprStmt):
            return self._eval_expr(stmt.expr, env)
        if isinstance(stmt, FunctionDecl):
            self.functions[stmt.name] = stmt
            return None

        raise LSRuntimeError(f"Unknown statement type: {type(stmt).__name__}")

    def _exec_var_decl(self, stmt: VarDecl, env: Environment):
        if stmt.is_global:
            # Global: only initialize if not already defined (cross-turn persistence)
            if stmt.name not in self.global_env.vars:
                value = self._eval_expr(stmt.init, env) if stmt.init else None
                self.global_env.define(stmt.name, value)
            # If already exists, skip — keeps the value from previous turn
        else:
            value = self._eval_expr(stmt.init, env) if stmt.init else None
            env.define(stmt.name, value)

    def _exec_assignment(self, stmt: Assignment, env: Environment):
        value = self._eval_expr(stmt.value, env)

        # Handle subscript assignment: arr[i] = val, map[k] = val
        if isinstance(stmt.target, Subscript):
            obj = self._eval_expr(stmt.target.obj, env)
            idx = self._eval_expr(stmt.target.index, env)

            if stmt.op == "=":
                new_val = value
            else:
                old_val = self._subscript_get(obj, idx)
                new_val = self._apply_compound_op(stmt.op, old_val, value)

            if isinstance(obj, list):
                idx = int(idx)
                if 0 <= idx < len(obj):
                    obj[idx] = new_val
            elif isinstance(obj, dict):
                obj[idx] = new_val
            return new_val

        # Handle property assignment
        if isinstance(stmt.target, PropertyAccess):
            obj = self._eval_expr(stmt.target.obj, env)
            if isinstance(obj, dict):
                if stmt.op == "=":
                    obj[stmt.target.prop] = value
                else:
                    old = obj.get(stmt.target.prop)
                    obj[stmt.target.prop] = self._apply_compound_op(stmt.op, old, value)
            return value

        # Simple variable assignment
        if isinstance(stmt.target, Identifier):
            name = stmt.target.name
            if stmt.op == "=":
                new_val = value
            else:
                old_val = env.get(name)
                if old_val is None:
                    old_val = self.global_env.get(name)
                new_val = self._apply_compound_op(stmt.op, old_val, value)

            # Try local scope first, then global
            if not env.set(name, new_val):
                if not self.global_env.set(name, new_val):
                    # Not found anywhere — define in current scope
                    env.define(name, new_val)
            return new_val

        raise LSRuntimeError(f"Invalid assignment target: {type(stmt.target).__name__}")

    def _apply_compound_op(self, op: str, old: Any, value: Any) -> Any:
        old = _to_num(old)
        value = _to_num(value)
        if op == "+=":
            # String concatenation if old was a string
            return old + value
        if op == "-=":
            return old - value
        if op == "*=":
            return old * value
        if op == "/=":
            return old / value if value != 0 else 0
        return value

    def _exec_if(self, stmt: IfStmt, env: Environment):
        if _is_truthy(self._eval_expr(stmt.condition, env)):
            return self._exec_block(stmt.then_body, env)
        elif stmt.else_body:
            return self._exec_block(stmt.else_body, env)

    def _exec_while(self, stmt: WhileStmt, env: Environment):
        iters = 0
        while _is_truthy(self._eval_expr(stmt.condition, env)):
            iters += 1
            if iters > MAX_LOOP_ITERATIONS:
                raise LSRuntimeError("While loop iteration limit exceeded")
            try:
                self._exec_block(stmt.body, env)
            except BreakSignal:
                break
            except ContinueSignal:
                continue

    def _exec_for_in(self, stmt: ForIn, env: Environment):
        iterable = self._eval_expr(stmt.iterable, env)
        iters = 0

        if isinstance(iterable, list):
            for item in iterable:
                iters += 1
                if iters > MAX_LOOP_ITERATIONS:
                    raise LSRuntimeError("For loop iteration limit exceeded")
                local = Environment(env)
                local.define(stmt.var_name, item)
                try:
                    self._exec_block(stmt.body, local)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
        elif isinstance(iterable, dict):
            for key in list(iterable.keys()):
                iters += 1
                if iters > MAX_LOOP_ITERATIONS:
                    raise LSRuntimeError("For loop iteration limit exceeded")
                local = Environment(env)
                local.define(stmt.var_name, key)
                try:
                    self._exec_block(stmt.body, local)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue

    def _exec_for_kv(self, stmt: ForKeyValue, env: Environment):
        iterable = self._eval_expr(stmt.iterable, env)
        iters = 0

        if isinstance(iterable, dict):
            for key, val in list(iterable.items()):
                iters += 1
                if iters > MAX_LOOP_ITERATIONS:
                    raise LSRuntimeError("For-kv loop iteration limit exceeded")
                local = Environment(env)
                local.define(stmt.key_name, key)
                local.define(stmt.val_name, val)
                try:
                    self._exec_block(stmt.body, local)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue
        elif isinstance(iterable, list):
            for idx, val in enumerate(iterable):
                iters += 1
                if iters > MAX_LOOP_ITERATIONS:
                    raise LSRuntimeError("For-kv loop iteration limit exceeded")
                local = Environment(env)
                local.define(stmt.key_name, idx)
                local.define(stmt.val_name, val)
                try:
                    self._exec_block(stmt.body, local)
                except BreakSignal:
                    break
                except ContinueSignal:
                    continue

    def _exec_for_classic(self, stmt: ForClassic, env: Environment):
        local = Environment(env)
        if stmt.init:
            self._exec_stmt(stmt.init, local)
        iters = 0
        while True:
            if stmt.condition:
                if not _is_truthy(self._eval_expr(stmt.condition, local)):
                    break
            iters += 1
            if iters > MAX_LOOP_ITERATIONS:
                raise LSRuntimeError("For loop iteration limit exceeded")
            try:
                self._exec_block(stmt.body, local)
            except BreakSignal:
                break
            except ContinueSignal:
                pass
            if stmt.update:
                if isinstance(stmt.update, Assignment):
                    self._exec_assignment(stmt.update, local)
                else:
                    self._eval_expr(stmt.update, local)

    def _exec_do_while(self, stmt: DoWhileStmt, env: Environment):
        iters = 0
        while True:
            iters += 1
            if iters > MAX_LOOP_ITERATIONS:
                raise LSRuntimeError("Do-while loop iteration limit exceeded")
            try:
                self._exec_block(stmt.body, env)
            except BreakSignal:
                break
            except ContinueSignal:
                pass
            if not _is_truthy(self._eval_expr(stmt.condition, env)):
                break

    def _exec_block(self, stmts: list, env: Environment) -> Any:
        result = None
        for stmt in stmts:
            result = self._exec_stmt(stmt, env)
        return result

    # ── Expression evaluation ───────────────────────────────────────

    def _eval_expr(self, expr: Any, env: Environment) -> Any:
        if expr is None:
            return None

        self.ops += 1
        if self.ops > MAX_OPS:
            raise LSRuntimeError("Operation limit exceeded")

        if isinstance(expr, NumberLit):
            return expr.value
        if isinstance(expr, StringLit):
            return expr.value
        if isinstance(expr, BoolLit):
            return expr.value
        if isinstance(expr, NullLit):
            return None

        if isinstance(expr, Identifier):
            # Check local scope, then global, then game API constants
            val = env.get(expr.name)
            if val is not None:
                return val
            val = self.global_env.get(expr.name)
            if val is not None:
                return val
            # Game API constants (CELL_OBSTACLE, USE_SUCCESS, etc.)
            if expr.name in self.game_api:
                return self.game_api[expr.name]
            return None

        if isinstance(expr, ArrayLit):
            return [self._eval_expr(e, env) for e in expr.elements]

        if isinstance(expr, MapLit):
            result = {}
            for k_expr, v_expr in expr.pairs:
                k = self._eval_expr(k_expr, env)
                v = self._eval_expr(v_expr, env)
                result[k] = v
            return result

        if isinstance(expr, BinaryOp):
            return self._eval_binary(expr, env)

        if isinstance(expr, UnaryOp):
            operand = self._eval_expr(expr.operand, env)
            if expr.op == "-":
                return -_to_num(operand)
            if expr.op == "!":
                return not _is_truthy(operand)
            return operand

        if isinstance(expr, Ternary):
            cond = self._eval_expr(expr.condition, env)
            if _is_truthy(cond):
                return self._eval_expr(expr.true_val, env)
            return self._eval_expr(expr.false_val, env)

        if isinstance(expr, FunctionCall):
            return self._eval_function_call(expr, env)

        if isinstance(expr, MethodCall):
            return self._eval_method_call(expr, env)

        if isinstance(expr, Subscript):
            obj = self._eval_expr(expr.obj, env)
            idx = self._eval_expr(expr.index, env)
            return self._subscript_get(obj, idx)

        if isinstance(expr, PropertyAccess):
            obj = self._eval_expr(expr.obj, env)
            if isinstance(obj, dict):
                return obj.get(expr.prop)
            return None

        if isinstance(expr, Increment):
            return self._eval_increment(expr, env)

        raise LSRuntimeError(f"Unknown expression type: {type(expr).__name__}")

    def _eval_binary(self, expr: BinaryOp, env: Environment) -> Any:
        # Short-circuit for && and ||
        if expr.op == "&&":
            left = self._eval_expr(expr.left, env)
            if not _is_truthy(left):
                return left
            return self._eval_expr(expr.right, env)

        if expr.op == "||":
            left = self._eval_expr(expr.left, env)
            if _is_truthy(left):
                return left
            return self._eval_expr(expr.right, env)

        left = self._eval_expr(expr.left, env)
        right = self._eval_expr(expr.right, env)

        # String concatenation
        if expr.op == "+" and (isinstance(left, str) or isinstance(right, str)):
            return _to_str(left) + _to_str(right)

        # Equality (v4: strict, but null == null is true)
        if expr.op == "==":
            return _ls_equal(left, right)
        if expr.op == "!=":
            return not _ls_equal(left, right)

        # Numeric operations
        l = _to_num(left)
        r = _to_num(right)

        if expr.op == "+":
            return l + r
        if expr.op == "-":
            return l - r
        if expr.op == "*":
            return l * r
        if expr.op == "/":
            return l / r if r != 0 else 0
        if expr.op == "%":
            return l % r if r != 0 else 0
        if expr.op == "<":
            return l < r
        if expr.op == ">":
            return l > r
        if expr.op == "<=":
            return l <= r
        if expr.op == ">=":
            return l >= r

        raise LSRuntimeError(f"Unknown operator: {expr.op}")

    def _eval_function_call(self, expr: FunctionCall, env: Environment) -> Any:
        # Resolve the callee
        if isinstance(expr.callee, Identifier):
            name = expr.callee.name
        else:
            # Dynamic call (rare)
            name = None

        args = [self._eval_expr(a, env) for a in expr.args]

        # Priority: game API > builtins > user functions
        if name and name in self.game_api:
            fn = self.game_api[name]
            if callable(fn):
                return fn(*args)
            return fn  # constant

        if name and name in self._builtins:
            return self._builtins[name](*args)

        if name and name in self.functions:
            return self._call_user_function(name, args)

        # Unknown function — return null (lenient, like real LS runtime)
        return None

    def _eval_method_call(self, expr: MethodCall, env: Environment) -> Any:
        obj = self._eval_expr(expr.obj, env)
        args = [self._eval_expr(a, env) for a in expr.args]

        # String methods
        if isinstance(obj, str):
            if expr.method == "length":
                return len(obj)
            if expr.method == "replace":
                return obj.replace(str(args[0]), str(args[1])) if len(args) >= 2 else obj
            if expr.method == "indexOf":
                return obj.find(str(args[0])) if args else -1
            if expr.method == "substring":
                start = int(args[0]) if args else 0
                end = int(args[1]) if len(args) > 1 else len(obj)
                return obj[start:end]
            if expr.method == "split":
                return obj.split(str(args[0])) if args else [obj]

        # Array methods
        if isinstance(obj, list):
            if expr.method == "push":
                if args:
                    obj.append(args[0])
                return None
            if expr.method == "pop":
                return obj.pop() if obj else None
            if expr.method == "length":
                return len(obj)
            if expr.method == "indexOf":
                try:
                    return obj.index(args[0]) if args else -1
                except ValueError:
                    return -1

        return None

    def _call_user_function(self, name: str, args: list) -> Any:
        func = self.functions[name]
        local_env = Environment(self.global_env)

        # Bind parameters
        for i, param in enumerate(func.params):
            local_env.define(param, args[i] if i < len(args) else None)

        try:
            self._exec_block(func.body, local_env)
        except ReturnSignal as r:
            return r.value

        return None

    def _eval_increment(self, expr: Increment, env: Environment) -> Any:
        delta = 1 if expr.op == "++" else -1

        if isinstance(expr.target, Identifier):
            name = expr.target.name
            old_val = env.get(name)
            if old_val is None:
                old_val = self.global_env.get(name)
            old_num = _to_num(old_val)
            new_val = old_num + delta

            if not env.set(name, new_val):
                if not self.global_env.set(name, new_val):
                    env.define(name, new_val)

            return old_num if not expr.prefix else new_val

        if isinstance(expr.target, Subscript):
            obj = self._eval_expr(expr.target.obj, env)
            idx = self._eval_expr(expr.target.index, env)
            old_val = self._subscript_get(obj, idx)
            old_num = _to_num(old_val)
            new_val = old_num + delta

            if isinstance(obj, list):
                idx_int = int(idx)
                if 0 <= idx_int < len(obj):
                    obj[idx_int] = new_val
            elif isinstance(obj, dict):
                obj[idx] = new_val

            return old_num if not expr.prefix else new_val

        return 0

    def _subscript_get(self, obj: Any, idx: Any) -> Any:
        if isinstance(obj, list):
            i = int(idx)
            if 0 <= i < len(obj):
                return obj[i]
            return None
        if isinstance(obj, dict):
            return obj.get(idx)
        if isinstance(obj, str):
            i = int(idx)
            if 0 <= i < len(obj):
                return obj[i]
            return None
        return None


# ── Helper functions ────────────────────────────────────────────────

def _to_num(val: Any) -> int | float:
    """Coerce value to number (LeekScript v4 semantics)."""
    if val is None:
        return 0
    if isinstance(val, bool):
        return 1 if val else 0
    if isinstance(val, (int, float)):
        return val
    if isinstance(val, str):
        try:
            return int(val)
        except ValueError:
            try:
                return float(val)
            except ValueError:
                return 0
    return 0


def _to_str(val: Any) -> str:
    """Coerce value to string."""
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, float):
        if val == int(val):
            return str(int(val))
        return str(val)
    if isinstance(val, list):
        return "[" + ", ".join(_to_str(v) for v in val) + "]"
    if isinstance(val, dict):
        if not val:
            return "[:]"
        pairs = [f"{_to_str(k)} : {_to_str(v)}" for k, v in val.items()]
        return "[" + ", ".join(pairs) + "]"
    return str(val)


def _is_truthy(val: Any) -> bool:
    """LeekScript truthiness: null, false, 0, "", [] are falsy."""
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val != 0
    if isinstance(val, str):
        return len(val) > 0
    if isinstance(val, list):
        return len(val) > 0
    if isinstance(val, dict):
        return len(val) > 0
    return True


def _ls_equal(a: Any, b: Any) -> bool:
    """LeekScript v4 equality (strict-ish but null == null)."""
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    # Number comparison: int and float interchangeable
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return float(a) == float(b)
    return a == b

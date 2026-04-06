"""Oracle tests extracted from the Java LeekScript test suite.

These test cases come from the canonical LeekScript compiler tests at:
  tools/leek-wars-generator/leekscript/src/test/java/test/Test*.java

Only v4-compatible tests are included (code() and code_v4_() patterns).
Skipped: classes, lambdas (->), try/catch, bitwise, sets, intervals,
          code_v1_*(), @-references, disabled tests.

Convention: Java tests use `code("...").equals("...")` where the LS code
contains a `return` statement. Our interpreter's `run()` returns that value.
"""

import pytest

from leekwars_agent.pysim.leekscript.lexer import tokenize
from leekwars_agent.pysim.leekscript.parser import Parser
from leekwars_agent.pysim.leekscript.interpreter import Interpreter, _to_str


def run_ls(code: str) -> str:
    """Tokenize, parse, interpret LeekScript and return string repr of result."""
    tokens = tokenize(code)
    program = Parser(tokens).parse()
    interp = Interpreter()
    result = interp.run(program)
    return _to_str(result)


# ---------------------------------------------------------------------------
# Booleans  (from TestBoolean.java)
# ---------------------------------------------------------------------------
BOOLEAN_CASES = [
    ("return true", "true"),
    ("return false", "false"),
    ("return not true", "false"),
    ("return not false", "true"),
    ("return true xor true", "false"),
    ("return true xor false", "true"),
    ("return false xor true", "true"),
    ("return false xor false", "false"),
]


@pytest.mark.parametrize("code,expected", BOOLEAN_CASES, ids=[c[0] for c in BOOLEAN_CASES])
def test_booleans(code, expected):
    assert run_ls(code) == expected


# ---------------------------------------------------------------------------
# Numbers  (from TestNumber.java)
# ---------------------------------------------------------------------------
NUMBER_CASES = [
    ("return 0", "0"),
    ("return -1", "-1"),
    ("return -(-1)", "1"),
    ("return 0 + 5;", "5"),
    ("return 10 - 3;", "7"),
    ("return 5 * 5;", "25"),
    ("return 12 ** 2;", "144"),
    ("return 2 ** 5;", "32"),
    ("return -12 * 2;", "-24"),
    ("return -12 ** 2;", "144"),
    # null is NOT zero
    ("return null == 0;", "false"),
    ("return null < 0;", "false"),
    # increment / decrement
    ("var a = 2 return a++;", "2"),
    ("var a = 2; return ++a;", "3"),
    ("var a = 2 return a--;", "2"),
    ("var a = 2; return --a;", "1"),
    # compound assignment
    ("var a = 2 return a += 5;", "7"),
    ("var a = 2 return a -= 5;", "-3"),
    ("var a = 2 return a *= 5;", "10"),
    ("var a = 56 return a %= 17;", "5"),
    ("var a = 15 return a **= 2;", "225"),
    # precedence
    ("return 5 * 2 + 3 * 4;", "22"),
    ("var a = 10; a += 10 - 2 * 3; return a;", "14"),
]


@pytest.mark.parametrize("code,expected", NUMBER_CASES, ids=[c[0][:55] for c in NUMBER_CASES])
def test_numbers(code, expected):
    assert run_ls(code) == expected


# ---------------------------------------------------------------------------
# Operators  (from TestOperators.java)
# ---------------------------------------------------------------------------
OPERATOR_CASES = [
    # v4 strict equality (no type coercion)
    ("return null == null", "true"),
    ("return true == true", "true"),
    ("return false == true", "false"),
    ("return true == 'true'", "false"),       # v4: no coercion
    ("return false == 0", "false"),            # v4: no coercion
    ("return true == 1", "false"),             # v4: no coercion
    ("return 0 == 0", "true"),
    ("return 50 == 50", "true"),
    ("return 'Chaine1' == 'Chaine1'", "true"),
    ("return 'Chaine1' == 'Chaine2'", "false"),
    ("return [] == []", "true"),
    ("return [0, 1] == [0, 1]", "true"),
    ("return [0, 1] == [0]", "false"),
    # strict identity
    ("return 1 === 1.0", "true"),
    ("return null == [null]", "false"),
    # null coercion in comparison
    ("return null < 3", "true"),
    # boolean arithmetic
    ("return true + 1", "2"),
    ("return false + null", "0"),
    ("return true + null", "1"),
    # complex expression
    ("var a = 1; var result = -10 + (1- (a-1)); return result", "-9"),
    ("var sum = 1, ops = 10 return sum < ops * 0.95 || sum > ops", "true"),
]


@pytest.mark.parametrize("code,expected", OPERATOR_CASES, ids=[c[0][:60] for c in OPERATOR_CASES])
def test_operators(code, expected):
    assert run_ls(code) == expected


# ---------------------------------------------------------------------------
# Conditionals  (from TestIf.java)
# ---------------------------------------------------------------------------
IF_CASES = [
    ("if (true) { return 12 } else { return 5 }", "12"),
    ("if (false) { return 12 } else { return 5 }", "5"),
    ("if (true) return 12;", "12"),
    ("if (false) return 12;", "null"),
    ("if (false) { return 12 } return 5;", "5"),
    ("if (false) { return 'hello' }", "null"),
    # dangling else
    ("var test = 0; if(false) if(true) test = 3; else test = 1; return test;", "0"),
    # is / is not
    ("var a = 1; if(a is 1) return 2; else return 0", "2"),
    ("var a = 1; if(a is not 2) return 2; else return 0", "2"),
    ("var a = true; if(not a) return 2; else return 0", "0"),
    # null checks
    ("var cell = 1 if (cell != null) return 12", "12"),
    ("var cell = null if (cell != null) return 12 return 5", "5"),
    # truthiness of various types
    ("if (1212) { return 'ok' } else { return 5 }", '"ok"'),
    ("if (null) { return 12 } else { return 5 }", "5"),
    ("if (['str', true][0]) { return 12 } else { return 5 }", "12"),
    # ternary
    ("return true ? 5 : 12;", "5"),
    ("return false ? 5 : 12;", "12"),
    ("return '' ? 5 : 12;", "12"),
    ("return 'good' ? 5 : 12;", "5"),
    # nested ternary
    ("return true ? true ? 5 : 12 : 7;", "5"),
    ("return false ? true ? 5 : 12 : 7;", "7"),
    ("return (5 > 10) ? 'a' : (4 == 2 ** 2) ? 'yes' : 'no';", '"yes"'),
]


@pytest.mark.parametrize("code,expected", IF_CASES, ids=[c[0][:60] for c in IF_CASES])
def test_conditionals(code, expected):
    assert run_ls(code) == expected


# ---------------------------------------------------------------------------
# Loops  (from TestLoops.java)
# ---------------------------------------------------------------------------
LOOP_CASES = [
    # while basics
    ("var i = 0 while (i < 10) { i++ } return i;", "10"),
    ("var i = 0 var s = 0 while (i < 10) { s += i i++ } return s;", "45"),
    ("var i = 0 while (i < 100) { i++ if (i == 50) break } return i;", "50"),
    ("var i = 0 var a = 0 while (i < 10) { i++ if (i < 8) continue a++ } return a;", "3"),
    ("while (true) { break }", "null"),
    ("while (true) { return 12 }", "12"),
    # while with decrement as condition
    ("var n = 5 var a = [] while (n--) { push(a, 1) } return a;", "[1, 1, 1, 1, 1]"),
    ("var i = 10 while (i--); return i;", "-1"),
    ("var i = 10 while (--i); return i;", "0"),
    # do-while
    ("var i = 0 do { i++ } while (i < 10); return i;", "10"),
    ("var i = 0 do { i++ if (i == 50) break } while (i < 100); return i;", "50"),
    ("do { break } while (true);", "null"),
    ("var t = 0; do { t++; return t; } while (t < 5);", "1"),
    # for loops
    ("var s = 0 for (var i = 0; i < 5; i++) { s += i } return s;", "10"),
    ("var a = 0 for (var i = 0; i < 10; i++) { if (i < 5) { continue } a++ } return a;", "5"),
    ("var a = 0 for (var i = 0; i < 10; i++) { if (i > 5) { break } a++ } return a;", "6"),
    ("for(var i=0;i<3;i++){ return i; }", "0"),
    # nested for
    ("var s = 0 for (var i = 0; i < 10; ++i) { for (var j = 0; j < 10; ++j) { s++ }} return s;", "100"),
    # for-in (foreach)
    ("var s = 0 for (var v in [1, 2, 3, 4]) { s += v } return s;", "10"),
    ("var s = 0 for (var k : var v in [1, 2, 3, 4]) { s += k * v } return s;", "20"),
    ("var a = 0 var x = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9] for (var i in x) { if (i < 5) { continue } a++ } return a;", "5"),
    # mix for and while
    ("var s = 0 for (var i = 0; i < 10; i += 1) { var j = 10 while (j--) { s++ }} return s;", "100"),
    # double while
    ("var s = [] var i = 0 while (i < 2) { i++ var j = 0 while (j < 3) { j++ push(s, j) }} return s;", "[1, 2, 3, 1, 2, 3]"),
]


@pytest.mark.parametrize("code,expected", LOOP_CASES, ids=[c[0][:60] for c in LOOP_CASES])
def test_loops(code, expected):
    assert run_ls(code) == expected


# ---------------------------------------------------------------------------
# Arrays  (from TestArray.java)
# ---------------------------------------------------------------------------
ARRAY_CASES = [
    # construction
    ("return [];", "[]"),
    ("return [1, 2, 3];", "[1, 2, 3]"),
    ("return [true, false, true];", "[true, false, true]"),
    # concatenation
    ("return [1, 2, 3] + [4, 5, 6];", "[1, 2, 3, 4, 5, 6]"),
    ("return [] + 1 + 2 + 3;", "[1, 2, 3]"),
    ("return [1] + null;", "[1, null]"),
    ("return [1] + true;", "[1, true]"),
    # subscript
    ("return [1, 2, 3][1]", "2"),
    ("var a = [1, 2, 3] a[0] = 5 return a[0]", "5"),
    ("var a = [1, 2, 3] a[1] = 12 return a", "[1, 12, 3]"),
    ("var a = [12]; a[0]++; return a", "[13]"),
    # out of bounds
    ("return [][1]", "null"),
    ("return [1, 2, 3][100]", "null"),
    # negative index (v4)
    ("var a = [1, 2, 3, 4] return a[-1]", "4"),
    ("var a = [1, 2, 3, 4] a[-1] += 10 return a", "[1, 2, 3, 14]"),
    # null array access
    ("var a = null return a[1]", "null"),
    # empty array truthiness
    ("var a = [] return !a", "true"),
    # nested access
    ("var v = [['a', 'b'], 12] return v[0][0]", '"a"'),
    ("var v = [['a', 'b'], 12] v[0][0] = 5 return v", '[[5, "b"], 12]'),
    # count + push
    ("return count([1, 2, 3, 4, 5]);", "5"),
    ("var a = [] push(a, 1) push(a, 2) push(a, 3) return a;", "[1, 2, 3]"),
    # element operators
    ("var a = [5] a[0] += 1 return a;", "[6]"),
    ("var a = [5]; return ++a[0];", "6"),
    ("var a = [5] a[0] *= 10 return a;", "[50]"),
    ("var a = [5] a[0] **= 2 return a;", "[25]"),
    # clone
    ("var a = [1, 2, 3] var b = clone(a) push(b, 4) return [a, b]", "[[1, 2, 3], [1, 2, 3, 4]]"),
    # in operator (v4)
    ("return 1 in [1, 2];", "true"),
    ("return 3 in [1, 2];", "false"),
    ("return 1 in [];", "false"),
]


@pytest.mark.parametrize("code,expected", ARRAY_CASES, ids=[c[0][:60] for c in ARRAY_CASES])
def test_arrays(code, expected):
    assert run_ls(code) == expected


# ---------------------------------------------------------------------------
# Maps  (from TestMap.java)
# ---------------------------------------------------------------------------
MAP_CASES = [
    # construction
    ("return [:]", "[:]"),
    ("return [1: 1, 2: 2]", "[1 : 1, 2 : 2]"),
    ('return [1: 1, 2: \'a\']', '[1 : 1, 2 : "a"]'),
    # access
    ("var m = [1: 1] return m[1]", "1"),
    ("var m = ['salut': 12] return m['salut']", "12"),
    ("var m = ['salut': 'yolo'] return m['salut']", '"yolo"'),
    # mutation
    ("var m = [1: 2, 3: 4] m[5] = 6 return m", "[1 : 2, 3 : 4, 5 : 6]"),
    ("var m = [1: 2, 3: 4] m[3] = 6 return m", "[1 : 2, 3 : 6]"),
    # equality
    ("return ['a': 'b'] == ['a': 'b']", "true"),
    ("return ['a': 'b'] == [1: 1]", "false"),
    # truthiness
    ("return ![2: 2]", "false"),
    ("if ([2: 2]) { return 12 } else { return 5 }", "12"),
    # iteration
    ("var s = '' for (var v in [1:2,3:4]) { s += v } return s", '"24"'),
    ("var s = '' for (var k : var v in ['a':'b','c':'d','e':'f']) { s += v } return s", '"bdf"'),
    ("var s = '' for (var k : var v in [1:2]) { s += (k + ' ' + v) } return s", '"1 2"'),
    # increment on map element
    ("var m = [1: 2] m[1]++ return m", "[1 : 3]"),
    # map + (v4)
    ("return [:] + [:]", "[:]"),
    ("return [1 : 2] + [3 : 4]", "[1 : 2, 3 : 4]"),
    # mapKeys / mapValues (v4)
    ("return mapKeys([1: 2, 3: 4, 5: 6])", "[1, 3, 5]"),
    ("return mapValues([1: 2, 3: 4, 5: 6])", "[2, 4, 6]"),
    ("return mapIsEmpty([:])", "true"),
    ("return mapIsEmpty([2 : 8])", "false"),
]


@pytest.mark.parametrize("code,expected", MAP_CASES, ids=[c[0][:60] for c in MAP_CASES])
def test_maps(code, expected):
    assert run_ls(code) == expected


# ---------------------------------------------------------------------------
# Functions  (from TestFunction.java)
# ---------------------------------------------------------------------------
FUNCTION_CASES = [
    # basic function call
    ("var f = function(x) { var r = x ** 2 return r + 1 } return f(10)", "101"),
    # conditional return
    ("var f = function(x) { if (x < 10) {return true} else {return 12} } return [f(5), f(20)]",
     "[true, 12]"),
    # function truthiness
    ("var a = function() {} if (a) { return 12 } return null", "12"),
    # recursion - factorial
    ("var fact = function(x) { if (x == 1) { return 1 } else { return fact(x - 1) * x } } return fact(8);", "40320"),
    # recursion - fibonacci
    ("var fib = function(n) { if (n <= 1) { return n } else { return fib(n - 1) + fib(n - 2) } } return fib(25);", "75025"),
    # closure
    ("function te(a){ return function(){ return a**2; }; } return te(2)();", "4"),
    # nested closure
    ("function te(a){ return function(b){ return function(c){return a*b*c;}; }; } return te(2)(1)(2);", "4"),
    # capture loop variable
    ("var sum = 0 for (var i = 0; i < 10; ++i) { sum += (function() { return i })() } return sum", "45"),
    # modify argument (value semantics)
    ("function test(x) { x += 10 return x } return test(5)", "15"),
    # function returning array
    ("function test() { var r = [1, 2, 3] return (r); } return test()", "[1, 2, 3]"),
    # function stored in array
    ("var a = [function() { return 12 }] return a[0]()", "12"),
    # null argument
    ("function f(a) { return 12; } return f(null);", "12"),
    # variable shadowing built-in name
    ("var count = count([1, 2, 3]) return count;", "3"),
    # recursive with conditional
    ("function cellsInRange(i) { var areaInRange = []; if (i == 0) { return cellsInRange(10); } else { return areaInRange; } } var myRange = cellsInRange(0); return myRange", "[]"),
]


@pytest.mark.parametrize("code,expected", FUNCTION_CASES, ids=[c[0][:60] for c in FUNCTION_CASES])
def test_functions(code, expected):
    assert run_ls(code) == expected

# LeekScript Language Specification

> Reverse-engineered from the official Java compiler at `tools/leek-wars-generator/leekscript/`.
> No formal grammar (BNF/PEG/ANTLR) exists anywhere. This is the closest thing.

## Architecture

LeekScript is **compiled to Java bytecode**, not interpreted:
1. Lexer (`LexicalParser.java`) -> Token stream
2. Parser (`WordCompiler.java`) -> AST (expression tree, not a clean AST node hierarchy)
3. Code gen (`JavaWriter.java`) -> Java source (class `AI_XXXXX`)
4. In-memory Java compilation -> JVM bytecode
5. Sandboxed execution with ops counting + RAM limits

Current version: **4** (game uses v4; v1-v3 are legacy with different semantics).

## Lexer

### Token Types (from `TokenType.java`)

```
NUMBER, STRING, VAR_STRING (quoted strings), OPERATOR, END_INSTRUCTION (;),
PAR_LEFT, PAR_RIGHT, VIRG (comma), ACCOLADE_LEFT/RIGHT, BRACKET_LEFT/RIGHT,
DOUBLE_POINT (:), DOT, DOT_DOT (..), ARROW (=> or ->), LEMNISCATE (∞), PI (π),
END_OF_FILE

Keywords: VAR, GLOBAL, RETURN, CONSTRUCTOR, FINAL, FOR, STATIC, IF, WHILE, IN,
ABSTRACT, AWAIT, BREAK, CONTINUE, EXPORT, IMPORT, GOTO, SWITCH, SUPER, CLASS,
CATCH, EXTENDS, TRUE, FALSE, CONST, ENUM, EVAL, CHAR, FLOAT, CASE, DOUBLE,
BYTE, DO, TRY, TYPEOF, VOID, WITH, YIELD, AS, FINALLY, INTERFACE, LONG, LET,
NATIVE, NEW, PACKAGE, THIS, FUNCTION, IMPLEMENTS, INT, NOT, NULL, PRIVATE,
PROTECTED, PUBLIC, SHORT, ELSE, INCLUDE, THROW, THROWS, TRANSIENT, VOLATILE,
DEFAULT, SYNCHRONIZED
```

### Reserved Words

All versions: `and`, `as`, `break`, `continue`, `do`, `else`, `false`, `for`, `function`, `global`, `if`, `in`, `not`, `null`, `or`, `return`, `true`, `var`, `while`, `xor`

Added in v2: `class`, `constructor`, `extends`, `instanceof`, `new`, `private`, `protected`, `public`, `static`, `super`, `this`

Added in v3+: `abstract`, `await`, `byte`, `case`, `catch`, `char`, `const`, `default`, `double`, `enum`, `eval`, `export`, `final`, `finally`, `float`, `goto`, `implements`, `import`, `int`, `interface`, `let`, `long`, `native`, `package`, `short`, `switch`, `synchronized`, `throw`, `throws`, `transient`, `try`, `typeof`, `void`, `volatile`, `with`, `yield`

### Case Sensitivity

- v1-v2: **case-insensitive** keywords (`Null`, `NULL`, `null` all work)
- v3+: **case-sensitive** (`null` only, `Null` is a class reference)

### Comments

```leekscript
// Line comment
/* Block comment */
```

### Number Literals

- Integers: `42`, `0xFF` (hex), `0b1010` (binary)
- Reals: `3.14`, `1.5e10`
- Numeric separators: `1_000_000` (single underscore only, `__` is error)
- Special: `∞` (infinity), `π` (pi)

### String Literals

- Single or double quotes: `'hello'` or `"hello"`
- Escape sequences: `\\`, `\'`, `\"`

### Operators (lexer order)

```
:
&& &= &
|| |= |
++ += +
-- -= -
**= ** *= *
/= /  \= \
%= %
=== == =
!== != !
<<<= <<< <<= << <= <
>>>= >= >
^= ^
~ @
? \
=> ->
..
. (v2+ only)
```

Word operators: `and` (&&), `or` (||), `xor`, `not` (!), `instanceof` (v2+), `is`, `is not`, `in`, `as`

## Operator Precedence (highest to lowest)

| Prec | Operators | Assoc |
|------|-----------|-------|
| 17 | `[]` `()` (subscript, call) | L |
| 16 | `.` (member access) | L |
| 15 | `as` `++` `--` `@` (ref) unary `-` | - |
| 14 | `!` (not / non-null) `~` (bitwise not) | R |
| 13 | `new` | R |
| 12 | `**` (power) | R |
| 11 | `*` `/` `\` (integer div) `%` | L |
| 10 | `+` `-` | L |
| 9 | `<<` `>>` `>>>` | L |
| 8 | `<` `<=` `>` `>=` `instanceof` `in` | L |
| 7 | `==` `!=` `===` `!==` | L |
| 6 | `&` (bitwise and) | L |
| 5 | `^` (bitwise xor) | L |
| 4 | `\|` (bitwise or) | L |
| 3 | `&&` / `and` | L |
| 2 | `\|\|` / `or` | L |
| 1 | `?` `:` (ternary) | R |
| 0 | `=` `+=` `-=` `*=` `/=` `\=` `%=` `**=` `<<=` `>>=` `>>>=` `&=` `\|=` `^=` | R |

### Special Operators

- `\` = integer division (floor)
- `@` = pass-by-reference (deprecated in v2+)
- `!` as suffix = non-null assertion
- `is` / `is not` = aliases for `==` / `!=`
- `xor` = logical XOR

## Type System

### Primitive Types

| Type | Java backing | Notes |
|------|-------------|-------|
| `null` | null | Coerced to 0 in numeric context (v1-v3) |
| `boolean` | Boolean | `true`, `false` |
| `integer` | Long (64-bit) | |
| `real` | Double (64-bit) | |
| `string` | String | |

### Collection Types

| Type | Syntax | Notes |
|------|--------|-------|
| `Array<T>` | `[1, 2, 3]` | Dynamic, mixed-type |
| `Map<K,V>` | `[1: 'a', 2: 'b']` | Ordered map. Empty: `[:]` |
| `Set<T>` | `<1, 2, 3>` | Unique values. Empty: `<>` |
| `Interval` | `[1..10]` | Integer or real range |
| `Object` | `{a: 1, b: 2}` | Anonymous object (v2+) |

### Type Annotations (optional, zero runtime cost)

```leekscript
var x: integer = 42
function add(a: integer, b: integer): integer { return a + b }
Array<integer> nums = [1, 2, 3]
Map<string, integer> scores = ['a': 1, 'b': 2]
Function<integer, integer => string> f = ...
```

Compound types: `integer | null`, `string?` (= `string | null`)

Special types: `any`, `void`

### Equality Semantics

**v1-v3**: Loose equality (like JS). `0 == false` is true, `1 == '1'` is true.
**v4**: Strict equality by default. `0 == false` is false, `1 == '1'` is false. Only same-type values are equal.

`===` / `!==` always strict (all versions). Deprecated in v4 (`==` is already strict).

## Statements

### Variable Declaration

```leekscript
var a = 5
var a, b, c = 3          // a=null, b=null, c=3
var a = 1, b = 2, c = 3  // multi-declare with init
```

### Global Declaration

```leekscript
global x = 10             // file-scoped, shared across includes
global a, b               // multi-declare
```

Globals can only be declared in the **main block** (not inside functions/loops).

### Include

```leekscript
include("module.leek")    // Only in main block. Must be .leek extension.
```

### If / Else If / Else

```leekscript
if (condition) { ... }
else if (condition) { ... }
else { ... }

// Without braces (single statement):
if (condition) statement;
if (condition) statement
```

### While

```leekscript
while (condition) { ... }
while (condition) statement;  // without braces
```

### Do-While

```leekscript
do { ... } while (condition);
do { ... } while (condition)  // semicolon optional
```

### For (C-style)

```leekscript
for (var i = 0; i < 10; i++) { ... }
for (i = 0; i < 10; i++) { ... }   // existing variable
for (var i = 0; i < 10; i++) statement;  // without braces
```

### For-each (value)

```leekscript
for (var x in array) { ... }
for (x in array) { ... }        // existing variable
```

### For-each (key:value)

```leekscript
for (var k : var v in map) { ... }
for (k : v in map) { ... }
```

### Break / Continue

```leekscript
break;
continue;
```

Only valid inside loops.

### Return

```leekscript
return;
return expression;
return? expression;  // optional return (?)
```

## Functions

### Named Functions

```leekscript
function add(a, b) {
    return a + b
}
```

Functions can only be declared at the **main block level** (not nested in other functions/blocks). They are hoisted (available before their declaration due to two-pass compilation).

### Anonymous Functions

```leekscript
var f = function(x) { return x * 2 }
```

### Lambda / Arrow Functions

```leekscript
var f = x -> x * 2          // single param, expression body
var f = x => x * 2          // => also works
var f = x, y -> x + y       // multiple params
var f = -> 12                // no params
var f = (x) -> x * 2        // parenthesized param
var f = (x, y) => { ... }   // block body
var f = (x) => integer { return x }  // with return type
```

### Default Parameters (v2+, in class methods)

```leekscript
class A {
    constructor(x, y = 2) { ... }
    m(a = 5) { ... }
}
```

### Pass-by-Reference (v1 only, deprecated)

```leekscript
function f(@a) { a += 2 }  // @ prefix = reference
var x = 10
f(x)  // x is now 12
```

## Classes (v2+)

```leekscript
class Animal {
    public name = ''
    private age = 0
    
    constructor(name, age) {
        this.name = name
        this.age = age
    }
    
    public getName() {
        return this.name
    }
    
    public static create(name) {
        return new Animal(name, 0)
    }
    
    public final id = 0  // immutable field
    
    public string() {     // toString override, must return string
        return this.name
    }
}

class Dog extends Animal {
    constructor(name) {
        super(name, 0)
    }
}
```

### Access Modifiers

- `public` (default)
- `private`
- `protected`

### Class Features

- `static` fields and methods
- `final` fields
- `constructor` (multiple overloads by param count, v2-v3; v4 forbids ambiguous overloads)
- `extends` (single inheritance)
- `super` keyword
- `this` keyword
- `class.name` returns class name as string
- `instanceof` operator
- Classes are values: `return A` returns `<class A>`
- Classes can only be declared at main block level

## Collections Detail

### Arrays

```leekscript
[]
[1, 2, 3]
[1 2 3]           // commas optional (space-separated)
Array()            // v3+ constructor
new Array()        // v3+ constructor

// Subscript access
a[0]
a[1:3]            // v4: slicing [start:end]
a[::2]            // v4: slicing with stride [::stride]
a[1:5:2]          // v4: [start:end:stride]

// Operators
[1, 2] + [3, 4]  // concatenation: [1, 2, 3, 4]
[1] + 2           // append: [1, 2]
```

### Maps

```leekscript
[:]                // empty map
[1: 'a', 2: 'b']  // map literal
['key': value]

map[key]           // access
map[key] = value   // set
```

### Sets (v4)

```leekscript
<>                 // empty set
<1, 2, 3>         // set literal
<(1 > 2), (1 < 2)>  // expressions need parens to disambiguate < >
```

### Intervals (v4)

```leekscript
[1..10]            // closed integer interval
[1.0..2.0]         // real interval
[-10..-2]
[1 * 5 .. 8 + 5]  // expression bounds

// Unbounded intervals
]-∞..5]            // ] = open, [ = closed
[1..∞[
]-∞..∞[
]..[               // fully unbounded
]..1]              // left-unbounded
[1..[              // right-unbounded
```

### Objects (v2+)

```leekscript
{}                     // empty
{a: 12, b: 5}         // with values
{a: 12 b: 5}          // commas optional
{a: 12 - 2 yo: -6}    // expressions as values

obj.field              // dot access
obj['field']           // bracket access
```

## Expression Parsing Details

The expression parser uses a precedence-climbing approach (Pratt-like). Key quirks:

1. **Semicolons are optional** between statements (like JS ASI, but simpler -- the parser just keeps trying)
2. **Commas in arrays/objects are optional** -- `[1 2 3]` and `{a: 1 b: 2}` are valid
3. **`!` is overloaded**: prefix = logical not, suffix = non-null assertion
4. **`>` is context-dependent**: in sets `<1, 2>`, `>` is the closing delimiter, not greater-than
5. **Lambda detection** uses lookahead: parser checks for `TOKEN =>` or `TOKEN,` patterns to distinguish lambdas from parenthesized expressions
6. **`in` operator** works both as for-each keyword and as containment check (`x in array`)

## Version Differences Summary

| Feature | v1 | v2 | v3 | v4 |
|---------|----|----|----|----|
| Case-insensitive keywords | Yes | Yes | No | No |
| `@` references | Yes | Deprecated (warning) | Deprecated | Deprecated |
| Classes | No | Yes | Yes | Yes |
| `new` keyword | No | Yes | Yes | Yes |
| Loose `==` | Yes | Yes | Yes | **Strict** |
| `===` | Exists | Exists | Exists | Deprecated |
| Sets `<>` | No | No | No | Yes |
| Intervals `[..]` | Partial | Partial | Partial | Full |
| Array slicing `[:]` | No | No | No | Yes |
| Redefine builtins | Yes | Yes | Yes | **Error** |
| `final` | No | No | Yes | Yes |
| `const`, `let`, etc. | No | No | Reserved | Reserved |
| Comma-optional arrays | Yes | Yes | Yes | Yes |
| `.` as member access | No | Yes | Yes | Yes |
| `null == 0` | true | true | true | **false** |

## Runtime Constraints

- **Operations limit**: each instruction costs ops; exceeding = `TOO_MUCH_OPERATIONS` (turn ends)
- **RAM limit**: arrays/maps/objects tracked; exceeding = `OUT_OF_MEMORY`
- **Stack depth**: `STACKOVERFLOW` on deep recursion
- **Sandboxed**: no file I/O, no network, no reflection, no threads

## Built-in Functions (partial list from tests)

### Math
`abs`, `sqrt`, `cos`, `sin`, `tan`, `acos`, `asin`, `atan`, `atan2`, `ceil`, `floor`, `round`, `min`, `max`, `pow`, `log`, `log2`, `log10`, `exp`, `random`, `randInt`, `toInt`, `toReal`

### Array
`push`, `pop`, `count`, `arrayMap`, `arrayFilter`, `arrayFoldLeft`, `arrayFoldRight`, `arraySort`, `arrayShuffle`, `arrayReverse`, `arraySlice`, `arrayConcat`, `arrayFlatten`, `arrayUnique`, `arraySearch`, `arrayContains`, `arrayRemove`, `arrayRemoveAll`, `arrayRemoveElement`, `arrayMin`, `arrayMax`, `arraySum`, `arrayAverage`, `arraySome`, `arrayEvery`, `arrayFill`, `arrayInsert`, `join`, `subArray`, `inArray`, `unshift`, `isEmpty`, `assocSort`, `keySort`

### Map
`mapMap`, `mapRemove`, `mapSearch`, `mapContains`, `mapContainsKey`, `mapMin`, `mapMax`, `mapSum`, `mapAverage`, `assocReverse`

### Set
`setPut`, `setRemove`

### Interval
`intervalMin`, `intervalMax`, `intervalIsEmpty`, `intervalIsBounded`, `intervalIsLeftBounded`, `intervalIsRightBounded`, `intervalAverage`, `intervalIntersection`

### String
`charAt`, `length`, `substring`, `replace`, `indexOf`, `split`, `toLower`, `toUpper`, `startsWith`, `endsWith`, `contains`, `string` (toString), `codePointAt`, `number` (parse)

### Type
`typeOf`, `getColor`, `getRed`, `getGreen`, `getBlue`, `color` (v1-v3 only, removed v4)

### Debug (FREE, no TP cost)
`debug`, `debugW`, `debugE`

### JSON
`jsonEncode`, `jsonDecode`

## No Formal Grammar Exists

- **No BNF/PEG/ANTLR file** in either the Java repo or the C++ leekscript-next repo
- The parser is hand-written recursive descent (in Java: `WordCompiler.java`)
- The lexer is hand-written character-by-character (`LexicalParser.java`)
- No external LeekScript parser/interpreter exists outside the game
- The `leekscript-next` repo (C++/LLVM) is a separate implementation with different semantics, not used in production

## Source Files Reference

| File | Purpose |
|------|---------|
| `leekscript/compiler/LexicalParser.java` | Lexer (tokenizer) |
| `leekscript/compiler/TokenType.java` | Token type enum |
| `leekscript/compiler/WordCompiler.java` | Parser (two-pass: declarations then body) |
| `leekscript/compiler/expression/Operators.java` | Operator IDs + precedence table |
| `leekscript/compiler/expression/LeekExpression.java` | Expression AST node |
| `leekscript/compiler/bloc/*.java` | Statement blocks (if, while, for, foreach, etc.) |
| `leekscript/compiler/instruction/*.java` | Instructions (var decl, return, break, etc.) |
| `leekscript/compiler/JavaWriter.java` | Code generator (LS -> Java) |
| `leekscript/runner/AI.java` | Base class for generated AIs |
| `leekscript/runner/LeekOperations.java` | Runtime operations (clone, equals, etc.) |
| `leekscript/runner/values/*.java` | Runtime value types |
| `leekscript/common/Error.java` | All 150 error types |
| `src/test/java/test/*.java` | Comprehensive test suite (~3000+ test cases) |

## Key Findings for Python Interpreter

1. **No formal grammar exists.** Must reverse-engineer from `LexicalParser.java` + `WordCompiler.java`.
2. **Operator precedence** is fully defined in `Operators.getPriority()` -- 18 levels.
3. **Semicolons are optional** -- statements end at `}`, `;`, or EOF.
4. **Commas are optional** in arrays and objects.
5. **Two-pass compilation**: first pass collects includes, globals, function names, class names. Second pass compiles body. Functions are hoisted.
6. **Version-dependent semantics**: v4 changed equality, removed loose coercion, forbids builtin redefinition. We use v4.
7. **The expression parser** is the most complex part: handles lambdas, ternary, array slicing, set delimiters, all via lookahead heuristics.
8. **~3000+ test cases** in `src/test/java/test/` provide an executable specification. These are the best reference for edge cases.
9. **`leekscript-next`** (C++/LLVM) is a separate abandoned experiment, not the production compiler.
10. **The `~~` operator** mentioned in leekscript-next README does NOT exist in the Java production compiler.

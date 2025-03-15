# Comments

Comments start with `#` and run until the end of the line.
They are ignored by the parser.

### Pattern
```
comment = "#" "[^\n]"*
```

# Atoms

Value literals and symbol names.

### Pattern
```
atom = null | boolean | integer | float | string | name
```

## `null`

Literal for the `null` value in evaluation.

### Pattern
```
null = "null"
```

## Booleans

Literals for the boolean values `true` and `false` in evaluation.

### Pattern
```
boolean = "true" | "false"
```

## Integers

Integer literals are strings of numbers that optionally start with a `-` to denote negative value.
Integer literals that fall outside the range [-(2^63), (2^63)-1] will result in a syntax error.
These will map to `int` values during evaluation.

### Pattern
```
integer = "-"? "[0-9]"+
```

## Float

Floats are strings of numbers that optionally start with a `-` to denote negative value.
They have a `.`-separated fractional part and/or a `e`-separated exponent part which also has an optional `-` to denote negative exponential value.
These will map to `float` values during evaluation.

### Pattern
```
fractional = "." "[0-9]"*
exponent = "e" "-"? "[0-9]"+
float = integer (fractional | fractional exponent | exponent)
```

## String

Strings are delimited with `"` and can contain any printable ASCII character.
The `\` character is used to denote as escape sequence which can be `\n`, `\t`, `\"`, or `\\`,
which correspond to the newline, tab, `"`, and character `\`, respectively.
Or it can be a hex-coded escape character `\x{hex}{hex}` which corresponds to the respective ASCII character by value.
These will map to `str` values during evaluation.

### Pattern
```
escape = "\\" | "\n" | "\t" | '\"' | "\x[0-7][0-9A-F]"
ascii_printable = "[\x20-\xFE]"
string_char = escape | ascii_printable
string = '"' string_char* '"'
```

## Names

Names are a string of printable characters that don't contain `(`, `)`, `{`, `}`, or `#` and
can't be parsed as a number;
can't be parsed as a string;
and aren't one of the keywords `null`, `true`, or `false`.

Convention says that names *should* follow the pattern `[a-zA-Z_][a-zA-Z0-9_]*` to prevent confusion.

### Pattern
```
name_char = !"[(){}#]" ascii_printable
name = !null !boolean !integer !float !string !comment name_char+
```

# Expressions

Expressions are the only syntactic element in the language.
Expressions are defined using `list`s.
This is typical of LISPs.
Atypical is the fact this language has three different ways to defined lines lexically:
parenthesized lists, significant whitespace lists, and curly bracket lists.
These all translated into `list` objects after parsing, so they are ultimately equivalent.
Choose the one that is the most readable in any given situation.

### Pattern
```
expr = paren_expr | ws_expr | curly_expr
value = expr | atom
```

## Parenthesized Lists

These lists start with `(` and end with `)`.
Elements of the list are separated with whitespace.
All whitespace between the start and end terminal character is ignored.
This is the common representation that the other two list syntaxes are converted to in the parser.
This common representation is also the representation that macros will operate on.
It should be familiar if you've ever written LISP.

Additionally, the only spelling of the empty list syntactically is using parentheses: `()`.

```
> (a b c)
(a b c)

> (
>     a b c
> )
(a b c)

> (a
> b                               c)
(a b c)

> (
>     a
>     b
>     c
> )
(a b c)
```

### Pattern
```
paren_expr_value = atom | paren_expr
paren_expr = "(" paren_expr_value+ ")"
```

## Significant Whitespace Lists

Most people who've written LISP know how tedious and unreadable the parentheses make everything.
This syntax allows the user to omit parens and use significant whitespace to implicitly start and end lists.

In this mode, lists start at the beginning of a line and finish at the end of the line if the next line is at the same level of indentation.

```
> a b c
> d e f
(a b c) (d e f)
```

If the next line increases the indentation, the list is *not* ended until a matching de-dentation is seen.

```
> a
>    b c
>    d e
>        f
>    g
(a (b c) (d e (f)) (g))
```

### Pattern
```
ws_expr = ws_line_list | ws_block_list
ws_line_list = value+ newline
ws_block_list = value+ indent value+ dedent
```

## Curly Bracket Lists

Curry bracket lists behave like something between whitespace and parenthesized lists.
Whitespace inside curly brackets is significant and generates INDENT, DEDENT, and NEWLINE tokens which map to list beginning and ends,
but like parenthesized lists, you can only close a curly bracket list with a `}`.

Effectively what this means is that the current indentation tracking it reset back to 0 after a curly bracket list starts.
Indentation tracking within the curly bracket cannot affect the indentation tracking of the enclosing list.

Additionally, all curly bracket lists are implicitly constructed into `block`s,
giving them a new variable scope and expression sequencing.

```
> {a b c}
(block (a b c))

> {
>   a b c
>   d e f
> }
(block (a b c) (d e f))

> if (> a b) {
>     print "max is a" a
> } else {
>     print "max is b" b
> }
(if (> a b) (block (print "max is a" a)) else (block (print "max is b" b)))
```

### Pattern
```
curly_expr = "{" value+ "}"
```

# Modules

Modules are single files.
Each module runs as if it were the body of a `block`.

```
var a 56
print a
print (+ a 7)
if (> a 20) {
    print a
}
```

### Pattern
```
module = expr*
```

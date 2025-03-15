# Special Forms

These look like regular expressions, but are evaluated differently, and thus require special support.
Mostly this deals with handling variables and variable scopes,
control flow functions that couldn't be written as normal functions,
and defining code.

## `var` and `const`

Adds a name to the current variable scope.
`var` is for variables that can later be `set`.
`const` variables cannot later be `set`.

The first argument is the name to add to the variable scope and is thus not evaluated.
The second argument is the value and is evaluated.

```
var a 1  # declares variable `a` that can later be set
const a 1  # declares variable `a` that *can't* be set
```

## `set`

Changes the value of the variable in the last scope that variable was seen.

The first argument is the variable name and is not evaluated.
The second argument is the new value and is evaluated.

```
var a 0
set a 1
```

## `del`

Removes a name from the current variable scope.
No-op if the name does not exist in the current scope.

The first argument is the variable name and is not evaluated.

```
var a 0
del a
```

## `block`

Introduces a new variable scope and provides sequencing.
This function can take any number of expressions and simply evaluates them, tossing the return value.
The result of the last expression, however, becomes the result of the `block` expression.

When `block`s end, all variables in the variable scope are automatically deleted.

```
block
    var a 1
    print a
    set a (+ a 1)
    print a
```

## `if` and `else`

The first argument, the condition, is evaluated.
If the condition is true, the second argument is evaluated and the result becomes the result of the `if` expression.
If the condition is false the fourth argument is evaluated and the result becomes the result of the `if` expression.
The third argument must the name `else`.

The `else` clause it optional.
In this case don't provide third argument (`else`) or the fourth argument.
In this case, if the condition is false the result of the `if` expression becomes the value `null`.

## `loop`

## `break` and `continue`

## `def`

## `defmacro`

TBD

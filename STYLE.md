Style Guide for the Core Framework
==================================

1. 72 characters line limit
-------------------------

### Rule
Lines of source code logic and comments should not exceed 72 characters.

### Justification
* Narrow code is easier to read

* Shorter lines encourage shorter identifier names (e.g. varibles,
  method names, etc.)

* Text editors can be used to vertically split more legible code 
  windows when lines are shorter. This enhances a developer's ability to
  understand the code they are working on.

### Exceptions
Occasionally, long lines of text need to be put in source code simply
because breaking those lines would be problematic. A typical example
would be a URL that exceeds the 72 character boundry. In those cases,
the text is free to break this rule.

### Tags
\#whitespace


2. Breaking lines
------------------

### Rule
To fall within the 72 character limit, long source code lines must
sometimes be broken.  There are specifice ways these should be broken.

### Examples

#### Method and function signatures
When a function signature exceeds the 72 character limit, perhaps due to
a long list of parameters, the parameters should be broken out like so:

    def myfunction(
        long, list, of, arguments, which, 
        exceed, the, limit, on, line, length
    ):
        ...

When the function is a method, the `self` argument should be placed on
the same line as the function name:

    def mymethod(self,
        long, list, of, arguments, which, 
        exceed, the, limit, on, line, length
    ):
        ...

The `column -t` commmand can be used to align the arguments if it
improves readability:

    def mymethod(self,
        long,    list,  of,     arguments,  which,
        exceed,  the,   limit,  on,         line,   length
    ):

#### Oversized lists, tuple, dicts, etc.
Oversize container assignments can be written as such:
    
    # List
    ls = [
        1,    2,    3,    ...
        100,  101,  102,  ...
    ]

    # Tuple
    tup = (
        1,    2,    3,    ...
        100,  101,  102,  ...
    )

    # dict
    d = {
        'key1': 'value1', 'key2': 'value2',
        'key3': 'value3', 'key4': 'value4',
    }

    # Strings
    s = (
        'Hello, '
        'world'
    )
     

### Justification
Breaking long source code lines in a uniform way improves readability.

### Exceptions
None

### Tags
\#whitespace #formatting


3. Multiple empty lines
----------------------------------------------

### Rule
Never have more than one empty line in source code file.

### Justification
All space in source code file is valuable. Don't waste verticle space by
having more than one empty line. A single empty line, however, can aid
in readability.

### Examples
Bad:

    a = b


    b = c
Good:

    a = b

    b = c
    
### Exceptions
None

### Tags
\#whitespace #formatting

4. Sort import lines
----------------------------------------------

### Rule
Sort the `import` lines at the top of modules alphabetically.

### Justification
Keeping the `import` lines sorted alphabetically makes it easier to
detect duplicate imports that may have been accedently introduced into
the source code.

### Examples
Bad:
    
    import re
    import decimal
    from dbg import B, PM

Good:

    from dbg import B, PM
    import decimal
    import re
    
### Exceptions
Sometimes an `import` line will need to stick out somehow, such as in
the the idiom that models the ORM entity classes:

    import apriori; apriori.model()

This doesn't need to be a part of the sorted `import` lines.

Also, conditionally `import`ed modules don't need to be sorted with the
other `import` lines.

### Implementation tips
You can sort the lines by filtering them through the `sort` command. To
sort them and ensure that all duplicates have been removed, use the `-u`
flag.

### Tags
\#whitespace #formatting

<!-- 

// CONVENTIONS
Create new objects within collections using methods with the name of the
object:

    rs = rows()
    assert rs.count == 0

    r1 = rows.row()
    assert rs.count == 1
    assert rs.first is r1

// TODO
@property getters and setters should have no prefix:
    
    @property
    def children
        ...

getter and setter methods should be prefixed with get and set:

    def getchildren(self, recursive)
        ...

    def setchildren(self, v)
        ...

generators shoud be prefixed with 'gen'

    def genchildren(self, recursive):
        ...

@property prefixes such as 'is' for booleans, 'was', and 'do'.

Put consequent block on newline (if cond:\n ...)

In general, import modules instead of module objects:
    
    import mymod

    # dont do this
    from mymod import *
    from mymod import myfunc


Varible names

    varible names should strive to be easily recognizable abbreviations
    of the object:
        
        cc = creditcard()

    The standard varible name for an object should be documented in the
    class's docstring. When there are more than one varibale of the same
    type, the second one should end in 1, the third in 2 and so on.

        cc = creditcard()
        cc1 = creditcard()
        cc2 = creditcard()

    The 0 is implicit in the first cc.

Method names

    Method names should strive to be one word. Underscores are
    prohibited except in conventional circumstances. Method names should
    be lowercase except in very unusual cases.

Class names

    Class names should strive to be one word. Underscores are
    prohibited except in conventional circumstances. They should
    be lowercase except in when they are exception classes in which case
    they should be StudlyCase.



Initialize primatives with objects instead of operators

    s = str()
    ls = list()
    d = dict()

Discuss uses of TODO, NOTE, XXX and bomb-comments.

Discuss housekeeping in git logs

Discuss performance metrics in git logs

Discuss prefering non-negated conditional:

    Good:
        if x:
            ...
        else:
            ...

    Bad 
        if not X
            ...
        else:
            ...
Discuss 'On branch <branch-name>' in git logs

Use x as default list comprension variable
    
    [x for x in ls if x.prop = 'value']

Discuss naming constants

Discuss the importance of keeping the repo small and its file structure
flat.

When testing Constants and object references, be sure to use the `is`
operator, even though the quality operator (`==`) works::

    if x is True:
        ...

    If x is None:
        ...

    if obj1 is obj2:
        ...

Abbreviation glossory

    index: ix
    counters in loops: i, j, k, etc.

Common method names:

    clear: Clears the state of an object or the collected data in a
    collection object

    demand: Raise an exception if the state of an object is invalid.
-->

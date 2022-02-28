Create new objects within collections using methods with the name of the
object:

    rs = rows()
    assert rs.count == 0

    r1 = rows.row()
    assert rs.count == 1
    assert rs.first is r1

Blocks that overflow 72 characters:
    
    def f(self,
        ..., ...
    ):

    ls = [x 
        for x in ...
    ]

    f(
        a, b, ...
    }
     
Sort imports alphabetically

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
    callables: f, callable
    value: v
    handler: hnd
    index: ix
    counters in loops: i, j, k, etc.

Common method names:

    clear: Clears the state of an object or the collected data in a
    collection object

    demand: Raise an exception if the state of an object is invalid.

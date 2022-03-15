Style Guide for the Core Framework
==================================

1. 72 characters line limit
-------------------------

### Rule
Lines of source code logic and comments should not exceed 72 characters.

### Justification
* Narrow code is easier to read

* Shorter lines encourage shorter identifier names (e.g. variables,
  method names, etc.)

* Text editors can be used to vertically split more legible code 
  windows when lines are shorter. This enhances a developer's ability to
  understand the code they are working on.

### Exceptions
Occasionally, long lines of text need to be put in source code simply
because breaking those lines would be problematic. A typical example
would be a URL that exceeds the 72 character boundary. In those cases,
the text is free to break this rule.

### Implementation tips
In Vim the 'textwidth' variable can be set in your .vimrc to control the
line width:

    set tw=72 

Also in Vim, if you have some comments that you want to format to be
within the 72 character limit, you can select the block of text and type
`gq`. This will reformat the comments to be within the 72 limit (if you
use the `tw` command above) and it will also do the right thing with
regards to comment tokens.

### Tags
\#whitespace


2. Breaking lines
------------------

### Rule
To fall within the 72 character limit, long source code lines must
sometimes be broken.  There are specific ways these should be broken.

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

The `column -t` command can be used to align the arguments if it
improves readability:

    def mymethod(self,
        long,    list,  of,     arguments,  which,
        exceed,  the,   limit,  on,         line,   length
    ):

#### Oversize lists, tuple, dicts, etc.
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
All space in source code file is valuable. Don't waste vertical space by
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
detect duplicate imports that may have been accidental introduced into
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

5. Naming variables
-------------------

### Rule
Varible names

    * should be all lowercase 
    * should be easy to remember abbreviations when possible
    * should be document in their class's docstring when they are used
      as object references
    * if not abbreviated, should be composed of a single word if humanly
      possible
    * should be in *scriptiocontinua* case when they are compound words
    * should not contain type information (such as in Hungarian
      notation)
    * Multiple uses of a variable name should end with 1, then 2,
      etc.

### Justification
The most important attributes of variable names is the ability to easily
type, read and remember them. Short, one word or abbreviated names are
easiest to use. Being free from having to consider uppercase
characters and underscores further contribute to ease of use. Type
information, such as in Hungarian notation adds unnessary clutter when
when methods are discrete, well written and properly documented. Using
*scriptiocontinua* case has the added benefit of encouraging single word
variables since compound variables written in *scriptiocontinua* are
a little difficult to read. Standard abbreviations also aid in
usability. Documenting the abbreviation in the class or an abbreviation
glossary has obvious benefits for standardization.

### Examples

    # Using a non-abbreviated variable
    name = usr.name

    # Using ls as a standard abbreviation for "list"
    ls = list()

    # If we can't use a single word, use *scriptiocontinua*
    firstname = per.firstname
    lastname = per.lastname

    # Note that this is an encourgement to find synonyms that are
    # single words:
    forname = per.firstname
    surname = per.lastname

    # Note that in this method, Hungarian notation would be surpurflous
    def getfullname(self, per):
        """ Return the full name of the `per` as a str.

        :param per person.person: The preson object from which to return
        the full name.
        """
        return per.forname + ' ' + per.surname

    # Here is how to document a standard abbreviation in a class's
    # docstring
    class persons:
        """ Represents a collection of real-life persons.

        :abbr: pers peeps
        """

    # Now we know what the standard varible name for `persons` is
    pers = persons()

    # or alternatively
    peeps = persons()

    # Multiple uses
    pers = persons()  # There is sort of an implied 0 suffix here
    pers1 = persons()
    pers2 = persons()

### Exceptions
Occasionally, to reflect another standard, it's permissable to use
underscores to seperate words. For example, the HTTP header
`Content-Type` should have a varibable name `content_type` because the
underscore symbolize the hyphen in the original standard. Additionally,
it is convential to uppercase SQL keywords, so the following may be
useful:

    SELECT  =  '*'
    FROM    =  'mytable'
    WHERE   =  'a=b'

### Implementation tips
None

### Tags
\#naming #variables

6. Naming @property methods
---------------------------

### Rule
Property methods 

    * should be all lowercase, 
    * should not include prefixes such as 'get' and 'set'
    * should be composed of a single word if humanly possible
    * should be implemented using the @property decorator

The setter property use `v` as the value parameter:

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, v):
        self._size = v

### Justification
Property methods are a nice feature of modern object-oriented
programming that clearly denote the attributes of an object.

    t = toy()
    t.color = 'blue'

'get' and 'set' prefixes add unnecessary clutter to property that are
created using the @property decorator. Single word properties that are
all lowercase are easier to remember, type and read. Methods that start
with prefixes such as 'get' and 'set' are difficult to type and
remember.

### Exceptions
Occasionally, uppercase characters can imply certain notions. SQL is
conventionally uppercase, so you could do the following.

    stmt = sql.statement()
    stmt.SELECT = '*'
    stmt.FROM = 'mytable'

The `SELECT` and `FROM` properties are uppercased to imply they refer to
the SQL keywords. However, it would probably be better to lowercase
these to make them easier to type and less jarring to read.

Also, occasionally compound words can't be avoided, though every effort
should be made to do so. For example, the `www.request` object currently
has a `content_type` property. This corresponds to the `Content-Type`
HTTP header. That header is a standard so it only makes sense to include
both words (the underscore symbolizes the hyphen).

Properties should be implemented as methods when arguments are required.
Usually, there should be an actual property for the default invocation:

    @property
    def children(self):
        return self.getchildren()

    def getchildren(self, recursive=False):
        ...

The 'is', 'does', 'has', prefix should be added to Boolean proprieties if
it enhances readability:
    
    if world.isflat:
        print('Nyoo my God')

    # 'is' or 'does' does not enhance readability here
    if file.exist:
        ...
    
### Implementation tips
None

### Tags
\#naming #property

7. Generators vs getters and @property methods.
------------------------------------------------

### Rule
@property methods and getter methods should not return generator
objects. If a generator is desired, a separate method prefixed with
'gen' should be written.

### Example
In the dom.element class, we see three methods to get an element's
child nodes.

    @property
    def children(self):
        ...

    def getchildren(self, recursive=False):
        ...

    def genchildren(self, recursive=False):
        ...

Here, we have the option of getting the child nodes through a simple
property and also through a getter method (if we want to get them
recursively). A third option, `genchildren` is presented if we want a
generator.

### Justification
Sometimes we want a generator and sometimes we want the actual
collection object return. In the example section above, we may want to
use the `children` property to mutate the DOM:

    children = p.children
    children.first.remove()

The above removes the first element from the &lt;p&gt; tag.  We could
proceed to iterate over the children as well:

    for child in children:
        ...

However, if there is a large number of children, this could be a
performance problem due to the work involved in building the collection
when `p.children` is called. A generator would help with this:
    
    for child in p.genchildren(recursive=True):
        ...

However, the down side of a generator is that, by using one, we can't
mutate the internal tree, thus we should always provide a property that
doesn't return a generator and only provide a generator if one is
needed.

### Exceptions
Generators are used sometimes in lower-level code, such as when
overriding an `__iter__`, the `builtin.enumerate` function, or language
tokenizers. This rule is intended to help make object models intended
for framework users easier to use. It's not intended to interfere with the
way lower-level code needs to be written.

### Tags
\#naming #generators

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

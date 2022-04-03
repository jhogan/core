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
    * should be in *scriptio continua* case when they are compound words
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
*scriptio continua* case has the added benefit of encouraging single word
variables since compound variables written in *scriptio continua* are
a little difficult to read. Standard abbreviations also aid in
usability. Documenting the abbreviation in the class or an abbreviation
glossary has obvious benefits for standardization.

### Examples

    # Using a non-abbreviated variable
    name = usr.name

    # Using ls as a standard abbreviation for "list"
    ls = list()

    # If we can't use a single word, use *scriptio continua*
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

Occasionally you may want to have two varibles with the same name and
which contain the same data, but the data is typed differently. Consider
a situation like the following:

    # User enters a telephone number as a string
    str_number = '480-555-2525'

    int_number = int(strnumber.replace('-', ''))

Here, we have the original phone number as a string and an integer. In
this situation, we want to maintain both version, perhaps the string
version wil be reported to the user later on for some reason and the
integer will be saved to the database. 

### Implementation tips
For help naming things in general, a thesaurus is one of the most
valuable resources.

For inspiration on creating abbreviations, it is useful to look at the
way other technologies abbreviate things. The standard UNIX command `ls`
inspired the abbreviations for "list".

### Tags
\#naming #variables

6. Writing methods
--------------------------------

### Rule
Methods 

    * should be all lowercase

    * should include prefixes such as 'get' and 'set' if they are
      getters or setters (see section on writing proprety methods for
      more on this subject).

    * should be composed of a single word if humanly possible

    * should be in *scriptio continua* case when they are compound words

    * should be document using a docstring that indicates its behaviour
      and return type
    
    * should be named a verb unless it is an getter or setter

    * Most methods will be instance methods. If the `self` parameters is
      not used in the body of the method, the method is probably a
      static method. In that case, remove the `self` parameter and add
      the @staticmethod decorator. You may also consider whether or not
      you have a @classmethod on your hands.

    * It's almost always a good idea to name the parameter during
      invocation, e.g., `foo.bar(baz=qux)`

    * should perform a single identifiable, reusable and testable behavor.

    * should not contain type annotaion

    * should start with an underscore if the method is considered private

The methods parameters:
    
    * should be named after standard variable names or standard
      abbreviations

    * should be thoughouly documented using the :param: keyword

    * should not contain type annotaion

When writing a parameter's default, don't put space before or after the
assignment operator, e.g.:

    def plot(self, grid, x=0, y=0):
        ...

Hopefully the method signature will fit on one line. If not, break using
this format:

    def plot(self
        grid, x = 0, y = 0
    ):
        ...

    # Even more parameters
    def plot(self
        alfa,     bravo,  charlie,  delta,  echo,
        foxtrot,  golf,   hotel,    grid,
        x = 0, y = 0
    ):
        ...

Note that a single space surounds the assignment operator for the
default assignments when using the broken format. It just looks nicer.
    
### Justification
In object-oriented programming, methods represent the actions that an
object takes. Thus, they should be named after "action words", i.e.,
verbs.

One word should be enough to describe the behavior. If you find yourself
using a compound word, consider if one of the words should be a
parameter.

Bad:
    
    class robot:
        def killhuman(self):
            ...

    rbt = robot()
    rbt.killhuman()

Good:
    
    class robot:
        def kill(self, obj):
            ...

    rbt = robot()
    rbt.kill(obj='human'

All methods should perform a discrete unit of work that can be tested.
(Not every method needs to be tested directly, though it's functionality
should have tests written for it.) Methods should be written with code
reuse in mind. A method that is used only once is probably a bad method.
This is why it's important that the logic in a method be discrete.
Descrete methods perform exactly one behaviour and are therefore more
reusable. Adding logic to a method that exceeds its scope makes reuse
impossible because calling the method no longer does the one thing that
the client code would expect.

Indiscrete method:

    class salesorder:
        def place(self):
            # Save order to database
            self.save()

            # Send the order's customer a message telling them it has
            # been placed.
            self.customer.email("You're order has been placed")

The `place` method does two things. If for some reason we need to call
the `place` method in an area of the code that doesn't want to bother
the customer with an email, we would not be able to use the `place`
method. Perhapse a better way would be to write the class like this:

    class salesorder:
        def place(self):
            # Save order to database
            self.save()

        def notify(who='customer', of='placement')
            if who is 'customer' and of == 'placment':

                # Send the order's customer a message telling them it has
                # been placed.
                self.customer.email("You're order has been placed")

This is far from perfect, but at least `place` and `notify` do what they
say they do.

Type annotation should not be used. The docstring should contain
information on parameter and return types. Consistent use of good
parameter names, along with discrete method bodies, further makes type
annotation unnecessary.

### Implementation tips
None

### Exceptions
Type annotaion is used in pom.page.main overrides, e.g.:

    class mypage(pom.page):
        def main(self, greet: bool):
            ...

This is a special case because the framework-level code that invokes
`main` introspects this annotation to enforce types and converts to the
annotated type.

### Tags
\#naming #methods

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
Property methods are a nice feature of some object-oriented
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

8. Initilize primatives with using object instantiation
-------------------------------------------------------

### Rule
When initializing primative variables to their default value, use
instatiate syntax instead of assignment syntax. 

### Examples
Bad:
    i    =  0
    s    =  ''
    d    =  {}
    tup  =  ()
    ls   =  []
    
Good:
    i    =  int()
    s    =  str()
    d    =  dict()
    tup  =  tuple()
    ls   =  list()
    
### Justification
Though this form is a little more verbose, it enhances readability.

### Exceptions
None

### Implementation tips
None

### Tags
\#initialization #variables


6. Import modules, not module objects
-------------------------------------

### Rule
Generally speaking, simply `import` modules, not individual objects
(such as classes and functions) from the module.

### Example
Bad
    
    from party import person
    from dom import *

Good:
    
    import person
    import dom

### Justification
The framework has a lot of classes that will be used to created the
logic for a given module. Using the simple `import` method reduces the
risk of nameing collision. For example, there is currently an `item`
class in 8 different modules:

    import budget
    import account
    budgitem = budget.item()
    acctitem = account.item()

Simple `import` lines add to clearity as well. For example, the line:
    
    itm = budget.item()

is fairly self-explanatory: create a new budget item. However,
encountering a line such as:

    itm = item()

would be much less clear.

### Implementation tips
None

### Tags
\#import #module

6. Put linefeed between conditionals and blocks
-----------------------------------------------------

### Rule
When writing a conditional construct, such as an `if` or `while`
statement, put a newline after after the contitional

### Example
Bad:
    
    if x == y: print('X equals Y')

    while x == y: print('X equals Y')

    for i in range(10): x += i

Good:
    if x == y: 
        print('X equals Y')

    while x == y: 
        print('X equals Y')

    for i in range(10): 
        x += i


### Justification
Most conditionals have multiline code blocks. Thus the eye becomes used
to seing the conditional seperated from the code block by a new line.
Sometimes, it may seem convenient to join the two on the same line, but
this has a negative impact on readability. 

### Implementation tips
None

### Tags
\#whitespace #formatting

6. Writting classes
--------------------------------

### Rule
Classes
    * should represent a distinct entiity that performs a set of
      identifiable, reusable and testable behavor

    * should be document using a docstring that indicates it's purpose
      and what it represents
    
    * should document the standard variable name(s) used for instances
      of that class

    * Should be composed of mostly instance methods, i.e., avoid the
      [Abuse Of Utility Classes](https://wiki.c2.com/?AbuseOfUtilityClasses)
      anti-pattern

    * should have a corresponding collection class

    * should represent a real-world entity (a sales order, a user
      account.) or a real-world concept (a database connection, a DOM
      element, etc.)

    * should start with an underscore if the class is considered private

Class names
    * should be all lowercase

    * should be composed of a single word if humanly possible

    * should be in *scriptio continua* case when they are compound words

    * should be nouns

### Justification
In object-oriented programming, classes represent entities. These
entiities can be real world objects such as cars, people, etc., or they
can be abstract entities, such as an encryption algorithm or database
tables. Thus the name for a class should always be a noun. 

Like all identifiers, class names are easier to rememember, write and
read if they are single words in all lowercase. A good abbreviations or
acronyms should be identified for use as the instance variables name of
a class. This prevents naming overlap:
    
    class person:
        """ Represents a person.

        :abbr: per
        """

    per = person()

*Scriptio continua* is used when compound names are used:

    class emailaddress:
        ...

Virtually all data represented in computer systems is hierarchical. This
means that instances of a class will need to be grouped in a container.
Convential programming approches are content to use `list`s and `dict`s
for this kind of thing. However, these simple container objects were not
designed to encapsulate business logic. A more sophisticated approach is to
use classes that represent objects as collections. So the `person` class
above should have a complementary `persons` collection which can contain
instances of `person`. For ORM entity classes, this is enforced by the
framework and is made possible through inheritence:

    class persons(orm.entities):
        ...

    class person(orm.entity):
        ...

    pers = persons()
    per = person()

    # Add per to the pers collection
    pers += per

However, if you are writting non-ORM classes, you can still create
collection classes by inheriting from `entities` base classes.

    import entities

    class tables(entities.entities):
        ...

    class table(entities.entity):
        ...

    tbls = tables()
    tbl = table()

    # Add tbl to the tbls collection
    tbls += tbl

### Exceptions
In keeping with the Python convention, exception class names should be
written in StudlyCase and should end in the suffix "Error":

    class ComputationalOperationError(Exception):
        pass

In the ORM, and underscore is used in orm.association classes to
seperate the names of the two entities being associated:

    class order(orm.entity):
        ...

    class customer(orm.entity):
        ...

    class customer_order(orm.association):
        ...

### Implementation tips
None

### Tags
\#naming #class

6. Comment tags
--------------------------------

### Rule

    * NOTE comments indicate something that anyone should read before
      working on the code beneath the comment:
        
        # NOTE: If the following call raises an AttributeError, it is
        # almost certainly because there was an issue connecting to the
        # database.

    * TODO comments indicate that something should be done at
      a future, but indefinite date. A TODO comment should coorsponding
      to a ticket in the ticketing system. The TODO should be proceeded
      by a : and 4 random bytes written in hex:

        # TODO:73d12047 Something should really be done about the logic
        # here.

    * HACK is like a TODO but indicates that the code is a workaround
      or some sort of trick to get something working for the current
      moment. A HACK is a suboptimal solution that should be fixed in
      the future:

        # HACK:241d1d7c Artificially increment `i` here to get around
        # the one-off issue.
    
    * FIXME comments indicate a bug has been discovered in the code.
      Like TODO comments, a FIXME comment should coorsponding
      to a ticket in the ticketing system. The FIXME should be succeeded
      by a : and 4 random bytes written in hex:

        # FIXME:c5248240 The below line will break if a list has zero
        # elements.
    
    * XXX comments imply that something must be fixed in a feature
      branch before the branch is merged back into main. It's like a
      FIXME but more urgent. There is usually no need to give it an
      identifier.

        # XXX This will cause the table to be truncated when called with
        # an integer. Type checking needs to be used here to avoid data
        # loss.

    * Bomb-comments are used to flag sensitive areas of source code.
      They are intended to bring attention to changes made to these
      parts of the source code when viewed in `git-log`, `git-diff` and
      other analysis tools used during code reviews and code analysis.
      Changes made to these areas of source code should receive more
      attention and scrutenty. Use these liberaly in areas dealing with
      authentication, authorization and other sensitive areas.

        class security:
            """
            💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
            A singleton that stores security related values such as the
            orm's owner, proprietor, and whether or not the
            accessibility override is set.
            💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣💣
            """
            ...

### Justification
It's normal for bugs and and code optizitions of varying severity to be
noted and accumulated in source code. Having standard, well defined
comment tags helps categorize the severity of the issues.

The 4 bytes of random hex is intended to be a unique identifier for the
comment. The identifier can be used in other comments to reference the
original issue.

At the moment, there is no ticket system, but there are plans to write a
program that creates tickets based on the comments found in the source
code. The semantic information in the tag, along with the identifier,
will be useful to that program.

### Exceptions
None.

### Implementation tips
Your text editor should be configured to highlight the comment tag. Vim
does this by default for TODO, FIXME and NOTE in Python comments.

The random hex digets can be generate using `uuidgen`:

    uuidgen | cut -c1-8

### Tags
\#comments

1. Don't use needless negation
-------------------------------

### Rule
Don't use the negation operator unless it necessary.


### Example
Bad 
    if not X
        ...
    else:
        ...

Good:
    if x:
        ...
    else:
        ...

### Justification
The negation operator can sometimes be when it doesn't need to be. To
the reader, this would simply represent one more thing to remember.
Strive to code that's as easiy to read as possible.  To solve complex
problems, our code must be as simple as possible.

### Exceptions
None

### Implementation tips
None

### Tags
\#negation #operators

1. Use x a list comprension variable
------------------------------------

### Rule
When writing list comprehentions, use x as the default variable.

### Example
    [x for x in ls if x.prop = 'value']

### Justification
I similar pattern to this is the use of `i` as the index variable in for
loops:

    for i in range(10):
        ...

This convention is seen used in almost every programming language. Like
the `i`, the intent of the `x` is instantly recognizable (or will be
once you program in the framework from some time). Also, since `x` is a
single character, it is easy to type and read, like the `i`.

### Exception
None

### Tags
\#list-comprension #naming

1. Naming constants
-------------------

### Definition
A constant is just a variable in Python. However, conventions, usually
based on case, can be established that certain varibles shouldn't be
assigned more than once.

### Rule
Use StudlyCase to indicate denote a variable as a constant.

### Example
        
    def area(r):
        Pi = 3.14
        return self.Pi * (r * r)

    class ratios:
        GoldenRatio       =  1.618
        SuperGoldenRatio  =  1.465571231876768026656731
### Exceptions
Exceptions can be made to honor traditions.

    class constants:
        # Underscore can symbolize the hythen
        Meissel_MertensConstant = 0.26149 

        # A lowercase, Greek Pi character
        π = 3.14159

### Tags
\#constants #naming

<!-- 

// CONVENTIONS


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

Writing inner functions

Don't chain lines using the semicolon

Create new objects within collections using methods with the name of the
object:

    rs = rows()
    assert rs.count == 0

    r1 = rows.row()
    assert rs.count == 1
    assert rs.first is r1

// TODO


Discuss housekeeping in git logs

Discuss performance metrics in git logs
Discuss 'On branch <branch-name>' in git logs
-->

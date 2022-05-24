Carapacian Core
================
Carapacian Core is a web framework written and maintained to
facilitate the creation of web application that deal with business data.
It offers the following features:

* An automated regression [testing framework](#assets-test-scripts)
* An [object-relational mapper](#assets-orm-module) (ORM)
* A [universal data model](#assets-gem) for business objects
* Server-side [DOM authoring](#assets-dom-module)
* A web [page object model](#assets-dom-module) (POM)
* [Robotic process automation](#assets-robotic-process-automation) (RPA)
* [Command-line administration](#assets-command-line-interface)
* Database [migration](#assets-command-line-interface)
* [Logging](#assets-logging)
* Robust [third-party API integration](#assets-third-party)

Assets
------
This section provides an overview of the various files in the framework.

<a id="assets-test-scripts"></a>
## Test Scripts ##
Most development begins with the test scripts. All test scripts are in
the glob pattern `test*.py`, e.g., [testlogs.py](testlogs.py). Each test script
corresponds to a module which is the subject of its tests. 

Each test class in the test scripts inherits from the `tester` class.
This class provides basic assert methods that you may be familiar with
from other testing frameworks.

For more information on test scripts, see the section [Running
tests](#hacking-running-tests).

Below is a list of the current test scripts:

* [testbot.py](testbot.py)              Tests classes in [bot.py](bot.py)
* [testdom.py](testdom.py)              Tests classes in [dom.py](dom.py)
* [testecommerce.py](testecommerce.py)  Tests classes in [ecommerce.py](ecommerce.py)
* [testentities.py](testentities.py)    Tests classes in [entities.py](entities.py)
* [testfile.py](testfile.py)            Tests classes in [file.py](file.py)
* [testlogs.py](testlogs.py)            Tests classes in [logs.py](logs.py)
* [testmessage.py](testmessage.py)      Tests classes in [message.py](message.py)
* [testorder.py](testorder.py)          Tests classes in [order.py](order.py)
* [testparty.py](testparty.py)          Tests classes in [party.py](party.py)
* [testpom.py](testpom.py)              Tests classes in [pom.py](pom.py)
* [testproduct.py](testproduct.py)      Tests classes in [product.py](product.py)
* [test.py](test.py)                    Tests classes in [orm.py](orm.py)
* [testsec.py](testsec.py)              Tests authorization related code.
* [testthird.py](testthird.py)          Tests classes in [third.py](third.py)
* [testwww.py](testwww.py)              Tests classes in [www.py](www.py)

<a id="assets-gem"></a>
## General Entity Model (GEM) ##
The **General Entity Model**, sometimes called the universal data model,
is a large collection of ORM objects designed to work together to manage
and store business data in a robust and universal way. 

The GEM is based on the data models provided by the book "The Data Model
Resource Book, Vol.  1: A Library of Universal Data Models for All
Enterprises" and its second volume "The Data Model Resource Book, Volume
2: A Library of Universal Data Models by Industry Types". These books
provide several hundred tables that form a single data model that spans
a number of business domains such as sales, product management, human
resource management, as well as industry specific data models such as
manufacturing and insurance. The GEM is a collection of ORM entity
classes that correspond to the data models from the books.  

Note that at the moment, only the data model from the first volume has
been fully incorporated into the framework. Also note that the books don't
provide a data model for every conceivable domain, for example, the book
doesn't provide a data model that could support a blog or other literary
data types. However, we can use the principles from the book to create
extensions to its data model that integrate with the rest of its data
model.

The GEM is truly vast and can be used to store and retrieve virtually
any business data in a highly normalized and robust way. The GEM
classes, being ORM classes, each have persistence logic built in.
Additionally, they contain the logic to ensure that the data they
contain is valid and that the user retrieving or persisting that data is
authorized to do so. Note that though many GEM classes have been fully
incorporated into the framework, validation and authorization is an
ongoing effort.

It is highly recommend that developers obtain these two books and
absorb the data modeling and business ontology concepts in them before
endeavoring to use or alter the GEM.

Below is a list of the modules that currently contain GEM classes.

* [account.py](account.py)        Contains classes that manage accounting data
* [apriori.py](apriori.py)        Contains GEMs that all GEM entities could use
* [asset.py](asset.py)            Contains classes that manage the assets used by people and organizations
* [budget.py](budget.py)          Contains classes that manage budgeting data
* [ecommerce.py](ecommerce.py)    Contains classes that manage web and user data
* [effort.py](effort.py)          Contains classes that manage work effort data
* [hr.py](hr.py)                  Contains classes involved in human resource management
* [invoice.py](invoice.py)        Contains classes related to invoicing
* [message.py](message.py)        Contains classes involved in messages such as email, SMS, chat, etc.
* [order.py](order.py)            Contains classes involved in sales and purchase orders
* [party.py](party.py)            Contains classes that track people and organizations
* [product.py](product.py)        Contains classes involved in product management
* [shipment.py](shipment.py)      Contains classes involved in shipping

## Entity modules ##
The entity modules, [entities.py](entities.py), contains base classes
that most of the classes in the framework ultimately inherit from. The
most import of these are `entities` and `entity`. The classes contain
many facilities that make working with collections of entity objects
easy. 

    import entities

    class products(entities.entities)
        pass

    class product(entitie.entity)
        pass

    # Create a collection
    prds = products()

    # Create some entity objects
    prd1 = product()
    prd2 = product()

    # Assert that the collection has no entities
    assset prds.count == 0

    # Append the entity objects to the collection
    prds += prd1
    prds += prd2

    # Assert that the collection has 2 entities
    assset prds.count == 2

Here, the `products` class acts as a smart array or list for the
`product` entity; we are free to add as much functionality to the
`products` collection class as we want.

The entity system also supports a robust event management system that
allows us to subscribe one or more event handlers to events that happen
to the `entities` and `entity` objects, such as the event when an
`entity` is added to the collection, or when an attribute of an `entity`
changes.

`entities` and `entity` classes also support robust validation logic
through their `brokenrule` properties.

Indexing is provided, as well, for fast lookup of `entity` objects within
an `entities` collection (although, for OLTP applications, this is rarely
needed.).

The `entities` and `entity` class provide the base classes for ORM
`entities` and `entity` classes. See the section on [object-relational
mapping](#assets-orm-module) for more on ORM classes.

<a id="assets-orm-module"></a>
## Object-relational mapper (ORM) module ##
An important part of the framework is the **object-relational mapper
(ORM)**. It provides the persistence layer for the [GEM](#assets-gem)
classes as well as other [active record](https://en.wikipedia.org/wiki/Active_record_pattern) 
classes. These classes are collectively referred to as "ORM classes".

Basic data mutation operations (e.g., creating, updating, and deleting)
for ORM object are provided through the `save()` method.  Data querying
is provided through the constructors.

The ORM protects data from invalid data through the ORM object's
`brokenrules` @property.

Data is further protected from unauthorized access and modification
through the ORM's `security` and `violations` classes.

Data can be streamed through collection objects by loading an arbitrary
number of records at a time. This is useful when working with large
datasets. See the `orm.streaming` class for more.

Atomic, cascading persistence is supported through the use of collection
objects:

    import order

    # Create order object
    ord = order.order()

    # Add 10 new order items to the order's `items` collection
    for _ in range(10):
        ord.items += order.item()

    # Save the order and all its line itmes
    ord.save()

Here, an order object is created and 10 child (constituent) items are
added to the order. When `save()` is called, the order and its items are
saved atomically resulting in 11 records being saved in two different
database tables. The cascading can go on indefinitely.

Database subclassing is also supported. That is to say, if an ORM class
has a subclass, the ORM class and its subclass each have corresponding
tables. For example, the `order.order` class above from the
[order](order.py) module is subclassed by the `order.salesorder` class.
If we create and save a `salesorder`, a record in its table, as well as
the `order` table, are saved atomically.

<a id="assets-dom-module"></a>
## DOM and POM modules ##
The DOM module, [dom.py](dom.py), provides class that support DOM authoring and
parsing - similar to the DOM objects provided to JavaScript through a
browser - though the interface is easier and more Pythonic. 

The DOM module also offers CSS3 selector support and automatic XHR
request management (through its subclassing of `entities.event`).

The POM (Page Object Model) module provides an abstraction that sits on top
of the DOM. It offers support for page-level objects such as page
headers, footers, navigation menus, sidebars, forms, pages and websites.
Many of its classes inherit from the DOM objects. For example, since
`pom page`s are basically HTML pages, `pom.page` objects inherit from
`dom.html`, while `pom.menu` represents a menu on a page, and therefore
inherits from `dom.nav`.

Entire websites are represented by classes that inherit from `pom.site`.
For example, in website modules, such as
[carpacian_com.py](carapacian_com.py), the `carapacian_com.site` class
inherits from `pom.site`, while classes that inherit from `pom.page`
exist in that module to represent the website's pages.

<a id="assets-robotic-process-automation"></a>
## Robotic process automation (RPA) ##
The [bot.py](bot.py) modules provides classes that inherit from the `bot.bot`
class. These bot's are intended to be run as background process to
automate a number of routine tasks. 

Currently, there is only the `sendbot` class which sends messages from
the message queue to third-party systems such as SMTP servers. However,
there are plans to develop a number of other bots to manage routine
administrative tasks such as an `adminbot` to monitor servers and a
`cfgbot` (configuration management bot) to maintain Git repositories and
automate running tests. 

Bots are intended to replace most tasks that are conventionally
performed by Bash scripts invoked by Crontabs. These bots will go a long
way toward reducing the administrative burden conventionally put on
software developers and will help to keep the systems secure. 

Another use for bots is to create QA bots that can run tests on live
servers.  These bots could be use for things like checking for spelling
or testing performance on live websites. This will help improve the
quality of service provided by these systems.

Though the [bot.py](bot.py) module is a collection of classes, it can be run as
an executable. Each invocation would bring to life a certain bot:

    ./bot.py --iterations 1 --verbosity 5 sendbot

Init systems, like systemd, can be used to invoke the bots this way.

## HTTP and WSGI modules ##
The [www.py](www.py) contains support for HTTP objects such as HTTP requests and
responses, HTTP exceptions and errors. It also contains a `browser`
object to make HTTP requests easier and more intuitive (for example, the
`www.browser` can store cookies).

In addition to providing HTTP facilities, it also contains an
`application` that, when instantiated, is a callable that the WSGI
server invokes thus providing an entry for HTTP requests into the
framework's logic (see `www.application.__call__`).

<a id="assets-command-line-interface"></a>
## Command line interface (crust) ##
`crust` is the main command-line interface to the framework. 
Currently,  `crust` is used to inactively perform database migrations.
Future uses would include issuing queries to learn about the framework's
environment as well as communicating with bots.

## Library dependency files ##
A couple of simple text files exists to store the third-party libraries
that the framework depends on. These files are [deb](deb) and
[pip](pip). The packages listed in deb should be installed using `apt`
while the packages listed in `pip` should be installed with `pip`. See
the [Operating system](#environment-operating-system) section for
details on how and why to use these files.

## Documentation files ##
There are a few files, all in uppercase, used for various documentation
purposes:

* [ABBREVIATIONS.md](ABBREVIATIONS.md) Contains a list of abbreviations
to be used for common variables (such as using `ls` for a variable
representing some sort of list). Note that typically, a class will
document the variable name that should be used for instances of the
class.

* [LICENSE_cssselect](LICENSE_cssselect)  The license for code copied
    into the framework from Ian Bicking's
    ['cssselect'](https://github.com/scrapy/cssselect) project to help
    with CSS selector tokenization.

* [LICENSE](LICENSE)      The Carapacian Core license

* [README.md](README.md)  The readme file that you are currently reading.

* [STYLE.md](STYLE.md)    The style guide to be followed when developing and
                          maintaining code for the framework.

* [VARIABLES](VARIABLES) Similar to [ABBREVIATIONS](ABBREVIATIONS.md),
                         but documents the conventional names given to
                         variables in certain contexts.

* [VERSION](VERSION)     Contains the version number of Carapacian Core

## File module ##
A file system for use by the framework and its users is provided by the
[file.py](file.py) module. File metadata is stored in the database, while file
contents are stored on the actual file system. Since the file classes
(a.k.a. *inodes*) inherit from `orm.entity`, they enforce their own
validation and authorization logic.

The file module is intended to be used to store user's avatars, their
multimedia uploads, and any other types of files they need to manage
through a website provide by the framework. The framework can also use
the file module for its own needs, though the database would probably
make a better choice for most use cases.

<a id="assets-third-party"></a>
## Third party module ##
The [third.py](third.py) module contains classes related to the integration of the
framework with third party systems such as external mail servers, credit
card processing systems, geocoding services etc. It contains facilities
that perform, monitor and manager these interactions.

<a id="assets-logging"></a>
## Logging ##
The logging module, [log.py](log.py), wraps calls to Python's native
logging library which can be configured to send messages to a remote or
local syslog.

The logging parameters, such as the log level, is configured in the
[config files](#assets-configuration). 

Log messages are intended to go to a local log file on the system.
Most logging should be done using the GEM class (or subclass thereof)
`apriori.log`. This way, the log message is in the database which is
ideal. However, the [log.py](log.py) module should be used to log locally
(usually to /var/log/syslog) for the following conditions:

* Logging verbose debug messages to assist with problem diagnostics.
* Logging informational log messages of interest to developer.
* Logging exceptions that occur when connecting to the database; if
  there is a problem connecting to the database, we have to use local
  file logging as a last resort.

<a id="assets-configuration"></a>
## Configuration ##
Configuration of the environment is made in two files. The first,
[configuration.py](configuration.py) is a versioned file which contains no secret
information, such as database passwords, but does provide a default
configuration through its `configuration` singleton. 

The second file, [config.py](config.py) is an unversioned file which contains a
class called `config` which inherits from `configuration`. This file
overrides the default version and can contain secrete information and
therefore **should never be committed to the Git repository**.  This file
should also have restrictive file permissions:

    chmod 400 config.py

In addition to storing secret information, `config` can also be used to
override the default configuration of `configuration` to suite the needs
of the given environment.

Unlike most configuration files, these files are full-fledged Python
libraries. This is a powerful approach to configuration because we can
use the full power of Python to configure the environment.

Environment
-----------

<a id="environment-operating-system"></a>
## Operating system ##
The recommend operating system for Carapacian Core is Linux. The Ubuntu
distribution of Linux is where the Core was developed and where it has
received most of its testing, however, it should run on most
Debian-based distributions without much modification - if any. It's
recommend that you use the latest LTS version of Ubuntu and use its
native packages for the Python interpreter along with Green Unicorn. The
version of Python shipped with the latest Ubuntu LTS version is
considered the framework's officially supported version.

There is a [deb](deb) file in the source directory that contains a list of
Ubuntu/Debian packages that Carapacian Core depends on. Currently, the
list contains the following:

    python3-mistune
    python3-inflect
    python3-mysqldb
    mysql-server
    python-mysqldb
    python3-dateutil

Thus running the following command is enough to install the OS level
dependencies.

    apt install `cat deb`

Ubuntu packages are preferred over PIP packages because running updates
on Ubuntu will capture updates to these packages:

    apt update && apt dist-upgrade -y

However, some dependencies are not available at the OS level. They can,
however, be obtain through PIP. Those packages can be found in the
[pip](pip) file. Its current contents are listed below:
    
    pyyaml
    ua-parser
    user-agents
    pytz

We can install them using `pip3`:

    pip3 install `cat pip`

Adding the `-U` flag causes the packages to be updated.

    pip3 install -U `cat pip`

## Database ##
The RDBMS of choice is MySQL. The configuration for the database
connections can set using the `config.accounts` property in the
[config.py](config.py) file. Iterate over the the accounts from the base class
`configuration` and find the MySQL connection, then set its values to
whatever you need. This will usually just be the password.

See the [Configuration](#assets-configuration) section for more details
on the configuration files.

    class config(configuration):
        @property
        def accounts(self):
            accts = super().accounts
            for acct in accts:
                if isinstance(acct, accounts.mysql):
                    acct.password = 'MyP@ssw0rd'

            return accts

The framework uses the database for persisting data and maintaining
indexes for fast data retrieval. It doesn't use the database to store
code such as in the case of stored procedures, views, UDF's, etc. Thus,
the SQL that it uses to interact with the RDBMS is fairly simple and
standard. It could probably be easily ported to another RDBMS if that
were somehow deemed desirable, however MySQL currently seems like an
excellent choice for the framework's needs.

The RDBMS is also expected to take care of its on scalability and
backup needs as well as provide network transparency. However, a
database bot will be written to tend the administration of these
functions.

## Lower environments ##
As of this writing, not much work has been done to determine how the
production environment, as well as the lower environments, such as UAT,
QA, and development will be managed. This section will be updated when
concrete solutions to this problem domain have been devised.

Hacking
-------

<a id="hacking-running-tests"></a>
## Running tests
Most feature development and bug fixes are done by adding a number of
tests to the [suite of regression testing scripts](#assets-test-scripts).

Each module has, or should have, a corresponding test module. For
example, the tests for the [product.py](product.py) module are located in
[testproduct.py](testproduct.py). Within the test module, there are (or should be)
*tester* classes which test classes in the corresponding module. 

For example, to test the ability of the ORM class
`product.product` to update itself, a tester method called
`testproduct.test_product.it_updates` contains code to update a
`product` and assert that the update works. Conventionally, tester
methods start with the `it_` prefix, though this isn't a strict
requirement of the tester framework. 

To run all the tests, you can simply run the [test.py](test.py) script.

    ./test.py

This runs all the tests in that file as well as all the tests in files
that match the pattern `test*.py`. Note that `test.py` should complete
with no failures on a feature branch before it is merged into 'main'.

To narrow you tests down a little, you choose to run only the
module-level tests. To run all the product tests, run the [testproduct.py](testproduct.py)
script mentioned above:

    ./testproduct.py


To narrow things down even more, you can choose to run a tester class
specifically:

    ./testproduct.py test_product

This only runs the tests in the `test_product` class.

During development, you will probably want to focus on one tester method
at a time. If you were testing the updating capabilities of the
`product` class, as described above, you could choose to run only the
`it_updates` method like this:

    ./testproduct.py test_product.it_updates

This is much faster. 

By default, tests rebuild database tables that are needed for the tests.
This takes some time and is often unnecessary. You can cause the test
process to skip this process with the `-T` flag.

    ./testproduct.py test_product.it_updates -T

Now the test runs even faster.

### Viewing SQL being issued to MySQL ###
For debugging purposes, you will occasionally take an interest in what
SQL the ORM is actually sending to the database. This is done by using
the snapshot context manager:

    import db, party

    par = party.company(name="Acme")
    with db.chronicler.snapshot():
        par.save()

The above should print out the `INSERT` statements used to create the
new company in the database.

<a href="hacking-debugger"></a>
### Dropping into the debugger ###
If the test reports exceptions, you can rerun the tests and cause the
test to break on those exceptions. This is an extremely important
technique to know because it makes development so much faster. All you
have to do is pass in the `-b` flag.

    ./testproduct.py test_product.it_updates -b

When the exception is encountered, you will be dropped into the PDB
debugger at the line that caused the exception. From there, you will be
able to get the values of any variable, step in, out of, and over lines
of code, print a stack trace, jump to different lines of code, etc. If
you don't know how to use PDB you can find a reference
[here](https://docs.python.org/3/library/pdb.html#debugger-commands).

You can also set breakpoints in the code. This is typically done by
calling the `B` function (the `B` function is imported in each module
with the line `from dbg import B`). For example, if you want to be
dropped in the debugger when the below method is called, just call `B`
on the first line:

    def some_dubious_logic(self):
        B()
        ...

Run the code as you normally would:

    ./test.py

If the `B` function is encountered, you will be dropped into PDB.

### When exceptions are caught ###
If an exception is raised and caught, you may find yourself in the
`except` block not knowing where the exception was actually raised.
Another function from `dbg` called `PM` is imported in most modules:

    from dbg import B, PM

You can use this to bring the PDB debugger to the actual line that
raised the exception.

    try:
        this_raises_an_exception_somewhere()
    except Exception as ex:
        # This line will bring us to the actual line that raise the
        # exception.
        PM(ex)
        ...

The `B` and `PM` functions are added to the actual source code. They
shouldn't be pushed into the Git repository, though. It's okay to push
them into feature branches if that is convenient, but they should never
be pushed into 'main'.

### Testing through Green Unicorn ###
On the occasion that you need to debug an issue through the HTTP
interface directly, you can run the Green Unicorn HTTP/WSGI server and
hit the services from a browser or some other user-agent like `curl`. To
run the service, you can `cd` into the framework's source directory and
run the command:

   gunicorn -b carapacian.com:8000 --reload --timeout 0 'www:application()' 

The `-b` flag binds the above invocation to the `carapacian.com`
interface on port 8000. 

The ``--reload`` option is useful because it causes `gunicorn` to detect
changes made to the source files. This way you don't have to rerun
`gunicorn` every time you make a change to the source. It uses
**inotify** to monitor files. inotify should be installed by default in
Ubuntu.

Setting `--timeout` to 0 means the worker classes will wait an
indefinite amount of time for the request to complete. This is useful
for step-by-step debugging described below because the time it takes to
debug an issues will likely be longer than the timeout.

the 'www.application()' instantiates the `application`` class in
`www.py` and returns an instance to ``gunicorn``. This is where the
framework code receives the HTTP request per the WSGI standard.

The above service can then be invoked with `curl`:

    curl carapacian.com:8000

You can set breakpoints in the code with the call `B()` described
[above](#hacking-debugger).  When the breakpoint is encountered, the
terminal that `gunicorn` is running in will display a PDB prompt giving
you PDB`s full capacity to debug the code at the breakpoint. When you
are ready for the request to complete, just enter the command `c` into
the PDB prompt to cause the code to continue. The request will complete
and the `gunicorn` daemon is ready for the next request.

### Interacting with the database ###

#### Using hex() ####
Hopefully, you won't need to issue SQL queries directly to the database;
you should be able see what's in the database through ORM objects.
However, if you do find yourself needing to issue SQL directly to the
database, you should get used to using the `hex()` function.

The primary keys (and therefore the foreign keys) are UUIDs stored in
the database as 16 byte binary strings. This does not render well by
default. Instead of writing a query like:

    select * from party_parties

you will want to specify the columns and decode key fields with `hex()`:

    select hex(id), id(proprietor__partyid), name from party_parties;

This provides you with hex representations of the binary strings.

#### Interacting with MySQL ####
While the `mysql` command line is a powerful tool to interact directly
with the database, you will probably want something more interactive. It
is recommend that you install
[dbext](https://github.com/vim-scripts/dbext.vim) into your Vim
environment (if you are using Vim). dbext allows you to write queries in
a Vim window, then issue those queries to the server. The result of the
queries appear in a separate Vim window. If you use Emacs or another
editor, it is recommend that you finds something similar to dbext.

Git usage and conventions
-------------------------
The 'main' branch always contains the latest, accepted code changes.
Feature branches are created off the 'main' branch to add features or
fix bugs.  After the code has been peer reviewed, it can be merged back
into the 'main' branch. Git tags **will** be used to mark specific
points in 'main's history indicating release of the framework. The Git
tags will use standard [semantic versioning](https://semver.org/).

### Code commits ###
Two main types of Git commits are used in the framework: standard code commits
and "housekeeping" commits.  The distinguishing feature of a code commit is
that it should only contain code changes. Any comments or whitespace in these
commits should be related the code changes,  e.g.:

    commit b76fa29ee3fc00efa86b75331b4e9cdecdb3bf9b
	Author: Jesse Hogan <jhogan@carapacian.com>
	Date:   Fri Mar 18 07:22:33 2022 +0000

		Add support for it_responds_to_two_different_buttons_with_single_handler

		This required that the `src` parameter of the event handler be a DOM
		representation of the UI element (i.e., <button>, <input>, etc) behind
		the event being triggered. Previously, it was just the HTTP request
		object.

		On branch page-events

	diff --git a/www.py b/www.py
	index feb993c..a6a16d8 100644
	--- a/www.py
	+++ b/www.py
	@@ -696,7 +696,8 @@ class _request:
			 if self.isevent:
				 eargs = dom.eventargs(
					 html = self.body['html'],
	-                hnd  = self.body['hnd']
	+                hnd  = self.body['hnd'],
	+                src  = self.body['src'],
				 )

			 try:

The first line of the commit message starts with a verb in its infinitive
(basic) form; in this case "Add". The first line should be 50 characters or
less. This is called the summary line. 

If more explanation for the commit should be documented, add a blank
line, then add as much explanation as you need. If you find yourself
writing a long explanation of the commit, take a moment to consider
whether or not the explanation would be better documented as comments in
the code. Either way, always have a mind toward posterity when writing
commit messages.

The comment should always end with the branch name. It should be prefaced with
'On branch ':

	On branch page-event

This exact text will be provide for you when you run `git commit -v` in the
commented area, so you can easily copy-and-paste it.

### Housekeeping commits ###
Housekeeping commits mainly consist of post facto comments, whitespace
changes, changes to documentation files, and other such changes that
have very little to do with computer logic.  They typically have one
word in their commit message: "Housekeeping", since most housekeeping
changes don't require a lot of explanation.  On a second line (after the
blank line), the branch name is included as in standard code commits:

	commit 3f7f8ba9eb633dfb44f74e9f7769f789be8cbf17
	Author: Jesse Hogan <jhogan@carapacian.com>
	Date:   Thu Feb 3 05:47:57 2022 +0000

		Housekeeping

		On branch perf

	diff --git a/orm.py b/orm.py
	index 39bfbec..14d62d1 100644
	--- a/orm.py
	+++ b/orm.py
	@@ -3196,6 +3196,8 @@ class entitymeta(type):
				 # collections.
				 map._name = k
				 maps.append(map)
	+
	+            # NOTE Appending to ls shaves some time off startup
				 orm_.mappings.ls.append(map)

			 # Iterate over the maps list. NOTE that iterating over the

The purpose for distinguishing **housekeeping** commits from **standard
code commits** is that analysis tool, such as `git-log` can include or
exclude housekeeping commits. Being able to exclude housekeeping commits
is convenient for code analysis because the analyst can focus on the
code logic while excluding changes in comments, whitespace formatting,
etc. To view code change while excluding housekeeping changes, you can
use a command like this:

    git log -p --grep Housekeeping --invert-grep

Removing `--invert-grep` shows only the housekeeping commits.

### Atomic commits ###
To make the git-log more useful, strive to make commits as atomic as
possible. Atomic commits are commits that contain changes to the source
code that address a single, specific issue. Atomic commits are easier to
work with and analyze. To create atomic commits, you can use the
`--patch` (`-p`) flag with `git-add` to select which portions of your
changes to stage.

Current issues
--------------

### Memory issue ###
At the moment, there is an unresolved issue with the way
[test.py](test.py) accumulates memory as it runs: It never seems to free
large portions of the objects it creates, and ends up allocating for
itself several hundred megabytes of memory before it has completed. 

On the machine the framework is currently being developed, there is a
total of 1GB of RAM. Occasionally, the [test.py](test.py) script will
consume so much that the operating system's oom\_reaper will cause MySQL
to restart, which causes tests in the script to begin to fail. A
convenient solution to this is to simply ensure that the following line
is set in
`/etc/mysql/my.cnf`:
    
    [mysqld]
    performance_schema = 0

Restart the mysqld and its default memory consumption will be reduce by
several hundred megabytes.

Read this 
[Stack Overflow question](https://stackoverflow.com/questions/10676753/reducing-memory-consumption-of-mysql-on-ubuntuaws-micro-instance)
for more details.

In the future, the `dba` bot should ensure this line is added.

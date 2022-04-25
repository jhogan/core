Carapacian Core
================
Carapacian Core is a web framework. It is written and maintained to
facilitate the creation of web application that deal with business data.
It offers the following features:

* An object-relational mapper (ORM)
* A univeral object/data model for business objects
* Robotic process automation (RPA)
* Command-line administration
* Database migration
* Server-side DOM authoring
* A web page object model (POM)
* Logging
* A automated unit/regression testing framework
* Robust third-party API integration

Environment
-----------

## Operating system ##
The recommend operating system for Carapacian Core is Linux. The Ubuntu
distribution of Linux is where the Core was developed and where it has
received most of its testing, however, it should run on moste
Debian-based distributions without much modification - if any. It's
recommend that you use the latest LTS version of Ubuntu and use its
native packages for the Python interpretor along with Green Unicorn. The
version of Python shipped with the latest Ubuntu LTS version is
considered the officially supported version.

There is a `deb` file in the source directory that contains a list of
Ubuntu/Debian packages that Carapacian Core depends on. Currently, the
list contains the following:

    python3-mistune
    python3-inflect
    python3-mysqldb
    mysql-server
    python-mysqldb
    python3-dateutil

Thus running the following command is enough to install the OS-level
dependencies.

    apt install `cat deb`

Ubuntu packages are prefered over PIP packages because running updates
on Ubuntu will capture updates to these packages:

    apt update && apt dist-upgrade -y

However, some dependencies are not available at the OS-level. They can,
however, be obtain through PIP. Those packages can be found in the `pip`
file. Listed are its current contents:
    
    pyyaml
    ua-parser
    user-agents
    pytz

We can install they using `pip3`:

    pip3 install `cat pip`

Adding the `-U` flag causes the packages to be update.

    pip3 install -U `cat pip`

## Database ##
The RDBMS of choice is MySQL. The configuration for the database
connection can set using the `config.accounts` property in the
`config.py` file. Iteratate over the the accounts from the base class
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

The framework's uses the database for persisting data and maintaining
indexes for fast data retrival. It doesn't use the database to store
code such as in the case of stored procedures, views, UDF's, etc. Thus,
the SQL that it uses to interact with the RDBMS is fairly simple and
standard. It could probably be easily ported to another RDBMS if that
were somehow deemed desireable, that MySQL seems like an excellent
choice for the framework's needs.

The RDBMS is also expected to take care of it's on scalability and
backup needs as well as provide network transparency. However, a
database bot <!--TODO reference the bot section--> will be written to
tend the administration of these functions.

## Lower environments ##
As of this writing, not much work has been done to determine how the
production environment, as well as the lower enviroments, such as UAT,
QA, and development will be managed. This section will be updated when
concrete solutions to this problem domain have been devised.

Assets
------
This section provides an overview of the various files in the framework.

## Test Scipts ##
Most development begins with the test scripts. All test scripts are in
the glob pattern `test*.py`, e.g., `testlogs.py`. Each test script
corresponds to a module which is the subject of its tests. 

Each test class in the test scripts inherits from the `tester` class.
This class provides basic assert methods that you may be familiar with
from other testing framworks.

For more information on test scripts, see the section [Running
tests](#hacking-running-tests).

Below is a list of the current test scripts:

* **testbot.py**        Test classes in bot.py
* **testdom.py**        Test classes in dom.py
* **testecommerce.py**  Test classes in ecommerce.py
* **testentities.py**   Test classes in ecommerce.py
* **testfile.py**       Test classes in file.py
* **testlogs.py**       Test classes in logs.py
* **testmessage.py**    Test classes in message.py
* **testorder.py**      Test classes in order.py
* **testparty.py**      Test classes in party.py
* **testpom.py**        Test classes in pom.py
* **testproduct.py**    Test classes in product.py
* **test.py**           Test classes in orm.py
* **testsec.py**        Test authorization related code.
* **testthird.py**      Test classes in third.py
* **testwww.py**        Test classes in www.py

## General Entity Model (GEM) ##
The General Entity Model, sometimes called the universal data model, is
a large collection of business objects designed to work together to
persist business data in a robust and universal way. 

The GEM is based on the data models provided by the book "The Data Model
Resource Book, Vol.  1: A Library of Universal Data Models for All
Enterprises" and its second volume "The Data Model Resource Book, Volume
2: A Library of Universal Data Models by Industry Types". These books
provide several hundred tables that form a single data model that span a
number of business domains such as order entry, product management,
human resource management, as wel as industry specific data models such
manufacturing and professional services. The GEM is a collection of ORM
entity classes that correspond to the data model from the books. Note
that at the moment, only the data model from the first volume has been
fully incorpated into the framework.

The GEM is truly vast, and can be used to persist and retrieve
virtually any business data in a highly normalized and robust way. The
GEM classes, being ORM classes, each have persistence logic built in.
Additionally, the contain the logic to ensure that the data they contain
is valid and that the user retriving or persisting that data is
authorized to do so. Note that though many GEM classes have been fully
incorporated into the framework, validation and authorization is an
ongoing effort.

It is highly recommend that developers obtain these two books and
absorb the data modeling and business ontology concepts in them before
endevoring to use or alter the GEM.

Below is a list of the modules that currently contain GEM classes.

* **account.py**    Contains class that manage accounting data
* **apriori.py**    Contains GEMs that all GEM entities could use
* **asset.py**      Contains class that manage the assets used by people and organizations
* **budget.py**     Contains class that manage budgeting data
* **ecommerce.py**  Contains class that manage web and user data
* **effort.py**     Contains class that manage work effort data
* **hr.py**         Contains class involved in human resource management
* **invoice.py**    Contains classes related to invoicing
* **message.py**    Contains classes involved in messages such as email,
                    SMS, chat, etc.
* **order.py**      Contains class involved in order entry
* **party.py**      Contains classes that track people and organizations
* **product.py**    Contains classes involved in product managemnts
* **shipment.py**   Contains class involved in shipping

## Entity modules ##
The entity modules, `entities.py`, contains base classes that most of
the class in the framework ultimately inherit from. The most import of
these are `entities` and `entity`. The classes contain many facilities
that make working with collections of entity objects easy. 

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
`product` entity because we are free to add as much functionality to the
`products` colllection class as we want.

The entity system also supports a rebost event management system that
allows us to subscribe one or more event handlers to events that happen
to the `entities` object or the `entity` object, such as the event when
an entity is added to the collection, or when an attribute of an entity
changes.

`entities` and `entity` classes also support robust validation logic
through their `brokenrule` properties.

Indexing is provided, as well, for fast lookup of `entity` objects within
an `entities` colection (although, for OLTP applications, this is rarely
needed.).

The `entities` and `entity` class provide the base classes for ORM
`entities` and `entity` classes. See [below](#assets-orm-module) for
more on ORM classes.

<a id="assets-orm-module"></a>
## ORM module ##
## DOM and POM modules ##
## Robotic process automation (RPA) ##
## HTTP and WSGI modules ##
## Command line interface (crust) ##
## Library dependency files ##
## Documentation files ##

<a id="assets-configuration"></a>
## Configuration ##

Hacking
-------

<a id="hacking-running-testes"></a>
## Running tests
Most feature development and bug fixes are done through the automated
regration testing scripts. 

Each module has, or should have, a corresponding test module. For
example, the tests for the `product.py` module are located in
`testproduct.py`. Within the test module, there are (or should be)
*tester* classes which test classes in the corresponding module. 

For example, to test the ability of the ORM class
`product.product` to update itself, a tester method called
`testproduct.test_product.it_updates` contains code to update a
`product` and assert that the update works. Conventionally, tester
methods start with the `it_` prefix, though this isn't a strict
requirement of the tester framework. 

To run all the tests, you can simply run the `test.py` script.

    ./test.py

This runs all the tests in that file as well as all the tests in files
that match the pattern `test*.py`. 

To narrow you tests down a little, you choose to run only the
module-level tests. To run all the product tests, run the testproduct.py
script mentioned above:

    ./testproduct.py


To narrow things down even more, you can choose to run a tester module
specifically:

    ./testproduct.py test_product

This only runs the tests in the `test_product` class.

During development, you will probably want to focus on one tester method
at a time. If you were testing the updating capabilities of the
`product` class, as described above, you could choose to run only the
`it_updates` method like this.

    ./testproduct.py test_product.it_updates

This is much faster. 

By default, tests rebuild database tables that are needed for the tests.
This takes some time and is often unnecessary. You can cause the test
process to skip this process with the `-T` flag.

    ./testproduct.py test_product.it_updates -T

Now the test runs even faster.

## Dropping into the debugger
If the test reports exceptions, you can rerun the tests and cause test
to break on those exceptions. This is an extremely important technique
to know because it makes development so much faster. All you have to do
is pass in the `-b` flag.

    ./testproduct.py test_product.it_updates -T -b

If there is an exception, you will be dropped into the PDB debugger. At
that point, you will be able to get the values of any variable, step in,
out of, and over lines of code, print a stack trace, jump to different
lines of code, etc. If you don't know how to use PDB you can find a
reference
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

If an exception is raised an caught, you may find yourself in the
`except` block not knowing where the exception was actually raised.
Another function from `dbg` called `PM` is imported in most modules:

    from dbg import B, PM

You can use this to bring the PDB debugger to the actual line that
raised the exception.

    try:
        this_raises_an_exception_somewhere()
    except AttributeError:
        # This line will bring us to the actual line that raise the
        # exception.
        PM(ex)
        ...

The `B` and `PM` functions are added to the actual source code. They
shouldn't be pushed into the Git repository, though. It's okay to push
them into feature branches if that is conventient, but the should never
be pushed into 'main'.

## Writing tests ##
<!-- TODO -->

## Testing through Green Unicorn ##
On the occasion that you need to debug an issue through the HTTP
interface directory, you can run the Green Unicorn HTTP/WSGI server and
hit the services from a browser of some other user agent like `curl`. To
run the service, you can `cd` into the framework's source directory and
run the command:

   gunicorn -b carapacian.com:8000 --reload --timeout 0 'www:application()' 

The `-b` flag binds the above invokation to the `carapacian.com`
interface on port 8000. 

The ``--reload`` option is useful because it
causes `gunicorn` to detect changes made to the source files. This way
you don't have to rerun `gunicorn` everytime you make a change to the
source. It uses **inotify** to monitor files. inotify should be
installed by default in Ubuntu.

Setting `--timeout` to 0 means the worker classes will wait an
indefinate amount of time for the request to complete. This is useful
for step-by-step debugging described below.

the 'www.application()' instantiates the `application`` class in
`www.py` and returns an instance to ``gunicorn``. This is where the
framework code takes the request per the WSGI standard.

The above service can then be invoked with `curl`:

    curl carapacian.com:8000

You can set breakpoints in the code with the call `B()` described above.
When the breakpoint is encounterd, the terminal that `gunicorn` is
running in will display a PDB prompt giving you PDB`s full capacity to
debug the code at the break point. When you are ready for the request to
complete, just enter the command `c` into the PDB prompt to cause the
code to continue. The request will complete and the `gunicorn` is ready
for the next request.

Git usage and conventions
-------------------------
The 'main' branch alwaws contains the latest, accepted code changes. Feature
branches are created off the 'main' branch to add features or fix bugs to the
framework. After the code has been peer reviewed, it can be merged back into
the 'main' branch. Git tags **will** be used to mark specific points in 'main's
history indicating release of the framework. The Git tags will use standard
[semantic versioning](https://semver.org/).

### Code commits ###
Two main types of Git commits are used in the framework: standard code commits
and "housekeeping" commits.  The distinguishing feature of a code commit is
that it should only contain code changes. Any comments are whitespaces in these
commits should be releated the code changes,  e.g.:

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

If more explanation for the commit should be document, add a blank line, then
add as much explanation as you need. If you find yourself writing a long
explanation of the commit, take a moment to consider whether or not the
explanation would be better documented as comments in the code. Either way,
always have a mind to posterity when writing commits messages.

The comment should always end with the branch name. It should be prefaced with
'On branch ':

	On branch page-event

This exact text will be provide for you when you run `git commit -v` in the
commented area, so you can easily copy-and-paste it.

### Housekeeping commits ###
Housekeeping commits mainly consist of post facto comments, whitespace
changes, changes to documentation files, and other such changes that
have very little to do with computer logic.  They typically have one
word in their commit message: "Housekeeping" since most housekeeping
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
code commits** is that analysis tool, such as `git log` can include or
exclude housekeeping commits. Being able to exclude housekeeping commits
is convenient for code analysis because the analist can focus on the
code logic while excluding changes in comments, whitespace formatting,
etc. To view code change while excluding housekeeping changes, you can
use a command like this:

    git log -p --grep Housekeeping --invert-grep

Removing `--invert-grep` shows only the housekeeping commits.

Current Memory Issues
---------------------

At the moment, there is an unresolved issue with the way test.py
accumulates memory as it runs: It never seems to free certain a large
portion of the objects it creates, and ends up allocating for itself
several hundred megabytes of memory before it has completed. 

On the machine the framework is currently being developed, there is a
total of 1GB of RAM. Occasionally, the test.py script will consume so
much that that the operating system's oom\_reaper will cause MySQL to
restart, which causes tests in the script to begin to fail. A convenient
solution to this is to simply ensure that the following line is set in
`/etc/mysql/my.cnf`:
    
    [mysqld]
    performance_schema = 0

Restart the mysqld and it's default memory consumption will reduce by
several hundred megabytes.

Read this [Stack Overflow question](https://stackoverflow.com/questions/10676753/reducing-memory-consumption-of-mysql-on-ubuntuaws-micro-instance)
for more details.

TODO In the future, the `dba` bot should ensure this line is added.

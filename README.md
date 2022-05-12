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

<a id="assets-configuration"></a>
## Configuration ##

Hacking
-------
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

TODO Explain how to view the SQL being sent to MySQL using the snapshot
context manager:
    with db.chronicler.snapshot():
        B()
        print(self.asset_parties)

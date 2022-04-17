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

Current Memory Issues
=====================

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

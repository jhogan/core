Core
====
A web framework.

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

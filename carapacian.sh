#!/usr/bin/bash

# This shell script shouldn't be run. It documents and explain what
# steps should be taken to set up a server that allows developers to
# create Gunicorn UNIX sockets that can be read and written to by Nginx.

# Use /run/core to put Gunicorn's UNIX sockets in
mkdir -p /run/core

# The directory should be accessable by Nginx so allow www-data access
# to it.
chgrp www-data /run/core
chown 770 /run/core

# Create a Gunicorn process like this. You can access it through Nginx
# with a URL like http://3b6b9aae.carapacian.com
gunicorn -b unix:/run/core/3b6b9aae.sock

# Put it in the www-data group so Nginx can r/w it
chgrp www-data /run/core/3b6b9aae.sock

# Adjust the socket so users in the www-data group can r/w it. 
chmod 770 /run/core/3b6b9aae.sock

# Make sure that developers are in the www-data group so they can create
# the sockets when they run `gunicorn' as we did above.
usermod -a -G www-data $DEVELOPER_USER_NAME

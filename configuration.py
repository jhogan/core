# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022

# TODO Add a `store` property. This is already being implemented in
# config.py. See file.inode.store.

# TODO Add a postmark property that raises a NotImplementedError. It
# should be overridden by config.py and return the postmark account from
# the `accounts` collection.

# TODO Reevaluate whether or not this needs to be a singlton. In
# retrospect, it doesn't appear that this adds much value. If it dose,
# use the __new__ method to manager the singleton and get rid of
# `getinstance`.

# TODO Determine whther this class should be abstract, that is to say,
# should we permit code to instantiate it. I don't think so. Code should
# only instantiate the `config` class. That way, the code will be taking
# advantage of custom configurations.

import accounts
from dbg import B

class configuration:
    """ This is the base configuration class. It contains configuration
    date that is stored in the version-control system.  However, it is
    never instantiated directly by application code. A subclass of
    ``configuration``, which is conventionally called ``config``,
    subclasses ``configuration`` to provide sensitive information to
    ``configuration``'s values.  ``config`` is the class that is used by
    application code despite never being versioned. A typical
    implementation of ``config`` might look like::

        from configuration import configuration

        class config(configuration):
            @property
            def accounts(self):
                ''' Override the accounts property to set the
                password for the accounts.
                '''

                accts = super().accounts
                for acct in accts:
                    
                    # All the passwords happen to be
                    # 'my-super-secret-password'
                    acct.password = 'my-super-secret-password'

                return accts

    You will want to make sure you have an unversioned file in your
    source code directory called config.py that has the ``config``
    class. This will contain the sensitive configuration data. If you
    don't have it, ask a team member.
    """
    recaptcha_key = '<RECAPTCHA-KEY>'

    # TODO Force the environment veriable to be set in the `config` class
    # by providing an environment @property here that raises
    # NotImplementedError
    environment = 'development'

    _instance = None
    @classmethod
    def getinstance(cls):
        """ Get the singleton instance of the configuration.

        :param: cls type: The ``configuration`` class or a subtype
        thereof.
        """
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    @property
    def inproduction(self):
        """ Returns True if the current environment is considered a
        production system per the configuration.
        """
        return self.environment == 'production'

    @property
    def indevelopment(self):
        """ Returns True if the current environment is considered a
        development system per the configuration.
        """
        return self.environment == 'development'

    @property
    def accounts(self):
        """ A collection of credentials used by the system. Passwords
        will be supplied by the ``config`` subclass.
        """
        return accounts.accounts(
            initial = [
                accounts.mysql(
                    username = 'epitest',
                    host     = 'localhost',
                    password = None,
                    database = 'epitest',
                ),
                accounts.postmark(
                    server = 'carapacian.com',
                )
            ]
        )

    @property
    def log(self):
        """ The configuration writing to syslogd.
        """
        return {
            'addr': '/dev/log', 
            'fac': 'user',
            'tag': 'CORETEST', 
            'fmt': '[%(process)d]: %(levelname)s '
                  '%(message)s (%(pathname)s:%(lineno)d) ',
            'lvl': 'NOTSET',
        }

    @property
    def jwtsecret(self):
        """ The secret code to sign JWTs for the system.
        """
        raise NotImplementedError('Must override')



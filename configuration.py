# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019

import accounts
from dbg import B
from logs import *

class configuration:
    """ This is the base configuration class. It contains configuration
    datt that can and should be stored in version-control system.
    However, it is never instantiated directly by application code. A
    subclass of ``configuration``, which is conventionally called
    ``config``, subclasses ``configuration`` to provide sensitive
    information to ``configuration``'s values.  ``config`` is the class
    that is used by application code despite never being versioned. A
    typical implementation of ``config`` might look like::

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
    """
    recaptcha_key = '<RECAPTCHA-KEY>'
    environment = 'development'

    def __init__(self):
        self._logs = None

    _instance = None
    @classmethod
    def getinstance(cls):
        if not cls._instance:
            cls._instance = cls()
        return cls._instance

    @property
    def inproduction(self):
        return self.environment == 'production'

    @property
    def indevelopment(self):
        return self.environment == 'development'

    @property
    def accounts(self):
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
    def logs(self):
        if not self._logs:
            self._logs = logs()
            self._logs += log(
                addr = '/dev/log', 
                fac = 'user',
                tag = 'CORETEST', 
                fmt = '[%(process)d]: %(levelname)s '
                      '%(message)s (%(pathname)s:%(lineno)d) ',
                lvl = 'NOTSET',
            )
        return self._logs

    @property
    def jwtsecret(self):
        raise NotImplementedError('Must override')


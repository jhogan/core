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
    recaptcha_key = '<RECAPTCHA-KEY>'
    environment = 'development'

    def __init__(self):
        self._logs = None

    @property
    def inproduction(self):
        return self.environment == 'production'

    @property
    def accounts(self):
        return accounts.accounts(
            accounts.mysql(
                username = 'epitest',
                host     = 'localhost',
                password = None,
                database = 'epitest',
            )
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


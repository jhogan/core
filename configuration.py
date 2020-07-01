# vim: set et ts=4 sw=4 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2019

import accounts
from dbg import B

class configuration:
    recaptcha_key = '<RECAPTCHA-KEY>'
    environment = 'development'

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


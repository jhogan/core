# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021
########################################################################

""" This module contains all classes related to third party network
API's.

TODOs:
"""

from func import enumerate, B
import product

class internetservices(product.services):
    pass

class apis(internetservices):
    pass

class internetservice(product.service):
    pass

class mails(apis):
    pass

class postmarks(mails):
    pass

class api(internetservice):
    # The secret API KEY
    key = str

    # Credentials
    username = str
    password = str

    host = str
    port = int

    @property
    def browser(self):
        if not self._browser:
            self._browser = www.browser()

            self.browser.onbeforerequest += \
                self._browser_onbeforerequest

        return self._browser

    def _browser_onbeforerequest(self, src, eargs):
        pass

class mail(api):
    def send(self):
        raise NotImplementedError(
            'Must be implemented by a subentity'
        )

class postmark(mail):
    """ A transactional email provider.

    URL: https://postmarkapp.com
    """
    def send(self, dis):
        """

        :param: dis message.delevery: The message delevery entity to
        send. Note that the delivery object will have the actual message
        entity that we are sending.
        """
        tab = self.browser.tab()

        msg = dis.message

        # TODO Convert msg to JSON

        res = tab.post()

        

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
import www
import json

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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._browser = None

    @property
    def browser(self):
        if not self._browser:
            self._browser = www.browser()

            '''
            self.browser.onbeforerequest += \
                self._browser_onbeforerequest
            '''

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
        import party
        body = {
            'From': str(msg.from_),
            'To': str(msg.gettos(type=party.email)),
            # TODO Add CC
            # TODO Add BCC
            'Subject': msg.subject,
            'HtmlBody', msg.html,
            'TextBody', msg.text,

        }
        print(json.dumps(body))
        B()

        # TODO Convert msg to JSON

        res = tab.post()

        

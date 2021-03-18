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
import pom
from config import config

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

    class Error(Exception):
        def __init__(self, ex):
            self.inner = ex
            self._code = None
            self._message = None

        @property
        def status(self):
            return self.inner.status

        @property
        def reason(self):
            return self.inner.reason

        @property
        def code(self):
            # Error code returned by API in response body. Distinct from
            # the HTTP status code.
            return self._code

        @code.setter
        def code(self, v):
            self._code = v

        @property
        def message(self):
            # Error message returned by API in response body. Distinct from
            # the HTTP status reason/phrase.
            return self._message

        @message.setter
        def message(self, v):
            self._message = v

        def __str__(self):
            r = str()

            if self.status:
                r += f'HTTP Status: {self.status}'

            if self.reason:
                if r: r += ' '
                r += f'{self.reason}.'

            if self.code:
                if r: r += ' '
                r += f'Server Error Code {self.code}'

            if self.message:
                if r: r += ' - '
                r += self.message

            return r

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
        tos = msg.getcontachmechanisms(type=party.email, name='to')
        ccs = msg.getcontachmechanisms(type=party.email, name='cc')
        bccs = msg.getcontachmechanisms(type=party.email, name='bcc')

        body = {
            'From':      str(msg.from_),
            'To':        str(tos),
            'Subject':   msg.subject,
            'HtmlBody':  msg.html,
            'TextBody':  msg.text,
        }

        if ccs.count:
            body['Cc'] = str(ccs)

        if bccs.count:
            body['Bcc'] = str(bccs)

        if msg.replyto:
            body['ReplyTo'] = msg.replyto.name

        # XXX Remove
        ws = pom.site(host='api.postmarkapp.com')
        pg = pom.page(name='email')


        req = www._request(url='https://api.postmarkapp.com/email')
        req.method = 'POST'
        req.headers += 'Accept: application/json'
        req.headers += 'Content-Type: application/json'
        
        key = config().postmark.key
        req.headers += f'X-Postmark-Server-Token: {key}'

        req.payload = json.dumps(body)

        import urllib
        try:
            res = tab.request(req)
        except urllib.error.HTTPError as ex:
            err = api.Error(ex)
            msg = ex.read()
            try:
                msg = json.loads(msg)
            except:
                err.message = msg
            else:
                err.code    = msg['ErrorCode']
                err.message = msg['Message']
            raise err

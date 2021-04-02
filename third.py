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

from config import config
from func import enumerate, B
import ecommerce
import json
import pom
import product
import urllib
import www
import primative
from contextlib import contextmanager

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
        self._base = None  # Base URL

        # If we want our tests to use the actual API instead of a
        # simulated on, we can set _exsimulate to True.
        self._exsimulate = False

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

            if self.code:
                if r: r += ' '
                r += f'Server Error Code {self.code}'

            if self.message:
                if r: r += ' - '
                r += self.message

            res = str(self.inner.response)
            if res:
                if r:
                    r += f'\n\n{"-" * 72}\nResponse:\n'
                    r += res

            return r

class mail(api):
    def send(self):
        raise NotImplementedError(
            'Must be implemented by a subentity'
        )

class postmark(mail):
    """ A transactional and broadcast email provider.

    URL: https://postmarkapp.com
    """
    def send(self, dis):
        """ Send an email via Postmark Email Service
        (https://postmarkapp.com/).

        :param: dis message.delevery: The message delevery entity to
        send. Note that the delivery object will have the actual message
        entity that we are sending.
        """
        import party
        import message

        tab = self.browser.tab()
        msg = dis.message

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

        req = www._request(url=self.base / 'email')

        req.method = 'POST'
        req.headers += 'Accept: application/json'
        req.headers += 'Content-Type: application/json'
        
        req.headers += f'X-Postmark-Server-Token: {self.key}'

        req.payload = json.dumps(body)

        try:
            res = tab.request(req)
        except Exception as ex:
            ex1 = api.Error(ex)
            payload = json.loads(ex.response.payload)
            ex1.code = payload['ErrorCode']
            ex1.message = payload['Message']
            raise ex1
        else:
            dis.statuses += message.status(
                begin = primative.datetime.utcnow(),
                statustype = message.statustype(
                    name = 'dispatched'
                )
            )
            dis.externalid = res['MessageID']
            dis.save()
            return res

    @property
    def base(self):
        if not self._base:
            self._base = ecommerce.url(address='https://api.postmarkapp.com')
        return self._base

    @property
    def key(self):
        if config().indevelopment:
            if self._exsimulate:
                return config().postmark.key
            else:
                return 'POSTMARK_API_TEST'
        elif config().inproduction:
            return config().postmark.key
        else:
            raise ValueError('Unsupported environment type')

    @contextmanager
    def exsimulate(self):
        self._exsimulate = True
        yield
        self._exsimulate = False

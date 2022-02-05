# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2021
########################################################################

""" This module contains all classes related to third party network
API's. Examples of third-party APIs may include SMTP/POP,
RESTful/GraphQL, SOAP-based web services, etc. These protocols can be
used for messaging (SMS, email), credit card processing, mapping
services, and any other services provided by a remote system.
"""

from config import config
from contextlib import contextmanager
from func import enumerate
from dbg import B
import ecommerce
import json
import pom
import primative
import product
import www

class internetservices(product.services):
    """ A collection of ``internetservice`` entities.
    """

class apis(internetservices):
    """ A collection of third-party ``api`` services.
    """

class internetservice(product.service):
    """ A type of service provided through the internet, often for a
    fee.
    """

class dispatchers(apis):
    """ A collection of ``dispatcher`` entities.
    """

class emailers(dispatchers):
    """ A collection of ``emailer`` entities.
    """

class postmarks(emailers):
    """ A collection of ``postmarks`` entities.
    """

class api(internetservice):
    """ An ``api`` is a ``internetservice`` by which the framework can
    communicate with external systems. An ``api`` has a ``browser``
    property with which it can communicate with systems over HTTP.
    Future "devices" may include a ``terminal`` to communicate over
    telnet/SSH, or a ``socket`` to communicate directly with TCP or UDP
    ports.
    """
    def __init__(self, *args, **kwargs):
        """ Initialize the abstract API class.
        """
        super().__init__(*args, **kwargs)
        self._browser = None

        # The base URL for the api service. Any endpoint called by the
        # API would start with this string. This would be useful for
        # HTTP based APIs.
        self._base = None

        # If we want our tests to use the actual API instead of a
        # simulated on, we can set _exsimulate to True.
        self._exsimulate = False

    @property
    def browser(self):
        """ A browser object used by ``api`` subentities whose API
        interactions are based on HTTP requests.
        """
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
        """ An API exception. API exception are usually created and
        raised by subclasses of ``api`` in the event that there was an
        exception during the interation with the external host.
        Therefore, the Error exception has an ``inner`` property which
        contains a reference to the original exception. However,
        sometimes the API Error is raised in response to an error
        message or code successfully returned to the ``api`` subclass.
        In that case, the ``code`` and ``message`` property are set to
        the values returned by the server. (Consider a RESTful API
        returning a JSON object with a ``code`` and ``messsage`` property
        to indicate an error.)
        """
        def __init__(self, ex):
            # The network exception that caused the API Error to be
            # raised.
            self.inner = ex

            self._code = None
            self._message = None

        @property
        def status(self):
            return self.inner.status

        @property
        def reason(self):
            """ The HTTP reason phrase.
            """
            return self.inner.reason

        @property
        def code(self):
            """ Error code returned by API in response body.  Distinct
            from the HTTP status code.
            """
            return self._code

        @code.setter
        def code(self, v):
            self._code = v

        @property
        def message(self):
            """ The error message returned by API in response body.
            Distinct from the HTTP status reason/phrase.  
            """
            return self._message

        @message.setter
        def message(self, v):
            self._message = v

        def __str__(self):
            """ A string representation of the API Error.
            """
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

class dispatcher(api):
    """ Subclasses of ``dispatcher`` deal with interactions between
    external systems that involve the dispatching and monitoring of
    messages (``message.message``). Message ``dispactcher`` include
    ``emailer``, and presumably in the future: ``smsdispatcher``, and
    for postal mail``mailer``.
    """
    @staticmethod
    def create(dis):
        """ A static factory method that returns a ``dispatcher``
        subtype for the given dispatch object (``message.dispatch``).

        :param dis message.dispatch: A dispatch object which may or may
        not be used in the process of selecting the correct dispatcher.
        """

        # Get dispatcher type
        type = dis.dispatchtype.name

        if type == 'email':
            return emailer.create(dis)

        elif type == 'sms':
            # TODO 
            raise NotImplementedError(f'{type} dispatcher not implemented')
        elif type == 'postal':
            # TODO
            raise NotImplementedError(f'{type} dispatcher not implemented')

    def dispatch(self, dis):
        raise NotImplementedError(
            'Must be implemented by a concrete class'
        )

class emailer(dispatcher):
    """ A ``dispatcher`` class intended for the the processing of
    dispatches (``message.dispatch``) that include email contact
    mechanisms (``party.email``).
    """
    @staticmethod
    def create(dis):
        """ A static factory method used to select a concrete
        ``dispatcher`` capable of processing the dispatch object
        ``dis``.

        :param dis message.dispatch: A dispatch object which may or may
        not be used in the process of selecting the correct dispatcher.
        """
        # NOTE In the future, we may want to use additional emailers for
        # different reasons, but for now, we can stick with postmark.
        return postmark()

class postmark(emailer):
    """ A transactional and broadcast email provider.

    URL: https://postmarkapp.com
    """
    def dispatch(self, dis):
        """ Send an email via Postmark Email Service
        (https://postmarkapp.com/).

        The dispatch (``dis``) object`s ``statuses`` collection will
        receive an new entry to indicate how the interation with
        Postmark's service went.

        :param: dis message.dispatch: The messages' dispatch entity to
        send. Note that the dispach object will have the actual message
        entity that we are sending.
        """
        import party
        import message

        # Get a new browser tab to make HTTP calls.
        tab = self.browser.tab()

        msg = dis.message

        # Get the various contact machanisms the msg was addressed to
        tos = msg.getcontactmechanisms(type=party.email, name='to')
        ccs = msg.getcontactmechanisms(type=party.email, name='cc')
        bccs = msg.getcontactmechanisms(type=party.email, name='bcc')
        
        # Create a dict to turn into JSON for the api call
        body = {
            'From':      str(msg.from_),
            'To':        str(tos),
            'Subject':   msg.subject,
            'HtmlBody':  msg.html,
            'TextBody':  msg.text,
        }

        # Continue building the dict
        if ccs.count:
            body['Cc'] = str(ccs)

        if bccs.count:
            body['Bcc'] = str(bccs)

        if msg.replyto:
            body['ReplyTo'] = msg.replyto.name

        # Build the HTTP request object
        req = www._request(url=self.base / 'email')

        req.method = 'POST'
        req.headers += 'Accept: application/json'
        req.headers += 'Content-Type: application/json'
        
        req.headers += f'X-Postmark-Server-Token: {self.key}'

        # Set the request object's body to a json represenation of
        # the body dict. 
        req.body = json.dumps(body)

        try:
            # Make the HTTP request
            res = tab.request(req)
        except Exception as ex:
            # TODO Some work needs to be done here. If the API responds
            # in a way that implies a hard bounce then we should just
            # record the status entry as such and raise an error.
            # However, if it is a soft bounce, we should create a new
            # status for a soft-bounce. Additionally, for soft-bounces,
            # we should create a new dispatch. The dispatch should be
            # scheduled for dispatching at an appropriate time in the
            # future. Regardless, an api.Error should be raised to let
            # the client know about any issue: for example, if the
            # api.Error indicates a network outage, the client can
            # decide to cease dispatching for the moment.

            # Add a status record
            dis.statuses += message.status(
                begin = primative.datetime.utcnow(),
                statustype = message.statustype(
                    name = 'hard-bounce'
                )
            )

            # Save dispatch
            dis.save()

            # HttpException have JSON responses so we can parse them
            # out. However, we may be getting a non-HttpException so
            # raise ex if we can't parse response. NOTE We may actually
            # want to create a seperate `except` block to deal with
            # HttpException's.
            try:
                # Convert Exception to api.Error exception
                ex1 = api.Error(ex)
                body = json.loads(ex.response.body)
                ex1.code = body['ErrorCode']
                ex1.message = body['Message']
            except:
                raise ex
            else:
                raise ex1
        else:
            # Successful POST to Postmark
            dis.statuses += message.status(
                begin = primative.datetime.utcnow(),
                statustype = message.statustype(
                    name = 'postmarked'
                )
            )
            dis.externalid = res['MessageID']
            dis.save()
            return res

    @property
    def base(self):
        """ The base URL for endpoints used by this ``api``class.
        """
        if not self._base:
            self._base = ecommerce.url(address='https://api.postmarkapp.com')
        return self._base

    @property
    def key(self):
        """ Returns the Postmark Server API Token. This is used for
        authenticating when making API calls to a Postmark server.

        https://postmarkapp.com/support/article/1008-what-are-the-account-and-server-api-tokens

        For HTTP API authentication, the key is used as the value for
        the X-Postmark-Server-Token header.

        The real key is found in the unversioned ``config.py`` file. The
        constant string literal, 'POSTMARK_API_TEST', is returned in
        development mode. When Postmark receives this literal, it will
        behave as if POSTs were sucessful, but won't actually send
        emails to recipient. 
        
        The POSTMARK_API_TEST is used when the environment is
        ``indevelopment``, however, this can be overriden by using the
        ``exsimulate`` context manager.
        """
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
        """ A context manager to break out of the simulation.

        When used, POSTs to Postmark will be unsimulated posts. That
        is to say: the 'POSTMARK_API_TEST' key won't be used for
        authentication (see docstring at postmark.key), but rather the
        real key found in config.py. 
        
        This can be useful for unit testing in certain situations. For
        example, Postmark can be manipulated into returning an
        non-successful response if the real token is used and a bad From
        email address is used. This way, unit tests can be written to
        ensure that errors from Postmark are handled correctly.
        """
        self._exsimulate = True
        yield
        self._exsimulate = False

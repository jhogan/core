# vim: set et ts=4 sw=4 fdm=marker
"""
MIT License

Copyright (c) 2016 Jesse Hogan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import smtplib
from email.message import EmailMessage
from email.headerregistry import Address
from entities import *
from pdb import set_trace; B=set_trace
from configfile import configfile


# TODO Write Tests
class email(entity):
    def __init__(self, type):
        self._type = type
        self._from = emailaddresses()
        self._to = emailaddresses()
        self._subject = ''
        self._text = ''

    @property
    def from_(self):
        return self._from

    @from_.setter
    def from_(self, v):
        self._from = v

    @property
    def to(self):
        return self._to

    @to.setter
    def to(self, v):
        self._to = v

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, v):
        self._text = v

    @property
    def type(self):
        return self._type

    def send(self):
        # TODO Add demandvalid()
        msg = EmailMessage()
        msg.set_content(self.text)

        msg['Subject'] = self.subject
        msg['From'] = self.from_.toaddress()
        msg['To'] = self.to.toaddresses()
        
        accts = configfile.getinstance().accounts

        accts = getattr(accts.smtpaccounts, self.type)

        for acct in accts:
            try:
                smtp = smtplib.SMTP(acct.host, acct.port)

                #smtp.set_debuglevel(1)

                smtp.login(acct.username, acct.password)
                smtp.send_message(msg)
                smtp.quit()
            except Exception:
                # Don't include username here because it can be the same
                # as password (e.g., smtp.postmarkapp.com).
                msg = 'Failed sending email using: ' + \
                      str(acct.host) + ':' + str(acct.port)

                self.log.exception(msg)
                continue

            break

class emailaddresses(entities):
    
    def toaddresses(self):
        r = []
        for addr in self:
            r.append(addr.toaddress())
        return r

class emailaddress(entity):
    def __init__(self, email, displayname):
        self._email = email
        self._displayname = displayname

    def toaddress(self):
        return Address(self.displayname, self.username, self.domain)

    @property
    def email(self):
        return self._email

    @property
    def displayname(self):
        return self._displayname

    @property
    def username(self):
        return self.email.split('@')[0]

    @property
    def domain(self):
        return self.email.split('@')[1]

    def __repr__(self):
        r = super().__repr__() + ' '
        r += self.displayname + ' <' + self.email + '>'
        return r





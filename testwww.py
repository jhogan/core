#!/usr/bin/python3
import apriori; apriori.model()

from datetime import timezone, datetime, date
from dbg import B
from func import enumerate, getattr
from uuid import uuid4
import tester
import www

class headers(tester.tester):
    def it_instantiates_headers(self):
        ''' Empty case '''
        hdrs = www.headers()
        self.zero(hdrs)

        ''' Sequences '''

        ''' List '''
        ls = [
            ('Content-Type', 'application/json'), 
            ('Accept-Encoding', 'gzip, deflate, br')
        ]

        hdrs = www.headers(ls)
        self.two(hdrs)
        self.eq('content-type', hdrs.first.name)
        self.eq('application/json', hdrs.first.value)
        self.eq('accept-encoding', hdrs.second.name)
        self.eq('gzip, deflate, br', hdrs.second.value)

        ''' Tuple '''
        tup = tuple(ls)

        hdrs = www.headers(tup)
        self.two(hdrs)
        self.eq('content-type', hdrs.first.name)
        self.eq('application/json', hdrs.first.value)
        self.eq('accept-encoding', hdrs.second.name)
        self.eq('gzip, deflate, br', hdrs.second.value)

        ''' Dict '''
        d = dict(ls)

        hdrs = www.headers(d)
        self.two(hdrs)
        self.eq('content-type', hdrs.first.name)
        self.eq('application/json', hdrs.first.value)
        self.eq('accept-encoding', hdrs.second.name)
        self.eq('gzip, deflate, br', hdrs.second.value)

        ''' kwargs '''
        hdrs = www.headers(
            Accept_Language = 'en-US,en;q=0.5', 
            Cache_Control   = 'public, max-age=2592000, s-maxage=2592000'
        )
        self.two(hdrs)
        self.eq('en-US,en;q=0.5', hdrs['accept-language'])
        self.eq(
            'public, max-age=2592000, s-maxage=2592000', 
            hdrs['cache-control']
        )

        ''' Sequence plus kwargs '''
        for seq in (ls, tup, d):
            hdrs = www.headers(
                d, 
                Accept_Language = 'en-US,en;q=0.5', 
                Cache_Control   = 'public, max-age=2592000, s-maxage=2592000'
            )
            self.four(hdrs)
            self.eq('application/json', hdrs['content-type'])
            self.eq('gzip, deflate, br', hdrs['accept-encoding'])
            self.eq('en-US,en;q=0.5', hdrs['accept-language'])
            self.eq(
                'public, max-age=2592000, s-maxage=2592000', 
                hdrs['cache-control']
            )

    def it_sets_values(self):
        hdrs = www.headers()
        hdrs += www.header('Content-Type', 'abc')
        hdrs += www.header('Accept-Language', 'xyz')

        self.eq('abc', hdrs['Content-Type'])
        self.eq('abc', hdrs.first.value)
        self.eq('xyz', hdrs.second.value)
        self.two(hdrs)

        # Ensure we can overwrite existing header
        hdrs['Content-Type'] = 'def'
        self.eq('def', hdrs['Content-Type'])
        self.eq('def', hdrs.first.value)
        self.eq('xyz', hdrs.second.value)
        self.two(hdrs)

        hdrs[0] = 'ghi'
        self.eq('ghi', hdrs['Content-Type'])
        self.eq('ghi', hdrs.first.value)
        self.eq('xyz', hdrs.second.value)
        self.two(hdrs)

class url(tester.tester):
    def it_gets_scheme(self):
        url = www.url('www.google.com')
        self.none(url.scheme)

        url = www.url('http://www.google.com')
        self.eq('http', url.scheme)

    def it_gets_host(self):
        url = www.url('www.google.com')
        self.none(url.host)

        url = www.url('http://www.google.com')
        self.eq('www.google.com', url.host)

    def it_gets_path(self):
        path = 'this/is/a/path'
        url = www.url(path)
        self.none(url.host)
        self.none(url.scheme)
        self.eq(path, url.path)

        url = www.url(f'http://www.google.com/{path}')
        self.eq('http', url.scheme)
        self.eq('www.google.com', url.host)
        self.eq('/' + path, url.path)

    def it_gets_query(self):
        url = www.url('http://www.google.com')
        self.none(url.query)

        url = www.url('http://www.google.com?s=test')
        self.eq('s=test', url.query)

    def it_gets_fragment(self):
        url = www.url('http://www.google.com')
        self.none(url.fragment)

        url = www.url('http://www.google.com#')
        self.none(url.fragment)

        url = www.url('http://www.google.com#frag')
        self.eq('frag', url.fragment)

        url = www.url('http://www.google.com?query=test#frag')

        self.eq('frag', url.fragment)

    def it_gets_username(self):
        url = www.url('http://www.google.com')
        self.none(url.username)

        url = www.url('http://uid@www.google.com')
        self.eq('uid', url.username)

        url = www.url('http://uid:pwd@www.google.com')
        self.eq('uid', url.username)

    def it_gets_password(self):
        url = www.url('http://www.google.com')
        self.none(url.password)

        url = www.url('http://uid@www.google.com')
        self.none(url.password)

        url = www.url('http://uid:pwd@www.google.com')
        self.eq('pwd', url.password)

    def it_gets_port(self):
        url = www.url('http://www.google.com')
        self.eq(80, url.port)

        url = www.url('https://www.google.com')
        self.eq(443, url.port)

        url = www.url('herpderp://www.google.com')
        self.none(url.port)

if __name__ == '__main__':
    tester.cli().run()

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
    def it_calls__init__(self):
        ''' With name '''
        url = www.url(
            'http://user:pass1@www.google.com:88?query=test#frag'
        )
        self.eq('http',            url.scheme)
        self.eq('user',            url.username)
        self.eq('pass1',           url.password)
        self.eq('www.google.com',  url.host)
        self.eq(88,                url.port)
        self.eq('query=test',      url.query)
        self.eq('frag',            url.fragment)

        ''' Without name '''
        url = www.url()
        self.none(url.scheme)
        self.none(url.username)
        self.none(url.password)
        self.none(url.host)
        self.none(url.port)
        self.none(url.query)
        self.none(url.fragment)

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

    def it_gets_qs(self):
        url = www.url('http://www.google.com')

        ### XXX
        #self.eq(dict(), url.qs)

        # Get a single qs params
        url = www.url('http://www.google.com?s=test')
        self.eq('test', url.qs['s'])

        # Get a multiple qs params
        url = www.url('http://www.google.com?s=test&lang=en')
        self.eq('test', url.qs['s'])
        self.eq('en', url.qs['lang'])

        # Test multiple values per param
        url = www.url('http://www.google.com?s=test&lang=en&lang=es')
        self.eq('test', url.qs['s'])
        self.eq(['en', 'es'], url.qs['lang'])

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

    def it_sets_host(self):
        url = www.url()
        url.host = 'www.google.com'
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.scheme = 'http'
        self.eq('http://www.google.com', str(url))
        self.eq('http://www.google.com', url.name)

    def it_sets_path(self):
        scheme = 'http'
        host = 'www.google.com'
        path =  'this/is/the/path'
        url = www.url()
        self.none(url.scheme)
        self.none(url.host)
        url.path = path
        self.eq(path, url.path)
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.host = host
        self.none(url.scheme)
        self.eq(path, url.path)
        self.eq(host, url.host)
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.scheme = scheme
        self.eq(scheme, url.scheme)
        self.eq(path, url.path)
        self.eq(host, url.host)
        self.eq(f'{scheme}://{host}/{path}', url.name)

    def it_sets_query(self):
        scheme = 'http'
        host = 'www.google.com'
        path =  'this/is/the/path'
        query = 'herp=derp&gerp=cherp'

        url = www.url()
        self.none(url.scheme)
        self.none(url.host)
        self.none(url.path)
        self.none(url.query)
        url.query = query
        self.eq(query, url.query)
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.scheme = scheme
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.host = host
        self.eq(f'{scheme}://{host}?{query}', url.name)
        self.eq(f'{scheme}://{host}?{query}', str(url))

        url.path = path
        self.eq(scheme, url.scheme)
        self.eq(path, url.path)
        self.eq(host, url.host)
        self.eq(f'{scheme}://{host}/{path}?{query}', url.name)
        self.eq(f'{scheme}://{host}/{path}?{query}', str(url))

    def it_sets_qs(self):
        ''' Setup URL object '''
        scheme = 'http'
        host = 'www.google.com'
        path =  'this/is/the/path'

        url = www.url()
        url.scheme = scheme
        url.host = host
        url.path = path

        ''' Assign dict '''
        url.qs = {'key': 'value'}

        self.eq('key=value', url.query)
        self.eq(f'{scheme}://{host}/{path}?key=value', url.name)
        self.eq(f'{scheme}://{host}/{path}?key=value', str(url))


        ''' Assign empty dict '''
        url.qs = dict()

        self.none(url.query)
        self.eq(f'{scheme}://{host}/{path}', url.name)
        self.eq(f'{scheme}://{host}/{path}', str(url))


        ''' Assign param '''
        url.qs['key'] = 'value'

        self.eq('key=value', url.query)
        self.eq(f'{scheme}://{host}/{path}?key=value', url.name)
        self.eq(f'{scheme}://{host}/{path}?key=value', str(url))

        ''' Assign new param '''
        url.qs['key1'] = 'value1'

        expect = 'key=value&key1=value1'
        self.eq(expect, url.query)

        expect = f'{scheme}://{host}/{path}?{expect}'
        self.eq(expect, url.name)
        self.eq(expect, str(url))

        ''' Reassign new param '''
        url.qs['key1'] = 'value2'

        expect = 'key=value&key1=value2'
        self.eq(expect, url.query)

        expect = f'{scheme}://{host}/{path}?{expect}'
        self.eq(expect, url.name)
        self.eq(expect, str(url))

        url.qs['key1'] = ['value1', 'value2']

        expect = 'key=value&key1=value1&key1=value2'
        self.eq(expect, url.query)

        expect = f'{scheme}://{host}/{path}?{expect}'
        self.eq(expect, url.name)
        self.eq(expect, str(url))

    def it_calls__contains_on__qs(self):
        ''' Setup URL object '''
        scheme = 'http'
        host = 'www.google.com'
        path = 'this/is/the/path'

        url = www.url()
        url.scheme = scheme
        url.host = host
        url.path = path

        ''' Assign dict '''
        url.qs = {'key': 'value'}

        self.in_(url.qs, 'key')
        self.notin(url.qs, 'not-in-qs')
        
    def it_dels_qs(self):
        ''' Setup URL object '''
        scheme = 'http'
        host = 'www.google.com'
        path =  'this/is/the/path'

        url = www.url()
        url.scheme = scheme
        url.host = host
        url.path = path

        ''' Assign dict '''
        url.qs['a'] = 1
        url.qs['b'] = 2
        url.qs['c'] = 3

        self.eq(
            'http://www.google.com/this/is/the/path?a=1&b=2&c=3',
            str(url)
        )

        del url.qs['a']

        self.eq(
            'http://www.google.com/this/is/the/path?b=2&c=3',
            str(url)
        )

        del url.qs['b']

        self.eq(
            'http://www.google.com/this/is/the/path?c=3',
            str(url)
        )

        del url.qs['c']

        self.eq(
            'http://www.google.com/this/is/the/path',
            str(url)
        )

    def it_sets_fragment(self):
        scheme = 'http'
        host = 'www.google.com'
        path =  'this/is/the/path'
        query = 'herp=derp&gerp=cherp'
        frag = 'this-part'

        url = www.url()
        self.none(url.scheme)
        self.none(url.host)
        self.none(url.path)
        self.none(url.query)
        self.none(url.fragment)
        url.fragment = frag
        self.eq(frag, url.fragment)
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.scheme = scheme
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.path = path
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.query = query
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.host = host
        self.eq(f'{scheme}://{host}/{path}?{query}#{frag}', url.name)
        self.eq(f'{scheme}://{host}/{path}?{query}#{frag}', str(url))

    def it_sets_username(self):
        scheme = 'http'
        host = 'www.google.com'
        path =  'this/is/the/path'
        query = 'herp=derp&gerp=cherp'
        frag = 'this-part'
        username = 'username'

        url = www.url()
        self.none(url.scheme)
        self.none(url.host)
        self.none(url.path)
        self.none(url.query)
        self.none(url.fragment)
        self.none(url.username)

        url.username = username
        self.eq(username, url.username)
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.fragment = frag
        self.eq(frag, url.fragment)
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.scheme = scheme
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.path = path
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.query = query
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.host = host
        self.eq(
            f'{scheme}://{username}@{host}/{path}?{query}#{frag}', 
            url.name
        )

        self.eq(
            f'{scheme}://{username}@{host}/{path}?{query}#{frag}', 
            str(url)
        )

    def it_sets_password(self):
        scheme = 'http'
        host = 'www.google.com'
        path =  'this/is/the/path'
        query = 'herp=derp&gerp=cherp'
        frag = 'this-part'
        username = 'username'
        password = 'password'

        url = www.url()
        self.none(url.scheme)
        self.none(url.host)
        self.none(url.path)
        self.none(url.query)
        self.none(url.fragment)
        self.none(url.username)
        self.none(url.password)

        url.password = password
        self.eq(password, url.password)
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.username = username
        self.eq(username, url.username)
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.fragment = frag
        self.eq(frag, url.fragment)
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.scheme = scheme
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.path = path
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.query = query
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.host = host
        expect = (
            f'{scheme}://{username}:{password}@{host}/{path}?{query}'
            f'#{frag}' 
        )

        self.eq(expect, url.name)
        self.eq(expect, str(url))

    def it_sets_port(self):
        scheme = 'http'
        host = 'www.google.com'
        path =  'this/is/the/path'
        query = 'herp=derp&gerp=cherp'
        frag = 'this-part'
        username = 'username'
        password = 'password'
        port = 88

        url = www.url()
        self.none(url.scheme)
        self.none(url.host)
        self.none(url.path)
        self.none(url.query)
        self.none(url.fragment)
        self.none(url.username)
        self.none(url.password)
        self.none(url.port)

        url.port = port
        self.eq(port, url.port)
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.password = password
        self.eq(password, url.password)
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.username = username
        self.eq(username, url.username)
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.fragment = frag
        self.eq(frag, url.fragment)
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.scheme = scheme
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.path = path
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.query = query
        self.expect(ValueError, lambda: url.name)
        self.expect(ValueError, lambda: str(url))

        url.host = host
        expect = (
            f'{scheme}://{username}:{password}@{host}:{port}'
            f'/{path}?{query}#{frag}' 
        )

        self.eq(expect, url.name)
        self.eq(expect, str(url))

        expect = (
            'url('
                'scheme="http", '
                'username="username", '
                'password="password", '
                'host="www.google.com", '
                'port=88, '
                'path="this/is/the/path", '
                'query="herp=derp&gerp=cherp", '
                'fragment="this-part"'
            ')'
        )

        self.eq(expect, repr(url))

if __name__ == '__main__':
    tester.cli().run()

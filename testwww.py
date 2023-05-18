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
        self.eq(url.host, url.name)
        self.eq(url.host, str(url))

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
        self.eq('/' + path, url.name)
        self.eq('/' + path, str(url.name))

        url.host = host
        self.none(url.scheme)
        self.eq(path, url.path)
        self.eq(host, url.host)
        self.eq(host + '/' + path, url.name)
        self.eq(host + '/' + path, str(url))

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
        self.eq('?' + query, url.name)
        self.eq('?' + query, str(url))

        url.scheme = scheme
        self.eq('http://?herp=derp&gerp=cherp', url.name)
        self.eq('http://?herp=derp&gerp=cherp', str(url))

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
        self.eq('#' + frag, url.name)
        self.eq('#' + frag, str(url))

        url.scheme = scheme
        self.eq(scheme + '://#' + frag, url.name)
        self.eq(scheme + '://#' + frag, str(url))

        url.path = path
        self.eq(scheme + ':///' + path + '#' + frag, url.name)
        self.eq(scheme + ':///' + path + '#' + frag, str(url))

        url.query = query
        self.eq(f'{scheme}:///{path}?{query}#{frag}', url.name)
        self.eq(f'{scheme}:///{path}?{query}#{frag}', str(url))

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
        self.eq(f'{username}@', url.name)
        self.eq(f'{username}@', str(url))

        url.fragment = frag
        self.eq(frag, url.fragment)
        self.eq(f'{username}@#{frag}', url.name)
        self.eq(f'{username}@#{frag}', str(url))

        url.scheme = scheme
        self.eq(f'{scheme}://{username}@#{frag}', url.name)
        self.eq(f'{scheme}://{username}@#{frag}', str(url))

        url.path = path
        self.eq(f'{scheme}://{username}@/{path}#{frag}', url.name)
        self.eq(f'{scheme}://{username}@/{path}#{frag}', str(url))

        url.query = query
        self.eq(
            f'{scheme}://{username}@/{path}?{query}#{frag}', url.name
        )
        self.eq(
            f'{scheme}://{username}@/{path}?{query}#{frag}', 
            str(url)
        )

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
        self.eq(f':{password}@', url.name)
        self.eq(f':{password}@', str(url))

        url.username = username
        self.eq(username, url.username)
        self.eq(f'{username}:{password}@', url.name)
        self.eq(f'{username}:{password}@', str(url))

        url.fragment = frag
        self.eq(frag, url.fragment)
        self.eq(f'{username}:{password}@#{frag}', url.name)
        self.eq(f'{username}:{password}@#{frag}', str(url))

        url.scheme = scheme
        self.eq(f'{scheme}://{username}:{password}@#{frag}', url.name)
        self.eq(f'{scheme}://{username}:{password}@#{frag}', str(url))

        url.path = path
        self.eq(
            f'{scheme}://{username}:{password}@/{path}#{frag}', url.name
        )
        self.eq(
            f'{scheme}://{username}:{password}@/{path}#{frag}', str(url)
        )


        url.query = query
        self.eq(
            f'{scheme}://{username}:{password}@/{path}?{query}#{frag}', 
            url.name
        )
        self.eq(
            f'{scheme}://{username}:{password}@/{path}?{query}#{frag}', 
            str(url)
        )

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
        self.eq(f':{port}', url.name)
        self.eq(f':{port}', str(url))

        url.password = password
        self.eq(password, url.password)
        self.eq(f':{password}@:{port}', url.name)
        self.eq(f':{password}@:{port}', str(url))

        url.username = username
        self.eq(username, url.username)
        self.eq(f'{username}:{password}@:{port}', url.name)
        self.eq(f'{username}:{password}@:{port}', str(url))

        url.fragment = frag
        self.eq(frag, url.fragment)
        self.eq(f'{username}:{password}@:{port}#{frag}', url.name)
        self.eq(f'{username}:{password}@:{port}#{frag}', str(url))

        url.scheme = scheme
        self.eq(
            f'{scheme}://{username}:{password}@:{port}#{frag}', 
            url.name
        )
        self.eq(
            f'{scheme}://{username}:{password}@:{port}#{frag}', 
            str(url.name)
        )


        url.path = path
        self.eq(
            f'{scheme}://{username}:{password}@:{port}/{path}#{frag}', 
            url.name
        )
        self.eq(
            f'{scheme}://{username}:{password}@:{port}/{path}#{frag}', 
            str(url.name)
        )

        url.query = query
        expect = (
            f'{scheme}://{username}:{password}@:{port}'
            f'/{path}?{query}#{frag}'
        )

        self.eq(expect, url.name)
        self.eq(expect, str(url))

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

    def it_calls_normal(self):
        url = www.url('HTtp://')
        self.eq('http://', url.normal)

        url = www.url('HTtp://eXample.org')
        self.eq('http://example.org:80', url.normal)

        url = www.url('HTtp://eXample.org:8181')
        self.eq('http://example.org:8181', url.normal)

        url = www.url('HTtp://eXample.org:8181/Index.html')
        self.eq('http://example.org:8181/Index.html', url.normal)

        url = www.url('HTtp://eXample.org:8181/Index.html')
        self.eq('http://example.org:8181/Index.html', url.normal)

        url = www.url('HTtp://eXample.org:8181/Path/Index.html')
        self.eq('http://example.org:8181/Path/Index.html', url.normal)

        url = www.url('HTtp://eXample.org:8181/Path/Index.html?a=1')
        self.eq(
            'http://example.org:8181/Path/Index.html?a=1', 
            url.normal
        )

        url = www.url('HTtp://eXample.org:8181/Path/Index.html?a=1&b=2')
        self.eq(
            'http://example.org:8181/Path/Index.html?a=1&b=2', 
            url.normal
        )

        url = www.url('HTtp://eXample.org:8181/Path/Index.html?b=2&a=1')
        self.eq(
            'http://example.org:8181/Path/Index.html?a=1&b=2', 
            url.normal
        )

        url = www.url('HTtp://eXample.org:8181?b=2&a=1&a=3')
        self.eq(
            'http://example.org:8181?a=1&a=3&b=2', 
            url.normal
        )

        url = www.url('HTtp://eXample.org:8181?b=2&a=3&a=1')
        self.eq(
            'http://example.org:8181?a=3&a=1&b=2', 
            url.normal
        )

        url = www.url('HTtp://eXample.org:8181?B=2&a=3&a=1')
        self.ne(
            'http://example.org:8181?B=2&a=1&a=3', 
            url.normal
        )

        url = www.url('HTtp://eXample.org:8181?a=1&a=3&B=2')
        self.eq(
            'http://example.org:8181?B=2&a=1&a=3', 
            url.normal
        )


        url = www.url('HTtp://eXample.org:8181?B=2&a=3&a=1#frag')
        self.ne(
            'http://example.org:8181?B=2&a=1&a=3#frag', 
            url.normal
        )

    def it_sets_name(self):
        url = www.url()
        url.name = 'http://example.org:8181?b=2&a=3&a=1#frag'
        self.eq('http://example.org:8181?b=2&a=3&a=1#frag', url.name)

        url.name = None
        self.none(url.name)

    def it_calls__eq__(self):
        ''' Scheme '''
        url = www.url('http://')
        url1 = www.url('https://')

        self.ne(url, url1)

        # TODO:8ae59b01 
        #self.two(set([url, url1]))

        url = www.url('https://')
        url1 = www.url('HTTPS://')

        self.eq(url, url1)

        # TODO:8ae59b01 Implement __hash__ so this will work.
        #self.one(set([url, url1]))

        ''' Scheme and host'''
        url.host = 'example.org'
        url1.host = 'example.com'

        self.ne(url, url1)

        url.host = 'EXAMPLE.COM'

        self.eq(url, url1)

        ''' Scheme, host and port'''
        url.port = 80
        url1.port = 8080

        self.ne(url, url1)

        url1.port = 80

        self.eq(url, url1)

        ''' Scheme, host, port and path'''
        url.path = 'index.html'
        url1.path = 'INDEX.HTML'

        self.ne(url, url1)

        url1.path = 'index.html'

        self.eq(url, url1)

        ''' Scheme, host, port, path and query string'''

        # Count
        url.query = 'a=1&b=1'
        url1.query = 'b=1'

        self.ne(url, url1)

        url1.query = 'a=1&b=1'

        self.eq(url, url1)

        # Values
        url.query = 'a=1&b=1'
        url1.query = 'a=1&b=2'


        self.ne(url, url1)

        url1.query = 'a=1&b=1'

        self.eq(url, url1)

        # Order of query params should not matter
        url.query = 'a=1&b=2'
        url1.query = 'b=2&a=1'

        self.eq(url, url1)

        # Order of query parameter "arrays" should matter
        url.query = 'a=1&b=2&b=1&b=0'
        url1.query = 'b=2&b=1&b=0&a=1'

        self.eq(url, url1)

        url1.query = 'b=0&b=1&b=2&a=1'

        self.ne(url, url1)


if __name__ == '__main__':
    tester.cli().run()

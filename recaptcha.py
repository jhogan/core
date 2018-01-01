import urllib
import urllib.request
import json

def validate(response, key):
    url = 'https://www.google.com/recaptcha/api/siteverify'

    values = {
        'secret': key,
        'response': response
    }

    data = urllib.parse.urlencode(values).encode()
    req =  urllib.request.Request(url, data=data)
    res = urllib.request.urlopen(req)
    return json.loads(res.read().decode())

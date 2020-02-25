# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2020
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

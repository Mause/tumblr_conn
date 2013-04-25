#!/usr/bin/env python
#
# Copyright 2012 Dominic May
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"generic items of utility"

# stdlib
import json
import urllib.parse

# thind party
import tornado.web
from requests.auth import AuthBase

default_status = {
    'queue': [],
    'queue_len': 0,
    'cur_index': 0,
    'running': False,
    'starttime': 0,
    'endtime': 0,
    'failed': False
}


class Session(dict):
    def __init__(self, handler):
        self.handler = handler

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def __getitem__(self, key):
        if key not in self.handler.request.cookies:
            raise KeyError('"{}" not in session'.format(key))
        else:
            value = self.handler.get_secure_cookie(key)
            value = value.decode('utf-8')
            value = json.loads(value)
            return value

    def __setitem__(self, key, value):
        value = json.dumps(value)
        return self.handler.set_secure_cookie(key, value)

    def __iter__(self):
        for item in self.handler.request.cookies.keys():
            yield item


# misc
class ParamAuth(AuthBase):
    """Adds API key to the given Request object's url."""
    def __init__(self, params):
        self.params = params

    def __call__(self, r):
        # modify and return the request
        extra = urllib.parse.urlencode(self.params)
        url = r.url.split('?')
        if len(url) > 1:
            first, second = url
            r.url = first + '?' + extra + '&' + second
        else:
            r.url = r.url + '?' + extra

        return r


class BaseHandler(tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        self.session = Session(self)
        return super(BaseHandler, self).__init__(*args, **kwargs)

    def render(self, filename, **template_values):
        """
        convenience function, performs monotonous operations
        required whenever a template needs to be rendered
        """
        if "to_console" not in list(template_values.keys()):
            template_values["to_console"] = {}

        super(BaseHandler, self).render(filename, **template_values)


def main():
    print(issubclass(Session, dict))

if __name__ == '__main__':
    main()

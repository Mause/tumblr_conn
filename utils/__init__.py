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

# stdlib
import json
import urllib.parse

# thind party
import iron_mq
import iron_cache

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


# mockers
class MemcacheContainer(object):
    caches = {}

    def __getitem__(self, cache_name):
        if cache_name not in self.caches:
            self.caches[cache_name] = iron_cache.IronCache(cache_name)
        return self.caches[cache_name]


memcache = MemcacheContainer()


class Message(object):
    def __init__(self, queue_obj, message):
        self.queue_obj = queue_obj
        self.messages = message['messages']

        for i, m in enumerate(self.messages):
            try:
                self.messages[i]['body'] = json.loads(m['body'])
            except (TypeError, ValueError):
                # if it aint
                pass

    def empty(self):
        return not self.messages

    def __getitem__(self, name):
        assert type(self.messages) == list
        assert type(self.messages[0]) == dict
        assert type(self.messages[0]['body']) == dict, self.messages[0]

        return self.messages[0]['body'].__getitem__(name)

    def delete(self):
        m_id = self.messages[0]['id']
        return self.queue_obj.delete(m_id)

    def __repr__(self):
        return '<Message {}>'.format(
            self.messages[0]['body']
            if not self.empty() else {})


class Taskqueue(object):
    # IronMQ wrapper
    def __init__(self, iron_mq, queues):
        self.iron_mq = iron_mq
        self.queues = {
            name: iron_mq.queue(name)
            for name in queues}
        self.default = 'blogs'

    def get(self, queue_name=None):
        selected_queue = queue_name or self.default

        message = self.queues[selected_queue].get()
        return Message(self.queues[selected_queue], message)

    def add(self, params, url=None, queue_name=None):
        # this is just a wrapper. in this implementation, we always ignore the url
        selected_queue = queue_name or self.default

        params = json.dumps(params)
        return self.queues[selected_queue].post(params)

taskqueue = Taskqueue(iron_mq.IronMQ(), ['blogs'])


class Session(dict):
    def __init__(self, handler):
        self.handler = handler

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def __getitem__(self, key):
        value = self.handler.get_secure_cookie(key)

        if not value:
            raise KeyError('"{}" not in session'.format(key))
        else:
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

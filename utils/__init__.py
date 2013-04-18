# stdlib
import json
import urllib.parse
from queue import Queue

# thind party
import tornado.web
from requests.auth import AuthBase


# this is more for debugging, to ensure it never gets changed
# and yes i know it is bad practice, as it is non-pythonic
class ConstantDict(dict):
    pass
    # def __init__(self, dictionary):
    #     self.dictionary = dictionary

    # def __getitem__(self, key):
    #     return self.dictionary.__getitem__(key)

    # def __repr__(self):
    #     return self.dictionary.__repr__()

    # def __setitem__(self, key, value):
    #     raise TypeError('Dictionary is constant')

default_status = ConstantDict({
    'queue': [],
    'cur_index': 0,
    'running': False,
    'starttime': 0,
    'endtime': 0,
    'failed': False
})


# mockers
class Memcache(dict):
    cache = {}

    def get(self, key):
        return super(Memcache, self).get(key)

    def set(self, key, value):
        self[key] = value

memcache = Memcache()


class Taskqueue(object):
    my_queue = Queue()

    def add(self, **kwargs):
        self.my_queue.put(kwargs)

taskqueue = Taskqueue()


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
        # logging.info('{}: {}'.format(key, value))
        if not value:
            raise KeyError
        else:
            value = value.decode('utf-8')
            value = json.loads(value)
            return value

    def __setitem__(self, key, value):
        value = json.dumps(value)
        return self.handler.set_secure_cookie(key, value)

    def __iter__(self):
        for item in self.request.cookies.keys():
            yield item


# misc
class APIKeyAuth(AuthBase):
    """Adds API key to the given Request object's url."""
    def __init__(self, api_key):
        self.api_key = api_key

    def __call__(self, r):
        # modify and return the request
        extra = urllib.parse.urlencode({'api_key': self.api_key})
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

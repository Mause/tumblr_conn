# stdlib
import json
import urllib.parse
from queue import Queue

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


# mockers
class Memcache(dict):
    # this will also be networked in the final implementation
    # * Memcached
    # * redis
    # * IronCache
    def get(self, key, default=None):
        return super(Memcache, self).get(key, default)

    def set(self, key, value):
        self[key] = value

memcache = Memcache()


class Taskqueue(Queue):
    # in the final implementation, this will be network based
    # so that both the web dyno's and the worker dyno's can access it

    # This may be one of a few things;
    # * custom postgres based implementation
    # * redis queue
    # * zmq queue (actually, no)
    # * IronMQ

    # this will probably end up being a wrapper
    pass

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

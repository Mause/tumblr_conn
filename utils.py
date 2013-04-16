import time
import json
import logging
import urllib.parse
from itertools import chain
from queue import Queue

import requests
import tornado.web
from requests.auth import AuthBase

default_status = {
    'queue': [],
    'cur_index': 0,
    'running': False,
    'starttime': 0,
    'endtime': 0,
    'failed': False}


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


# tumblr data accessing and processing
def reblog_path_source(hostname, post_id, auth):
    url = 'http://api.tumblr.com/v2/blog/{hostname}.tumblr.com/posts'.format(
        hostname=hostname)
    cur_post = requests.get(url,
                            auth=auth,
                            params={
                                "reblog_info": True,
                                "id": post_id
                            })

    # if this post is original to this blog
    if 'reblogged_root_name' not in cur_post['response']['posts'][0]:
        return (None, None, None)

    # record destination in log book ;)
    dest = cur_post['response']['posts'][0]['reblogged_root_name']

    relations = []
    logging.info(
        'Tracing a post from "%s" with post id "%s"' % (hostname, post_id))

    # loop until we arrive at our destination
    while dest != cur_post['response']['posts'][0]['blog_name']:
        try:
            # request the selected post
            cur_post = requests.get(url, auth=auth, params={"id": post_id})
        except requests.DownloadError:
            # if any errors occurred, ignore em and try try again
            logging.info('Try try again')
        else:
            # if no errors occurred
            try:
                if ('reblogged_from_name' not in cur_post['response']['posts'][0] or
                        cur_post['response']['posts'][0]['reblogged_from_name'] ==
                        cur_post['response']['posts'][0]['blog_name']):
                    break
            except TypeError:
                # if something bad happened, abandon this post
                logging.info('Not found? %s' % cur_post)
                break

            hostname = cur_post['response']['posts'][0]['reblogged_from_name']
            post_id = cur_post['response']['posts'][0]['reblogged_from_id']

            relations.append([
                cur_post['response']['posts'][0]['blog_name'],
                cur_post['response']['posts'][0]['reblogged_from_name']])

            logging.info('%s reblogged from %s' % (
                cur_post['response']['posts'][0]['blog_name'],
                cur_post['response']['posts'][0]['reblogged_from_name']))
            time.sleep(2)

    return (relations, hostname, post_id)

# reblog_path_sink is currently in development; see test_sink.py


# graph representation generators
def process_graph_data(handler, processing_function):
    blog_name = handler.get_argument('blog_name')
    output_json = {'nodes': [], 'links': []}

    if blog_name:
        sink, source = [], []
        sink = memcache.get(blog_name + '_sink') or {}
        source = memcache.get(blog_name + '_source') or {}

        # looks messy, but just combines the dicts into one big dict
        all_data = source
        all_data.update(sink)
        all_data = all_data.values()

        if all_data:
            # yay for (memory efficient) generators \o/
            all_data = filter(bool, all_data)
            all_data = chain.from_iterable(all_data)
            all_data = set(all_data)

            output_json = processing_function(all_data)

    return json.dumps(
        output_json)


def compute_d3_points(relations):
    output_json = {'links': [], 'nodes': []}
    if relations:
        id_relations = {}
        unique = set(chain.from_iterable(relations))

        for cur_id, frag in enumerate(unique):
            id_relations[frag] = cur_id

        for rel in unique:
            output_json['nodes'].append(
                {'name': rel, 'group': id_relations[rel]})

        for rel in relations:
            output_json['links'].append(
                {
                    'source': id_relations[rel[0]],
                    'target': id_relations[rel[1]],
                    'value': 5
                })

        logging.info('Posts; {}'.format(len(output_json['nodes'])))
        logging.info('Post links; {}'.format(len(output_json['links'])))

    return output_json


def compute_radial_d3_points(relations):
    if relations:
        id_relations = {}
        unique = set(chain.from_iterable(relations))

        for frag in unique:
            id_relations[frag] = {
                "name": frag,
                "imports": []}

        for rel in relations:
            id_relations[rel[0]]['imports'].append(rel[1])

        logging.info('Posts; %s' % len(id_relations))

        return list(id_relations.values())
    else:
        return []


# url manipulation and verification
def is_url(string):
    # domain tld's
    tlds = [
        'com', 'co', 'net', 'org', 'edu', 'gov', 'io', 'me', 'cc', 'ly', 'gl', 'by',    # top level domain extensions
        'fr', 'de', 'se', 'us', 'au', 'eu', 'wa', 'it',                                 # country codes
        'info', 'name',                                                                 # specials
        'www'                                                                           # unlikely but perhaps necessary
    ]
    netloc = urllib.parse.urlsplit(string).netloc
    if netloc.split('.')[-1] in tlds:
        # eh, good enough
        return True
    else:
        return False


def expand_hostname(hostname):
    if hostname.endswith('.tumblr.com'):
        return

    if not is_url(hostname):
        # if it appears to be invalid, format as tumblr url
        return '{}.tumblr.com'.format(hostname)
    else:
        return hostname


def build_url(hostname):
    hostname = expand_hostname(hostname)
    return 'http://api.tumblr.com/v2/blog/{hostname}.tumblr.com/'.format(
        hostname)


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

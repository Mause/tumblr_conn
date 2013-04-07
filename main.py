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
import os
import sys
import time
import json
import logging
import urllib.parse
import http.client
from itertools import chain, groupby

# third party
import tornado
import requests
import tornado.options

# from tumblpy import TumblPy
# from tumblr import TumblrClient
from tumblr.oauth import TumblrOAuthClient

# application specific
from utils import BaseHandler
from utils import reblog_path_source
from auth_data import consumer_key, consumer_secret
from utils import compute_radial_d3_points, compute_d3_points

sys.argv.append('--logging=INFO')
tornado.options.parse_command_line()

# callback_url = 'http://tumblr-conn.appspot.com/callback'
callback_url = 'http://tumblr-conn.herokuapp.com/callback'

tumblr_oauth = TumblrOAuthClient(
    consumer_key,
    client_secret=consumer_secret)
# tumblr_oauth = TumblPy(
#     consumer_key, consumer_secret)

default_status = {
    'queue': [],
    'cur_index': 0,
    'running': False,
    'starttime': 0,
    'endtime': 0,
    'failed': False}


class MainHandler(BaseHandler):
    def get(self):
        auth_url = (
            tumblr_oauth.get_authorize_url() + '&' +
            urllib.parse.urlencode({'oauth_callback': callback_url}))

        if not self.session.get('authorized', False):
            self.redirect(auth_url)
            return

        access_key = self.session.get('access_key', None)
        access_secret = self.session.get('access_secret', None)

        if not access_secret or not access_key:
            self.session['blog_name'] = self.get_argument('blog_name', None)

            logging.info('oauth_token; {}'.format(
                tumblr_oauth.request_token['oauth_token']))
            logging.info('oauth_token_secret; {}'.format(
                tumblr_oauth.request_token['oauth_token_secret']))

            self.session['oauth_token'] = str(
                tumblr_oauth.request_token['oauth_token'])
            self.session['oauth_token_secret'] = str(
                tumblr_oauth.request_token['oauth_token_secret'])

            self.render('auth.html', auth_url=auth_url)
        else:
            blog_name = self.request.get('blog_name')
            if not blog_name:
                self.render('input_blog.html')
            else:
                self.session['blog_name'] = blog_name
                self.render('primary_view.html', blog_name=blog_name)


class CallbackHandler(BaseHandler):
    def get(self):
        self.session['authorized'] = True
        oauth_verifier = self.get_argument('oauth_verifier')
        access_token = tumblr_oauth.get_access_token(
            oauth_verifier,
            oauth_token=self.session['oauth_token'],
            oauth_token_secret=self.session['oauth_token_secret'])
        self.session['access_key'] = access_token.key
        self.session['access_secret'] = access_token.secret

        redirect_url = '/'
        if self.session['blog_name']:
            redirect_url += '?' + urllib.parse.urlencode({
                'blog_name': self.session['blog_name']})

        self.redirect(redirect_url)


class MappingWorker(tornado.web.RequestHandler):
    def post(self):
        root_blog_name = self.request.get('blog_name')
        logging.info('Going to analyse "%s"' % (root_blog_name))
        hostname = root_blog_name + '.tumblr.com'

        # cur_status = memcache.get(root_blog_name + '_mapping_status')
        # if not cur_status:
        cur_status = default_status.copy()
        cur_status['starttime'] = time.time()
        cur_status['running'] = True
        # memcache.set(root_blog_name + '_mapping_status', cur_status)

        access_key = self.request.get('access_key')
        access_secret = self.request.get('access_secret')
        logging.info('access_key; %s' % access_key)
        logging.info('access_secret; %s' % access_secret)

        if not access_secret or not access_key:
            logging.info('Please authenticate')
            return

        # token = oauth.Token(access_key, access_secret)
        # consumer = oauth.Consumer(consumer_key, consumer_secret)
        # client = TumblrClient(root_blog_name, consumer, token)
        # client = []
        params = {'reblog_info': 'true', 'notes_info': 'true'}
        con = []
        json_response = None
        url = (
            'http://api.tumblr.com/v2/blog/{hostname}'
            '/posts'.format(hostname=hostname))
        while not json_response:
            try:
                json_response = requests.get(url, auth=tumblr_oauth,
                    params=params)
            except http.client.HTTPException as e:
                logging.info(str(e))
        logging.info(json_response)
        con += json_response['response']['posts']

        logging.info('This many posts; %s' % len(con))
        cur_status['queue'] = con
        # memcache.set(root_blog_name + '_mapping_status', cur_status)

        if con:
            source = {}
            for cur_index, post in enumerate(con):
                returned_data = reblog_path_source(
                    post['blog_name'], post['id'], tumblr_oauth)
                if list(filter(bool, returned_data)):
                    source[post['id']], hostname, post_id = returned_data
                    # memcache.set(str(root_blog_name) + '_source', source)
                    logging.info(
                        'The original poster was %s and the post id was %s' % (
                            hostname, post_id))
                    logging.info(
                        'Set the returned data to the "{}_source" key'.format(
                            root_blog_name))
                else:
                    logging.info(
                        'Incomplete data was returned. '
                        'Ignoring, was likely an original post')

                # these lines are commented while i work on the
                # path sink function
                # sink = []
                # sink = reblog_path_sink(hostname, post_id, client)
                # memcache.set('sink', sink)

                cur_status['cur_index'] = cur_index + 1
                # memcache.set(root_blog_name + '_mapping_status', cur_status)
        else:
            logging.info('get_blog_posts return None')
            cur_status['failed'] = True

        cur_status['endtime'] = time.time()
        cur_status['running'] = False
        cur_status['queue'] = []
        # memcache.set(root_blog_name + '_mapping_status', cur_status)
        logging.info('And i am done here')


def process_graph_data(handler, processing_function):
    blog_name = handler.request.get('blog_name')
    if blog_name:
        sink, source = [], []
        # sink = memcache.get(str(blog_name) + '_sink') or {}
        # source = memcache.get(str(blog_name) + '_source') or {}
        all_data = dict(
            list(source.items()) +
            list(sink.items()))
        if all_data:
            all_data = list(filter(bool, list(all_data.values())))
            all_data = list(chain.from_iterable(all_data))
            all_data = [x[0] for x in sorted(list(groupby(all_data)))]
            all_data = processing_function(all_data)
            return json.dumps(all_data)
        else:
            return json.dumps(
                {'nodes': [], 'links': []})
    else:
        return json.dumps(
            {'nodes': [], 'links': []})


class ForceGraphHandler(BaseHandler):
    def get(self):
        blog_name = self.request.get('blog_name')
        self.render('force_graph.html', **{'blog_name': blog_name})


class ForceGraphDataHandler(BaseHandler):
    def get(self):
        self.response.write(process_graph_data(
            self, processing_function=compute_d3_points))


class BundleGraphDataHandler(BaseHandler):
    def get(self):
        self.response.write(process_graph_data(
            self, processing_function=compute_radial_d3_points))


class AnalyseHandler(BaseHandler):
    def get(self):
        if self.session['blog_name']:
            self.render(
                'analyse.html', {'blog_name': self.session['blog_name']})
        else:
            self.redirect('/')


settings = {
    'cookie_secret': 'key_kay_wooookoo',
    "static_path": os.path.join(os.path.dirname(__file__), "static"),
    "template_path": os.path.join(os.path.dirname(__file__), 'templates'),
    "debug": True,
}

application = tornado.web.Application([
    (r'/static/(.*)',
        tornado.web.StaticFileHandler, {'path': settings['static_path']}),

    (r'/', MainHandler),
    (r'/callback', CallbackHandler),
    (r'/graph/force', ForceGraphHandler),
    (r'/graph/force/graph_data', ForceGraphDataHandler),
    # (r'/graph/bundle/graph_data', BundleGraphDataHandler),
    (r'/map_blog_post', MappingWorker),
    (r'/analyse', AnalyseHandler)
    ], **settings
)

if __name__ == "__main__":
    application.listen(os.environ.get('PORT', 8888))
    tornado.ioloop.IOLoop.instance().start()

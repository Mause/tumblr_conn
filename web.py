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
import urllib
import logging

# third party
import tornado
import requests
import tornado.options
from requests_oauthlib import OAuth1
from tumblr.oauth import TumblrOAuthClient

# application specific
import ajax
import debug
from utils import BaseHandler
from utils.url import expand_hostname
from utils.graph_data import process_d3_points
from auth_data import consumer_key, consumer_secret

sys.argv.append('--logging=INFO')
tornado.options.parse_command_line()

tumblr_auth = TumblrOAuthClient(
    consumer_key,
    client_secret=consumer_secret)


class MainHandler(BaseHandler):
    def get(self):
        is_authorized = self.session.get('is_authorized', None)

        if not is_authorized:
            """ Step 1 of the authentication workflow, obtain a temporary
            resource owner key and use it to redirect the user. The user
            will authorize the client (our flask app) to access its resources
            and perform actions in its name (aka get feed and post updates)."""

            # In this step you will need to supply your twitter
            # provided key and secret
            tumblr = OAuth1(consumer_key,
                            client_secret=consumer_secret,
                            decoding=None)

            # We will be using the default method of
            # supplying parameters, which is in the authorization header.
            r = requests.post(tumblr_auth.REQUEST_TOKEN_URL, auth=tumblr)

            # Extract the temporary resource owner key from the response
            info = urllib.parse.parse_qs(r.text)

            assert 'oauth_token' in info, r.text
            assert info['oauth_callback_confirmed'][0] == 'true'

            oauth_token = info["oauth_token"][0]

            # Create the redirection url and send the user to twitter
            # This is the start of Step 2
            auth_url = tumblr_auth.AUTHORIZE_URL + '?' + urllib.parse.urlencode({"oauth_token": oauth_token})

            self.session['blog_name'] = self.get_argument('blog_name', None)
            self.session['oauth_token'] = oauth_token
            self.session['oauth_token_secret'] = info['oauth_token_secret'][0]

            self.render('auth.html', auth_url=auth_url)
        else:
            blog_name = self.get_argument('blog_name', None)
            if not blog_name:
                self.render('input_blog.html')
            else:
                blog_name = expand_hostname(blog_name)
                logging.info(blog_name)
                self.session['blog_name'] = blog_name
                self.render('primary_view.html', blog_name=blog_name)


class CallbackHandler(BaseHandler):
    def get(self):
        logging.warning('CALLBACK RECIEVED')
        verifier = self.get_argument("oauth_verifier")
        token = self.get_argument("oauth_token")
        secret = self.session['oauth_token_secret']

        # self.session.delete('oauth_token_secret')

        logging.debug('verifier; {}'.format(verifier))
        logging.debug('token; {}'.format(token))
        logging.debug('secret; {}'.format(secret))

        # In this step we also use the verifier
        tumblr = OAuth1(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=token,
            resource_owner_secret=secret,
            verifier=verifier)
        r = requests.post(tumblr_auth.ACCESS_TOKEN_URL, auth=tumblr)

        # This is the end of Step 3,
        # we can now extract resource owner key & secret
        # as well as some extra information such as screen name.
        info = urllib.parse.parse_qs(r.text)

        if 'oauth_token' not in info:
            logging.warning('"oauth_token" not in info, redirecting to homepage')
            self.redirect('/')
            return

        assert 'oauth_token' in info, r.text
        assert 'oauth_token_secret' in info, r.text

        # Save credentials in the session,
        # it is VERY important that these are not
        # shown to the resource owner,
        # Flask session cookies are encrypted so we are ok.
        self.session["access_token"] = info["oauth_token"][0]
        self.session["token_secret"] = info["oauth_token_secret"][0]
        self.session["is_authorized"] = True

        redirect_url = '/'
        if 'blog_name' in self.session:
            redirect_url += '?' + urllib.parse.urlencode(
                {'blog_name': self.session['blog_name']})

        self.redirect(redirect_url)


class ForceGraphHandler(BaseHandler):
    def get(self):
        blog_name = self.get_argument('blog_name')
        self.render('force_graph.html', blog_name=blog_name)


class ForceGraphDataHandler(BaseHandler):
    def get(self):
        blog_name = self.get_argument('blog_name')
        self.write(process_d3_points(blog_name))


class AnalyseHandler(BaseHandler):
    def get(self):
        is_authorized = self.session.get('is_authorized', default=False)
        if is_authorized:
            blog_name = self.session['blog_name']
            self.render('analyse.html', blog_name=blog_name)
        else:
            self.redirect('/')


settings = {
    'cookie_secret': '7e442e29bd724847bfbebc51e59850259edc6d3aadd94bcbab3c8d765db90e3bd4c9bcee4f9c43729c068391e17bd702',
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

    (r'/analyse', AnalyseHandler),
    (r'/ajax/(?P<blog_name>[^/]*)/mapping/status',
        ajax.MappingStatusHandler),

    (r'/db/test', debug.TestHandler),
    (r'/db/view', debug.ViewHandler),
    (r'/db/(?P<key>[^/]*)', debug.MainHandler),
    (r'/db/?', debug.DebugHandler),
], **settings)


if __name__ == "__main__":
    port = os.environ.get('PORT', 8888)
    application.listen(port)
    tornado.ioloop.IOLoop.instance().start()

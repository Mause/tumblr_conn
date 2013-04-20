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
import logging

# third party
import tornado
import requests
import tornado.options

# application specific
import ajax
import debug
from auth_data import api_key
from utils.url import expand_hostname, build_url
from utils.data_attainment import reblog_path_source
from utils.graph_data import compute_d3_points, process_graph_data
from utils import APIKeyAuth, BaseHandler, default_status, memcache

sys.argv.append('--logging=DEBUG')
tornado.options.parse_command_line()

callback_url = 'http://tumblr-conn.herokuapp.com/callback'
tumblr_auth = APIKeyAuth(api_key)


class MainHandler(BaseHandler):
    def get(self):
        blog_name = self.get_argument('blog_name', None)
        if not blog_name:
            self.render('input_blog.html')
        else:
            blog_name = expand_hostname(blog_name)
            logging.info(blog_name)
            self.session['blog_name'] = blog_name
            self.render('primary_view.html', blog_name=blog_name)


class MappingWorker(tornado.web.RequestHandler):
    def get(self):
        return self.work()

    def post(self):
        return self.work()

    def work(self):
        if self:
            root_blog_name = self.get_argument('blog_name')
        else:
            logging.info('Debugging init')
            root_blog_name = 'normal.blog.mause.me'
        hostname = expand_hostname(root_blog_name)
        logging.info('Going to analyse "%s"' % (hostname))
        url = build_url(hostname) + 'posts'

        cur_status = memcache.get(hostname + '_mapping_status', None)
        if not cur_status:
            cur_status = default_status.copy()
            cur_status.update({
                'starttime': time.time(),
                'running': True
            })
        memcache.set(hostname + '_mapping_status', cur_status)

        params = {'reblog_info': 'true', 'notes_info': 'true'}
        json_response = requests.get(url,
                                     auth=tumblr_auth,
                                     params=params)

        logging.info(json_response)
        con = json_response.json()['response']['posts']

        logging.info('Reblogged? {}'.format('reblogged_from_id' in con[0]))

        logging.info('This many posts; %s' % len(con))
        cur_status['queue'] = con
        memcache.set(hostname + '_mapping_status', cur_status)

        if con:
            source = {}
            for cur_index, post in enumerate(con):
                returned_data = reblog_path_source(
                    post['blog_name'], post['id'], tumblr_auth)

                if returned_data:
                    source[post['id']], hostname, post_id = returned_data
                    memcache.set(hostname + '_source', source)
                    logging.info('The original poster was {} and the post id was {}'.format(hostname, post_id))
                else:
                    logging.info('incomplete data; likely an original post')

                # these lines are commented while i work on the
                # path sink function
                # sink = []
                # sink = reblog_path_sink(hostname, post_id, client)
                # memcache.set('sink', sink)

                cur_status['cur_index'] = cur_index + 1
                memcache.set(hostname + '_mapping_status', cur_status)
        else:
            logging.info('failed to fetch blog posts')
            cur_status['failed'] = True

        cur_status.update({
            'endtime': time.time(),
            'running': False,
            'queue': []
        })
        memcache.set(hostname + '_mapping_status', cur_status)
        logging.info('And i am done here')


class ForceGraphHandler(BaseHandler):
    def get(self):
        blog_name = self.get_argument('blog_name')
        self.render('force_graph.html', **{'blog_name': blog_name})


class ForceGraphDataHandler(BaseHandler):
    def get(self):
        self.write(
            process_graph_data(self, processing_function=compute_d3_points))


class AnalyseHandler(BaseHandler):
    def get(self):
        if self.session['blog_name']:
            self.render(
                'analyse.html',
                {'blog_name': self.session['blog_name']})
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

    (r'/graph/force', ForceGraphHandler),
    (r'/graph/force/graph_data', ForceGraphDataHandler),

    (r'/map_blog_post', MappingWorker),
    (r'/analyse', AnalyseHandler),
    (r'/ajax/(?P<blog_name>[^/]*)/mapping/status',
        ajax.MappingStatusHandler),

    (r'/db/test', debug.TestHandler),
    (r'/db/view', debug.ViewHandler),
    (r'/db/(?P<key>[^/]*)', debug.MainHandler),
    (r'/db[/]?', debug.DebugHandler),
], **settings)


if __name__ == "__main__":
    application.listen(os.environ.get('PORT', 8888))
    tornado.ioloop.IOLoop.instance().start()

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
import logging

# third party
import tornado
import tornado.options

# application specific
import ajax
import debug
from auth_data import api_key
from utils.url import expand_hostname
from utils import ParamAuth, BaseHandler
from utils.graph_data import compute_d3_points, process_graph_data

sys.argv.append('--logging=DEBUG')
tornado.options.parse_command_line()

callback_url = 'http://tumblr-conn.herokuapp.com/callback'
tumblr_auth = ParamAuth({'api_key': api_key})


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

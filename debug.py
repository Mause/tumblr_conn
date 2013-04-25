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

import time
import logging

from utils import BaseHandler, default_status
from utils.iron_wrap import memcache, taskqueue


class MainHandler(BaseHandler):
    def get(self, key):
        self.write('{}; {}'.format(key, self.session[key]))


class ViewHandler(BaseHandler):
    def get(self):
        blog_name = self.get_argument('blog_name', None)

        self.write('<h2>%s</h2>' % blog_name)
        if blog_name:
            self.write('<style>.r {margin-left: 40px;}</style>')
            tests = memcache['sources'].get(blog_name)
            if tests:
                for item in tests:
                    self.write('%s;</br>' % (item))
                    if tests[item]:
                        for sub in tests[item]:
                            self.write('<div class="r">{}</div>'.format(sub))
                        self.write('</br>')
                    else:
                        self.write('<div class="r">Empty item</div></br>')
            else:
                self.write('No data yet')
        else:
            self.write('Please provide a valid blog name')


class TestHandler(BaseHandler):
    def get(self):
        blog_name = self.session.get('blog_name', None)
        if not blog_name:
            logging.info('Empty blog name')
        taskqueue['blog-post-mapper'].add({'blog_name': blog_name})
        self.write(
            'Task for "%s" dispatched at %s. '
            'Check <a href="/ajax/%s/mapping/status">here</a> '
            'for current status' %
            (blog_name, time.ctime(), blog_name))
        memcache['mapping_status'].set(blog_name, default_status.copy())


class DebugHandler(BaseHandler):
    def get(self):
        self.write('%s</br>' % self.session['access_key'])
        self.write('%s</br>' % self.session['access_secret'])


class TemplateTester(BaseHandler):
    def get(self, template):
        self.render(template, blog_name='mause-me')

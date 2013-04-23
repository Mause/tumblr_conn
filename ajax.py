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

import logging

from utils import BaseHandler, default_status, memcache


class MappingStatusHandler(BaseHandler):
    def get(self, blog_name):
        cur_status = memcache.get(blog_name + '_mapping_status') or default_status.copy()

        logging.info('queue position -> {}, len(queue) -> {}'.format(
            cur_status['cur_index'],
            len(cur_status['queue'])))

        self.set_header('Content-Type', 'application/json')
        self.set_header('Access-Control-Allow-Origin', '*')
        self.write(cur_status)

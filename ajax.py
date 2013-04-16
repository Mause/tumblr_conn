import json
import logging

from utils import BaseHandler
from utils import default_status


class MappingStatusHandler(BaseHandler):
    def get(self, blog_name):
        cur_status = {} or default_status.copy()
        # cur_status = memcache.get(blog_name + '_mapping_status')

        logging.info('queue position -> {}, len(queue) -> {}'.format(
            cur_status['cur_index'],
            len(cur_status['queue'])))

        self.set_header('Content-Type', 'application/json')
        self.set_header('Access-Control-Allow-Origin', '*')
        self.write(json.dumps(cur_status, indent=4))

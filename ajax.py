import json
import logging
import webapp2
from google.appengine.api import memcache

from auth_data import config
from utils import BaseHandler
from main import default_status


class MappingStatusHandler(BaseHandler):
    def get(self, blog_name):
        cur_status = memcache.get(
            blog_name + '_mapping_status') or default_status.copy()
        if cur_status:
            logging.info('Position in post queue; %s' %
                cur_status['cur_index'])
            logging.info('Number of posts in queue; %s' %
                len(cur_status['queue']))
        else:
            logging.info('No data in current status')
        self.response.headers['Content-Type'] = 'application/json'
        self.response.headers['Access-Control-Allow-Origin'] = '*'
        self.response.write(json.dumps(cur_status))


app = webapp2.WSGIApplication(
    [(r'/ajax/(?P<blog_name>[^/]*)/mapping/status', MappingStatusHandler)],
    debug=True, config=config)

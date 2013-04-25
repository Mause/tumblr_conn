import time
import logging

from utils import (
    memcache,
    taskqueue,
    BaseHandler,
    default_status
)


class MainHandler(BaseHandler):
    def get(self, key):
        self.write('%s; %s' % (key, self.session[key]))


class ViewHandler(BaseHandler):
    def get(self):
        blog_name = self.get_argument('blog_name')

        self.write('<h2>%s</h2>' % blog_name)
        if blog_name:
            self.write('<style>.r {margin-left: 40px;}</style>')
            tests = memcache['sources'].get(blog_name)
            if tests:
                for item in tests:
                    self.write('%s;</br>' % (item))
                    if tests[item]:
                        for sub in tests[item]:
                            self.write(
                                '<div class="r">%s</div>' % (sub))
                        self.write('</br>')
                    else:
                        self.write(
                            '<div class="r">Empty item</div></br>')
            else:
                self.write('No data yet')
        else:
            self.write('Please provide a valid blog name')


class TestHandler(BaseHandler):
    def get(self):
        blog_name = self.session.get('blog_name', None)
        if not blog_name:
            logging.info('Empty blog name')
        taskqueue.add(
            queue_name='blog-post-mapper',
            url='/map_blog_post',
            params={'blog_name': blog_name})
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

import time

import webapp2
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from utils import render
from utils import BaseHandler
from auth_data import config
from main import default_status


class MainHandler(BaseHandler):
    def get(self, key):
        if key in self.session:
            self.response.write('%s; %s' % (key, self.session[key]))
        else:
            self.response.write('No such key')


class ViewHandler(BaseHandler):
    def get(self):
        blog_name = self.request.get('blog_name')
        self.response.write('<h2>%s</h2>' % blog_name)
        if blog_name:
            test_key = str(blog_name) + '_source'
            self.response.write('<style>.r {margin-left: 40px;}</style>')
            tests = memcache.get(test_key)
            if tests:
                for item in tests:
                    self.response.write('%s;</br>' % (item))
                    if tests[item]:
                        for sub in tests[item]:
                            self.response.write(
                                '<div class="r">%s</div>' % (sub))
                        self.response.write('</br>')
                    else:
                        self.response.write(
                            '<div class="r">Empty item</div></br>')
            else:
                self.response.write('No data yet')
        else:
            self.response.write('Please provide a valid blog name')


class TestHandler(BaseHandler):
    def get(self):
        access_key = self.session.get('access_key', None)
        access_secret = self.session.get('access_secret', None)
        blog_name = self.session.get('blog_name', None)
        taskqueue.add(
            queue_name='blog-post-mapper',
            url='/map_blog_post',
            params={
                'blog_name': blog_name,
                'access_key': access_key,
                'access_secret': access_secret
                })
        self.response.write(
            'Task for "%s" dispatched at %s. '
            'Check <a href="/ajax/%s/mapping/status">here</a> '
            'for current status' %
            (blog_name, time.ctime(), blog_name))
        memcache.set(blog_name + '_mapping_status', default_status.copy())


class DebugHandler(BaseHandler):
    def get(self):
        self.response.write('%s</br>' % self.session['access_key'])
        self.response.write('%s</br>' % self.session['access_secret'])


class TemplateTester(BaseHandler):
    def get(self, template):
        render(self, template, {'blog_name': 'mause-me'})

app = webapp2.WSGIApplication([
    # (r'/db/(?P<template>[^.]*.html)', TemplateTester),
    (r'/db/test', TestHandler),
    (r'/db/view', ViewHandler),
    (r'/db/(?P<key>[^/]*)', MainHandler),
    (r'/db[/]?', DebugHandler),
], debug=True, config=config)

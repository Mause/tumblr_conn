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
import time
import logging
import threading

# third party
import requests

# application specific
from auth_data import api_key
from utils.url import expand_hostname, build_url
from utils.data_attainment import reblog_path_source
from utils import memcache, taskqueue, default_status, ParamAuth

logging.info = print
logging.debug = print

tumblr_auth = ParamAuth({'api_key': api_key})


def process_blog(root_blog_name, num_to_analyse):
    hostname = expand_hostname(root_blog_name)
    logging.info('Going to analyse "%s"' % (hostname))
    url = build_url(hostname) + 'posts'
    logging.info('URL; {}'.format(url))

    cur_status = memcache.get(hostname + '_mapping_status', None)
    if not cur_status:
        cur_status = default_status.copy()
        cur_status.update({
            'starttime': time.time(),
            'running': True
        })
    memcache.set(hostname + '_mapping_status', cur_status)

    params = {'reblog_info': 'true', 'limit': num_to_analyse}
    json_response = requests.get(url,
                                 auth=tumblr_auth,
                                 params=params)

    logging.info(json_response.url)
    logging.info(json_response)
    con = json_response.json()['response']['posts']

    logging.info('This many posts; %s' % len(con))

    cur_status['queue_len'] = len(con)
    memcache.set(hostname + '_mapping_status', cur_status)

    if con:
        source = {}

        for cur_index, post in enumerate(con):
            if 'reblogged_root_name' not in post:
                logging.info('Not reblogged')
                continue

            logging.info('fetching {} from {}, with sights set for {}'.format(
                post['id'], post['blog_name'], post['reblogged_root_name'] if 'reblogged_root_name' in post else '...'))
            returned_data = reblog_path_source(from_post=post, auth=tumblr_auth)

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
        # 'queue': []
        'queue_len': 0
    })
    memcache.set(hostname + '_mapping_status', cur_status)
    logging.info('And i am done here')


def worker(taskqueue, shutdown_event, num_to_analyse):
    while True and not shutdown_event.is_set():
        task = taskqueue.get()
        if shutdown_event.is_set():
            break
        elif not task.empty():
            print('new task! {}'.format(task))
            task.delete()
            process_blog(task['blog_name'], num_to_analyse)

            # may implement task done later
            # task.task_done()
        time.sleep(0.5)


def main():
    shutdown_event = threading.Event()
    all_workers = []
    num_worker_threads = 4
    num_to_analyse = 10

    for i in range(num_worker_threads):
        t = threading.Thread(target=worker, args=(taskqueue, shutdown_event, num_to_analyse))
        t.start()
        all_workers.append(t)

    logging.info('Workers initialised')
    try:
        while True:
            pass
    finally:
        shutdown_event.set()

if __name__ == '__main__':
    main()

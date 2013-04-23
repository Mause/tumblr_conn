# stdlib
import time
import queue
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


def process_blog(root_blog_name):
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
    # cur_status['queue'] = con
    cur_status['queue_len'] = len(con)
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
        # 'queue': []
        'queue_len': 0
    })
    memcache.set(hostname + '_mapping_status', cur_status)
    logging.info('And i am done here')


def worker(taskqueue, shutdown_event):
    while True and not shutdown_event.is_set():
        try:
            task = taskqueue.get(timeout=1)
        except queue.Empty:
            pass
            # if shutdown_event.is_set():
            #     break
        else:
            process_blog(task['blog_name'])
            task.task_done()


def main():
    shutdown_event = threading.Event()
    all_workers = []
    num_worker_threads = 4

    for i in range(num_worker_threads):
        t = threading.Thread(target=worker, args=(taskqueue, shutdown_event))
        t.start()
        all_workers.append(t)

    try:
        n = input('New blog? ')
        taskqueue.put({'blog_name': n})
        while True:
            pass
    finally:
        shutdown_event.set()

if __name__ == '__main__':
    main()

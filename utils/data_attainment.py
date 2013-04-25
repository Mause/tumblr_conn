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
"tumblr data accessing and processing"

# stdlib
import time
import json
import logging
from pprint import pprint

# third party
import requests

# application specific
from .url import build_url


# heck
def get_reblogs(post_id, client, url_template):
    selection_index = 0

    r = requests.get(
        url_template + str(post_id),
        auth=client)

    assert r.ok, r.text
    cur_post = r.json()
    with open('debug/first.json', 'w') as fh:
        json.dump(cur_post, fh)

    # lets filter out anything that is not a reblog
    all_reblogs = filter(lambda x: x['type'] == 'reblog',
                         cur_post['response']['posts'][selection_index]['notes'])
    all_reblogs = list(all_reblogs)
    return all_reblogs


def reblog_path_source(from_post, auth):
    # pprint(from_post)
    hostname = from_post['blog_name']
    post_id = from_post['id']

    url = build_url(hostname) + 'posts'

    pprint({
        k: v
        for k, v in from_post.items()
        if k.startswith('reblog')})

    # if this post is original to this blog
    if 'reblogged_root_name' not in from_post:
        return None

    relations = []
    logging.info('Tracing a post from "{}" with post id "{}"'.format(hostname, post_id))

    # loop until we arrive at our destination
    # while dest != cur_post['response']['posts'][0]['blog_name']:
    while True:
        try:
            # request the selected post
            cur_post = requests.get(url, auth=auth, params={"id": post_id})
        except requests.DownloadError:
            # if any errors occurred, ignore em and try try again
            logging.info('Try try again')
        else:
            # if no errors occurred
            try:
                if ('reblogged_from_name' not in cur_post['response']['posts'][0] or
                        cur_post['response']['posts'][0]['reblogged_from_name'] ==
                        cur_post['response']['posts'][0]['blog_name']):
                    break
            except TypeError:
                # if something bad happened, abandon this post
                logging.info('Not found? %s' % cur_post)
                break

            hostname = cur_post['response']['posts'][0]['reblogged_from_name']
            post_id = cur_post['response']['posts'][0]['reblogged_from_id']

            relations.append([
                cur_post['response']['posts'][0]['blog_name'],
                cur_post['response']['posts'][0]['reblogged_from_name']])

            logging.info('%s reblogged from %s' % (
                cur_post['response']['posts'][0]['blog_name'],
                cur_post['response']['posts'][0]['reblogged_from_name']))
            time.sleep(2)

    return (relations, hostname, post_id)

# reblog_path_sink is currently in development; see test_sink.py

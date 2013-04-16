# stdlib
import json

import logging
from pprint import pprint

# third party
import requests

logging.info = print
logging.debug = print

import auth_data
from utils import APIKeyAuth
from utils import build_url
from utils import expand_hostname


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


def reblog_path_sink(hostname, post_id, client, depth=0, posts_seen=set()):
    hostname = expand_hostname(hostname)
    url_template = build_url(hostname) + 'posts?reblog_info=true&notes_info=true&id={}'

    tree = {}
    logging.info('user="{}" && id="{}" && depth="{}"'.format(hostname, post_id, depth))

    all_reblogs = get_reblogs(
        post_id,
        client,
        url_template)

    with open('okay_go.json', 'w') as fh:
        fh.write(json.dumps(all_reblogs))

    for reblog in all_reblogs:
        # print(reblog)
        if reblog['blog_name'] != hostname:
            if reblog['post_id'] not in posts_seen:
                posts_seen.add(reblog['post_id'])
                tree[reblog['post_id']] = reblog_path_sink(
                    reblog['blog_name'], reblog['post_id'], client, depth + 1)
            else:
                pass
                # print('abort, seen before')

    return (tree, hostname, post_id)

client = APIKeyAuth(auth_data['api_key'])

e_tree, _, _ = reblog_path_sink('dearestherquotes', '46848673358', client)
pprint(e_tree)

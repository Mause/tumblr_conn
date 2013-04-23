# stdlib
import json

import logging
from pprint import pprint

# third party
logging.info = print
logging.debug = print

import auth_data
from utils import ParamAuth
from utils.url import build_url, expand_hostname
from utils.data_attainment import get_reblogs


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

client = ParamAuth(auth_data.api_key)

e_tree, _, _ = reblog_path_sink('dearestherquotes', '46848673358', client)
pprint(e_tree)

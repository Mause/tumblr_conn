"tumblr data accessing and processing"
import time
import json
import logging

import requests

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


def reblog_path_source(hostname, post_id, auth):

    url = build_url(hostname) + 'posts'
    cur_post = requests.get(url,
                            auth=auth,
                            params={
                                "reblog_info": True,
                                "id": post_id
                            })

    # if this post is original to this blog
    if 'reblogged_root_name' not in cur_post['response']['posts'][0]:
        return (None, None, None)

    # record destination in log book ;)
    dest = cur_post['response']['posts'][0]['reblogged_root_name']

    relations = []
    logging.info(
        'Tracing a post from "%s" with post id "%s"' % (hostname, post_id))

    # loop until we arrive at our destination
    while dest != cur_post['response']['posts'][0]['blog_name']:
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

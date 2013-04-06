import json
import os
# from itertools import chain, groupby
import requests


class Logging:
    def info(self, message):
        print message
logging = Logging()


class CLIENT:
    def make_oauth_request(self, url):
        return json.loads(requests.get(url).content)

    def get_api_key(self):
        return 'XCnTLihnMZpJoG0z2uBnqBFGqkv5OxDawCNTE56n0muP5IScfJ'
client = CLIENT()


def reblog_path_sink(hostname, post_id, client):
    logging.info('This is going to be expensive. I hope you can afford it :P')
    cur_post = None
    tree = {}
    logging.info(
        'Just to confirm, we are starting at the user %s'
        ' and their post with id %s' % (hostname, post_id))

    print 'Reloop'

    # root_hostname = hostname
    # root_post_id = post_id
    while not cur_post:
        try:
            cur_post = client.make_oauth_request(
                'http://api.tumblr.com/v2/blog/{hostname}.tumblr.com'
                '/posts?api_key={key}&id={id}&reblog_info=true&'
                'notes_info=true'.format(
                        hostname=hostname,
                        key=client.get_api_key(),
                        id=post_id))
            with open('debug%sfirst.json' % os.sep, 'w') as fh:
                fh.write(json.dumps(cur_post))
        except requests.exceptions.ConnectionError:
            logging.info('Could not reach remote server. Try try again')

    # lets filter out anything that is not a reblog
    all_reblogs = filter(
        lambda x: x['type'] == 'reblog',
        cur_post['response']['posts'][0]['notes'])
    with open('okay_go.json', 'w') as fh:
        fh.write(json.dumps(all_reblogs))

    for reblog in all_reblogs:
        print reblog
        if reblog['blog_name'] != hostname:
            tree[post_id][reblog['post_id']] = reblog_path_sink(
                reblog['blog_name'], reblog['post_id'], client)

    return (tree, hostname, post_id)

print reblog_path_sink(u'realitybitesus', u'35691493805', client)[1:]

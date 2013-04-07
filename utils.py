import time
import logging
from itertools import chain, groupby

import requests
import tornado.web


class Session(object):
    def __getitem__(self, key):
        return self.get_secure_cookie(key)

    def __setitem__(self, key, value):
        return self.set_secure_cookie(key, value)


class BaseHandler(tornado.web.RequestHandler):
    def render(self, filename, **template_values):
        """
        convenience function, performs monotonous operations
        required whenever a template needs to be rendered
        """
        if "to_console" not in list(template_values.keys()):
            template_values["to_console"] = {}

        super(BaseHandler, self).render(filename, **template_values)

    session = Session()

    # def dispatch(self):
    #     # Get a session store for this request.
    #     self.session_store = sessions.get_store(request=self.request)

    #     try:
    #         # Dispatch the request.
    #         webapp2.RequestHandler.dispatch(self)
    #     finally:
    #         # Save all sessions.
    #         self.session_store.save_sessions(self.response)

    # @webapp2.cached_property
    # def session(self):
    #     # Returns a session using the default cookie key.
    #     return self.session_store.get_session()


def reblog_path_source(hostname, post_id, client):
    cur_post = client.make_oauth_request(
        'http://api.tumblr.com/v2/blog/{hostname}.tumblr.com'
        '/posts?api_key={key}&id={id}&reblog_info=true'.format(
                hostname=hostname,
                key=client.get_api_key(),
                id=post_id))

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
            cur_post = client.make_oauth_request(
                'http://api.tumblr.com/v2/blog/{hostname}.tumblr.com'
                '/posts?api_key={key}&id={id}&reblog_info=true'.format(
                    hostname=hostname,
                    key=client.get_api_key(),
                    id=post_id))
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

            relations.append([cur_post['response']['posts'][0]['blog_name'],
                cur_post['response']['posts'][0]['reblogged_from_name']])

            logging.info('%s reblogged from %s' % (
                cur_post['response']['posts'][0]['blog_name'],
                cur_post['response']['posts'][0]['reblogged_from_name']))
            time.sleep(2)

    return (relations, hostname, post_id)


def reblog_path_sink(hostname, post_id, client):
    logging.info('This is going to be expensive. I hope you can afford it :P')
    cur_post = client.make_oauth_request(
        'http://api.tumblr.com/v2/blog/{hostname}.tumblr.com'
        '/posts?api_key={key}&id={id}&reblog_info=true'.format(
                hostname=hostname,
                key=client.get_api_key(),
                id=post_id))

    tree = {}
    logging.info(
        'Just to confirm, we are starting at the user %s '
        'and their post with id %s' % (hostname, post_id))

    while True:
        try:
            cur_post = client.make_oauth_request(
                'http://api.tumblr.com/v2/blog/{hostname}.tumblr.com'
                '/posts?api_key={key}&id={id}&reblog_info=true'.format(
                    hostname=hostname,
                    key=client.get_api_key(),
                    id=post_id))

        except requests.DownloadError:
            logging.info(
                'Try try again')  # ignore these errors, and try try again
        else:
            try:
                if ('reblogged_from_name' not in cur_post['response']['posts'][0] or
                    cur_post['response']['posts'][0]['reblogged_from_name'] ==
                    cur_post['response']['posts'][0]['blog_name']):
                    break
            except TypeError:
                logging.info('Not found? %s' % cur_post)
                break

            hostname = cur_post['response']['posts'][0]['reblogged_from_name']
            post_id = cur_post['response']['posts'][0]['reblogged_from_id']

            tree[post_id].append(
                [cur_post['response']['posts'][0]['blog_name'],
                cur_post['response']['posts'][0]['reblogged_from_name']])

            logging.info('%s reblogged from %s' % (
                cur_post['response']['posts'][0]['blog_name'],
                cur_post['response']['posts'][0]['reblogged_from_name']))

    return (tree, hostname, post_id)


def compute_d3_points(relations):
    if relations:
        id_relations = {}
        cur_id = 0
        unique = [x[0] for x in
            groupby(sorted(chain.from_iterable(relations)))]

        for frag in unique:
            if frag not in id_relations:
                id_relations[frag] = cur_id
                cur_id += 1

        output_json = {'links': [], 'nodes': []}

        for rel in unique:
            output_json['nodes'].append(
                {'name': rel, 'group': id_relations[rel]})

        for rel in relations:
            output_json['links'].append(
                {'source': id_relations[rel[0]],
                'target': id_relations[rel[1]],
                'value': 5})

        logging.info('Posts; %s' % len(output_json['nodes']))
        logging.info('Post links; %s' % len(output_json['links']))

        return output_json
    else:
        return


def compute_radial_d3_points(relations):
    if relations:
        id_relations = {}
        unique = [x[0] for x in
            groupby(sorted(chain.from_iterable(relations)))]

        for frag in unique:
            id_relations[frag] = {
                "name": frag,
                "imports": []}

        for rel in relations:
            id_relations[rel[0]]['imports'].append(rel[1])

        logging.info('Posts; %s' % len(id_relations))

        return list(id_relations.values())
    else:
        return

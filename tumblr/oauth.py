import logging
import urlparse
import oauth2 as oauth


class TumblrOAuthClient(object):
    REQUEST_TOKEN_URL = 'https://www.tumblr.com/oauth/request_token'
    AUTHORIZE_URL = 'https://www.tumblr.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://www.tumblr.com/oauth/access_token'
    XAUTH_ACCESS_TOKEN_URL = 'https://www.tumblr.com/oauth/access_token'
    request_token = {}

    def __init__(self, consumer_key, consumer_secret):
        self.consumer = oauth.Consumer(consumer_key, consumer_secret)

    def get_authorize_url(self):
        client = oauth.Client(self.consumer)
        resp, content = client.request(self.REQUEST_TOKEN_URL, "GET")
        if resp['status'] != '200':
            raise Exception("Invalid response %s." % resp['status'])

        self.request_token = dict(urlparse.parse_qsl(content))
        return "%s?oauth_token=%s" % (self.AUTHORIZE_URL,
            self.request_token['oauth_token'])

    def get_access_token(self, oauth_verifier, oauth_token=None, oauth_token_secret=None):
        # logging.info(oauth_verifier)
        # logging.info(oauth_token or self.request_token['oauth_token'])
        # logging.info(oauth_token_secret or self.request_token['oauth_token_secret'])
        token = oauth.Token(
            oauth_token or self.request_token['oauth_token'],
            oauth_token_secret or self.request_token['oauth_token_secret'])
        token.set_verifier(oauth_verifier)
        client = oauth.Client(self.consumer, token)

        resp, content = client.request(self.ACCESS_TOKEN_URL, "POST")
        # logging.info('Responce; %s' % resp)
        # logging.info('Content; %s' % content)
        access_token = dict(urlparse.parse_qsl(content))
        logging.info('access_token; %s' % access_token)
        if 'oauth_token' not in access_token:
            raise Exception(str(access_token))
        return oauth.Token(access_token['oauth_token'],
            access_token['oauth_token_secret'])

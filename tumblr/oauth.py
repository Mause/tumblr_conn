import logging
import urllib.parse

import requests
import oauthlib.oauth1
from requests_oauthlib import OAuth1


class TumblrOAuthClient(OAuth1):
    REQUEST_TOKEN_URL = 'https://www.tumblr.com/oauth/request_token'
    AUTHORIZE_URL = 'https://www.tumblr.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://www.tumblr.com/oauth/access_token'
    XAUTH_ACCESS_TOKEN_URL = 'https://www.tumblr.com/oauth/access_token'

    def get_authorize_url(self):
        r = requests.post(url=self.REQUEST_TOKEN_URL, auth=self)

        self.request_token = dict(urllib.parse.parse_qsl(r.text))
        params = {"oauth_token": self.request_token['oauth_token']}
        return self.AUTHORIZE_URL + "?" + urllib.parse.urlencode(params)

    def get_access_token(self, oauth_verifier, oauth_token=None,
            oauth_token_secret=None):
        # token = oauth.Token(
        # token = oauthlib.oauth2.draft25.tokens.BearerToken.create_token(
        #     oauth_token or self.request_token['oauth_token'],
        #     oauth_token_secret or self.request_token['oauth_token_secret'])
        # token.set_verifier(oauth_verifier)
        # client = oauthlib.oauth1.Client(self.consumer, token)

        resp = requests.post(self.ACCESS_TOKEN_URL, auth=self)
        logging.info('Responce; %s' % resp.text)
        # logging.info('Content; %s' % content)
        access_token = dict(urllib.parse.parse_qsl(resp.text))
        logging.info('access_token; %s' % access_token)
        if 'oauth_token' not in access_token:
            raise Exception(str(access_token))

        return oauthlib.oauth2.draft25.tokens.BearerToken.create_token(
            access_token['oauth_token'],
            access_token['oauth_token_secret'])



# class TumblrOAuthClient(object):
#     request_token = {}

#     def __init__(self, consumer_key, consumer_secret):
#         pass
#         # self.consumer = oauthlib.Consumer(consumer_key, consumer_secret)

#     def get_authorize_url(self):
#         client = oauthlib.oauth1.Client(self.consumer)
#         resp, content = client.request(self.REQUEST_TOKEN_URL, "GET")
#         if resp['status'] != '200':
#             raise Exception("Invalid response %s." % resp['status'])

#         self.request_token = dict(urllib.parse.parse_qsl(content))
#         return "%s?oauth_token=%s" % (self.AUTHORIZE_URL,
#             self.request_token['oauth_token'])

#     def get_access_token(self, oauth_verifier, oauth_token=None,
#             oauth_token_secret=None):
#         # token = oauth.Token(
#         token = oauthlib.oauth2.draft25.tokens.BearerToken.create_token(
#             oauth_token or self.request_token['oauth_token'],
#             oauth_token_secret or self.request_token['oauth_token_secret'])
#         token.set_verifier(oauth_verifier)
#         client = oauthlib.oauth1.Client(self.consumer, token)

#         resp, content = client.request(self.ACCESS_TOKEN_URL, "POST")
#         # logging.info('Responce; %s' % resp)
#         # logging.info('Content; %s' % content)
#         access_token = dict(urllib.parse.parse_qsl(content))
#         logging.info('access_token; %s' % access_token)
#         if 'oauth_token' not in access_token:
#             raise Exception(str(access_token))
#         return oauthlib.oauth2.draft25.tokens.BearerToken.create_token(
#             access_token['oauth_token'],
#             access_token['oauth_token_secret'])

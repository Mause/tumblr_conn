# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

"""
oauthlib.oauth1
~~~~~~~~~~~~~~

This module is a wrapper for the most recent implementation of OAuth 1.0 Client
and Server classes.
"""

from .rfc5849 import Client, Server
from .rfc5849 import SIGNATURE_HMAC, SIGNATURE_RSA, SIGNATURE_PLAINTEXT
from .rfc5849 import SIGNATURE_TYPE_AUTH_HEADER, SIGNATURE_TYPE_QUERY
from .rfc5849 import SIGNATURE_TYPE_BODY

# appease the linters
(Client, Server, SIGNATURE_HMAC, SIGNATURE_RSA, SIGNATURE_PLAINTEXT, SIGNATURE_TYPE_AUTH_HEADER, SIGNATURE_TYPE_QUERY, SIGNATURE_TYPE_BODY)
